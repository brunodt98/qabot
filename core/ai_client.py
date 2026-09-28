"""
QABot — AI Client
Gerencia a conexão com os backends de IA: Groq (online) e Ollama (local).
"""

import logging
import re
import time
from dataclasses import dataclass

import requests
from groq import Groq


# Teto de tokens da resposta. A análise devolve um JSON que cresce com o
# número de problemas encontrados: cada problema traz trecho original,
# correção e explicação. Com teto baixo a resposta é cortada no meio e o
# JSON fica inválido — o arquivo aparece como "erro ao processar" sem que
# o motivo real (o teto) fique visível.
MAX_TOKENS_ANALISE = 8000
MAX_TOKENS_CHAT = 2000

TEMPERATURA = 0.2

TIMEOUT_OLLAMA = 300


class ErroDeIA(RuntimeError):
    """Falha ao chamar o backend, com mensagem já legível para a interface."""


@dataclass
class RespostaIA:
    """Resposta do modelo com os metadados necessários para diagnóstico."""

    texto: str
    truncada: bool = False
    tokens_entrada: int = 0
    tokens_saida: int = 0
    segundos: float = 0.0

    @property
    def tokens_total(self) -> int:
        return self.tokens_entrada + self.tokens_saida


def build_groq_client(api_key: str) -> Groq | None:
    """Instancia e retorna o cliente Groq. Retorna None em caso de erro."""
    try:
        return Groq(api_key=api_key)
    except Exception as e:
        logging.error(f"Erro ao criar cliente Groq: {e}")
        return None


def test_ollama_connection(base_url: str = "http://localhost:11434") -> tuple[bool, list[str]]:
    """
    Testa conexão com Ollama local.
    Retorna (success, lista_de_modelos_disponíveis).
    """
    try:
        r = requests.get(f"{base_url}/api/tags", timeout=5)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
        return True, models
    except Exception as e:
        logging.error(f"Ollama offline: {e}")
        return False, []


def _teto_do_erro(e: Exception) -> int | None:
    """Extrai o limite de max_tokens que a API informou na recusa."""
    texto = str(e)

    if "max_tokens" not in texto:
        return None

    # A recusa vem no formato "max_tokens must be less than or equal to N".
    # Buscar qualquer numero pegaria o 400 do codigo HTTP, entao ancora-se
    # na frase.
    achado = re.search("less than or equal to ([0-9]+)", texto)

    return int(achado.group(1)) if achado else None


def _mensagem_de_erro_groq(e: Exception) -> str:
    """Traduz a exceção do SDK numa mensagem que diz o que fazer."""
    texto = str(e)
    codigo = getattr(getattr(e, "response", None), "status_code", None)

    if codigo == 401 or "invalid_api_key" in texto or "Invalid API Key" in texto:
        return "API Key da Groq inválida. Gere outra em console.groq.com."

    if codigo == 429 or "rate_limit" in texto:
        return ("Limite de uso da Groq atingido. Aguarde alguns instantes ou "
                "troque para um modelo menor na barra lateral.")

    if "model_terms_required" in texto:
        return ("Este modelo exige aceitar os termos de uso no painel da Groq "
                "antes do primeiro uso. Escolha outro modelo na lista ou "
                "aceite os termos em console.groq.com/playground.")

    if codigo == 413 or "too large" in texto.lower():
        return ("O arquivo excede o limite de contexto deste modelo. "
                "Analise-o em partes ou escolha um modelo com contexto maior.")

    return f"Falha ao chamar a Groq: {texto[:300]}"


def call_groq(client: Groq, model: str, messages: list[dict],
              max_tokens: int = MAX_TOKENS_ANALISE) -> RespostaIA:
    """Envia mensagens para a API Groq e devolve a resposta com metadados."""
    if client is None:
        raise ErroDeIA("Cliente Groq não configurado. Informe a API Key na barra lateral.")

    inicio = time.perf_counter()

    try:
        resposta = client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=TEMPERATURA,
            max_tokens=max_tokens,
        )
    except Exception as e:
        # Alguns modelos aceitam menos tokens de saida do que pedimos. Quando
        # o teto nao veio junto com a lista, a API recusa com 400 e informa o
        # limite: tenta uma vez com o valor aceito, em vez de desistir.
        limite = _teto_do_erro(e)
        if limite is None or limite >= max_tokens:
            raise ErroDeIA(_mensagem_de_erro_groq(e))
        try:
            resposta = client.chat.completions.create(
                messages=messages,
                model=model,
                temperature=TEMPERATURA,
                max_tokens=limite,
            )
        except Exception as e2:
            raise ErroDeIA(_mensagem_de_erro_groq(e2))

    segundos = time.perf_counter() - inicio

    escolha = resposta.choices[0]
    uso = getattr(resposta, "usage", None)

    return RespostaIA(
        texto=escolha.message.content or "",
        truncada=(escolha.finish_reason == "length"),
        tokens_entrada=getattr(uso, "prompt_tokens", 0) or 0,
        tokens_saida=getattr(uso, "completion_tokens", 0) or 0,
        segundos=segundos,
    )


def call_ollama(model: str, messages: list[dict],
                base_url: str = "http://localhost:11434",
                max_tokens: int = MAX_TOKENS_ANALISE) -> RespostaIA:
    """Envia mensagens para o Ollama local e devolve a resposta com metadados."""
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": TEMPERATURA, "num_predict": max_tokens},
    }

    inicio = time.perf_counter()

    try:
        r = requests.post(f"{base_url}/api/chat", json=payload, timeout=TIMEOUT_OLLAMA)
        r.raise_for_status()
    except requests.Timeout:
        raise ErroDeIA(
            f"O Ollama não respondeu em {TIMEOUT_OLLAMA}s. "
            "Modelos grandes em CPU podem passar disso — tente um modelo menor."
        )
    except requests.ConnectionError:
        raise ErroDeIA(
            f"Não foi possível conectar ao Ollama em {base_url}. "
            "Verifique se ele está em execução."
        )
    except requests.HTTPError as e:
        raise ErroDeIA(f"O Ollama respondeu com erro: {e}")

    segundos = time.perf_counter() - inicio
    dados = r.json()

    return RespostaIA(
        texto=dados.get("message", {}).get("content", "") or "",
        # O Ollama informa o motivo da parada em done_reason nas versões
        # recentes; quando ausente, assume-se resposta completa.
        truncada=(dados.get("done_reason") == "length"),
        tokens_entrada=dados.get("prompt_eval_count", 0) or 0,
        tokens_saida=dados.get("eval_count", 0) or 0,
        segundos=segundos,
    )


def call_ai(backend: str, client, model: str, messages: list[dict],
            ollama_url: str = "http://localhost:11434",
            max_tokens: int = MAX_TOKENS_ANALISE) -> RespostaIA:
    """
    Roteador unificado: chama Groq ou Ollama conforme backend selecionado.
    Devolve sempre um RespostaIA, e levanta ErroDeIA com mensagem legível.
    """
    if backend == "Groq":
        return call_groq(client, model, messages, max_tokens=max_tokens)
    return call_ollama(model, messages, base_url=ollama_url, max_tokens=max_tokens)


def listar_modelos_groq(api_key: str) -> tuple[list[str], dict[str, int], str | None]:
    """
    Pergunta a' Groq quais modelos esta chave pode usar, e o teto de saida
    de cada um.

    Lista fixa no codigo apodrece: a Groq aposenta e renomeia modelos, e o
    usuario so descobre com um 404 na hora de analisar. Aqui a lista vem do
    proprio servico, ja filtrada pelo que a chave tem acesso.

    O teto importa porque varia por modelo: pedir mais do que o modelo aceita
    e' recusado com 400 antes de gerar qualquer coisa.

    Devolve (modelos, tetos, erro). Em caso de falha, devolve ([], {}, msg)
    para que a interface possa cair na lista de reserva.
    """
    try:
        r = requests.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15,
        )
    except requests.RequestException as e:
        return [], {}, f"Nao foi possivel consultar os modelos: {e}"

    if r.status_code == 401:
        return [], {}, "API Key da Groq invalida."

    if r.status_code != 200:
        return [], {}, f"A Groq respondeu {r.status_code} ao listar modelos."

    dados = r.json().get("data", [])

    modelos = _filtrar_modelos_de_texto(dados)

    tetos = {}

    for m in dados:
        if not isinstance(m, dict) or m.get("id") not in modelos:
            continue
        # A Groq informa max_completion_tokens quando o teto de saida e'
        # menor que a janela de contexto. Sem o campo, fica o padrao.
        teto = m.get("max_completion_tokens") or m.get("context_window")
        if isinstance(teto, int) and teto > 0:
            tetos[m["id"]] = teto

    return modelos, tetos, None


# Familias que a conta expoe mas que nao geram texto (fala, transcricao) ou
# que servem a outro proposito (moderacao). Escolher uma delas so produz erro
# na hora de analisar.
FAMILIAS_NAO_TEXTUAIS = (
    "whisper", "tts", "speech", "orpheus", "playai", "audio",
    "guard", "moderation", "prompt-guard",
)

# Preferidos aparecem primeiro, para que o seletor ja abra num modelo que
# funciona. O resto vem depois, em ordem alfabetica.
PREFERIDOS = (
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
)


def _filtrar_modelos_de_texto(dados: list) -> list[str]:
    """Mantem so modelos de texto e poe os preferidos no topo."""
    ids = [
        m["id"] for m in dados
        if isinstance(m, dict) and m.get("id")
        and m.get("active", True)
        and not any(f in m["id"].lower() for f in FAMILIAS_NAO_TEXTUAIS)
    ]

    topo = [m for m in PREFERIDOS if m in ids]
    resto = sorted(m for m in ids if m not in topo)

    return topo + resto

"""
QABot — Analyzer
Define os prompts do sistema e a lógica de parsing das respostas da IA.
"""

import json
import re
from dataclasses import dataclass

from core.ai_client import MAX_TOKENS_ANALISE, ErroDeIA, call_ai

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT — Análise de Arquivo
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT_ANALYSIS = """
Você é o QABot, um especialista sênior em Garantia de Qualidade de Software (QA).

Sua tarefa é analisar o código fornecido e retornar uma resposta EXCLUSIVAMENTE em JSON válido,
sem nenhum texto antes ou depois do JSON.

O JSON deve seguir EXATAMENTE este schema:
{
  "resumo": "string — diagnóstico geral em 2-3 frases objetivas",
  "score_qualidade": <inteiro 0-100>,
  "classificacao_dificuldade": "Fácil" | "Médio" | "Difícil",
  "justificativa_dificuldade": "string — explique em 1 frase o porquê",
  "problemas": [
    {
      "id": <inteiro sequencial>,
      "tipo": "erro" | "aviso" | "segurança" | "performance" | "estilo",
      "severidade": "crítico" | "alto" | "médio" | "baixo",
      "linha_inicio": <inteiro ou null>,
      "linha_fim": <inteiro ou null>,
      "titulo": "string curta — nome do problema",
      "descricao": "string — o que está errado e por quê é um problema",
      "trecho_original": "string — copie o trecho EXATO do código com o erro (máx 5 linhas)",
      "correcao_sugerida": "string — versão corrigida do mesmo trecho",
      "explicacao_correcao": "string — explique o que mudou e por quê"
    }
  ],
  "pontos_positivos": ["string", "string"],
  "recomendacoes_gerais": ["string", "string"]
}

REGRAS DE CLASSIFICAÇÃO DE DIFICULDADE — siga rigorosamente:
- "Fácil": código simples, curto, erros apenas de estilo ou boas práticas (imports não usados, variáveis não usadas, prints de debug). Nenhuma vulnerabilidade de segurança.
- "Médio": código moderadamente complexo, erros que podem causar falhas em tempo de execução, credenciais hardcoded, falta de tratamento de exceções, lógica incorreta.
- "Difícil": código complexo com vulnerabilidades críticas de segurança como SQL Injection, execução arbitrária de comandos (os.system/eval/exec com input externo), exposição de senhas em logs, recursão infinita, race conditions ou falhas que comprometem a integridade do sistema.

REGRAS DE SCORE — siga rigorosamente:
- Problemas de estilo/boas práticas: score entre 70-90
- Problemas de qualidade/lógica: score entre 40-69
- Vulnerabilidades críticas de segurança: score entre 0-39

REGRAS OBRIGATÓRIAS:
- Sempre copie o trecho_original EXATAMENTE como está no código — não invente.
- Se não houver linha definida, use null.
- O score_qualidade deve refletir a gravidade dos problemas encontrados.
- Se não houver problemas, retorne "problemas": [].
- Nunca adicione texto fora do JSON. Apenas o JSON.
"""

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT — Chat QA
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT_CHAT = """
Você é o QABot, um especialista em Garantia de Qualidade de Software (QA).
Responda perguntas sobre: testes, boas práticas de código, CI/CD, segurança, 
padrões de projeto, refatoração, cobertura de testes e qualidade de software em geral.
Seja direto, técnico e didático. Use português do Brasil.
Quando mostrar código, use blocos de código com a linguagem correta.
"""


def build_analysis_messages(filename: str, language: str, content: str) -> list[dict]:
    """Monta o payload de mensagens para análise de um arquivo."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT_ANALYSIS},
        {
            "role": "user",
            "content": (
                f"Analise o arquivo `{filename}` (linguagem: {language}).\n\n"
                f"```{language}\n{content}\n```\n\n"
                f"Retorne apenas o JSON conforme o schema solicitado."
            ),
        },
    ]


def parse_analysis_response(raw: str) -> dict | None:
    """
    Extrai e parseia o JSON da resposta da IA.
    Retorna o dict ou None se falhar.
    """
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        pass

    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(raw[start:end])
        except json.JSONDecodeError:
            pass

    return None


def get_severity_rank(severidade: str) -> int:
    """Retorna rank numérico para ordenar por severidade."""
    return {"crítico": 0, "alto": 1, "médio": 2, "baixo": 3}.get(severidade, 4)


# ─────────────────────────────────────────────────────────────────────────────
# NORMALIZAÇÃO DO RESULTADO
# ─────────────────────────────────────────────────────────────────────────────

TIPOS_VALIDOS = {"erro", "aviso", "segurança", "performance", "estilo"}
SEVERIDADES_VALIDAS = {"crítico", "alto", "médio", "baixo"}
DIFICULDADES_VALIDAS = {"Fácil", "Médio", "Difícil"}


def _texto(valor, padrao: str = "") -> str:
    """Devolve sempre string. O modelo às vezes manda null ou número."""
    if valor is None:
        return padrao
    return str(valor)


def _inteiro(valor, padrao: int = 0, minimo: int = 0, maximo: int = 100) -> int:
    try:
        return max(minimo, min(maximo, int(float(valor))))
    except (TypeError, ValueError):
        return padrao


def _linha(valor) -> int | None:
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _lista_de_textos(valor) -> list[str]:
    if not isinstance(valor, list):
        return []
    return [_texto(v) for v in valor if v is not None]


def normalizar_analise(data: dict | None) -> dict | None:
    """
    Garante que o resultado tem os campos e os TIPOS que a renderização espera.

    O parsing só assegura que o JSON é válido, não que ele segue o schema: o
    modelo pode mandar `problemas` como lista de strings, `linha_inicio` como
    texto ou `trecho_original` como null. Sem isso, o erro só aparece na hora
    de desenhar a tela.
    """
    if not isinstance(data, dict):
        return None

    problemas = []

    for i, bruto in enumerate(data.get("problemas") or [], start=1):
        if not isinstance(bruto, dict):
            # Modelo devolveu texto solto no lugar do objeto: preserva o
            # conteúdo como descrição em vez de descartar o achado.
            problemas.append({
                "id": i,
                "tipo": "aviso",
                "severidade": "médio",
                "linha_inicio": None,
                "linha_fim": None,
                "titulo": "Problema relatado sem estrutura",
                "descricao": _texto(bruto),
                "trecho_original": "",
                "correcao_sugerida": "",
                "explicacao_correcao": "",
            })
            continue

        tipo = _texto(bruto.get("tipo"), "aviso").lower()
        severidade = _texto(bruto.get("severidade"), "médio").lower()

        problemas.append({
            "id": _inteiro(bruto.get("id"), i, minimo=1, maximo=10_000),
            "tipo": tipo if tipo in TIPOS_VALIDOS else "aviso",
            "severidade": severidade if severidade in SEVERIDADES_VALIDAS else "médio",
            "linha_inicio": _linha(bruto.get("linha_inicio")),
            "linha_fim": _linha(bruto.get("linha_fim")),
            "titulo": _texto(bruto.get("titulo"), "Problema"),
            "descricao": _texto(bruto.get("descricao")),
            "trecho_original": _texto(bruto.get("trecho_original")),
            "correcao_sugerida": _texto(bruto.get("correcao_sugerida")),
            "explicacao_correcao": _texto(bruto.get("explicacao_correcao")),
        })

    dificuldade = _texto(data.get("classificacao_dificuldade"), "Médio").capitalize()

    if dificuldade not in DIFICULDADES_VALIDAS:
        dificuldade = "Médio"

    return {
        "resumo": _texto(data.get("resumo")),
        "score_qualidade": _inteiro(data.get("score_qualidade"), 0),
        "classificacao_dificuldade": dificuldade,
        "justificativa_dificuldade": _texto(data.get("justificativa_dificuldade")),
        "problemas": problemas,
        "pontos_positivos": _lista_de_textos(data.get("pontos_positivos")),
        "recomendacoes_gerais": _lista_de_textos(data.get("recomendacoes_gerais")),
    }


def build_retry_messages(mensagens_originais: list[dict], resposta_invalida: str) -> list[dict]:
    """
    Monta uma segunda tentativa quando a primeira resposta não era JSON válido.

    Em vez de repetir a mesma pergunta, devolve ao modelo o que ele respondeu
    e pede a correção — o que costuma bastar quando o erro foi texto extra
    em volta do JSON.
    """
    return mensagens_originais + [
        {"role": "assistant", "content": resposta_invalida[:2000]},
        {
            "role": "user",
            "content": (
                "Sua resposta anterior não é um JSON válido. Reescreva-a "
                "seguindo exatamente o schema pedido, começando com { e "
                "terminando com }, sem nenhum texto antes ou depois, sem "
                "cercas de código e sem comentários."
            ),
        },
    ]


# ─────────────────────────────────────────────────────────────────────────────
# ORQUESTRAÇÃO DA ANÁLISE
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ResultadoAnalise:
    """Resultado de analisar um arquivo, com o diagnóstico do que aconteceu."""

    nome: str
    linguagem: str
    dados: dict | None = None
    erro: str | None = None
    bruto: str = ""
    truncada: bool = False
    tentativas: int = 1
    segundos: float = 0.0
    tokens_entrada: int = 0
    tokens_saida: int = 0

    @property
    def ok(self) -> bool:
        return self.dados is not None

    @property
    def tokens_total(self) -> int:
        return self.tokens_entrada + self.tokens_saida


def _teto(ai_cfg: dict) -> int:
    """Teto de saida a pedir: o do modelo, quando menor que o nosso padrao."""
    do_modelo = ai_cfg.get("max_tokens")

    if isinstance(do_modelo, int) and do_modelo > 0:
        return min(do_modelo, MAX_TOKENS_ANALISE)

    return MAX_TOKENS_ANALISE


def analisar_conteudo(ai_cfg: dict, filename: str, language: str,
                      content: str) -> ResultadoAnalise:
    """
    Analisa um arquivo de ponta a ponta: monta o prompt, chama o modelo,
    tenta interpretar o JSON e, se falhar, faz UMA nova tentativa pedindo a
    correção do formato.

    Nunca levanta exceção: devolve sempre um ResultadoAnalise, com `erro`
    preenchido quando não deu certo, para que um arquivo problemático não
    interrompa a análise em lote.
    """
    mensagens = build_analysis_messages(filename, language, content)

    resultado = ResultadoAnalise(nome=filename, linguagem=language)

    try:
        resposta = call_ai(
            ai_cfg["backend"], ai_cfg.get("client"), ai_cfg["model"],
            mensagens, ai_cfg.get("ollama_url", "http://localhost:11434"),
            max_tokens=_teto(ai_cfg),
        )
    except ErroDeIA as e:
        resultado.erro = str(e)
        return resultado
    except Exception as e:
        resultado.erro = f"Erro inesperado: {type(e).__name__}: {e}"
        return resultado

    resultado.bruto = resposta.texto
    resultado.truncada = resposta.truncada
    resultado.segundos = resposta.segundos
    resultado.tokens_entrada = resposta.tokens_entrada
    resultado.tokens_saida = resposta.tokens_saida

    dados = normalizar_analise(parse_analysis_response(resposta.texto))

    if dados is not None:
        resultado.dados = dados
        return resultado

    # A resposta veio cortada no teto de tokens: repetir não adianta, o
    # segundo corte cairia no mesmo lugar. Reportar a causa real.
    if resposta.truncada:
        resultado.erro = (
            "A resposta do modelo foi cortada por atingir o limite de tokens. "
            "Isso costuma acontecer quando o arquivo tem muitos problemas. "
            "Analise-o em partes ou escolha um modelo com saída maior."
        )
        return resultado

    # Formato inválido sem truncamento: normalmente é texto em volta do
    # JSON, e uma segunda tentativa pedindo a correção resolve.
    resultado.tentativas = 2

    try:
        retry = call_ai(
            ai_cfg["backend"], ai_cfg.get("client"), ai_cfg["model"],
            build_retry_messages(mensagens, resposta.texto),
            ai_cfg.get("ollama_url", "http://localhost:11434"),
            max_tokens=_teto(ai_cfg),
        )
    except ErroDeIA as e:
        resultado.erro = str(e)
        return resultado
    except Exception as e:
        resultado.erro = f"Erro inesperado na segunda tentativa: {e}"
        return resultado

    resultado.segundos += retry.segundos
    resultado.tokens_entrada += retry.tokens_entrada
    resultado.tokens_saida += retry.tokens_saida
    resultado.truncada = resultado.truncada or retry.truncada

    dados = normalizar_analise(parse_analysis_response(retry.texto))

    if dados is None:
        resultado.bruto = retry.texto
        resultado.erro = (
            "O modelo não devolveu JSON válido em duas tentativas. "
            "Modelos menores costumam falhar nisso — tente um modelo maior "
            "na barra lateral."
        )
        return resultado

    resultado.dados = dados
    return resultado

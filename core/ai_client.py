"""
QABot — AI Client
Gerencia a conexão com os backends de IA: Groq (online) e Ollama (local).
"""

import requests
import logging
from groq import Groq


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


def call_groq(client: Groq, model: str, messages: list[dict]) -> str:
    """Envia mensagens para a API Groq e retorna o texto da resposta."""
    response = client.chat.completions.create(
        messages=messages,
        model=model,
        temperature=0.2,
        max_tokens=3000,
    )
    return response.choices[0].message.content


def call_ollama(model: str, messages: list[dict],
                base_url: str = "http://localhost:11434") -> str:
    """Envia mensagens para o Ollama local e retorna o texto da resposta."""
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.2},
    }
    r = requests.post(f"{base_url}/api/chat", json=payload, timeout=180)
    r.raise_for_status()
    return r.json()["message"]["content"]


def call_ai(backend: str, client, model: str,
            messages: list[dict], ollama_url: str = "http://localhost:11434") -> str:
    """
    Roteador unificado: chama Groq ou Ollama conforme backend selecionado.
    """
    if backend == "Groq":
        return call_groq(client, model, messages)
    else:
        return call_ollama(model, messages, base_url=ollama_url)

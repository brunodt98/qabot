"""QABot — Sidebar"""

import streamlit as st

from core.ai_client import (
    build_groq_client,
    listar_modelos_groq,
    test_ollama_connection,
)
from ui import theme


# Lista de reserva, usada só quando a consulta à API falha. Pode estar
# desatualizada: a lista boa é a que a própria Groq devolve para a chave.
GROQ_MODELOS_RESERVA = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]


@st.cache_data(show_spinner=False, ttl=600)
def _modelos_da_chave(api_key: str) -> tuple[list[str], dict[str, int], str | None]:
    """Cacheia a lista por chave, para não consultar a cada rerun."""
    return listar_modelos_groq(api_key)


def _render_groq() -> tuple[object, str | None, int | None, bool]:
    """Controles do backend Groq. Devolve (client, modelo, teto, pronto)."""
    api_key = st.text_input(
        "API Key Groq",
        type="password",
        help="Gratuita em console.groq.com/keys. A chave começa com gsk_.",
    )

    if not api_key:
        st.caption(
            "Crie uma chave gratuita em "
            "[console.groq.com/keys](https://console.groq.com/keys) — "
            "não pede cartão."
        )
        st.selectbox("Modelo", GROQ_MODELOS_RESERVA, disabled=True)
        return None, None, None, False

    client = build_groq_client(api_key)

    if client is None:
        st.error("Não foi possível criar o cliente com essa chave.")
        return None, None, None, False

    modelos, tetos, erro = _modelos_da_chave(api_key)

    if erro:
        st.error(erro)
        st.caption("Usando a lista de reserva — pode conter modelo aposentado.")
        modelos = GROQ_MODELOS_RESERVA
        tetos = {}
    else:
        st.success(f"Conectado. {len(modelos)} modelos disponíveis.")

    modelo = st.selectbox(
        "Modelo",
        modelos,
        help="Lista obtida da própria Groq, já filtrada pelo que esta chave acessa.",
    )

    teto = tetos.get(modelo)

    if teto:
        st.caption(f"Saída máxima deste modelo: {teto:,} tokens.".replace(",", "."))

    return client, modelo, teto, True


def _render_ollama() -> tuple[str, str | None, bool]:
    """Controles do backend Ollama. Devolve (url, modelo, pronto)."""
    ollama_url = st.text_input("Endereço", value="http://localhost:11434")

    modelos_locais = st.session_state.get("ollama_modelos", [])

    if st.button("Buscar modelos instalados"):
        ok, modelos = test_ollama_connection(ollama_url)
        if ok:
            st.session_state["ollama_modelos"] = modelos
            modelos_locais = modelos
        else:
            st.session_state["ollama_modelos"] = []
            st.error("O Ollama não respondeu neste endereço. Ele está rodando?")

    if modelos_locais:
        modelo = st.selectbox("Modelo", modelos_locais)
        st.caption(f"{len(modelos_locais)} modelo(s) instalado(s) nesta máquina.")
    else:
        modelo = st.text_input("Modelo", value="llama3")
        st.caption(
            "Instale um modelo com `ollama pull llama3` e clique em "
            "buscar para escolher da lista."
        )

    return ollama_url, modelo, bool(modelo and ollama_url)


def render_sidebar() -> dict:
    with st.sidebar:
        theme.marca_lateral("QABot", "Qualidade de código")

        st.markdown("<div class='side-rule'></div>", unsafe_allow_html=True)
        st.markdown("<div class='side-lbl'>Motor de IA</div>", unsafe_allow_html=True)

        escolha = st.selectbox(
            "Backend",
            ["Groq — online, gratuito", "Ollama — local, offline"],
            label_visibility="collapsed",
        )

        backend = "Groq" if "Groq" in escolha else "Ollama"

        client = None
        ollama_url = "http://localhost:11434"

        if backend == "Groq":
            client, model, max_tokens, ready = _render_groq()
        else:
            ollama_url, model, ready = _render_ollama()
            max_tokens = None

        st.markdown("<div class='side-rule'></div>", unsafe_allow_html=True)

        theme.rodape_lateral(
            "FT",
            "<b>Bruno Silva</b><br>Ciência de Dados · FATEC Cotia<br>"
            "Parceiro: Outtech Services IT",
        )

    return {
        "backend": backend,
        "client": client,
        "model": model,
        "ollama_url": ollama_url,
        "max_tokens": max_tokens,
        "ready": ready,
    }

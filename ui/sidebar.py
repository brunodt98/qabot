"""QABot — Sidebar"""

import streamlit as st
from core.ai_client import build_groq_client, test_ollama_connection
from ui import theme

GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama3-70b-8192",
    "mixtral-8x7b-32768",
    "llama3-8b-8192",
]

def render_sidebar() -> dict:
    with st.sidebar:
        theme.marca_lateral("QABot", "Qualidade de código")

        st.markdown("<div class='side-rule'></div>", unsafe_allow_html=True)
        st.markdown("<div class='side-lbl'>Motor de IA</div>", unsafe_allow_html=True)

        backend_choice = st.selectbox(
            "Backend",
            ["Groq — online, gratuito", "Ollama — local, offline"],
        )
        backend = "Groq" if "Groq" in backend_choice else "Ollama"

        client = None
        model  = None
        ollama_url = "http://localhost:11434"
        ready  = False

        if backend == "Groq":
            api_key = st.text_input("API Key Groq", type="password",
                                    help="Gratuita em console.groq.com/keys")
            model = st.selectbox("Modelo", GROQ_MODELS)

            if api_key:
                client = build_groq_client(api_key)
                if client:
                    st.success("✅ Groq conectado!")
                    ready = True
                else:
                    st.error("❌ Chave inválida.")
            else:
                st.info("Insira sua API Key para começar.\n\nhttps://console.groq.com/keys")
        else:
            ollama_url = st.text_input("URL Ollama", value="http://localhost:11434")
            model      = st.text_input("Modelo", value="llama3")
            if st.button("Testar conexão"):
                ok, modelos = test_ollama_connection(ollama_url)
                if ok:
                    st.success(f"Conectado. Modelos: {', '.join(modelos[:3])}")
                    ready = True
                else:
                    st.error("Ollama não respondeu neste endereço.")
            if model and ollama_url:
                ready = True

        st.divider()
        st.markdown("**Sobre o QABot**")
        st.markdown("Projeto Integrador · FATEC Cotia\nCiência de Dados · 2024\n\nParceiro: **Outtech Services IT**")
        st.caption("v2.0")

    return {"backend": backend, "client": client, "model": model,
            "ollama_url": ollama_url, "ready": ready}

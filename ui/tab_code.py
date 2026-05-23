"""QABot — Tab: Analisar Código"""

import streamlit as st
from core.analyzer import build_analysis_messages, parse_analysis_response
from core.ai_client import call_ai
from utils.helpers import render_full_analysis

LANGUAGES = {
    "Python": "python", "JavaScript": "javascript", "TypeScript": "typescript",
    "Java": "java", "C#": "csharp", "C/C++": "cpp", "Go": "go",
    "SQL": "sql", "Shell/Bash": "bash", "HTML": "html", "CSS": "css",
    "JSON": "json", "YAML": "yaml",
}


def render_tab_code(ai_cfg: dict):
    st.markdown("#### 📝 Cole um trecho de código para análise rápida")
    st.caption("O QABot identifica erros com localização exata, mostra o código problemático, a correção e explica em linguagem simples.")

    col1, col2 = st.columns([1, 2])
    with col1:
        lang_name = st.selectbox("Linguagem", list(LANGUAGES.keys()))
        filename  = st.text_input("Nome do arquivo", value=f"trecho.{LANGUAGES[lang_name][:2]}")
    with col2:
        st.info("💡 **Dica:** quanto mais contexto você fornecer (imports, funções completas), mais precisa será a análise.")

    lang = LANGUAGES[lang_name]
    code_input = st.text_area("Cole o código aqui:", height=300,
                              placeholder=f"# Cole seu código {lang_name} aqui...")

    if st.button("🔬 Analisar", type="primary", use_container_width=True):
        if not code_input.strip():
            st.warning("Cole um trecho de código antes de analisar.")
            return
        if not ai_cfg["ready"]:
            st.error("Configure a IA na barra lateral.")
            return

        with st.spinner("🔍 Analisando..."):
            messages = build_analysis_messages(filename, lang, code_input)
            try:
                raw  = call_ai(ai_cfg["backend"], ai_cfg["client"],
                               ai_cfg["model"], messages, ai_cfg["ollama_url"])
                data = parse_analysis_response(raw)
                if data:
                    st.divider()
                    render_full_analysis(data, filename, lang)
                else:
                    st.warning("A IA não retornou resposta estruturada. Resposta bruta:")
                    st.code(raw, language="text")
            except Exception as e:
                st.error(f"Erro ao comunicar com a IA: {e}")

"""QABot — Tab: Analisar Código"""

import streamlit as st
from core.analyzer import analisar_conteudo
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
            res = analisar_conteudo(ai_cfg, filename, lang, code_input)

        if res.ok:
            st.divider()
            render_full_analysis(res.dados, filename, lang)
            st.caption(
                f"⏱️ {res.segundos:.1f}s · {res.tokens_total} tokens"
                + (f" · {res.tentativas} tentativas" if res.tentativas > 1 else "")
            )
        else:
            st.error(res.erro)
            if res.bruto:
                with st.expander("Resposta bruta do modelo"):
                    st.code(res.bruto, language="text")

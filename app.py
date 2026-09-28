"""
QABot — Ponto de entrada
Execute: streamlit run app.py
"""
import streamlit as st

st.set_page_config(
    page_title="QABot — análise de qualidade de código",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from ui import theme  # noqa: E402

theme.aplicar()

from ui.sidebar     import render_sidebar   # noqa: E402
from ui.tab_project import render_tab_project  # noqa: E402
from ui.tab_code    import render_tab_code     # noqa: E402
from ui.tab_chat    import render_tab_chat     # noqa: E402

ai_cfg = render_sidebar()

theme.cabecalho(
    "Análise de qualidade de código",
    "QABot",
    "Revisa código-fonte com um modelo de linguagem e devolve um laudo "
    "estruturado: cada problema com a linha, o trecho original, a correção "
    "sugerida e a explicação do que mudou.",
)

theme.regua()

tab1, tab2, tab3 = st.tabs(["Analisar projeto", "Analisar código", "Chat QA"])

with tab1:
    render_tab_project(ai_cfg)
with tab2:
    render_tab_code(ai_cfg)
with tab3:
    render_tab_chat(ai_cfg)

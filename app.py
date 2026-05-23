"""
QABot — Ponto de entrada
Execute: streamlit run app.py
"""
import streamlit as st

st.set_page_config(
    page_title="QABot",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background-color: #0f1117; }
    section[data-testid="stSidebar"] { background-color: #141820; }
    div[data-testid="stExpander"] { background-color: #141820; border: 1px solid #1e2a3a; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

from ui.sidebar     import render_sidebar
from ui.tab_project import render_tab_project
from ui.tab_code    import render_tab_code
from ui.tab_chat    import render_tab_chat

st.markdown("# 🛡️ QABot")
st.caption("Assistente de Qualidade de Software com Inteligência Artificial · FATEC Cotia × Outtech Services IT")
st.divider()

ai_cfg = render_sidebar()

tab1, tab2, tab3 = st.tabs(["📁  Analisar Projeto", "📝  Analisar Código", "💬  Chat QA"])

with tab1:
    render_tab_project(ai_cfg)
with tab2:
    render_tab_code(ai_cfg)
with tab3:
    render_tab_chat(ai_cfg)

st.divider()
st.caption("🛡️ QABot v2.0 · Projeto Integrador FATEC Cotia · Ciência de Dados · 2024 · Outtech Services IT")

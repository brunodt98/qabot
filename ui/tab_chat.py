"""QABot — Tab: Chat QA"""

import streamlit as st
from core.analyzer import SYSTEM_PROMPT_CHAT
from core.ai_client import call_ai


def render_tab_chat(ai_cfg: dict):
    st.markdown("#### 💬 Tire dúvidas sobre qualidade de software")
    st.caption("Pergunte sobre testes, CI/CD, boas práticas, padrões de projeto, segurança e muito mais.")

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🗑️ Limpar", use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Pergunta sobre QA, testes, boas práticas...")
    if not prompt:
        return

    if not ai_cfg["ready"]:
        st.error("Configure a IA na barra lateral.")
        return

    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    api_msgs = [{"role": "system", "content": SYSTEM_PROMPT_CHAT}]
    api_msgs += st.session_state.chat_messages

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                resp = call_ai(ai_cfg["backend"], ai_cfg["client"],
                               ai_cfg["model"], api_msgs, ai_cfg["ollama_url"])
                st.markdown(resp)
                st.session_state.chat_messages.append(
                    {"role": "assistant", "content": resp})
            except Exception as e:
                st.error(f"Erro: {e}")

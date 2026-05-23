"""QABot — Tab: Analisar Projeto"""

import pathlib
import streamlit as st
from core.file_scanner import scan_project, read_file, get_language_from_ext, build_file_tree
from core.analyzer import build_analysis_messages, parse_analysis_response
from core.ai_client import call_ai
from utils.helpers import render_full_analysis, render_file_tree


def render_tab_project(ai_cfg: dict):

    with st.expander("ℹ️ Como usar — clique para ver o passo a passo"):
        st.markdown("""
**1.** Cole o caminho da pasta do projeto no campo abaixo
- Windows: `C:/Users/silva/Downloads/knimepy`
- Mac/Linux: `/home/silva/projetos/knimepy`

**2.** Clique em **🔍 Escanear** — o QABot lista todos os arquivos de código

**3.** Selecione quais arquivos analisar (ou clique em "Todos")

**4.** Clique em **▶️ Iniciar Análise** e aguarde

**O QABot retorna para cada arquivo:**
- 📊 Score de qualidade (0–100)
- 🔍 Localização exata de cada erro (linha + trecho do código)
- ✅ Correção sugerida com exemplo de código
- 💡 Explicação simples de por que é um problema
        """)

    st.markdown("#### 📁 Passo 1 — Informe a pasta do projeto")

    col_path, col_btn = st.columns([5, 1])
    with col_path:
        folder_path = st.text_input(
            "Caminho",
            placeholder="Ex: C:/Users/silva/Downloads/knimepy",
            label_visibility="collapsed",
        )
    with col_btn:
        scan_btn = st.button("🔍 Escanear", use_container_width=True)

    if scan_btn and folder_path:
        with st.spinner("Escaneando arquivos..."):
            files, err = scan_project(folder_path)

        if err:
            st.error(err)
            st.caption("Dica: verifique se o caminho existe e use barras normais `/` no Windows também.")
            return

        if not files:
            st.warning("Nenhum arquivo de código encontrado nessa pasta.")
            st.caption("Formatos suportados: .py .js .ts .java .cs .go .sql .html .css .json .yaml .md .sh")
            return

        st.session_state["proj_files"]   = files
        st.session_state["proj_root"]    = folder_path
        st.session_state["proj_results"] = {}
        st.success(f"✅ {len(files)} arquivo(s) encontrado(s)!")

    if "proj_files" not in st.session_state:
        return

    files: list[pathlib.Path] = st.session_state["proj_files"]
    root: str                 = st.session_state["proj_root"]

    st.divider()
    st.markdown("#### 📂 Passo 2 — Arquivos encontrados")
    tree = build_file_tree(files, root)
    render_file_tree(tree, root)

    st.divider()
    st.markdown("#### ✅ Passo 3 — Selecione os arquivos para analisar")

    file_options = [str(f.relative_to(root)) for f in files]
    col_sel, col_all = st.columns([4, 1])
    with col_sel:
        selected = st.multiselect("Arquivos:", options=file_options,
                                  label_visibility="collapsed")
    with col_all:
        if st.button("Todos ✅", use_container_width=True):
            selected = file_options
            st.session_state["_sel_all"] = file_options

    if "proj_results" not in st.session_state:
        st.session_state["proj_results"] = {}

    if not selected and "_sel_all" in st.session_state:
        selected = st.session_state["_sel_all"]

    if selected:
        st.caption(f"✅ {len(selected)} arquivo(s) selecionado(s)")

    st.divider()
    st.markdown("#### ▶️ Passo 4 — Analisar com IA")

    if not ai_cfg["ready"]:
        st.warning("⚠️ Configure a IA na barra lateral antes de continuar.")
        return

    if not selected:
        st.caption("Selecione ao menos um arquivo no passo anterior.")
        return

    if st.button("▶️ Iniciar Análise com IA", type="primary", use_container_width=True):
        selected_paths = [f for f in files if str(f.relative_to(root)) in selected]
        results = {}
        progress = st.progress(0)

        for i, fpath in enumerate(selected_paths):
            progress.progress((i + 1) / len(selected_paths),
                              text=f"🔍 Analisando {fpath.name} ({i+1}/{len(selected_paths)})...")
            content  = read_file(fpath)
            lang     = get_language_from_ext(fpath.suffix)
            messages = build_analysis_messages(fpath.name, lang, content)
            try:
                raw  = call_ai(ai_cfg["backend"], ai_cfg["client"],
                               ai_cfg["model"], messages, ai_cfg["ollama_url"])
                data = parse_analysis_response(raw)
                results[str(fpath.relative_to(root))] = {
                    "data": data, "raw": raw, "lang": lang, "name": fpath.name
                }
            except Exception as e:
                results[str(fpath.relative_to(root))] = {
                    "data": None, "raw": str(e), "lang": lang, "name": fpath.name
                }

        progress.progress(1.0, text="✅ Concluído!")
        st.session_state["proj_results"] = results
        st.success(f"🎉 {len(results)} arquivo(s) analisado(s)! Veja os resultados abaixo.")

    results = st.session_state.get("proj_results", {})
    if not results:
        return

    st.divider()
    st.markdown(f"## 📊 Resultados — {len(results)} arquivo(s)")

    for rel_path, res in results.items():
        if res["data"]:
            render_full_analysis(res["data"], res["name"], res["lang"])
        else:
            with st.expander(f"⚠️ {res['name']} — erro ao processar"):
                st.error("A IA não retornou resposta estruturada para este arquivo.")
                st.caption("Isso pode acontecer com arquivos muito grandes. Tente analisá-lo individualmente.")
                st.code(res["raw"], language="text")

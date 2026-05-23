"""QABot — Tab: Analisar Projeto"""

import pathlib
import zipfile
import tempfile
import io
import streamlit as st
from core.file_scanner import scan_project, read_file, get_language_from_ext, build_file_tree
from core.analyzer import build_analysis_messages, parse_analysis_response
from core.ai_client import call_ai
from utils.helpers import render_full_analysis, render_file_tree

EXTENSIONS_ALLOWED = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cs",
    ".cpp", ".c", ".go", ".rb", ".php", ".html", ".css",
    ".json", ".yaml", ".yml", ".md", ".sql", ".sh"
}

MAX_CHARS_PER_FILE = 8_000


def _read_uploaded_content(content: bytes, filename: str) -> str:
    """Lê bytes de um arquivo e retorna string com limite de caracteres."""
    try:
        text = content.decode("utf-8", errors="ignore")
        if len(text) > MAX_CHARS_PER_FILE:
            text = text[:MAX_CHARS_PER_FILE] + "\n\n[... arquivo truncado ...]"
        return text
    except Exception as e:
        return f"[Erro ao ler arquivo: {e}]"


def _process_zip(uploaded_zip) -> tuple[list[dict], str | None]:
    """
    Extrai arquivos do ZIP e retorna lista de dicts:
    {name, relative_path, ext, size_kb, content}
    """
    files = []
    try:
        with zipfile.ZipFile(uploaded_zip, "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                p = pathlib.PurePosixPath(info.filename)
                ignore_dirs = {"__pycache__", ".git", "node_modules", ".venv",
                               "venv", "env", "dist", "build", ".idea", ".vscode"}
                if any(part in ignore_dirs for part in p.parts):
                    continue
                ext = p.suffix.lower()
                if ext not in EXTENSIONS_ALLOWED:
                    continue
                if info.file_size > 500_000:
                    continue
                content_bytes = zf.read(info.filename)
                content = _read_uploaded_content(content_bytes, p.name)
                files.append({
                    "name": p.name,
                    "relative_path": str(p),
                    "ext": ext,
                    "size_kb": round(info.file_size / 1024, 1),
                    "depth": len(p.parts) - 1,
                    "content": content,
                })
        return files, None
    except zipfile.BadZipFile:
        return [], "❌ Arquivo inválido. Envie um .zip válido."
    except Exception as e:
        return [], f"❌ Erro ao processar ZIP: {e}"


def _process_multiple_files(uploaded_files) -> tuple[list[dict], str | None]:
    """
    Processa lista de arquivos enviados individualmente.
    """
    files = []
    for uf in uploaded_files:
        p = pathlib.PurePosixPath(uf.name)
        ext = p.suffix.lower()
        if ext not in EXTENSIONS_ALLOWED:
            continue
        content_bytes = uf.read()
        if len(content_bytes) > 500_000:
            continue
        content = _read_uploaded_content(content_bytes, uf.name)
        files.append({
            "name": uf.name,
            "relative_path": uf.name,
            "ext": ext,
            "size_kb": round(len(content_bytes) / 1024, 1),
            "depth": 0,
            "content": content,
        })
    return files, None


def _render_file_tree_inline(files: list[dict]):
    """Renderiza árvore de arquivos a partir de lista de dicts (sem pathlib)."""
    EXT_ICON = {
        ".py":"🐍", ".js":"📜", ".ts":"📘", ".jsx":"⚛️", ".tsx":"⚛️",
        ".java":"☕", ".go":"🔵", ".cs":"💠", ".cpp":"⚙️", ".c":"⚙️",
        ".json":"📋", ".yaml":"📄", ".yml":"📄", ".md":"📝",
        ".sql":"🗄️", ".html":"🌐", ".css":"🎨", ".sh":"🖥️",
    }

    total_kb = sum(f["size_kb"] for f in files)
    c1, c2, c3 = st.columns(3)
    c1.metric("Arquivos encontrados", len(files))
    c2.metric("Tamanho total", f"{total_kb:.1f} KB")
    c3.metric("Status", "✅ Ok")

    with st.expander("📂 Ver arquivos do projeto", expanded=True):
        ext_count: dict = {}
        for f in files:
            ext_count[f["ext"]] = ext_count.get(f["ext"], 0) + 1

        resumo = "  |  ".join(
            f"{EXT_ICON.get(e,'📄')} {e.upper()}: {c}"
            for e, c in sorted(ext_count.items(), key=lambda x: -x[1])
        )
        st.caption(resumo)
        st.divider()

        for f in files:
            indent = "    " * f["depth"]
            icon = EXT_ICON.get(f["ext"], "📄")
            st.text(f"{indent}{icon}  {f['name']}   ({f['size_kb']} KB)")


def render_tab_project(ai_cfg: dict):

    with st.expander("ℹ️ Como usar — clique para ver o passo a passo"):
        st.markdown("""
**Opção A — Upload de ZIP:**
Compacte toda a pasta do projeto em `.zip` e envie abaixo.
- Windows: botão direito na pasta → *Compactar em arquivo ZIP*
- Mac: botão direito → *Comprimir*

**Opção B — Selecionar arquivos:**
Selecione vários arquivos de código diretamente (sem precisar compactar).

**Depois:**

**3.** Clique em **🔍 Escanear** — o QABot lista todos os arquivos de código

**4.** Selecione quais arquivos analisar (ou clique em "Todos")

**5.** Clique em **▶️ Iniciar Análise** e aguarde

**O QABot retorna para cada arquivo:**
- 📊 Score de qualidade (0–100)
- 🔍 Localização exata de cada erro (linha + trecho do código)
- ✅ Correção sugerida com exemplo de código
- 💡 Explicação simples de por que é um problema
        """)

    st.markdown("#### 📁 Passo 1 — Envie o projeto")

    modo = st.radio(
        "Como deseja enviar?",
        ["🗜️ Upload de ZIP (projeto inteiro)", "📄 Selecionar arquivos individuais"],
        horizontal=True,
    )

    if "🗜️" in modo:
        col_up, col_btn = st.columns([5, 1])
        with col_up:
            uploaded_zip = st.file_uploader(
                "Selecione o ZIP do projeto",
                type=["zip"],
                label_visibility="collapsed",
            )
        with col_btn:
            scan_btn = st.button("🔍 Escanear", use_container_width=True)

        if scan_btn:
            if not uploaded_zip:
                st.warning("Selecione um arquivo ZIP antes de escanear.")
                return
            with st.spinner("Extraindo e escaneando arquivos..."):
                files_data, err = _process_zip(uploaded_zip)
            if err:
                st.error(err)
                return
            if not files_data:
                st.warning("Nenhum arquivo de código encontrado no ZIP.")
                st.caption("Formatos suportados: .py .js .ts .java .cs .go .sql .html .css .json .yaml .md .sh")
                return
            st.session_state["proj_files_data"] = files_data
            st.session_state["proj_results"] = {}
            st.success(f"✅ {len(files_data)} arquivo(s) encontrado(s) no ZIP!")

    else:
        col_up, col_btn = st.columns([5, 1])
        with col_up:
            uploaded_files = st.file_uploader(
                "Selecione os arquivos do projeto",
                accept_multiple_files=True,
                label_visibility="collapsed",
            )
        with col_btn:
            scan_btn = st.button("🔍 Escanear", use_container_width=True)

        if scan_btn:
            if not uploaded_files:
                st.warning("Selecione ao menos um arquivo antes de escanear.")
                return
            with st.spinner("Processando arquivos..."):
                files_data, err = _process_multiple_files(uploaded_files)
            if err:
                st.error(err)
                return
            if not files_data:
                st.warning("Nenhum arquivo de código compatível encontrado.")
                st.caption("Formatos suportados: .py .js .ts .java .cs .go .sql .html .css .json .yaml .md .sh")
                return
            st.session_state["proj_files_data"] = files_data
            st.session_state["proj_results"] = {}
            st.success(f"✅ {len(files_data)} arquivo(s) pronto(s) para análise!")

    if "proj_files_data" not in st.session_state:
        return

    files_data: list[dict] = st.session_state["proj_files_data"]

    st.divider()
    st.markdown("#### 📂 Passo 2 — Arquivos encontrados")
    _render_file_tree_inline(files_data)

    st.divider()
    st.markdown("#### ✅ Passo 3 — Selecione os arquivos para analisar")

    file_options = [f["relative_path"] for f in files_data]
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
        selected_files = [f for f in files_data if f["relative_path"] in selected]
        results = {}
        progress = st.progress(0)

        for i, finfo in enumerate(selected_files):
            progress.progress(
                (i + 1) / len(selected_files),
                text=f"🔍 Analisando {finfo['name']} ({i+1}/{len(selected_files)})..."
            )
            content  = finfo["content"]
            lang     = get_language_from_ext(finfo["ext"])
            messages = build_analysis_messages(finfo["name"], lang, content)
            try:
                raw  = call_ai(ai_cfg["backend"], ai_cfg["client"],
                               ai_cfg["model"], messages, ai_cfg["ollama_url"])
                data = parse_analysis_response(raw)
                results[finfo["relative_path"]] = {
                    "data": data, "raw": raw, "lang": lang, "name": finfo["name"]
                }
            except Exception as e:
                results[finfo["relative_path"]] = {
                    "data": None, "raw": str(e), "lang": lang, "name": finfo["name"]
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

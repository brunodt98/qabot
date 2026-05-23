"""
QABot — Renderização visual
100% componentes nativos Streamlit. Sem mistura de HTML + st.code() / st.columns().
"""

import streamlit as st
from core.analyzer import get_severity_rank

EXT_ICON = {
    ".py":"🐍", ".js":"📜", ".ts":"📘", ".jsx":"⚛️", ".tsx":"⚛️",
    ".java":"☕", ".go":"🔵", ".cs":"💠", ".cpp":"⚙️", ".c":"⚙️",
    ".json":"📋", ".yaml":"📄", ".yml":"📄", ".md":"📝",
    ".sql":"🗄️", ".html":"🌐", ".css":"🎨", ".sh":"🖥️",
}

SEV_ICON  = {"crítico":"🚨", "alto":"🔥", "médio":"⚠️", "baixo":"💡"}
TIPO_ICON = {"erro":"🔴", "segurança":"🔐", "aviso":"🟡", "performance":"⚡", "estilo":"📐"}


def _score_label(s):
    if s >= 90: return "Excelente 🏆"
    if s >= 75: return "Bom 😊"
    if s >= 60: return "Regular 🙂"
    if s >= 40: return "Precisa melhorar 😟"
    return "Crítico 😱"


def render_file_tree(tree: list, root: str):
    """Árvore de arquivos usando expander + texto nativo."""
    total = len(tree)
    total_kb = sum(f["size_kb"] for f in tree)

    col1, col2, col3 = st.columns(3)
    col1.metric("Arquivos encontrados", total)
    col2.metric("Tamanho total", f"{total_kb:.1f} KB")
    col3.metric("Pasta", "✅ Ok")

    with st.expander("📂 Ver arquivos do projeto", expanded=True):
        # Contagem por extensão
        ext_count: dict = {}
        for f in tree:
            ext_count[f["ext"]] = ext_count.get(f["ext"], 0) + 1

        resumo = "  |  ".join(
            f"{EXT_ICON.get(e,'📄')} .{e.replace('.','').upper()}: {c}"
            for e, c in sorted(ext_count.items(), key=lambda x: -x[1])
        )
        st.caption(resumo)
        st.divider()

        for f in tree:
            indent = "    " * f["depth"]
            icon   = EXT_ICON.get(f["ext"], "📄")
            st.text(f"{indent}{icon}  {f['name']}   ({f['size_kb']} KB)")


def render_full_analysis(data: dict, filename: str, lang: str):
    """Renderização completa e estável de uma análise de arquivo."""
    score     = data.get("score_qualidade", 0)
    dif       = data.get("classificacao_dificuldade", "?")
    justif    = data.get("justificativa_dificuldade", "")
    resumo    = data.get("resumo", "")
    problemas = sorted(
        data.get("problemas", []),
        key=lambda p: get_severity_rank(p.get("severidade", "baixo"))
    )
    positivos = data.get("pontos_positivos", [])
    recomend  = data.get("recomendacoes_gerais", [])

    ext      = ("." + filename.split(".")[-1]) if "." in filename else ""
    ext_icon = EXT_ICON.get(ext, "📄")

    # ── Cabeçalho ────────────────────────────────────────────────────────────
    st.markdown(f"### {ext_icon} `{filename}`")
    st.progress(score / 100)

    # ── Métricas ─────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📊 Score", f"{score}/100", _score_label(score))
    c2.metric("🔍 Problemas", len(problemas))
    c3.metric("📐 Complexidade", dif)

    contagem = {}
    for p in problemas:
        s = p.get("severidade", "baixo").lower()
        contagem[s] = contagem.get(s, 0) + 1

    criticos = contagem.get("crítico", 0) + contagem.get("alto", 0)
    c4.metric("🚨 Críticos/Altos", criticos)

    # ── Resumo e dificuldade ─────────────────────────────────────────────────
    with st.expander("📋 Diagnóstico geral", expanded=True):
        st.info(f"**Diagnóstico:** {resumo}")
        st.caption(f"**Complexidade:** {dif} — {justif}")
        if contagem:
            detalhes = " | ".join(
                f"{SEV_ICON.get(s,'•')} {s.capitalize()}: {n}"
                for s, n in sorted(contagem.items(), key=lambda x: get_severity_rank(x[0]))
            )
            st.caption(f"**Distribuição:** {detalhes}")

    # ── Problemas ────────────────────────────────────────────────────────────
    if not problemas:
        st.success("🎉 **Nenhum problema encontrado!** Este arquivo está seguindo boas práticas.")
    else:
        st.markdown(f"#### 🔍 {len(problemas)} problema(s) — do mais grave ao menos grave")

        for i, p in enumerate(problemas):
            _render_problem(p, lang, i + 1, len(problemas))

    # ── Pontos positivos e recomendações ─────────────────────────────────────
    col_pos, col_rec = st.columns(2)

    with col_pos:
        if positivos:
            st.markdown("**✅ O que está bom**")
            for item in positivos:
                st.success(f"✅ {item}")

    with col_rec:
        if recomend:
            st.markdown("**💡 Próximos passos**")
            for item in recomend:
                st.warning(f"💡 {item}")

    st.divider()


def _render_problem(p: dict, lang: str, idx: int, total: int):
    """Renderiza um problema individual — 100% componentes nativos."""
    tipo      = p.get("tipo", "aviso")
    sev       = p.get("severidade", "médio").lower()
    titulo    = p.get("titulo", "Problema")
    descricao = p.get("descricao", "")
    linha_ini = p.get("linha_inicio")
    linha_fim = p.get("linha_fim")
    trecho    = p.get("trecho_original", "").strip()
    correcao  = p.get("correcao_sugerida", "").strip()
    explicacao= p.get("explicacao_correcao", "").strip()

    t_icon = TIPO_ICON.get(tipo, "⚠️")
    s_icon = SEV_ICON.get(sev, "⚠️")

    linha_str = ""
    if linha_ini:
        linha_str = (f"Linha {linha_ini}" if not linha_fim or linha_ini == linha_fim
                     else f"Linhas {linha_ini}–{linha_fim}")

    # Título do expander com todas as infos relevantes
    expander_label = f"{s_icon} {t_icon}  Problema {idx}/{total} — {titulo}"
    if linha_str:
        expander_label += f"  |  📍 {linha_str}"
    expander_label += f"  |  [{sev.upper()}]"

    with st.expander(expander_label, expanded=True):

        # Descrição
        if sev in ("crítico", "alto"):
            st.error(f"**{s_icon} {sev.upper()}** — {descricao}")
        elif sev == "médio":
            st.warning(f"**{s_icon} {sev.upper()}** — {descricao}")
        else:
            st.info(f"**{s_icon} {sev.upper()}** — {descricao}")

        # Localização
        if linha_str:
            st.caption(f"📍 **Localização:** {linha_str}")

        st.divider()

        # Código com problema e correção — lado a lado de forma segura
        if trecho and correcao:
            col_err, col_fix = st.columns(2)
            with col_err:
                st.markdown("**❌ Código com problema:**")
                st.code(trecho, language=lang)
            with col_fix:
                st.markdown("**✅ Correção sugerida:**")
                st.code(correcao, language=lang)

        elif trecho:
            st.markdown("**❌ Código com problema:**")
            st.code(trecho, language=lang)
            st.caption("⚠️ Correção não disponível — peça ao QABot no chat.")

        elif correcao:
            st.markdown("**✅ Correção sugerida:**")
            st.code(correcao, language=lang)

        # Explicação didática
        if explicacao:
            st.divider()
            st.markdown("**💡 Por que isso é um problema?**")
            st.info(explicacao)

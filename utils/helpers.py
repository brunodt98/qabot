"""
QABot — Renderização visual
100% componentes nativos Streamlit. Sem mistura de HTML + st.code() / st.columns().
"""

import streamlit as st
from core.analyzer import get_severity_rank
from ui import theme

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

    contagem = {}
    for problema in problemas:
        nivel = problema.get("severidade", "baixo").lower()
        contagem[nivel] = contagem.get(nivel, 0) + 1

    criticos = contagem.get("crítico", 0) + contagem.get("alto", 0)

    # ── Cabeçalho ────────────────────────────────────────────────────────────
    theme.titulo_arquivo(f"{ext_icon} {filename}", _score_label(score))

    # ── Métricas ─────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Score de qualidade", f"{score}/100")
    c2.metric("Problemas encontrados", len(problemas))
    c3.metric("Complexidade", dif)
    c4.metric("Críticos ou altos", criticos)

    # A barra do score usa a mesma faixa de cor que o prompt impõe ao modelo:
    # 70+ boas práticas, 40–69 qualidade, abaixo disso vulnerabilidade.
    st.markdown(
        f"<div style='height:6px;border-radius:999px;background:{theme.GRID};"
        f"margin:.5rem 0 .2rem;overflow:hidden'>"
        f"<div style='height:100%;width:{max(score, 2)}%;"
        f"background:{theme.cor_do_score(score)};border-radius:999px'></div></div>",
        unsafe_allow_html=True,
    )

    theme.barra_severidades(contagem, SEV_ICON)

    # ── Diagnóstico ──────────────────────────────────────────────────────────
    # Sem problemas, o resumo do modelo já diz que está limpo: uma segunda
    # frase nossa dizendo o mesmo só ocupa espaço. Os dois viram um box só.
    texto_diag = (
        f"{resumo}<br><br><b>Complexidade {dif}</b> — {justif}"
        if resumo and justif else resumo
    )

    if not problemas:
        theme.sem_problemas(texto_diag or "Nenhum problema apontado neste arquivo.")
    else:
        if texto_diag:
            theme.diagnostico(texto_diag)

    # ── Problemas ────────────────────────────────────────────────────────────
    if problemas:
        theme.secao(
            f"{len(problemas)} problema(s) encontrado(s)",
            "Ordenados do mais grave para o menos grave.",
        )

        for i, problema in enumerate(problemas):
            _render_problem(problema, lang, i + 1, len(problemas))

    # ── Pontos positivos e recomendações ─────────────────────────────────────
    if positivos or recomend:
        col_pos, col_rec = st.columns(2)

        with col_pos:
            if positivos:
                theme.secao("O que está bom")
                for item in positivos:
                    st.markdown(f"- {item}")

        with col_rec:
            if recomend:
                theme.secao("Próximos passos")
                for item in recomend:
                    st.markdown(f"- {item}")

    theme.regua()


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

    rotulo = f"{t_icon}  {titulo}"
    if linha_str:
        rotulo += f"  ·  {linha_str}"

    # Expandido só o que é grave: num arquivo com muitos apontamentos de
    # estilo, abrir todos empurra o que importa para fora da tela.
    with st.expander(rotulo, expanded=sev in ("crítico", "alto")):

        st.markdown(
            theme.selo_severidade(sev, s_icon)
            + f"  <span style='color:{theme.MUTED};font-size:.74rem'>"
            f"{tipo} · problema {idx} de {total}</span>",
            unsafe_allow_html=True,
        )

        if descricao:
            st.markdown(
                f"<p style='font-size:.87rem;color:{theme.INK_2};"
                f"line-height:1.6;margin:.6rem 0 .2rem'>{descricao}</p>",
                unsafe_allow_html=True,
            )

        if trecho and correcao:
            col_err, col_fix = st.columns(2)
            with col_err:
                st.caption("Como está")
                st.code(trecho, language=lang)
            with col_fix:
                st.caption("Correção sugerida")
                st.code(correcao, language=lang)

        elif trecho:
            st.caption("Como está")
            st.code(trecho, language=lang)
            st.caption("O modelo não propôs correção para este trecho.")

        elif correcao:
            st.caption("Correção sugerida")
            st.code(correcao, language=lang)

        # Explicação didática
        if explicacao:
            st.markdown(
                f"<div class='diag' style='margin-top:.7rem'>"
                f"<b>O que muda:</b> {explicacao}</div>",
                unsafe_allow_html=True,
            )

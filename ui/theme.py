"""
QABot — Identidade visual

Mesmos tokens dos outros projetos (painel ICMS Educacional SP e chatbot RAG
de legislação), para que os três sejam lidos como um conjunto: azul-marinho e
vermelho da bandeira paulista, dourado no estado ativo, IBM Plex Sans no
corpo e Source Serif nos títulos e nos números.
"""

import streamlit as st


# ─────────────────────────────────────────────────────────────────────────────
# DESIGN TOKENS
# ─────────────────────────────────────────────────────────────────────────────

SURFACE = "#ffffff"
PLANE = "#f4f3ef"
INK = "#14161a"
INK_2 = "#4a4f57"
MUTED = "#767c86"
GRID = "#e3e1da"

NAVY_DEEP = "#0b1f3d"   # barra lateral
NAVY = "#12305c"        # institucional
NAVY_LINE = "#1e3a63"   # divisórias sobre o navy
BLUE = "#2c6bb8"        # acento
GOLD = "#e8b33a"        # estado ativo

ON_NAVY = "#c6d4e6"
ON_NAVY_DIM = "#9fb2cc"

SANS = '"IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif'
SERIF = '"Source Serif 4", Georgia, "Times New Roman", serif'


# ─────────────────────────────────────────────────────────────────────────────
# PALETA DE STATUS — SEVERIDADE
# ─────────────────────────────────────────────────────────────────────────────
# Severidade é escala de STATUS, não categórica: os tons não são
# intercambiáveis e nunca aparecem sozinhos — sempre acompanhados de ícone e
# do nome do nível, porque cor sozinha não é acessível.
#
# Os quatro passos foram validados contra a superfície clara (#fcfcfb).
# O par mais próximo (médio ↔ alto) fica em ΔE 16,2 em visão normal e 14,5 em
# deuteranopia, acima do piso exigido. A variação de luminosidade é
# deliberada: quanto mais grave, mais pesado; "baixo" é cinza de propósito,
# para ser recessivo.

SEVERIDADE_COR = {
    "crítico": "#8f1220",
    "alto": "#d1731c",
    "médio": "#e8b33a",
    "baixo": "#767c86",
}

SEVERIDADE_FUNDO = {
    "crítico": "#fbeced",
    "alto": "#fdf1e4",
    "médio": "#fdf6e3",
    "baixo": "#f2f3f4",
}

# Faixas do score, nas mesmas regras que o prompt de análise impõe ao modelo.
SCORE_COR = [
    (70, "#1f7a4d"),   # 70–100: estilo e boas práticas
    (40, "#d1731c"),   # 40–69: qualidade e lógica
    (0, "#8f1220"),    # 0–39: vulnerabilidade crítica
]


def cor_do_score(score: int) -> str:
    for minimo, cor in SCORE_COR:
        if score >= minimo:
            return cor
    return MUTED


MARCA_SVG = f"""
<svg width="34" height="34" viewBox="0 0 38 38" aria-hidden="true" class="mark">
  <rect x="0" y="0" width="38" height="38" rx="7" fill="#ffffff"></rect>
  <path d="M19 5 L31 9 L31 19 C31 26 25 31 19 33 C13 31 7 26 7 19 L7 9 Z"
        fill="none" stroke="{NAVY}" stroke-width="2.4"></path>
  <path d="M13.5 19.5 L17.5 23.5 L25 15" fill="none" stroke="{GOLD}"
        stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"></path>
</svg>"""


CSS = f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,500;8..60,600&display=swap');

  .stApp {{ background: {PLANE}; }}
  [data-testid="stHeader"] {{ background: transparent; }}
  [data-testid="stMainBlockContainer"] {{
      padding: 1.9rem 2.4rem 5rem; max-width: 1240px;
  }}
  html, body, [class*="st-"] {{ font-family: {SANS}; }}

  /* Ícones do Streamlit são ligaduras de fonte própria: a regra acima
     alcança esses spans e imprimiria o NOME do ícone como texto. */
  [data-testid="stIconMaterial"],
  span[class*="material-symbols"] {{
      font-family: "Material Symbols Rounded" !important;
  }}

  /* ---------- barra lateral ---------- */
  [data-testid="stSidebar"] {{ background: {NAVY_DEEP}; border-right: 0; }}
  [data-testid="stSidebar"] [data-testid="stSidebarContent"] {{
      padding: 1.5rem 1.15rem 1.2rem;
  }}
  [data-testid="stSidebar"] * {{ color: #ffffff; }}
  [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{
      font-size: .76rem !important; color: {ON_NAVY_DIM}; font-weight: 500;
  }}
  .side-lbl {{
      font-size: .66rem; letter-spacing: .1em; text-transform: uppercase;
      color: #7e93b3; margin: .1rem 0 .55rem;
  }}
  .side-rule {{ height: 1px; background: {NAVY_LINE}; margin: 1.15rem 0; }}
  .side-brand {{ display: flex; align-items: center; gap: .72rem; }}
  .side-brand .nm {{
      font-family: {SERIF}; font-size: 1.02rem; font-weight: 600;
      letter-spacing: -.01em; line-height: 1.15; color: #fff;
  }}
  .side-brand .uf {{
      font-size: .68rem; letter-spacing: .05em; text-transform: uppercase;
      color: {ON_NAVY_DIM}; margin-top: .12rem;
  }}
  .side-foot {{
      display: flex; align-items: center; gap: .65rem;
      padding-top: .95rem; border-top: 1px solid {NAVY_LINE}; margin-top: .6rem;
  }}
  .side-foot .sigla {{
      width: 30px; height: 30px; border-radius: 6px; background: #b7202e;
      display: flex; align-items: center; justify-content: center;
      font-size: .66rem; font-weight: 600; color: #fff; flex: 0 0 auto;
  }}
  .side-foot .txt {{ font-size: .68rem; color: {ON_NAVY_DIM}; line-height: 1.4; }}
  .side-foot .txt b {{ color: #fff; font-weight: 500; }}

  [data-testid="stSidebar"] [data-baseweb="select"] > div,
  [data-testid="stSidebar"] [data-testid="stTextInput"] input {{
      background: #112b52; border-color: #2a4b7c; color: #fff;
      border-radius: 7px; font-size: .82rem;
  }}
  [data-testid="stSidebar"] [data-baseweb="radio"] svg {{ fill: {GOLD}; }}
  [data-testid="stSidebar"] [data-testid="stButton"] button {{
      background: transparent; border: 1px solid #2a4b7c; color: {ON_NAVY};
      font-size: .82rem; border-radius: 7px; width: 100%;
  }}
  [data-testid="stSidebar"] [data-testid="stButton"] button:hover {{
      border-color: {GOLD}; color: #fff;
  }}

  /* ---------- cabeçalho ---------- */
  .eyebrow {{
      font-size: .7rem; font-weight: 600; letter-spacing: .09em;
      text-transform: uppercase; color: {MUTED}; margin-bottom: .45rem;
  }}
  h1.hero {{
      font-family: {SERIF}; font-size: 2.05rem; font-weight: 600;
      letter-spacing: -.022em; color: {INK}; margin: 0 0 .45rem; line-height: 1.1;
  }}
  .lede {{
      font-size: .93rem; color: {INK_2}; max-width: 74ch;
      line-height: 1.55; margin-bottom: .9rem;
  }}
  .rule {{ height: 1px; background: {GRID}; margin: 1.35rem 0 1.2rem; border: 0; }}

  /* ---------- títulos de seção ---------- */
  .sec {{ margin: 1.8rem 0 .8rem; }}
  .sec h2 {{
      font-size: 1.02rem; font-weight: 640; color: {INK};
      margin: 0 0 .2rem; letter-spacing: -.01em;
  }}
  .sec p {{ font-size: .82rem; color: {MUTED}; margin: 0; line-height: 1.5; }}

  /* ---------- abas ---------- */
  [data-testid="stTabs"] [data-baseweb="tab-list"] {{
      gap: .3rem; border-bottom: 1px solid {GRID};
  }}
  [data-testid="stTabs"] [data-baseweb="tab"] {{
      font-size: .88rem; font-weight: 500; color: {MUTED};
      padding: .55rem .9rem;
  }}
  [data-testid="stTabs"] [aria-selected="true"] {{ color: {NAVY}; }}
  [data-testid="stTabs"] [data-baseweb="tab-highlight"] {{ background: {NAVY}; }}

  /* ---------- stat tiles ---------- */
  [data-testid="stMetric"] {{
      background: {SURFACE}; border: 1px solid {GRID};
      border-top: 3px solid {NAVY}; border-radius: 10px; padding: .8rem .95rem;
  }}
  [data-testid="stMetricLabel"] p {{
      font-size: .74rem !important; font-weight: 550; color: {MUTED};
      letter-spacing: .01em; line-height: 1.3;
  }}
  [data-testid="stMetricValue"] {{
      font-family: {SERIF}; font-size: 1.5rem !important; font-weight: 600;
      color: {INK}; letter-spacing: -.02em;
  }}
  [data-testid="stMetricDelta"] {{ font-size: .74rem !important; }}

  /* ---------- cartão do arquivo analisado ---------- */
  .arquivo {{
      display: flex; align-items: baseline; justify-content: space-between;
      gap: 1rem; border-bottom: 1px solid {GRID};
      padding-bottom: .5rem; margin: 1.6rem 0 .9rem;
  }}
  .arquivo .nome {{
      font-family: {SERIF}; font-size: 1.15rem; font-weight: 600; color: {INK};
  }}
  .arquivo .nota {{ font-size: .78rem; color: {MUTED}; }}

  /* ---------- selo de severidade ---------- */
  /* Status nunca é só cor: o selo sempre traz o ícone e o nome do nível. */
  .sev {{
      display: inline-flex; align-items: center; gap: .35rem;
      font-size: .72rem; font-weight: 600; border-radius: 999px;
      padding: .2rem .6rem; border: 1px solid transparent;
  }}
  .barra-sev {{
      display: flex; gap: .4rem; flex-wrap: wrap; margin: .3rem 0 .2rem;
  }}

  /* ---------- diagnóstico ---------- */
  .diag {{
      background: {SURFACE}; border: 1px solid {GRID};
      border-left: 3px solid {BLUE}; border-radius: 8px;
      padding: .85rem 1.05rem; font-size: .88rem; color: {INK_2};
      line-height: 1.6;
  }}
  .diag b {{ color: {INK}; font-weight: 620; }}

  .limpo {{
      background: #edf7f1; border: 1px solid #c6e3d3;
      border-left: 3px solid #1f7a4d; border-radius: 8px;
      padding: .85rem 1.05rem; font-size: .88rem; color: #17553a;
  }}

  /* ---------- expander como cartão ---------- */
  [data-testid="stExpander"] {{
      background: {SURFACE}; border: 1px solid {GRID};
      border-radius: 10px; margin-bottom: .5rem;
  }}
  [data-testid="stExpander"] summary {{ font-size: .86rem; color: {INK}; }}

  [data-testid="stElementToolbar"] {{ display: none; }}
</style>
"""


def aplicar() -> None:
    """Injeta a folha de estilo. Chamar uma vez, logo após set_page_config."""
    st.markdown(CSS, unsafe_allow_html=True)


def cabecalho(eyebrow: str, titulo: str, lede: str) -> None:
    st.markdown(
        f"<div class='eyebrow'>{eyebrow}</div>"
        f"<h1 class='hero'>{titulo}</h1>"
        f"<p class='lede'>{lede}</p>",
        unsafe_allow_html=True,
    )


def secao(titulo: str, sub: str = "") -> None:
    st.markdown(
        f"<div class='sec'><h2>{titulo}</h2>"
        f"{f'<p>{sub}</p>' if sub else ''}</div>",
        unsafe_allow_html=True,
    )


def regua() -> None:
    st.markdown("<hr class='rule'>", unsafe_allow_html=True)


def marca_lateral(nome: str, subtitulo: str) -> None:
    st.markdown(
        f"<div class='side-brand'>{MARCA_SVG}"
        f"<div><div class='nm'>{nome}</div>"
        f"<div class='uf'>{subtitulo}</div></div></div>",
        unsafe_allow_html=True,
    )


def rodape_lateral(sigla: str, texto: str) -> None:
    st.markdown(
        f"<div class='side-foot'><div class='sigla'>{sigla}</div>"
        f"<div class='txt'>{texto}</div></div>",
        unsafe_allow_html=True,
    )


def selo_severidade(nivel: str, icone: str, quantidade: int | None = None) -> str:
    """HTML de um selo de severidade: cor + ícone + nome, nunca cor sozinha."""
    nivel = (nivel or "baixo").lower()
    cor = SEVERIDADE_COR.get(nivel, MUTED)
    fundo = SEVERIDADE_FUNDO.get(nivel, "#f2f3f4")
    texto = nivel.capitalize() if quantidade is None else f"{nivel.capitalize()}: {quantidade}"

    return (
        f"<span class='sev' style='color:{cor};background:{fundo};"
        f"border-color:{cor}33'>{icone} {texto}</span>"
    )


def barra_severidades(contagem: dict, icones: dict) -> None:
    """Distribuição dos problemas por severidade, do mais grave ao menos."""
    ordem = ["crítico", "alto", "médio", "baixo"]
    selos = [
        selo_severidade(nivel, icones.get(nivel, "•"), contagem[nivel])
        for nivel in ordem
        if contagem.get(nivel)
    ]

    if selos:
        st.markdown(
            f"<div class='barra-sev'>{''.join(selos)}</div>",
            unsafe_allow_html=True,
        )


def titulo_arquivo(nome: str, nota: str = "") -> None:
    st.markdown(
        f"<div class='arquivo'><span class='nome'>{nome}</span>"
        f"<span class='nota'>{nota}</span></div>",
        unsafe_allow_html=True,
    )


def diagnostico(texto: str) -> None:
    st.markdown(f"<div class='diag'>{texto}</div>", unsafe_allow_html=True)


def sem_problemas(texto: str) -> None:
    st.markdown(f"<div class='limpo'>{texto}</div>", unsafe_allow_html=True)

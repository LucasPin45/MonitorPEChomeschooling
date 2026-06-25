# app_pec_homeschooling.py
# Streamlit 1.54+
# 📖 PEC do Homeschooling — Monitor de Apoiamentos & Mobilização
# Reconhecimento constitucional do ensino domiciliar
# Código Infoleg: CD268562833200
# Autoria: Dep. Júlia Zanatta (PL/SC)

from __future__ import annotations

import io
import re
import time
import unicodedata
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import requests
import streamlit as st

# ═══════════════════════════════════════════
# Config
# ═══════════════════════════════════════════

st.set_page_config(
    page_title="PEC do Homeschooling — Apoie",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CAMARA_API_BASE = "https://dadosabertos.camara.leg.br/api/v2"
USER_AGENT = "monitor-pec-homeschooling/apoiamentos (streamlit)"
META_PEC = 171  # 1/3 da Câmara — mínimo constitucional para protocolar uma PEC (art. 60, I, CF)

COD_INFOLEG = "CD268562833200"
LINK_APOIAMENTO = "https://applinks.camara.leg.br/iit6MXhrRcwV"

ZANATTA_ID = 220559
ZANATTA_FOTO = f"https://www.camara.leg.br/internet/deputado/bandep/{ZANATTA_ID}.jpg"
ZANATTA_BIO = f"https://www.camara.leg.br/deputados/{ZANATTA_ID}/biografia"

MENSAGEM_MOBILIZACAO = """🚨 PEC DO HOMESCHOOLING 📖

Nobres colegas,

Peço o apoio e a assinatura da PEC que reconhece expressamente o ensino domiciliar (homeschooling) como modalidade legítima de cumprimento do dever educacional familiar.

A proposta garante segurança jurídica às famílias, assegura a liberdade de escolha educacional dos pais e estabelece parâmetros constitucionais para o exercício responsável do ensino domiciliar, com avaliação periódica do aprendizado e respeito integral aos direitos da criança e do adolescente.

Assine pelo link:
applinks.camara.leg.br/iit6MXhrRcwV

Código da PEC: CD268562833200

Conto com seu apoio.

Atenciosamente,
Dep. Federal Júlia Zanatta (PL/SC)"""

ASSUNTO_EMAIL = "Pedido de apoiamento — PEC do Homeschooling (CD268562833200)"

# ═══════════════════════════════════════════
# CSS — identidade visual: educação no lar
# verde-escuro institucional + âmbar "luz de leitura"
# ═══════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
code, pre, .stCode { font-family: 'JetBrains Mono', monospace !important; }

.hero-header {
    background: linear-gradient(135deg, #123524 0%, #1d5238 55%, #2a6b48 100%);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    color: white;
    position: relative;
    overflow: hidden;
}
.hero-header::before {
    content: '';
    position: absolute;
    top: -30%; right: -10%;
    width: 320px; height: 320px;
    background: radial-gradient(circle, rgba(244,196,84,0.12) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-header h1 { margin: 0 0 0.3rem 0; font-size: 1.75rem; font-weight: 700; letter-spacing: -0.02em; }
.hero-header p  { margin: 0; opacity: 0.88; font-size: 0.95rem; }
.hero-badge {
    display: inline-block;
    background: rgba(244,196,84,0.18);
    border: 1px solid rgba(244,196,84,0.45);
    color: #f4c454;
    border-radius: 6px;
    padding: 0.18rem 0.65rem;
    font-size: 0.78rem; font-weight: 700;
    margin-bottom: 0.6rem; letter-spacing: 0.05em;
}
.hero-cta {
    display: inline-block;
    margin-top: 0.9rem;
    background: #f4c454;
    color: #123524 !important;
    font-weight: 700;
    font-size: 0.92rem;
    padding: 0.55rem 1.3rem;
    border-radius: 8px;
    text-decoration: none !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.hero-cta:hover { transform: translateY(-1px); box-shadow: 0 6px 18px rgba(0,0,0,0.25); }

.hero-flex { display: flex; align-items: center; gap: 2rem; position: relative; z-index: 1; }
.hero-text { flex: 1; min-width: 0; }
.hero-autora {
    flex-shrink: 0;
    text-align: center;
}
.hero-autora img {
    width: 130px; height: 130px;
    border-radius: 50%;
    object-fit: cover;
    object-position: top;
    border: 3px solid #f4c454;
    box-shadow: 0 6px 20px rgba(0,0,0,0.35);
    display: block;
    margin: 0 auto 0.5rem auto;
}
.hero-autora .autora-nome {
    font-size: 0.88rem; font-weight: 700; color: white; line-height: 1.25;
}
.hero-autora .autora-cargo {
    font-size: 0.72rem; color: #f4c454; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.15rem;
}
.hero-autora a { text-decoration: none; }
@media (max-width: 740px) {
    .hero-flex { flex-direction: column-reverse; gap: 1.2rem; }
    .hero-autora img { width: 105px; height: 105px; }
}

.kpi-card {
    background: white; border: 1px solid #e6ece8;
    border-radius: 12px; padding: 1.2rem 1.4rem;
    text-align: center; transition: box-shadow 0.2s ease;
}
.kpi-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.06); }
.kpi-label { font-size: 0.78rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: #6b7d72; margin-bottom: 0.35rem; }
.kpi-value { font-size: 2rem; font-weight: 700; line-height: 1; margin-bottom: 0.15rem; }
.kpi-sub   { font-size: 0.75rem; color: #8a9890; }
.kpi-green  .kpi-value { color: #1d7a4d; }
.kpi-red    .kpi-value { color: #c2453a; }
.kpi-amber  .kpi-value { color: #b8860b; }
.kpi-forest .kpi-value { color: #123524; }
.kpi-purple .kpi-value { color: #6d28d9; }

.progress-wrapper { margin: 1.2rem 0 1.8rem 0; }
.progress-label-row { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.5rem; }
.prog-title { font-weight: 600; font-size: 0.95rem; color: #25382e; }
.prog-pct   { font-weight: 700; font-size: 1.1rem; }
.progress-track { background: #e9efeb; border-radius: 10px; height: 26px; position: relative; overflow: hidden; }
.progress-fill  { height: 100%; border-radius: 10px; transition: width 0.6s cubic-bezier(0.22, 1, 0.36, 1); position: relative; }
.progress-fill::after {
    content: ''; position: absolute; top:0; left:0; right:0; bottom:0;
    background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.15) 50%, transparent 100%);
}
.progress-marker { position: absolute; top: -4px; bottom: -4px; width: 2px; background: #25382e; opacity: 0.5; z-index: 2; }
.progress-marker-label { position: absolute; top: -20px; transform: translateX(-50%); font-size: 0.7rem; font-weight: 600; color: #25382e; opacity: 0.7; white-space: nowrap; }

.status-banner { border-radius: 10px; padding: 0.8rem 1.2rem; font-weight: 600; font-size: 0.9rem; display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem; }
.status-ok   { background: #ecfdf3; color: #14532d; border: 1px solid #a7e8c3; }
.status-warn { background: #fffbeb; color: #92400e; border: 1px solid #fde68a; }

.mob-card {
    background: #f7faf8; border: 1px solid #dbe7df;
    border-radius: 12px; padding: 1.2rem 1.4rem; margin-bottom: 1rem;
}
.mob-card h4 { margin: 0 0 0.4rem 0; color: #123524; font-size: 1rem; }
.mob-card p  { margin: 0 0 0.4rem 0; font-size: 0.88rem; color: #41544a; }
.mob-step {
    display: inline-flex; align-items: center; justify-content: center;
    width: 26px; height: 26px; border-radius: 50%;
    background: #123524; color: #f4c454; font-weight: 700; font-size: 0.85rem;
    margin-right: 0.5rem;
}

[data-testid="stDataEditor"] { border: 1px solid #e6ece8; border-radius: 10px; overflow: hidden; }

section[data-testid="stSidebar"] { background: #f7faf8; }
section[data-testid="stSidebar"] .stTextArea textarea { font-size: 0.82rem; line-height: 1.4; font-family: 'JetBrains Mono', monospace; }

.streamlit-expanderHeader { font-weight: 600; }
button[data-baseweb="tab"] { font-weight: 600; font-size: 0.88rem; }
.block-container { padding-top: 1.5rem; max-width: 1200px; }

.chart-title { font-size: 0.88rem; font-weight: 600; color: #374842; margin-bottom: 0.6rem; }

.alias-suggestion {
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;
    padding: 0.6rem 1rem; margin: 0.3rem 0;
    font-size: 0.82rem; color: #374151;
}
.alias-suggestion code { background: #e2e8f0; padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════
# Aliases e stopwords
# ═══════════════════════════════════════════

ALIASES_OFICIAIS: Dict[str, str] = {
    "julia zanatta": "Julia Zanatta",
    "franciane bayer": "Franciane Bayer",
    "carlos jordy": "Carlos Jordy",
    "lincoln portela": "Lincoln Portela",
    "marcelo moraes": "Marcelo Moraes",
    "eros biondini": "Eros Biondini",
    "marcelo alvaro antonio": "Marcelo Álvaro Antônio",
    "sargento goncalves": "Sargento Gonçalves",
    "sostenes cavalcante": "Sóstenes Cavalcante",
    "rodolfo nogueira": "Rodolfo Nogueira",
    "dilceu sperafico": "Dilceu Sperafico",
    "general girao": "General Girão",
    "itamar paim": "Itamar Paim",
    "rodrigo da zaeli": "Rodrigo Da Zaeli",
    "pastor eurico": "Pastor Eurico",
    "diego garcia": "Diego Garcia",
    "caroline de toni": "Caroline De Toni",
    "cabo gilberto silva": "Cabo Gilberto Silva",
    # aliases herdados — úteis caso novos nomes entrem na lista
    "gilvan da federal": "Gilvan da Federal",
    "delegado paulo bilynskyj": "Delegado Paulo Bilynskyj",
    "delegado fabio costa": "Delegado Fabio Costa",
    "capitao alden": "Capitão Alden",
    "ze trovao": "Zé Trovão",
    "ze haroldo cathedral": "Zé Haroldo Cathedral",
    "bia kicis": "Bia Kicis",
    "luisa canziani": "Luísa Canziani",
    "da vitoria": "Da Vitória",
    "nikolas ferreira": "Nikolas Ferreira",
    "marcel van hattem": "Marcel Van Hattem",
    "aluisio mendes": "Aluísio Mendes",
    "luiz gastao": "Luiz Gastão",
    "dr flavio": "Dr. Flávio",
    "mauricio marcon": "Maurício Marcon",
}

STOPWORDS_LINHAS = {
    "autoria", "coautoria deputado(s)", "coautoria deputados",
    "subscritor", "subscritores", "assinaturas", "assinaram", "assinou",
    "apoiadores", "apoiamento",
}

ASSINANTES_RAW_DEFAULT = """Julia Zanatta
Franciane Bayer
Carlos Jordy
Lincoln Portela
Marcelo Moraes
Eros Biondini
Marcelo Álvaro Antônio
Sargento Gonçalves
Sóstenes Cavalcante
Rodolfo Nogueira
Dilceu Sperafico
General Girão
Itamar Paim
Rodrigo da Zaeli
Pastor Eurico
Diego Garcia
Caroline de Toni
Cabo Gilberto Silva
Delegado Paulo Bilynskyj
Kim Kataguiri
Alfredo Gaspar
Alberto Fraga
Adilson Barroso
Coronel Meira
Filipe Martins
Carla Dickson
Marcos Pollon
Messias Donato
Chris Tonietto
Capitão Alden
Sargento Fahur
Missionário José Olimpio
Clarissa Tércio
Vinicius Carvalho
Dr. Luiz Ovando
Bibo Nunes


"""

PREFIX_STRIP_RE = re.compile(
    r"^(dep|deputado|dra|dr\.?|delegada|delegado|coronel|capitao|capitão|pr|pastor|general|sargento|cabo)\s+",
    re.IGNORECASE,
)


# ═══════════════════════════════════════════
# Normalização e parsing
# ═══════════════════════════════════════════

def _strip_accents(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))


def normalize_name(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    s = s.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    s = _strip_accents(s).lower()
    s = re.sub(r"[^a-z0-9\s]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_assinantes(raw: str) -> List[str]:
    seen: set = set()
    out: List[str] = []
    for ln in (raw or "").splitlines():
        ln = ln.strip().lstrip("*•-– ")
        if not ln:
            continue
        k = normalize_name(ln)
        if not k or k in STOPWORDS_LINHAS or k in seen:
            continue
        seen.add(k)
        out.append(ln)
    return out


# ═══════════════════════════════════════════
# API Câmara
# ═══════════════════════════════════════════

def requests_get_json(url: str, params: Optional[dict] = None, timeout: int = 20) -> dict:
    headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
    last_err = None
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_err = e
            time.sleep(0.6 * (attempt + 1))
    raise RuntimeError(f"Falha ao acessar API da Câmara: {last_err}")


@dataclass
class Dep:
    id: int
    nome: str
    siglaPartido: str
    siglaUf: str
    urlFoto: str
    email: str

    @property
    def key(self) -> str:
        return normalize_name(self.nome)


@st.cache_data(ttl=60 * 20, show_spinner=False)
def fetch_deputados_em_exercicio() -> Tuple[List[Dep], str]:
    url = f"{CAMARA_API_BASE}/deputados"
    params = {"itens": 600, "ordem": "ASC", "ordenarPor": "nome"}
    data = requests_get_json(url, params=params)
    deps: List[Dep] = []
    for d in data.get("dados", []) or []:
        try:
            deps.append(Dep(
                id=int(d.get("id")),
                nome=str(d.get("nome", "")).strip(),
                siglaPartido=str(d.get("siglaPartido", "")).strip(),
                siglaUf=str(d.get("siglaUf", "")).strip(),
                urlFoto=str(d.get("urlFoto", "")).strip(),
                email=str(d.get("email", "") or "").strip(),
            ))
        except Exception:
            continue
    deps = [x for x in deps if x.nome and x.id]
    return deps, datetime.now().strftime("%d/%m/%Y %H:%M")


# ═══════════════════════════════════════════
# Matching
# ═══════════════════════════════════════════

def build_index(deps: List[Dep]) -> Dict[str, Dep]:
    return {dep.key: dep for dep in deps}


def _suggest_similar(query_key: str, idx: Dict[str, Dep], top_n: int = 3) -> List[str]:
    words = set(query_key.split())
    scored: List[Tuple[int, str]] = []
    for key, dep in idx.items():
        score = sum(1 for w in words if w in key)
        if score > 0:
            scored.append((score, dep.nome))
    scored.sort(key=lambda x: -x[0])
    return [nome for _, nome in scored[:top_n]]


def _mailto(email: str) -> str:
    if not email:
        return ""
    subject = urllib.parse.quote(ASSUNTO_EMAIL)
    body = urllib.parse.quote(MENSAGEM_MOBILIZACAO)
    return f"mailto:{email}?subject={subject}&body={body}"


def _dep_row(x: Dep) -> dict:
    return {
        "Foto": x.urlFoto,
        "Nome": x.nome,
        "Partido": x.siglaPartido,
        "UF": x.siglaUf,
        "E-mail": x.email,
        "Pedir apoio": _mailto(x.email),
        "ID": x.id,
    }


def match_assinantes(
    assinantes_raw: List[str],
    deps: List[Dep],
) -> Tuple[pd.DataFrame, List[Tuple[str, List[str]]]]:
    idx = build_index(deps)
    resolved = [ALIASES_OFICIAIS.get(normalize_name(n), n) for n in assinantes_raw]
    found: List[Dep] = []
    nao_encontrados: List[Tuple[str, List[str]]] = []
    seen_dep_ids: set = set()

    for n in resolved:
        k = normalize_name(n)
        if not k:
            continue
        dep = idx.get(k)
        if dep is None:
            k2 = PREFIX_STRIP_RE.sub("", k).strip()
            dep = idx.get(k2)
        if dep is None:
            nao_encontrados.append((n, _suggest_similar(k, idx)))
            continue
        if dep.id in seen_dep_ids:
            continue
        seen_dep_ids.add(dep.id)
        found.append(dep)

    df = pd.DataFrame([_dep_row(x) for x in found])
    if not df.empty:
        df = df.sort_values("Nome").reset_index(drop=True)
    return df, nao_encontrados


def make_df_nao_assinou(deps: List[Dep], df_assinou: pd.DataFrame) -> pd.DataFrame:
    assinou_ids = set(df_assinou["ID"].tolist()) if not df_assinou.empty else set()
    rows = [_dep_row(d) for d in deps if d.id not in assinou_ids]
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("Nome").reset_index(drop=True)
    return df


def build_df_bancada(deps: List[Dep], df_assinou: pd.DataFrame) -> pd.DataFrame:
    assinou_ids = set(df_assinou["ID"].tolist()) if not df_assinou.empty else set()
    totais: Dict[str, int] = {}
    assinaram_ct: Dict[str, int] = {}
    for d in deps:
        p = d.siglaPartido or "?"
        totais[p] = totais.get(p, 0) + 1
        if d.id in assinou_ids:
            assinaram_ct[p] = assinaram_ct.get(p, 0) + 1
    rows = []
    for p, total in totais.items():
        assinou = assinaram_ct.get(p, 0)
        rows.append({
            "Partido": p,
            "Total na Câmara": total,
            "Assinaram": assinou,
            "Faltam": total - assinou,
            "% Adesão": round(assinou / total * 100, 1) if total > 0 else 0.0,
        })
    return pd.DataFrame(rows).sort_values("Assinaram", ascending=False).reset_index(drop=True)


# ═══════════════════════════════════════════
# Helpers visuais
# ═══════════════════════════════════════════

def render_kpi(label: str, value, css_class: str = "", sub: str = ""):
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div class="kpi-card {css_class}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def render_progress_bar(assinou: int, meta: int, total: int):
    pct = min(assinou / meta * 100, 100) if meta > 0 else 0
    if pct >= 100:
        color, pct_color = "linear-gradient(90deg,#1d7a4d,#2fae6e)", "#1d7a4d"
    elif pct >= 60:
        color, pct_color = "linear-gradient(90deg,#b8860b,#f4c454)", "#b8860b"
    else:
        color, pct_color = "linear-gradient(90deg,#123524,#2a6b48)", "#1d5238"
    marker_pct = (meta / total * 100) if total > 0 else 50
    st.markdown(f"""
    <div class="progress-wrapper">
        <div class="progress-label-row">
            <span class="prog-title">Caminho até as {meta} assinaturas necessárias para protocolar a PEC</span>
            <span class="prog-pct" style="color:{pct_color}">{assinou}/{meta} ({pct:.1f}%)</span>
        </div>
        <div class="progress-track">
            <div class="progress-fill" style="width:{min(pct,100):.2f}%;background:{color};"></div>
            <div class="progress-marker" style="left:{marker_pct:.1f}%;">
                <span class="progress-marker-label">{meta}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_table(df: pd.DataFrame, search_text: str = "", show_email: bool = True):
    if df.empty:
        st.info("Nenhum deputado com os filtros aplicados.")
        return
    df_show = df.copy()
    if search_text.strip():
        mask = df_show.apply(
            lambda r: any(search_text.lower() in str(r[c]).lower() for c in ["Nome", "Partido", "UF"]),
            axis=1,
        )
        df_show = df_show[mask].reset_index(drop=True)
    if df_show.empty:
        st.info(f'Nenhum resultado para "{search_text}".')
        return
    col_config = {
        "Foto":    st.column_config.ImageColumn("📷", help="Foto oficial — Câmara", width="small"),
        "Nome":    st.column_config.TextColumn("Nome", width="medium"),
        "Partido": st.column_config.TextColumn("Partido", width="small"),
        "UF":      st.column_config.TextColumn("UF", width="small"),
        "ID":      None,
    }
    if show_email:
        col_config["E-mail"] = st.column_config.TextColumn("E-mail", width="medium")
        col_config["Pedir apoio"] = st.column_config.LinkColumn(
            "✉️ Pedir apoio", display_text="Enviar e-mail",
            help="Abre seu e-mail com a mensagem de mobilização já preenchida",
        )
    else:
        col_config["E-mail"] = None
        col_config["Pedir apoio"] = None
    st.data_editor(
        df_show, hide_index=True, disabled=True, use_container_width=True,
        column_config=col_config,
    )
    st.caption(f"Exibindo {len(df_show)} deputado(s)")


def to_xlsx_multi(df_assinou: pd.DataFrame, df_nao: pd.DataFrame, df_bancada: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        configs = [
            (df_assinou,  "Assinaram",       ["Nome", "Partido", "UF", "E-mail"]),
            (df_nao,      "Ainda não",        ["Nome", "Partido", "UF", "E-mail"]),
            (df_bancada,  "Por Bancada",      ["Partido", "Total na Câmara", "Assinaram", "Faltam", "% Adesão"]),
        ]
        for df, sheet, cols in configs:
            df_exp = df[[c for c in cols if c in df.columns]] if not df.empty else pd.DataFrame(columns=cols)
            df_exp.to_excel(writer, index=False, sheet_name=sheet)
            ws = writer.sheets[sheet]
            for i, col in enumerate(df_exp.columns, 1):
                max_len = max(df_exp[col].astype(str).str.len().max() if not df_exp.empty else 0, len(col)) + 3
                ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = min(max_len, 45)
    return buf.getvalue()


def plot_partido(df: pd.DataFrame, color: str = "#1d5238") -> None:
    grouped = df.groupby("Partido").size().reset_index(name="Qtd")
    grouped = grouped.sort_values("Qtd", ascending=True).tail(15)
    if grouped.empty:
        st.info("Sem dados suficientes.")
        return
    fig, ax = plt.subplots(figsize=(6, max(3, len(grouped) * 0.45)))
    ax.barh(grouped["Partido"], grouped["Qtd"], color=color, height=0.65, edgecolor="none")
    for bar in ax.patches:
        w = bar.get_width()
        ax.text(w + 0.15, bar.get_y() + bar.get_height() / 2, f"{int(w)}", va="center", fontsize=8, fontweight="bold", color="#25382e")
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=8)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def plot_uf(df: pd.DataFrame, color: str = "#2a6b48") -> None:
    grouped = df.groupby("UF").size().reset_index(name="Qtd").sort_values("Qtd", ascending=False)
    if grouped.empty:
        st.info("Sem dados suficientes.")
        return
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(grouped["UF"], grouped["Qtd"], color=color, width=0.65, edgecolor="none")
    for bar in ax.patches:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.15, f"{int(h)}", ha="center", va="bottom", fontsize=7, fontweight="bold", color="#25382e")
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="x", labelsize=7, rotation=45)
    ax.tick_params(axis="y", labelsize=8)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def plot_oportunidade(df_bancada: pd.DataFrame) -> None:
    top = df_bancada.sort_values("Total na Câmara", ascending=False).head(15)
    top = top.sort_values("Assinaram", ascending=True)
    if top.empty:
        st.info("Sem dados suficientes.")
        return
    fig, ax = plt.subplots(figsize=(7, max(3, len(top) * 0.5)))
    ax.barh(top["Partido"], top["Assinaram"], color="#1d7a4d", height=0.65, edgecolor="none", label="Assinaram")
    ax.barh(top["Partido"], top["Faltam"], left=top["Assinaram"], color="#e5e7eb", height=0.65, edgecolor="none", label="Potencial restante")
    for _, row in top.iterrows():
        if row["Assinaram"] > 0:
            ax.text(row["Assinaram"] / 2, row["Partido"], str(int(row["Assinaram"])),
                    va="center", ha="center", fontsize=7, fontweight="bold", color="white")
        ax.text(row["Total na Câmara"] + 0.4, row["Partido"], f'{row["% Adesão"]:.0f}%',
                va="center", ha="left", fontsize=7, color="#6b7d72")
    ax.set_xlim(0, top["Total na Câmara"].max() * 1.18)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=8)
    ax.legend(loc="lower right", fontsize=8, framealpha=0.7)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


# ═══════════════════════════════════════════
# SIDEBAR (área de gestão — atualização da lista)
# ═══════════════════════════════════════════

with st.sidebar:
    st.markdown("### 📖 Atualizar lista de assinaturas")
    st.caption(
        "Área da equipe: cole aqui a lista do **Infoleg Autenticador** "
        "(campo 'Assinaturas do Documento'), um nome por linha. "
        "O painel é recalculado na hora."
    )
    assinantes_text = st.text_area(
        "Lista",
        value=ASSINANTES_RAW_DEFAULT,
        height=320,
        label_visibility="collapsed",
        placeholder="Cole a lista aqui…",
    )
    assinantes_list = parse_assinantes(assinantes_text)
    st.markdown(f"**{len(assinantes_list)}** nome(s) identificado(s)")

    st.divider()
    if st.button("🔄 Atualizar dados da Câmara", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.markdown(f"**Código Infoleg:** `{COD_INFOLEG}`")
    st.markdown("**Meta:** 171 assinaturas (1/3 da Câmara)")
    st.caption("Fonte: [Dados Abertos — Câmara](https://dadosabertos.camara.leg.br)")


# ═══════════════════════════════════════════
# Carregar dados
# ═══════════════════════════════════════════

with st.spinner("Consultando deputados em exercício…"):
    deps, fetch_ts = fetch_deputados_em_exercicio()

df_assinou, nao_encontrados = match_assinantes(assinantes_list, deps)
df_nao_assinou = make_df_nao_assinou(deps, df_assinou)
df_bancada     = build_df_bancada(deps, df_assinou)

total_api     = len(deps)
assinou_n     = int(df_assinou.shape[0])

# Foto oficial da autora: prioriza a URL retornada pela própria API
zanatta_foto = next((d.urlFoto for d in deps if d.id == ZANATTA_ID and d.urlFoto), ZANATTA_FOTO)
nao_assinou_n = total_api - assinou_n
faltam        = max(0, META_PEC - assinou_n)
pct_meta      = (assinou_n / META_PEC * 100) if META_PEC > 0 else 0
partidos_rep  = int(df_assinou["Partido"].nunique()) if not df_assinou.empty else 0


# ═══════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════

st.markdown(f"""
<div class="hero-header">
    <div class="hero-flex">
        <div class="hero-text">
            <div class="hero-badge">🚨 EM COLETA DE ASSINATURAS</div>
            <h1>📖 PEC do Homeschooling</h1>
            <p>
                <strong>Reconhecimento constitucional do ensino domiciliar</strong> como modalidade legítima
                de cumprimento do dever educacional familiar
            </p>
            <p style="margin-top:0.5rem;opacity:0.75;font-size:0.84rem;">
                Para ser protocolada, a PEC precisa da assinatura de <strong>171 deputados federais</strong> (1/3 da Câmara).
                Acompanhe abaixo quem já assinou — e ajude a mobilizar quem ainda falta.
            </p>
            <a class="hero-cta" href="{LINK_APOIAMENTO}" target="_blank">✍️ Deputado(a): assine a PEC aqui</a>
            <p style="margin-top:0.6rem;opacity:0.65;font-size:0.78rem;">
                Código Infoleg: {COD_INFOLEG} &nbsp;·&nbsp; Dados da Câmara: {fetch_ts}
            </p>
        </div>
        <div class="hero-autora">
            <a href="{ZANATTA_BIO}" target="_blank" title="Ver biografia oficial na Câmara dos Deputados">
                <img src="{zanatta_foto}" alt="Deputada Federal Júlia Zanatta">
                <div class="autora-nome">Dep. Júlia Zanatta<br>(PL/SC)</div>
                <div class="autora-cargo">Autora da PEC</div>
            </a>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════
# KPIs
# ═══════════════════════════════════════════

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    render_kpi("Já assinaram", assinou_n, "kpi-green", f"de {total_api} em exercício")
with k2:
    render_kpi("Faltam", faltam if faltam > 0 else "✓",
               "kpi-amber" if faltam > 0 else "kpi-green",
               "para protocolar a PEC")
with k3:
    render_kpi("% da meta", f"{pct_meta:.1f}%", "kpi-forest", f"{assinou_n} de {META_PEC}")
with k4:
    render_kpi("Partidos", partidos_rep, "kpi-purple", "bancadas representadas")
with k5:
    render_kpi("Ainda não assinaram", nao_assinou_n, "kpi-red",
               "potencial de mobilização")


# ═══════════════════════════════════════════
# Progresso + status
# ═══════════════════════════════════════════

render_progress_bar(assinou_n, META_PEC, total_api)

if nao_encontrados:
    st.markdown(
        f'<div class="status-banner status-warn">⚠️ {len(nao_encontrados)} nome(s) da lista não reconhecido(s) na base oficial — veja detalhes no fim da página.</div>',
        unsafe_allow_html=True,
    )
elif assinou_n >= META_PEC:
    st.markdown('<div class="status-banner status-ok">🎉 Meta atingida! A PEC já tem as assinaturas necessárias para ser protocolada.</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════
# Sobre a PEC (público externo)
# ═══════════════════════════════════════════

with st.expander("📘 O que diz a PEC? Entenda em 1 minuto"):
    st.markdown("""
A proposta altera os arts. 205, 208 e 226 da Constituição e acrescenta o art. 139 ao ADCT para:

- **Reconhecer o ensino domiciliar** ministrado pelos pais ou responsáveis legais como forma legítima de cumprir o dever educacional da família, **sem necessidade de autorização prévia** (art. 205, § 1º);
- **Garantir a liberdade de escolha educacional dos pais**, vedando ao Estado impor modalidade única de ensino (art. 226, § 9º);
- **Equiparar o ensino domiciliar ao cumprimento da educação básica obrigatória**, sem reduzir nenhuma garantia do ensino público (art. 208, § 4º);
- **Fixar parâmetros de responsabilidade**: avaliação anual do aprendizado, registro dos educandos junto ao poder público, preservação da convivência familiar e comunitária e atuação plena dos Conselhos Tutelares (art. 139 do ADCT);
- **Proteger as famílias**: o exercício regular do ensino domiciliar não configura abandono intelectual nem infração ao dever de matrícula — fim das multas e da criminalização de famílias diligentes.

Em 2018, o STF (RE 888.815, Tema 822) decidiu que a Constituição **não proíbe** o homeschooling, mas que cabe ao Congresso regulamentá-lo. Esta PEC ocupa exatamente o espaço que o próprio Supremo indicou.
""")

st.markdown("---")


# ═══════════════════════════════════════════
# Tabs principais
# ═══════════════════════════════════════════

tab_mob, tab_vis, tab_assinaram, tab_faltam, tab_bancada_t = st.tabs([
    "📣 Mobilização",
    "📊 Visão Geral",
    f"✅ Já assinaram ({assinou_n})",
    f"⏳ Ainda não assinaram ({nao_assinou_n})",
    "🎯 Por Bancada",
])

ufs      = sorted({d.siglaUf for d in deps if d.siglaUf})
partidos = sorted({d.siglaPartido for d in deps if d.siglaPartido})


# ─── Mobilização ──────────────────────────────────────────────────────────────

with tab_mob:
    col_msg, col_acoes = st.columns([3, 2])

    with col_msg:
        st.markdown("""
        <div class="mob-card">
            <h4><span class="mob-step">1</span>Copie a mensagem</h4>
            <p>Texto pronto para enviar por WhatsApp, e-mail ou redes sociais aos gabinetes.
            Use o ícone de copiar no canto do bloco abaixo.</p>
        </div>
        """, unsafe_allow_html=True)
        st.code(MENSAGEM_MOBILIZACAO, language=None)

    with col_acoes:
        st.markdown(f"""
        <div class="mob-card">
            <h4><span class="mob-step">2</span>Compartilhe o link de assinatura</h4>
            <p>Deputados assinam diretamente pelo aplicativo Infoleg:</p>
        </div>
        """, unsafe_allow_html=True)
        st.code(LINK_APOIAMENTO, language=None)
        st.code(f"Código da PEC: {COD_INFOLEG}", language=None)

        st.markdown("""
        <div class="mob-card">
            <h4><span class="mob-step">3</span>Aborde quem ainda não assinou</h4>
            <p>Na aba <strong>⏳ Ainda não assinaram</strong>, cada deputado tem um botão
            <strong>✉️ Pedir apoio</strong> que abre seu e-mail com a mensagem já preenchida.
            Ou copie abaixo a lista completa de e-mails para um envio em massa (use CCO).</p>
        </div>
        """, unsafe_allow_html=True)

        emails_faltantes = [e for e in (df_nao_assinou["E-mail"].tolist() if not df_nao_assinou.empty else []) if e]
        with st.expander(f"📋 Copiar e-mails de quem ainda não assinou ({len(emails_faltantes)})"):
            st.caption("Lista separada por ponto e vírgula — cole no campo CCO do seu e-mail.")
            st.code("; ".join(emails_faltantes), language=None)

        filtro_partido_mob = st.multiselect(
            "Ou gere a lista de e-mails por partido:",
            options=partidos, default=[],
            help="Útil para mobilização direcionada por bancada.",
        )
        if filtro_partido_mob and not df_nao_assinou.empty:
            emails_filtrados = [
                e for e in df_nao_assinou[df_nao_assinou["Partido"].isin(filtro_partido_mob)]["E-mail"].tolist() if e
            ]
            st.code("; ".join(emails_filtrados) if emails_filtrados else "Nenhum e-mail disponível para o filtro.", language=None)
            st.caption(f"{len(emails_filtrados)} e-mail(s) no filtro selecionado")


# ─── Visão Geral ──────────────────────────────────────────────────────────────

with tab_vis:
    gc1, gc2 = st.columns(2)
    with gc1:
        st.markdown('<div class="chart-title">Assinaturas por Partido (top 15)</div>', unsafe_allow_html=True)
        plot_partido(df_assinou)
    with gc2:
        st.markdown('<div class="chart-title">Assinaturas por Estado</div>', unsafe_allow_html=True)
        plot_uf(df_assinou)


# ─── Já assinaram ─────────────────────────────────────────────────────────────

with tab_assinaram:
    st.caption("Deputados que já assinaram a PEC. Que tal agradecer publicamente nas redes? Reconhecimento também mobiliza. 💚")
    fa1, fa2, fa3 = st.columns([2, 2, 3])
    with fa1:
        uf_sel_a = st.multiselect("UF", options=ufs, default=[], key="uf_assinaram")
    with fa2:
        partido_sel_a = st.multiselect("Partido", options=partidos, default=[], key="part_assinaram")
    with fa3:
        search_a = st.text_input("🔍 Buscar", key="search_assinaram", placeholder="Nome, partido ou UF…")

    df_view_a = df_assinou.copy()
    if uf_sel_a:
        df_view_a = df_view_a[df_view_a["UF"].isin(uf_sel_a)]
    if partido_sel_a:
        df_view_a = df_view_a[df_view_a["Partido"].isin(partido_sel_a)]
    render_table(df_view_a.reset_index(drop=True), search_a, show_email=False)

    if not df_assinou.empty:
        st.download_button(
            "⬇️ Baixar relatório completo (Excel — Assinaram / Ainda não / Por Bancada)",
            data=to_xlsx_multi(df_assinou, df_nao_assinou, df_bancada),
            file_name="pec_homeschooling_apoiamentos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


# ─── Ainda não assinaram ──────────────────────────────────────────────────────

with tab_faltam:
    st.caption(
        "Estes deputados ainda não assinaram. Use os filtros para encontrar os parlamentares "
        "do seu estado e clique em **✉️ Pedir apoio** para enviar a mensagem de mobilização."
    )
    fn1, fn2, fn3 = st.columns([2, 2, 3])
    with fn1:
        uf_sel_n = st.multiselect("UF", options=ufs, default=[], key="uf_faltam")
    with fn2:
        partido_sel_n = st.multiselect("Partido", options=partidos, default=[], key="part_faltam")
    with fn3:
        search_n = st.text_input("🔍 Buscar", key="search_faltam", placeholder="Nome, partido ou UF…")

    df_view_n = df_nao_assinou.copy()
    if uf_sel_n:
        df_view_n = df_view_n[df_view_n["UF"].isin(uf_sel_n)]
    if partido_sel_n:
        df_view_n = df_view_n[df_view_n["Partido"].isin(partido_sel_n)]
    render_table(df_view_n.reset_index(drop=True), search_n, show_email=True)


# ─── Por Bancada ──────────────────────────────────────────────────────────────

with tab_bancada_t:
    st.markdown(
        "Visão estratégica por partido: tamanho de cada bancada, quantos já assinaram "
        "e onde está o maior potencial de novas assinaturas."
    )

    bc1, bc2 = st.columns([1, 1])

    with bc1:
        st.markdown('<div class="chart-title">Bancada: assinaram ✅ vs. potencial restante (top 15 por tamanho)</div>', unsafe_allow_html=True)
        plot_oportunidade(df_bancada)

    with bc2:
        st.markdown('<div class="chart-title">Tabela detalhada</div>', unsafe_allow_html=True)
        search_b = st.text_input("🔍 Filtrar partido", key="search_bancada", placeholder="Ex: PL, PT, UNIÃO…")
        df_b_view = df_bancada.copy()
        if search_b.strip():
            df_b_view = df_b_view[df_b_view["Partido"].str.contains(search_b.strip(), case=False)]

        st.dataframe(
            df_b_view.reset_index(drop=True),
            hide_index=True,
            use_container_width=True,
            column_config={
                "Partido":         st.column_config.TextColumn("Partido", width="small"),
                "Total na Câmara": st.column_config.NumberColumn("Total", format="%d"),
                "Assinaram":       st.column_config.NumberColumn("✅ Assinaram", format="%d"),
                "Faltam":          st.column_config.NumberColumn("⏳ Faltam", format="%d"),
                "% Adesão":        st.column_config.ProgressColumn(
                    "% Adesão", min_value=0, max_value=100, format="%.1f%%"
                ),
            },
        )
        st.caption(f"{len(df_b_view)} partido(s) exibido(s)")


# ═══════════════════════════════════════════
# Nomes não reconhecidos (com sugestões)
# ═══════════════════════════════════════════

if nao_encontrados:
    st.markdown("---")
    with st.expander(f"⚠️ Nomes não reconhecidos ({len(nao_encontrados)}) — sugestões de correção", expanded=True):
        st.markdown(
            "Esses nomes constam na lista mas não foram localizados entre os deputados em exercício. "
            "Podem ser senadores, ex-deputados, ou grafia diferente do nome parlamentar oficial. "
            "Para cada um são sugeridos os nomes mais próximos encontrados na API:"
        )
        for nome, sugestoes in nao_encontrados:
            sug_html = "  →  " + " / ".join(f"<code>{s}</code>" for s in sugestoes) if sugestoes else ""
            st.markdown(
                f'<div class="alias-suggestion">❓ <strong>{nome}</strong>{sug_html}</div>',
                unsafe_allow_html=True,
            )
        st.caption(
            "Para corrigir: adicione o alias correto no dicionário ALIASES_OFICIAIS no topo do arquivo, "
            "ou ajuste o nome diretamente na lista colada na sidebar."
        )


# ═══════════════════════════════════════════
# Rodapé
# ═══════════════════════════════════════════

st.markdown("---")
st.caption(
    f"📖 PEC do Homeschooling · Autoria: Dep. Júlia Zanatta (PL/SC) · Código Infoleg: {COD_INFOLEG} · "
    f"Dados oficiais da [API de Dados Abertos da Câmara dos Deputados](https://dadosabertos.camara.leg.br), "
    f"atualizados em {fetch_ts}. A lista de assinaturas é conferida manualmente pelo gabinete via Infoleg Autenticador."
)

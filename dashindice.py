"""
╔══════════════════════════════════════════════════════════════════╗
║   DASHBOARD INSTITUCIONAL MARKET MAKER — MINI ÍNDICE (WIN)      ║
║   Engine: V9.6  |  Layout: Cyberpunk HUD  |  WIN EDITION V4.1   ║
║   6 PILARES: EWZ · VALE · PBR · SPY · USO · EEM                ║
║   MODO: VISÃO AGREGADA TOTAL — 100% ESPAÇO WIN                  ║
║                                                                  ║
║   v4.1 — CORREÇÕES MOMENTUM REAL:                               ║
║     Bug 1: OI estrutural usa df_win_all (todos strikes, vol>=0) ║
║     Bug 2: Vol/OI calculado após groupby (ratio do agregado)    ║
╚══════════════════════════════════════════════════════════════════╝
"""

import json, os, re, math, glob, io
import re as _re
import requests
import yaml
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime, datetime as _dt, date as _date

st.set_page_config(
    page_title="Dashboard WIN — 6 Pilares (Agregado)",
    layout="wide",
    initial_sidebar_state="expanded",
)

import time as _time
if "last_refresh" not in st.session_state:
    st.session_state["last_refresh"] = _time.time()
_elapsed = _time.time() - st.session_state["last_refresh"]
if _elapsed > 60:
    st.session_state["last_refresh"] = _time.time()
    st.rerun()

HUD_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    background: radial-gradient(circle at 20% 30%, #0a0c12, #030507) !important;
    color: #c5f5ef; font-family: 'JetBrains Mono', monospace; font-size: 13px;
}
.stApp { background: radial-gradient(circle at 20% 30%, #0a0c12, #030507) !important; }
[data-testid="stAppViewContainer"] { background: radial-gradient(circle at 20% 30%, #0a0c12, #030507) !important; }
[data-testid="stHeader"] { background: rgba(3, 5, 7, 0.95) !important; }
[data-testid="stMain"] { background: transparent !important; }
section[data-testid="stMain"] > div { background: transparent !important; }
[data-testid="stSidebar"] {
    background: rgba(8, 12, 20, 0.85) !important; backdrop-filter: blur(12px);
    border-right: 1px solid rgba(0, 255, 255, 0.2);
}
[data-testid="stSidebar"] * { color: #c5f5ef !important; font-size: 13px !important; }
[data-testid="stSidebar"] input {
    background: rgba(12, 18, 28, 0.8) !important; border: 1px solid rgba(0, 255, 255, 0.3) !important;
    color: #00ffe7 !important; font-size: 13px !important;
}
[data-testid="stSidebar"] label { color: #0ff !important; font-size: 13px !important; letter-spacing: 1px; }
h1, h2, h3, .stMarkdown h1, .stMarkdown h2 {
    font-family: 'Inter', sans-serif; font-weight: 700; letter-spacing: -0.5px;
    background: linear-gradient(135deg, #FFFFFF 0%, #88AAFF 100%);
    -webkit-background-clip: text; background-clip: text; color: transparent;
    text-shadow: 0 0 8px rgba(136,170,255,0.3);
}
.dashboard-card {
    background: rgba(12, 18, 28, 0.65); backdrop-filter: blur(8px);
    border: 1px solid rgba(0, 255, 255, 0.2); border-radius: 16px;
    padding: 1rem; margin-bottom: 1rem;
    box-shadow: 0 8px 20px rgba(0,0,0,0.5), 0 0 12px rgba(0, 255, 255, 0.1);
}
.dashboard-card:hover { border-color: #0ff; box-shadow: 0 0 18px rgba(0,255,255,0.3); background: rgba(12,18,28,0.8); }
.win-card {
    background: rgba(12, 18, 28, 0.65); backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 180, 0, 0.35); border-radius: 16px;
    padding: 1rem; margin-bottom: 1rem;
    box-shadow: 0 8px 20px rgba(0,0,0,0.5), 0 0 12px rgba(255,180,0,0.12);
}
.kpi-card {
    background: rgba(12, 18, 28, 0.65); backdrop-filter: blur(8px);
    border: 1px solid rgba(0, 255, 255, 0.2); border-left: 3px solid #00ffe7;
    border-radius: 12px; padding: 14px 16px; margin-bottom: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4), 0 0 8px rgba(0, 255, 255, 0.08);
}
.kpi-label {
    font-family: 'JetBrains Mono', monospace; font-size: 13px; letter-spacing: 2px;
    color: #0ff; text-shadow: 0 0 4px #0ff; text-transform: uppercase; margin-bottom: 4px;
}
.kpi-value {
    font-family: 'JetBrains Mono', monospace; font-size: 22px; font-weight: 700;
    color: #f0f3fa; text-shadow: 0 0 5px rgba(0,255,255,0.5); letter-spacing: -0.5px; line-height: 1;
}
.kpi-value.bull { color: #0f0; text-shadow: 0 0 10px rgba(0,255,0,0.5); }
.kpi-value.bear { color: #f44; text-shadow: 0 0 10px rgba(255,68,68,0.5); }
.kpi-value.neutral { color: #fa0; }
.kpi-sub { font-size: 13px; color: #8a9bb5; margin-top: 4px; }
.sec-header {
    font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 700;
    letter-spacing: 3px; color: #0ff; text-shadow: 0 0 4px #0ff;
    border-bottom: 1px solid rgba(0, 255, 255, 0.2);
    padding-bottom: 6px; margin: 18px 0 10px 0; text-transform: uppercase;
}
.sec-header::before { content: "◈  "; color: rgba(0,255,255,0.5); }
.sec-header-win {
    font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 700;
    letter-spacing: 3px; color: #ffb400; text-shadow: 0 0 4px #ffb400;
    border-bottom: 1px solid rgba(255,180,0,0.3);
    padding-bottom: 6px; margin: 18px 0 10px 0; text-transform: uppercase;
}
.sec-header-win::before { content: "◈  "; color: rgba(255,180,0,0.5); }
.alert-success { background:rgba(0,255,0,0.08); border:1px solid rgba(0,255,0,0.4); border-left:4px solid #0f0; border-radius:8px; padding:10px 14px; font-size:13px; color:#0f0; margin:8px 0; font-family:'JetBrains Mono',monospace; }
.alert-warning { background:rgba(255,165,0,0.08); border:1px solid rgba(255,165,0,0.4); border-left:4px solid #fa0; border-radius:8px; padding:10px 14px; font-size:13px; color:#fa0; margin:8px 0; font-family:'JetBrains Mono',monospace; }
.alert-danger  { background:rgba(255,68,68,0.08);  border:1px solid rgba(255,68,68,0.4);  border-left:4px solid #f44; border-radius:8px; padding:10px 14px; font-size:13px; color:#f44; margin:8px 0; font-family:'JetBrains Mono',monospace; }
.alert-info    { background:rgba(0,255,231,0.06);  border:1px solid rgba(0,255,231,0.3);  border-left:4px solid #0ff; border-radius:8px; padding:10px 14px; font-size:13px; color:#0ff; margin:8px 0; font-family:'JetBrains Mono',monospace; }
.alert-win     { background:rgba(255,180,0,0.07);  border:1px solid rgba(255,180,0,0.4);  border-left:4px solid #ffb400; border-radius:8px; padding:10px 14px; font-size:13px; color:#ffb400; margin:8px 0; font-family:'JetBrains Mono',monospace; }
.hud-table { width:100%; border-collapse:collapse; font-family:'JetBrains Mono',monospace; font-size:13px; }
.hud-table th { color:#0ff; text-shadow:0 0 3px #0ff; text-align:left; font-size:13px; letter-spacing:1.5px; border-bottom:1px solid rgba(0,255,255,0.3); padding:6px 8px; text-transform:uppercase; }
.hud-table td { padding:7px 8px; border-bottom:1px solid rgba(255,255,255,0.04); color:#ccddf8; font-size:13px; }
.hud-table tr:hover td { background: rgba(0,255,255,0.04); }
.pine-box {
    background:rgba(4,8,14,0.9); border:1px solid rgba(0,255,255,0.25);
    border-left:4px solid #00ffe7; border-radius:10px; padding:14px 16px;
    font-family:'JetBrains Mono',monospace; font-size:12px; color:#8AE6C0;
    white-space:pre; overflow-x:auto; margin:8px 0;
}
.win-badge {
    display:inline-block; background:rgba(255,180,0,0.15); border:1px solid rgba(255,180,0,0.5);
    border-radius:6px; padding:2px 8px; font-size:13px; color:#ffb400;
    font-family:'JetBrains Mono',monospace; font-weight:bold; text-shadow:0 0 6px rgba(255,180,0,0.5);
}
.whale-card {
    background:rgba(12,18,28,0.65); border:1px solid rgba(0,255,255,0.15);
    border-radius:8px; padding:8px 12px; margin-bottom:6px;
    font-size:13px; font-family:'JetBrains Mono',monospace;
}
.tag { padding:2px 8px; border-radius:20px; font-size:13px; font-weight:700; font-family:'JetBrains Mono',monospace; background:rgba(0,0,0,0.5); backdrop-filter:blur(4px); border:1px solid; }
.tag-bull   { background:rgba(0,255,0,0.12);   color:#0f0; border-color:#0f0; box-shadow:0 0 5px #0f0; }
.tag-bear   { background:rgba(255,50,50,0.12);  color:#f44; border-color:#f44; box-shadow:0 0 5px #f44; }
.tag-neutral{ background:rgba(255,165,0,0.12);  color:#fa0; border-color:#fa0; box-shadow:0 0 5px #fa0; }
.text-green { color:#0f0; text-shadow:0 0 3px #0f0; }
.text-red   { color:#f44; text-shadow:0 0 3px #f44; }
.text-cyan  { color:#0ff; text-shadow:0 0 3px #0ff; }
.text-dim   { color:#8a9bb5; font-size:13px; letter-spacing:0.5px; }
.text-gold  { color:#fa0; text-shadow:0 0 3px #fa0; }
.text-win   { color:#ffb400; text-shadow:0 0 4px rgba(255,180,0,0.6); font-weight:bold; }
.glow-divider     { height:1px; background:linear-gradient(90deg, transparent, #0ff, #0ff, transparent); margin:12px 0; }
.glow-divider-win { height:1px; background:linear-gradient(90deg, transparent, #ffb400, #ffb400, transparent); margin:12px 0; }
body::after {
    content:""; position:fixed; top:0; left:0; width:100vw; height:100vh;
    background:repeating-linear-gradient(0deg,rgba(0,255,255,0.015) 0px,rgba(0,255,255,0.015) 2px,transparent 2px,transparent 6px);
    pointer-events:none; z-index:9999;
}
div[data-testid="stNumberInput"] input, div[data-testid="stTextInput"] input {
    background:rgba(12,18,28,0.8) !important; border:1px solid rgba(0,255,255,0.2) !important;
    color:#00ffe7 !important; font-family:'JetBrains Mono',monospace !important;
    border-radius:6px !important; font-size:13px !important;
}
.stSelectbox > div > div { background:rgba(12,18,28,0.8) !important; border:1px solid rgba(0,255,255,0.2) !important; color:#00ffe7 !important; border-radius:6px !important; font-size:13px !important; }
.stDownloadButton button { background:linear-gradient(90deg,#0a2b3a,#02131c); border:1px solid #0ff; border-radius:40px; color:#0ff; font-family:'JetBrains Mono',monospace; transition:0.2s; font-size:13px !important; }
.stDownloadButton button:hover { box-shadow:0 0 12px #0ff; border-color:#0ff; color:#fff; }
::-webkit-scrollbar { width:4px; height:4px; }
::-webkit-scrollbar-track { background:rgba(3,5,7,0.8); }
::-webkit-scrollbar-thumb { background:rgba(0,255,255,0.3); border-radius:2px; }
::-webkit-scrollbar-thumb:hover { background:#0ff; }
hr { border-color:rgba(0,255,255,0.15) !important; }
</style>
"""
st.markdown(HUD_CSS, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# LOGIN · CONTROLE DE ACESSO POR EMAIL
# ══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=60)
def carregar_emails_autorizados():
    GITHUB_USER   = "fclfrancis"
    GITHUB_REPO   = "dashboard-etf"
    GITHUB_BRANCH = "main"
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/config.yaml"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            emails = []
            for linha in r.text.splitlines():
                linha = linha.strip()
                if linha.startswith("- "):
                    email = linha[2:].strip().strip('"').strip("'").lower()
                    if "@" in email:
                        emails.append(email)
            return emails
    except:
        pass
    return []

def tela_login():
    st.markdown(
        "<div style='max-width:420px;margin:80px auto 0;'>"
        "<div class='dashboard-card' style='padding:32px;text-align:center;'>"
        "<div style='font-family:Inter,sans-serif;font-size:22px;font-weight:700;"
        "background:linear-gradient(135deg,#fff,#ffb400);-webkit-background-clip:text;"
        "background-clip:text;color:transparent;margin-bottom:8px;'>📡 WIN DASHBOARD</div>"
        "<div style='color:#4a7a75;font-size:13px;letter-spacing:2px;margin-bottom:28px;'>"
        "DASHBOARD INSTITUCIONAL · V9.6 WIN</div>"
        "</div></div>",
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        email_input = st.text_input(
            "📧 Seu email:",
            placeholder="seuemail@exemplo.com",
            key="login_email"
        )
        entrar = st.button("ENTRAR", use_container_width=True)
        if entrar:
            email = email_input.lower().strip()
            autorizados = carregar_emails_autorizados()
            if email and email in autorizados:
                st.session_state["email_logado"] = email
                st.rerun()
            elif email:
                st.markdown(
                    "<div class='alert-danger'>❌ Email não autorizado. Entre em contato com o administrador.</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "<div class='alert-warning'>⚠ Digite seu email para continuar.</div>",
                    unsafe_allow_html=True,
                )
    st.stop()

if "email_logado" not in st.session_state:
    tela_login()

with st.sidebar:
    st.markdown(
        f"<div style='font-size:13px;color:#4a7a75;margin-bottom:8px;'>"
        f"✅ {st.session_state['email_logado']}</div>",
        unsafe_allow_html=True,
    )
    if st.button("🚪 Sair", use_container_width=True):
        del st.session_state["email_logado"]
        st.rerun()
    st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# 1 · CONSTANTES
# ══════════════════════════════════════════════════════════════════
LAST_STALE_THRESHOLD = 0.85
COLOR_CALL   = "#FF3131"
COLOR_PUT    = "#00FF00"
COLOR_NEON   = "#00ffe7"
COLOR_PURPLE = "#7b2fff"
COLOR_ORANGE = "#ff6b35"
COLOR_GOLD   = "#f0c040"
COLOR_WIN    = "#ffb400"

TICKERS_PILARES    = ["EWZ", "VALE", "PBR", "SPY", "USO", "EEM"]
TICKERS_SUPORTADOS = TICKERS_PILARES

_PESOS_CORR = {
    "EWZ": 1.00, "VALE": 0.11014, "PBR": 0.08307,
    "SPY": 0.40, "USO":  0.30,    "EEM": 0.20,
}
_BUCKET_WIN = 100
_MULT       = 100.0

# ══════════════════════════════════════════════════════════════════
# 2 · HELPERS UI
# ══════════════════════════════════════════════════════════════════

def fmt_M(v):
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))): return "—"
    a = abs(v); sign = "-" if v < 0 else "+"
    return f"{sign}{a/1e3:.1f}K" if a < 1e6 else f"{sign}{a/1e6:.1f}M"

def fmt_win(pts):
    return f"{int(pts):,.0f}".replace(",", ".")

def _fmt_strike(v: float) -> str:
    if v == 0: return "0"
    if abs(v) < 100: return f"{v:.5f}".rstrip("0").rstrip(".")
    return f"{v:,.0f}".replace(",", ".")

def kpi(label, value, cls="", sub=""):
    return (f"<div class='kpi-card'><div class='kpi-label'>{label}</div>"
            f"<div class='kpi-value {cls}'>{value}</div>"
            f"<div class='kpi-sub'>{sub}</div></div>")

def alert_box(msg, kind="info"):
    return f"<div class='alert-{kind}'>{msg}</div>"

def section(title, win=False):
    cls = "sec-header-win" if win else "sec-header"
    st.markdown(f"<div class='{cls}'>{title}</div>", unsafe_allow_html=True)

def dist_win(a: int, b: int) -> str:
    d = a - b
    return f"{d:+,}".replace(",", ".") + " pts"

# ══════════════════════════════════════════════════════════════════
# 3 · HELPERS MATEMÁTICOS
# ══════════════════════════════════════════════════════════════════

def _clean_num(x):
    if x is None: return 0.0
    try:
        s = str(x).strip().replace(",", "").replace("N/A", "0")
        return float(s) if s not in ("", "None", "null", "nan") else 0.0
    except: return 0.0

def _clean(v) -> float:
    try:
        v = float(v)
        return 0.0 if (math.isnan(v) or math.isinf(v)) else v
    except: return 0.0

def _zscore_series(s: pd.Series) -> pd.Series:
    std = s.std()
    if std == 0 or math.isnan(std): return pd.Series(0.0, index=s.index)
    return (s - s.mean()) / std

def _bucket_win(win_pts: float) -> int:
    return int(round(win_pts / _BUCKET_WIN) * _BUCKET_WIN)

def strike_to_win(strike_usd: float, spot_usd: float, ibov: float) -> int:
    if spot_usd <= 0: return 0
    return int(round(ibov * (strike_usd / spot_usd) / 100) * 100)

# ══════════════════════════════════════════════════════════════════
# 4 · AGRUPAMENTO DE ARQUIVOS
# ══════════════════════════════════════════════════════════════════

def agrupar_snapshots(caminhos: list) -> dict:
    snapshots: dict = {}
    for caminho in caminhos:
        nome  = os.path.basename(caminho)
        match = re.search(r"(\d{4}-\d{2}-\d{2})", nome)
        chave = match.group(1) if match else nome.rsplit(".", 1)[0]
        snapshots.setdefault(chave, []).append(caminho)
    return dict(sorted(snapshots.items(), reverse=True))

def agrupar_por_ticker(caminhos: list) -> dict:
    grupos: dict = {}
    for c in caminhos:
        nome = os.path.basename(c).upper()
        for tk in TICKERS_SUPORTADOS:
            if tk in nome:
                grupos.setdefault(tk, []).append(c)
                break
    return {tk: v for tk, v in grupos.items() if tk in TICKERS_PILARES}

# ══════════════════════════════════════════════════════════════════
# 5 · PARSER JSON
# ══════════════════════════════════════════════════════════════════

def parse_json(source) -> pd.DataFrame | None:
    try:
        if hasattr(source, "read"):
            source.seek(0); js = json.load(source)
        else:
            with open(source, "r", encoding="utf-8") as fh: js = json.load(fh)
    except Exception as e:
        st.warning(f"Erro ao abrir {getattr(source, 'name', source)}: {e}")
        return None

    data_block = js.get("data", {})
    records = []

    if isinstance(data_block, dict) and ("Call" in data_block or "Put" in data_block):
        for opt_type in ("Call", "Put"):
            for row in data_block.get(opt_type, []):
                raw = row.get("raw", row)
                raw["_opt_type"]   = opt_type
                raw["_strike_str"] = str(raw.get("strikePrice", raw.get("strike", "0")))
                if "tradeTime" not in raw and "tradeTime" in row:
                    raw["tradeTime"] = row["tradeTime"]
                records.append(raw)
    elif isinstance(data_block, dict):
        key  = list(data_block.keys())[0] if data_block else ""
        rows = data_block.get(key, [])
        if not isinstance(rows, list): rows = []
        for row in rows:
            raw = row.get("raw", row)
            strike_str = str(row.get("strike", raw.get("strike", "")))
            raw["_opt_type"]    = "Call" if strike_str.upper().endswith("C") else "Put"
            raw["_strike_str"]  = strike_str
            raw["tradeTime_str"] = str(row.get("tradeTime", ""))
            records.append(raw)
    elif isinstance(data_block, list):
        for row in data_block:
            raw = row.get("raw", row)
            strike_str = str(row.get("strike", raw.get("strike", "")))
            raw["_opt_type"]    = "Call" if strike_str.upper().endswith("C") else "Put"
            raw["_strike_str"]  = strike_str
            raw["tradeTime_str"] = str(row.get("tradeTime", ""))
            records.append(raw)

    if not records: return None
    df = pd.DataFrame(records)

    def _parse_strike(row):
        s = str(row.get("_strike_str", row.get("strikePrice", row.get("strike", "0"))))
        s = re.sub(r"[CPcp]$", "", s.replace(",", "").strip())
        try: return float(s)
        except: return 0.0

    df["strikePrice"] = df.apply(_parse_strike, axis=1)
    df["optionType"]  = df["_opt_type"]

    for col in ["strikePrice", "bidPrice", "askPrice", "lastPrice",
                "volume", "openInterest", "delta", "gamma", "vega"]:
        if col in df.columns: df[col] = df[col].apply(_clean_num)
        else: df[col] = 0.0

    df = df[df["strikePrice"] > 0].copy()
    return df if not df.empty else None

# ══════════════════════════════════════════════════════════════════
# 6 · DETECÇÃO DE SPOT
# ══════════════════════════════════════════════════════════════════

def detectar_spot(df: pd.DataFrame, spot_manual=None) -> float:
    if spot_manual and spot_manual > 0: return float(spot_manual)
    calls = df[df["optionType"] == "Call"].copy()
    if calls.empty: return 0.0
    valid = calls[calls["delta"].between(0.01, 0.99)]
    if valid.empty: return float(calls["strikePrice"].median())
    return float(valid.loc[(valid["delta"] - 0.5).abs().idxmin(), "strikePrice"])

def _detectar_spot_pcp(df: pd.DataFrame) -> float:
    try:
        by_strike = {}
        for _, row in df.iterrows():
            sk  = float(row.get("strikePrice", 0))
            bid = float(row.get("bidPrice", 0) or 0)
            ask = float(row.get("askPrice", 0) or 0)
            d   = float(row.get("delta", 0) or 0)
            opt = row.get("optionType", "")
            if sk <= 0 or bid <= 0 or ask <= 0: continue
            by_strike.setdefault(sk, {})
            if opt == "Call": by_strike[sk]["call"] = {"mid": (bid+ask)/2, "delta": abs(d)}
            elif opt == "Put": by_strike[sk]["put"]  = {"mid": (bid+ask)/2}
        estimates = []
        for sk, sides in by_strike.items():
            c = sides.get("call"); p = sides.get("put")
            if not c or not p: continue
            F = sk + c["mid"] - p["mid"]
            w = 1.0 / (abs(c["delta"] - 0.5) + 0.001)
            estimates.append((F, w))
        if not estimates: return 0.0
        tw = sum(w for _, w in estimates)
        return sum(F*w for F, w in estimates) / tw
    except: return 0.0

# ══════════════════════════════════════════════════════════════════
# 7 · ENGINE V9 — cálculo de greeks por linha (espaço USD)
# ══════════════════════════════════════════════════════════════════

def calcular_v9(df_raw: pd.DataFrame, spot: float, mult: float = 100.0) -> pd.DataFrame:
    df = df_raw[df_raw["volume"] > 0].copy()
    if df.empty: return df

    records = []
    for _, row in df.iterrows():
        last  = _clean_num(row.get("lastPrice", 0))
        bid   = _clean_num(row.get("bidPrice",  0))
        ask   = _clean_num(row.get("askPrice",  0))
        delta = _clean_num(row.get("delta",     0))
        gamma = _clean_num(row.get("gamma",     0))
        vega  = _clean_num(row.get("vega",      0))
        vol   = _clean_num(row.get("volume",    0))
        oi    = _clean_num(row.get("openInterest", 0))
        sp    = _clean_num(row.get("strikePrice",  0))
        opt   = row.get("optionType", "Call")
        tt    = row.get("tradeTime", row.get("tradeTime_str", None))

        bid_ask_ok = bid > 0 and ask > 0
        mid_price  = (bid + ask) / 2 if bid_ask_ok else last
        last_ok    = bid_ask_ok and last > 0 and (last >= bid * LAST_STALE_THRESHOLD)

        if last_ok:
            direction = 1 if last >= mid_price else -1
            side      = "BUY" if direction == 1 else "SELL"
        elif bid_ask_ok:
            direction = 0; side = "BRUTO_STALE"
        else:
            direction = 0; side = "BRUTO_NOBID"

        greeks_ok = not (delta == 0 and gamma == 0 and vega == 0 and sp != spot)
        opt_sign  = 1 if opt == "Call" else -1

        d_flow    = delta * vol * mult * spot * direction
        dex_total = d_flow
        gex_total = (gamma * vol * mult * (spot**2) * opt_sign * direction
                     if greeks_ok and direction != 0 else 0.0)
        vanna_total = ((delta * vega / spot) * vol * mult * direction * opt_sign
                       if greeks_ok and spot > 0 and direction != 0 else 0.0)
        fin_flow  = mid_price * vol * mult
        hiro      = -opt_sign * abs(delta) * vol * mult * spot
        dex_oi    = delta * oi * mult * spot * opt_sign
        gex_oi    = gamma * oi * mult * (spot**2) * opt_sign if greeks_ok else 0.0

        records.append({
            "strikePrice": sp, "optionType": opt,
            "side": side, "direction": direction, "greeks_ok": greeks_ok,
            "volume": vol, "openInterest": oi,
            "delta": delta, "gamma": gamma, "vega": vega,
            "lastPrice": last, "bidPrice": bid, "askPrice": ask,
            "d_flow": d_flow, "g_flow": gex_total,
            "gex_total": gex_total, "dex_total": dex_total,
            "vanna_total": vanna_total, "financial_flow": fin_flow,
            "hiro": hiro, "dex_oi": dex_oi, "gex_oi": gex_oi,
            "tradeTime": tt,
        })

    return pd.DataFrame(records) if records else pd.DataFrame()

# ══════════════════════════════════════════════════════════════════
# 8 · PROCESSAR INTELIGÊNCIA
# ══════════════════════════════════════════════════════════════════

def processar_inteligencia(df: pd.DataFrame, spot: float, threshold: float = 2.5):
    if df is None or df.empty: return None, 0.0
    std = df["d_flow"].std()
    df  = df.copy()
    df["z_score"] = (df["d_flow"] - df["d_flow"].mean()) / std if std > 0 else 0.0
    whales    = df[df["z_score"].abs() > threshold].copy()
    net_delta = df["d_flow"].sum()

    gex_by_s  = df.groupby("strikePrice")["gex_total"].sum().sort_index()
    gex_vals  = gex_by_s.values; gex_idx = gex_by_s.index.tolist()
    gamma_flip = 0.0
    for i in range(len(gex_vals) - 1):
        if gex_vals[i] * gex_vals[i+1] < 0:
            k0, k1 = gex_idx[i], gex_idx[i+1]
            g0, g1 = gex_vals[i], gex_vals[i+1]
            gamma_flip = k0 + (k1-k0)*(-g0)/(g1-g0)
            break
    if gamma_flip == 0.0 and not gex_by_s.empty:
        gamma_flip = float(gex_by_s.abs().idxmin())

    if   spot > gamma_flip and net_delta > 0: stat, msg = "success", "🔥 ALTA CONVICÇÃO (Safe Zone) — MMs provêm liquidez para a subida."
    elif spot < gamma_flip and net_delta > 0: stat, msg = "warning", f"🚀 RISCO DE SQUEEZE! MMs precisam cobrir Delta acima de {_fmt_strike(gamma_flip)}"
    elif spot < gamma_flip and net_delta < 0: stat, msg = "danger",  "💀 CASCATA (Falling Knife) — Zona de aceleração negativa. Evite compras."
    else:                                     stat, msg = "info",    "⚖️ MERCADO EM EQUILÍBRIO / CONSOLIDAÇÃO — Aguarde confirmação."

    return {"whales": whales, "msg": msg, "status": stat,
            "net_delta": net_delta, "z_score": df["z_score"]}, gamma_flip

# ══════════════════════════════════════════════════════════════════
# 9 · LEGENDAS CONTEXTUAIS
# ══════════════════════════════════════════════════════════════════

def legenda_vanna_ctx(valor, serie, strike, spot):
    p75 = serie.abs().quantile(0.75); p90 = serie.abs().quantile(0.90)
    alto = abs(valor) > p90; medio = abs(valor) > p75; pos = valor >= 0
    if pos and alto:        return "⚡ VANNA MÁXIMO+", "Strike muito sensível à IV. Se vol subir, MM compra delta — favorece alta."
    elif pos and medio:     return "⚡ VANNA ALTO+",   "Aumento de IV empurra MM a comprar delta nesse nível."
    elif pos:               return "🔵 VANNA LEVE+",   "Pequena sensibilidade positiva à vol."
    elif not pos and alto:  return "⚡ VANNA MÁXIMO−", "Strike muito sensível à IV. Se vol subir, MM vende delta — favorece baixa."
    elif not pos and medio: return "⚡ VANNA ALTO−",   "Aumento de IV empurra MM a vender delta nesse nível."
    else:                   return "🔵 VANNA LEVE−",   "Pequena sensibilidade negativa à vol."

# ══════════════════════════════════════════════════════════════════
# 10 · CARGA E PROCESSAMENTO POR PILAR → WIN PONDERADO
# ══════════════════════════════════════════════════════════════════

def _carregar_pilar_win(tk: str, arqs: list, ibov: float, peso: float) -> pd.DataFrame:
    frs = [parse_json(a) for a in arqs]
    frs = [f for f in frs if f is not None and not f.empty]
    if not frs: return pd.DataFrame()

    df_p = pd.concat(frs, ignore_index=True)

    # Opção A: filtro DTE>=2 removido — inclui 0DTE/weekly
    # O volume real do dia (inclusive vencimento no dia) é preservado.

    if tk in ("EEM", "EWZ", "VALE", "PBR"):
        try:
            bid_n = pd.to_numeric(df_p["bidPrice"], errors="coerce").fillna(0)
            ask_n = pd.to_numeric(df_p["askPrice"], errors="coerce").fillna(0)
            oi_n  = pd.to_numeric(df_p["openInterest"], errors="coerce").fillna(0)
            mid_n = (bid_n + ask_n) / 2
            spread_pct = ((ask_n - bid_n) / mid_n.where(mid_n > 0, 1)).fillna(0)
            df_p = df_p[(spread_pct < 0.50) | (oi_n > 1000)].copy()
        except: pass

    if df_p.empty: return pd.DataFrame()
    sp = _detectar_spot_pcp(df_p) or detectar_spot(df_p)
    if sp <= 0: return pd.DataFrame()

    SG = (sp**2) * 0.01; SD = sp
    rows = []
    for _, row in df_p.iterrows():
        sk   = float(row.get("strikePrice", 0)); opt = row.get("optionType", "Call")
        vol  = float(row.get("volume", 0) or 0); oi  = float(row.get("openInterest", 0) or 0)
        dlt  = float(row.get("delta", 0) or 0);  gma = float(row.get("gamma", 0) or 0)
        vega = float(row.get("vega", 0) or 0);   last= float(row.get("lastPrice", 0) or 0)
        bid  = float(row.get("bidPrice", 0) or 0);ask = float(row.get("askPrice", 0) or 0)

        if sk <= 0: continue
        opt_sign   = 1 if opt == "Call" else -1
        sk_win     = _bucket_win(ibov * (sk / sp))
        bid_ask_ok = bid > 0 and ask > 0
        mid_price  = (bid + ask) / 2 if bid_ask_ok else last
        last_ok    = bid_ask_ok and last > 0 and (last >= bid * LAST_STALE_THRESHOLD)
        direction  = (1 if last >= mid_price else -1) if last_ok else (0 if bid_ask_ok else 0)
        greeks_ok  = not (dlt == 0 and gma == 0 and vega == 0 and sk != sp)

        # OI estrutural — incluído independente de vol (fix Bug 1)
        gex_oi   = gma * oi  * _MULT * SG * opt_sign * peso if greeks_ok else 0.0
        dex_oi   = dlt * oi  * _MULT * SD * opt_sign  * peso

        # Fluxo do dia — requer vol > 0
        gex_vol  = gma * vol * _MULT * SG * opt_sign * direction * peso if greeks_ok and direction != 0 and vol > 0 else 0.0
        dex_vol  = dlt * vol * _MULT * SD * direction * peso if vol > 0 else 0.0
        vanna_vol= ((dlt * vega / sp) * vol * _MULT * direction * opt_sign * peso
                    if greeks_ok and sp > 0 and direction != 0 and vol > 0 else 0.0)
        fin_flow = mid_price * vol * _MULT * peso if vol > 0 else 0.0

        rows.append({
            "strike_win": sk_win, "optionType": opt,
            "volume": vol * peso,
            "openInterest": oi * peso,       # OI estrutural preservado para todos strikes
            "financial_flow": fin_flow, "gex_total": gex_vol, "gex_oi": gex_oi,
            "dex_total": dex_vol, "dex_oi": dex_oi, "vanna_total": vanna_vol,
        })
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def _calcular_pilar_normalizado(tk: str, arqs: list, ibov: float, peso: float) -> pd.DataFrame:
    frs = [parse_json(a) for a in arqs]
    frs = [f for f in frs if f is not None and not f.empty]
    if not frs: return pd.DataFrame()
    df_p = pd.concat(frs, ignore_index=True)

    # Opção A: filtro DTE>=2 removido — inclui 0DTE/weekly
    # O volume real do dia (inclusive vencimento no dia) é preservado.
    if tk in ("EEM", "EWZ", "VALE", "PBR"):
        try:
            bid_n = pd.to_numeric(df_p["bidPrice"], errors="coerce").fillna(0)
            ask_n = pd.to_numeric(df_p["askPrice"], errors="coerce").fillna(0)
            oi_n  = pd.to_numeric(df_p["openInterest"], errors="coerce").fillna(0)
            mid_n = (bid_n + ask_n) / 2
            spread_pct = ((ask_n - bid_n) / mid_n.where(mid_n > 0, 1)).fillna(0)
            df_p = df_p[(spread_pct < 0.50) | (oi_n > 1000)].copy()
        except: pass
    if df_p.empty: return pd.DataFrame()
    sp = _detectar_spot_pcp(df_p) or detectar_spot(df_p)
    if sp <= 0: return pd.DataFrame()

    SG = (sp**2)*0.01; SD = sp
    d = df_p.copy()
    for col in ["strikePrice","delta","gamma","openInterest","volume"]:
        d[col] = pd.to_numeric(d[col], errors="coerce").fillna(0.0)
    d = d[d["strikePrice"] > 0].copy()
    if d.empty: return pd.DataFrame()

    d["Sign"] = np.where(d["optionType"]=="Call", 1, -1)
    d["GEX_VOL"] = d["gamma"]*d["volume"]*_MULT*SG*d["Sign"]
    d["GEX_OI"]  = d["gamma"]*d["openInterest"]*_MULT*SG*d["Sign"]
    d["DEX_VOL"] = d["delta"]*d["volume"]*_MULT*SD
    d["DEX_OI"]  = d["delta"]*d["openInterest"]*_MULT*SD

    calls = d[d["optionType"]=="Call"].groupby("strikePrice").agg(
        GEX_VOL_C=("GEX_VOL","sum"),GEX_OI_C=("GEX_OI","sum"),
        DEX_VOL_C=("DEX_VOL","sum"),DEX_OI_C=("DEX_OI","sum"),
        VOL_C=("volume","sum"),OI_C=("openInterest","sum")).reset_index()
    puts = d[d["optionType"]=="Put"].groupby("strikePrice").agg(
        GEX_VOL_P=("GEX_VOL","sum"),GEX_OI_P=("GEX_OI","sum"),
        DEX_VOL_P=("DEX_VOL","sum"),DEX_OI_P=("DEX_OI","sum"),
        VOL_P=("volume","sum"),OI_P=("openInterest","sum")).reset_index()
    merged = pd.merge(calls, puts, on="strikePrice", how="outer").fillna(0)
    for col in ("GEX_VOL_P","GEX_OI_P","DEX_VOL_P","DEX_OI_P"):
        merged[col] = -merged[col].abs()

    cols_norm = ["GEX_VOL_C","GEX_VOL_P","GEX_OI_C","GEX_OI_P",
                 "DEX_VOL_C","DEX_VOL_P","DEX_OI_C","DEX_OI_P","VOL_C","VOL_P","OI_C","OI_P"]
    for col in cols_norm:
        merged[col+"_Z"] = _zscore_series(merged[col]) * peso
    merged["strike_win"] = merged["strikePrice"].apply(lambda sk: _bucket_win(ibov*(sk/sp)))

    rows = []
    for _, r in merged.iterrows():
        for opt_type in ("Call","Put"):
            sfx = "_C" if opt_type=="Call" else "_P"
            rows.append({"strike_win": int(r["strike_win"]), "opt_type": opt_type,
                "gex_vol_norm": _clean(r[f"GEX_VOL{sfx}_Z"]),
                "gex_oi_norm":  _clean(r[f"GEX_OI{sfx}_Z"]),
                "dex_vol_norm": _clean(r[f"DEX_VOL{sfx}_Z"]),
                "dex_oi_norm":  _clean(r[f"DEX_OI{sfx}_Z"]),
                "vol_norm":     _clean(r[f"VOL{sfx}_Z"]),
                "oi_norm":      _clean(r[f"OI{sfx}_Z"])})
    return pd.DataFrame(rows)

# ══════════════════════════════════════════════════════════════════
# 11 · PIPELINE FLOW EVOLUTION
# ══════════════════════════════════════════════════════════════════

def _parse_tradetime(tt_val) -> _dt | None:
    if tt_val is None: return None
    try:
        ts = int(float(str(tt_val)))
        if ts <= 0 or ts == -62169984000: return None
        return _dt.fromtimestamp(ts)
    except (ValueError, OSError): pass
    tt_str = str(tt_val).strip()
    m = _re.match(r'^(\d{1,2}):(\d{2})\s+CT$', tt_str)
    if not m: return None
    h_ct, mn = int(m.group(1)), int(m.group(2))
    return _dt(_date.today().year, _date.today().month, _date.today().day, (h_ct+2)%24, mn)


def _carregar_pilar_bruto(tk: str, arqs: list, mult: float = 100.0) -> pd.DataFrame:
    frs = [parse_json(a) for a in arqs]
    frs = [f for f in frs if f is not None and not f.empty]
    if not frs: return pd.DataFrame()

    df_p = pd.concat(frs, ignore_index=True)

    # Opção A: filtro DTE>=2 removido — inclui 0DTE/weekly
    # O volume real do dia (inclusive vencimento no dia) é preservado.
    if tk in ("EEM","EWZ","VALE","PBR"):
        try:
            bid_n = pd.to_numeric(df_p["bidPrice"], errors="coerce").fillna(0)
            ask_n = pd.to_numeric(df_p["askPrice"], errors="coerce").fillna(0)
            oi_n  = pd.to_numeric(df_p["openInterest"], errors="coerce").fillna(0)
            mid_n = (bid_n + ask_n) / 2
            spread_pct = ((ask_n - bid_n) / mid_n.where(mid_n > 0, 1)).fillna(0)
            df_p = df_p[(spread_pct < 0.50) | (oi_n > 1000)].copy()
        except: pass

    if df_p.empty: return pd.DataFrame()
    sp = _detectar_spot_pcp(df_p) or detectar_spot(df_p)
    if sp <= 0: return pd.DataFrame()

    df_v9 = calcular_v9(df_p, sp, mult)
    if df_v9.empty: return pd.DataFrame()

    rows = []
    for _, row in df_v9.iterrows():
        tt = row.get("tradeTime", None)
        dt = _parse_tradetime(tt)
        if dt is None: continue
        if dt.hour == 4 and dt.minute == 0 and dt.second == 0: continue
        vol = float(row.get("volume", 0) or 0)
        if vol <= 0: continue
        rows.append(dict(
            dt=dt, tk=tk, opt=row.get("optionType","Call"),
            vol=vol, spot=sp,
            d_flow=float(row.get("d_flow", 0) or 0),
            g_flow=float(row.get("gex_total", 0) or 0),
            hiro=float(row.get("hiro", 0) or 0),
        ))
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def _build_temporal_df(frames_bruto: list) -> pd.DataFrame:
    if not frames_bruto: return pd.DataFrame()
    df_t = pd.concat(frames_bruto, ignore_index=True)
    if df_t.empty: return pd.DataFrame()
    df_t = df_t.sort_values("dt").reset_index(drop=True)
    df_t["d_flow_cum"] = df_t["d_flow"].cumsum()
    df_t["g_flow_cum"] = df_t["g_flow"].cumsum()
    df_t["hiro_cum"]   = df_t["hiro"].cumsum()
    return df_t

# ══════════════════════════════════════════════════════════════════
# 12 · MÉTRICAS WIN AGREGADAS
# ══════════════════════════════════════════════════════════════════

def _calcular_metricas_win(df_win: pd.DataFrame, ibov: int) -> dict:
    if df_win.empty: return {}

    agg = df_win.groupby("strike_win").agg(
        gex_total=("gex_total","sum"), gex_oi=("gex_oi","sum"),
        dex_total=("dex_total","sum"), dex_oi=("dex_oi","sum"),
        vanna_total=("vanna_total","sum"), volume=("volume","sum"),
        openInterest=("openInterest","sum"), financial_flow=("financial_flow","sum"),
    ).sort_index()

    calls_agg = df_win[df_win["optionType"]=="Call"].groupby("strike_win").agg(
        volume=("volume","sum"), financial_flow=("financial_flow","sum"),
        dex_total=("dex_total","sum")).sort_index()
    puts_agg  = df_win[df_win["optionType"]=="Put"].groupby("strike_win").agg(
        volume=("volume","sum"), financial_flow=("financial_flow","sum"),
        dex_total=("dex_total","sum")).sort_index()

    gex_s = agg["gex_total"]; dex_s = agg["dex_total"]
    vol_s = agg["volume"];    vanna_s = agg["vanna_total"]
    strikes = gex_s.index.tolist()

    net_gex   = float(gex_s.sum()); net_dex = float(dex_s.sum())
    net_vanna = float(vanna_s.sum())
    net_vol_c = float(df_win[df_win["optionType"]=="Call"]["volume"].sum())
    net_vol_p = float(df_win[df_win["optionType"]=="Put"]["volume"].sum())

    gamma_wall = int(gex_s.abs().idxmax()) if not gex_s.empty else ibov

    gamma_flip = None
    for i in range(len(strikes)-1):
        g0 = gex_s.iloc[i]; g1 = gex_s.iloc[i+1]
        if g0*g1 < 0:
            k0 = strikes[i]; k1 = strikes[i+1]
            gamma_flip = int(round((k0+(k1-k0)*(-g0)/(g1-g0))/100)*100); break
    if gamma_flip is None:
        gamma_flip = int(gex_s.abs().idxmin()) if not gex_s.empty else ibov

    delta_flip = None
    for i in range(len(strikes)-1):
        d0 = dex_s.iloc[i]; d1 = dex_s.iloc[i+1]
        if d0*d1 < 0: delta_flip = int(strikes[i+1]); break
    if delta_flip is None and not dex_s.empty:
        delta_flip = int(dex_s.abs().idxmin())

    max_vol_win = int(vol_s.idxmax()) if not vol_s.empty and vol_s.sum() > 0 else ibov
    vol_trigger = int(round((gamma_flip+0.75*(gamma_wall-gamma_flip))/100)*100) if gamma_wall != gamma_flip else gamma_flip

    cw_vol = int(calls_agg["volume"].idxmax())          if not calls_agg.empty and calls_agg["volume"].sum() > 0 else None
    cw_oi  = int(calls_agg["financial_flow"].idxmax())  if not calls_agg.empty and calls_agg["financial_flow"].sum() > 0 else None
    pw_vol = int(puts_agg["volume"].idxmax())           if not puts_agg.empty and puts_agg["volume"].sum() > 0 else None
    pw_oi  = int(puts_agg["financial_flow"].idxmax())   if not puts_agg.empty and puts_agg["financial_flow"].sum() > 0 else None

    top_vanna  = vanna_s.abs().nlargest(3).index.tolist()
    gex_oi_s   = agg["gex_oi"]; dex_oi_s = agg["dex_oi"]
    gex_oi_pos = int(gex_oi_s.idxmax()) if not gex_oi_s.empty else ibov
    gex_oi_neg = int(gex_oi_s.idxmin()) if not gex_oi_s.empty else ibov
    dex_oi_pos = int(dex_oi_s.idxmax()) if not dex_oi_s.empty else ibov
    dex_oi_neg = int(dex_oi_s.idxmin()) if not dex_oi_s.empty else ibov

    ic_win = calls_agg.nlargest(2, "dex_total") if not calls_agg.empty else pd.DataFrame()
    ip_win = puts_agg.nsmallest(2, "dex_total") if not puts_agg.empty else pd.DataFrame()

    regime = "LONG GAMMA 🛡️" if net_gex > 0 else "SHORT GAMMA 🚨"
    regime_cls = "bull" if net_gex > 0 else "bear"
    bias = "ALTISTA 🟢" if net_dex > 0 else "BAIXISTA 🔴"
    bias_cls = "bull" if net_dex > 0 else "bear"
    vol_bias = "LONG VOL ⚡" if net_vanna > 0 else "SHORT VOL 📉"
    vol_cls  = "bull"        if net_vanna > 0 else "bear"
    mom_val  = net_vol_c / net_vol_p if net_vol_p > 0 else 1.0

    return dict(
        agg=agg, calls_agg=calls_agg, puts_agg=puts_agg,
        gex_s=gex_s, dex_s=dex_s, vanna_s=vanna_s, vol_s=vol_s,
        net_gex=net_gex, net_dex=net_dex, net_vanna=net_vanna,
        net_vol_c=net_vol_c, net_vol_p=net_vol_p, mom_val=mom_val,
        gamma_wall=gamma_wall, gamma_flip=gamma_flip, delta_flip=delta_flip,
        max_vol_win=max_vol_win, vol_trigger=vol_trigger,
        cw_vol=cw_vol, cw_oi=cw_oi, pw_vol=pw_vol, pw_oi=pw_oi,
        top_vanna=top_vanna, gex_oi_pos=gex_oi_pos, gex_oi_neg=gex_oi_neg,
        dex_oi_pos=dex_oi_pos, dex_oi_neg=dex_oi_neg,
        ic_win=ic_win, ip_win=ip_win,
        regime=regime, regime_cls=regime_cls,
        bias=bias, bias_cls=bias_cls, vol_bias=vol_bias, vol_cls=vol_cls,
        alerta_flip=(abs(ibov - gamma_flip) <= 500),
    )

# ══════════════════════════════════════════════════════════════════
# 13 · GRÁFICOS WIN
# ══════════════════════════════════════════════════════════════════

def _fmt_win_tick(pts: int) -> str:
    return f"{int(pts):,.0f}".replace(",", ".")

def build_vol_oi_chart_win(df_win: pd.DataFrame, ibov: int, focus_pct: float = 0.15) -> go.Figure:
    s_lo = ibov*(1-focus_pct); s_hi = ibov*(1+focus_pct)
    strikes_all = sorted(df_win["strike_win"].unique())
    sy_num = [s for s in strikes_all if s_lo <= s <= s_hi] or strikes_all
    sy_lbl = [_fmt_win_tick(s) for s in sy_num]

    def get_cp(metric, opt):
        sub = df_win[df_win["optionType"]==opt]
        return sub.groupby("strike_win")[metric].sum().reindex(sy_num, fill_value=0)

    vol_c = get_cp("volume","Call"); vol_p = -get_cp("volume","Put")
    ff_c  = get_cp("financial_flow","Call"); ff_p = -get_cp("financial_flow","Put")

    fig = make_subplots(rows=1, cols=2, shared_yaxes=True,
                        subplot_titles=["VOLUME  (Call + | Put −)", "OPEN INTEREST  (Call + | Put −)"])

    def mk_colors(vals):
        return [COLOR_CALL if v >= 0 else COLOR_PUT for v in vals]

    for col, (xc, xp, op) in enumerate([(vol_c,vol_p,0.85),(ff_c,ff_p,0.45)], 1):
        fig.add_trace(go.Bar(y=sy_num, x=xc, orientation="h", marker_color=mk_colors(xc), marker_opacity=op, showlegend=False), row=1, col=col)
        fig.add_trace(go.Bar(y=sy_num, x=xp, orientation="h", marker_color=mk_colors(xp), marker_opacity=op, showlegend=False), row=1, col=col)
        if sy_num and sy_num[0] <= ibov <= sy_num[-1]:
            fig.add_hline(y=ibov, line_color=COLOR_NEON, line_width=1.5, line_dash="dot", row=1, col=col)

    if sy_num and sy_num[0] <= ibov <= sy_num[-1]:
        fig.add_annotation(xref="x2 domain", yref="y2", x=1.01, y=ibov,
                           text=f"SPOT {fmt_win(ibov)}", showarrow=False,
                           font=dict(color=COLOR_NEON, size=10, family="JetBrains Mono"), xanchor="left")

    y_margin = (sy_num[-1]-sy_num[0])*0.02 if len(sy_num)>1 else 50
    _h = min(max(len(sy_num)*75, 500), 2000)
    yaxis_cfg = dict(tickvals=sy_num, ticktext=sy_lbl, range=[sy_num[0]-y_margin, sy_num[-1]+y_margin],
                     showgrid=False, tickfont=dict(size=11, family="JetBrains Mono"))
    fig.update_layout(height=_h, template="plotly_dark", barmode="relative", bargap=0.0, bargroupgap=0.0,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(8,12,20,0.6)",
                      margin=dict(t=40,b=20,l=10,r=160), font=dict(family="JetBrains Mono",size=11,color="#ccddf8"),
                      yaxis=yaxis_cfg, yaxis2=yaxis_cfg,
                      xaxis=dict(showgrid=True,gridcolor="rgba(0,255,255,0.06)"),
                      xaxis2=dict(showgrid=True,gridcolor="rgba(0,255,255,0.06)"))
    for t in fig.layout.annotations[:2]:
        t.update(font=dict(color=COLOR_NEON, size=12, family="JetBrains Mono"))
    return fig


def build_pressure_chart_win(df_win: pd.DataFrame, ibov: int, focus_pct: float = 0.15) -> go.Figure:
    s_lo = ibov*(1-focus_pct); s_hi = ibov*(1+focus_pct)
    strikes_all = sorted(df_win["strike_win"].unique())
    sy_num = [s for s in strikes_all if s_lo <= s <= s_hi] or strikes_all
    sy_lbl = [_fmt_win_tick(s) for s in sy_num]

    agg_opt = (df_win.groupby(["strike_win","optionType"])
               .agg(dex=("dex_total","sum"),gex=("gex_total","sum"),
                    vanna=("vanna_total","sum"),oi=("openInterest","sum")).reset_index())

    def get_vals(col, opt):
        sub = agg_opt[agg_opt["optionType"]==opt].set_index("strike_win")[col]
        return sub.reindex(sy_num, fill_value=0).values

    def colored_bars(vals, pc, nc):
        return [pc if v >= 0 else nc for v in vals]

    fig = make_subplots(rows=1, cols=3, shared_yaxes=True,
                        subplot_titles=["DELTA FLOW (DEX)","GAMMA EXPOSURE (GEX)","VANNA (dΔ/dVol)"],
                        horizontal_spacing=0.02)

    for i, (metric, cp, cn) in enumerate([("dex",COLOR_NEON,COLOR_ORANGE),("gex",COLOR_PURPLE,COLOR_ORANGE),("vanna","#00e676","#ff1744")], 1):
        cv = get_vals(metric,"Call"); pv = get_vals(metric,"Put"); net_vol = cv+pv
        oi_c = get_vals("oi","Call"); oi_p = get_vals("oi","Put")
        max_net = max(abs(v) for v in net_vol) if any(net_vol) else 1
        max_oi  = max(max(oi_c), max(oi_p), 1)
        net_oi  = (oi_c+oi_p)*(max_net/max_oi if max_oi > 0 else 1)
        fig.add_trace(go.Bar(y=sy_num,x=net_vol,orientation="h",marker_color=colored_bars(net_vol,cp,cn),marker_opacity=0.9,showlegend=False),row=1,col=i)
        fig.add_trace(go.Bar(y=sy_num,x=net_oi, orientation="h",marker_color=colored_bars(net_oi, cp,cn),marker_opacity=0.3,showlegend=False),row=1,col=i)
        if sy_num and sy_num[0] <= ibov <= sy_num[-1]:
            fig.add_hline(y=ibov, line_color=COLOR_NEON, line_width=1.2, line_dash="dot", row=1, col=i)
            if i==2:
                fig.add_annotation(xref="x2 domain",yref="y2",x=0.5,y=ibov,
                                   text=f"SPOT {fmt_win(ibov)}",showarrow=False,yshift=8,
                                   font=dict(color=COLOR_NEON,size=10,family="JetBrains Mono"),xanchor="center")

    y_margin = (sy_num[-1]-sy_num[0])*0.02 if len(sy_num)>1 else 50
    _h = min(max(len(sy_num)*75, 500), 2000)
    yaxis_cfg = dict(tickvals=sy_num,ticktext=sy_lbl,range=[sy_num[0]-y_margin,sy_num[-1]+y_margin],
                     showgrid=False,tickfont=dict(size=13,family="JetBrains Mono"))
    fig.update_layout(height=_h,template="plotly_dark",showlegend=False,barmode="relative",bargap=0.0,bargroupgap=0.0,
                      paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(8,12,20,0.6)",
                      margin=dict(t=40,b=20,l=10,r=10),font=dict(family="JetBrains Mono",size=11,color="#ccddf8"),
                      yaxis=yaxis_cfg,yaxis2=yaxis_cfg,yaxis3=yaxis_cfg,
                      xaxis=dict(showgrid=True,gridcolor="rgba(0,255,255,0.06)"),
                      xaxis2=dict(showgrid=True,gridcolor="rgba(0,255,255,0.06)"),
                      xaxis3=dict(showgrid=True,gridcolor="rgba(0,255,255,0.06)"))
    for t in fig.layout.annotations:
        t.update(font=dict(color=COLOR_NEON,size=12,family="JetBrains Mono"))
    return fig

# ══════════════════════════════════════════════════════════════════
# 14 · FLOW EVOLUTION — gráfico de série temporal
# ══════════════════════════════════════════════════════════════════

def _flow_fig(df_t, col_cum, title, color_pos, color_neg, extras=None):
    t = df_t["dt"]; v = df_t[col_cum]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t,y=v,mode="lines",line=dict(color=color_pos,width=1.8),name=title,showlegend=False))
    def rgba(hx,a):
        r,g,b = int(hx[1:3],16),int(hx[3:5],16),int(hx[5:7],16)
        return f"rgba({r},{g},{b},{a})"
    fig.add_trace(go.Scatter(x=t,y=v.clip(lower=0),fill="tozeroy",fillcolor=rgba(color_pos,0.12),line=dict(width=0),showlegend=False,hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=t,y=v.clip(upper=0),fill="tozeroy",fillcolor=rgba(color_neg,0.12),line=dict(width=0),showlegend=False,hoverinfo="skip"))
    for ec_col,ec_color,ec_name in (extras or []):
        fig.add_trace(go.Scatter(x=t,y=df_t[ec_col],mode="lines",line=dict(color=ec_color,width=1.0,dash="dot"),name=ec_name,opacity=0.65))
    fig.add_hline(y=0,line_color=COLOR_NEON,line_width=0.8,line_dash="dash",opacity=0.35)
    vals = v.values
    for i in range(len(vals)-1):
        if vals[i]!=0 and vals[i+1]!=0 and (vals[i]>0)!=(vals[i+1]>0):
            fig.add_vline(x=t.iloc[i],line_color=COLOR_GOLD,line_width=0.8,line_dash="dot",opacity=0.5)

    from datetime import timedelta
    t_min = t.min(); t_max = t.max()
    span  = t_max - t_min
    margin = max(span * 0.05, timedelta(minutes=5))
    x_range = [t_min - margin, t_max + margin]

    fig.update_layout(height=240,template="plotly_dark",
                      paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(8,12,20,0.6)",
                      margin=dict(t=32,b=20,l=10,r=10),
                      title=dict(text=f"◈ {title}",font=dict(color=COLOR_NEON,size=13,family="JetBrains Mono"),x=0),
                      font=dict(family="JetBrains Mono",size=13,color="#ccddf8"),
                      xaxis=dict(showgrid=True,gridcolor="rgba(0,255,255,0.06)",
                                 tickfont=dict(size=13), range=x_range,
                                 tickformat="%H:%M"),
                      yaxis=dict(showgrid=True,gridcolor="rgba(0,255,255,0.06)",
                                 zerolinecolor="rgba(0,255,255,0.3)",zerolinewidth=1,tickfont=dict(size=13)),
                      showlegend=bool(extras),
                      legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1,
                                  font=dict(size=13,family="JetBrains Mono"),bgcolor="rgba(0,0,0,0)"),
                      hovermode="x unified")
    return fig

# ══════════════════════════════════════════════════════════════════
# 15 · PINE SCRIPT
# ══════════════════════════════════════════════════════════════════

def _construir_niveis_win_agg(m: dict, ibov: int) -> list:
    niveis = []
    def add(label, win_pts, cor, estilo):
        niveis.append(dict(nome=label, win_pts=int(round(win_pts/100)*100), cor_pine=cor, estilo=estilo))

    gw = m["gamma_wall"]; gf = m["gamma_flip"]
    add("MAX GEX | GAMMA WALL | MM VENDE" if gw>ibov else "MAX GEX | GAMMA WALL | MM COMPRA",
        gw, "color.rgb(57,142,232)", "Sólido")
    add("GAMMA FLIP | Divisor de Regime", gf, "color.rgb(82,157,255)", "Sólido")
    if m["max_vol_win"]: add("MAX VOL | Imã de Liquidez", m["max_vol_win"], "color.rgb(240,192,64)", "Tracejado")
    if m["delta_flip"]:  add("DELTA FLIP | Inversao de Risco", m["delta_flip"], "color.rgb(82,157,255)", "Sólido")
    if m["cw_vol"]: add("CALL WALL (VOL) | Resistencia de Fluxo", m["cw_vol"], "color.rgb(176,39,46)", "Tracejado")
    if m["cw_oi"]:  add("CALL WALL (OI) | Teto Estrutural", m["cw_oi"], "color.rgb(176,39,46)", "Sólido")
    if m["pw_vol"]: add("PUT WALL (VOL) | Defesa de Fluxo", m["pw_vol"], "color.rgb(82,157,255)", "Tracejado")
    if m["pw_oi"]:  add("PUT WALL (OI) | Muro Estrutural", m["pw_oi"], "color.rgb(82,157,255)", "Sólido")

    vanna_s = m["vanna_s"]
    for sw in m["top_vanna"]:
        val = float(vanna_s.get(sw, 0)); pos = val > 0
        add("VANNA + | Pressao Compradora" if pos else "VANNA - | Pressao Vendedora",
            sw, "color.rgb(0,230,118)" if pos else "color.rgb(255,23,68)", "Tracejado")

    add("VOL TRIGGER | Perda de Controle", m["vol_trigger"], "color.rgb(76,87,77)", "Sólido")
    add("MAX GEX | GAMMA POS (OI) | Suporte Estrutural", m["gex_oi_pos"], "color.rgb(57,142,232)", "Sólido")
    add("MIN GEX | GAMMA NEG (OI) | VOL ATTACK | Risco Estrutural", m["gex_oi_neg"], "color.rgb(91,2,2)", "Sólido")
    add("DELTA POS (OI) | MM Vendido Estrutural", m["dex_oi_pos"], "color.rgb(57,142,232)", "Sólido")
    add("DELTA NEG (OI) | MM Comprado Estrutural", m["dex_oi_neg"], "color.rgb(91,2,2)", "Sólido")

    gex_s = m["gex_s"]
    if not gex_s.empty:
        add("GAMMA POS (VOL) | Zona de Atracao", int(gex_s.idxmax()), "color.rgb(82,157,255)", "Tracejado")
        add("GAMMA NEG (VOL) | Pressao de Venda", int(gex_s.idxmin()), "color.rgb(235,12,12)", "Tracejado")
    dex_s = m["dex_s"]
    if not dex_s.empty:
        add("DELTA POS (VOL) | Amplificacao de Compra", int(dex_s.idxmax()), "color.rgb(82,157,255)", "Tracejado")
        add("DELTA NEG (VOL) | Defesa Ativa Venda", int(dex_s.idxmin()), "color.rgb(235,12,12)", "Tracejado")
    add("SPOT", ibov, "color.gray", "Sólido")
    return sorted(niveis, key=lambda x: x["win_pts"], reverse=True)


def _niveis_to_pine(niveis, pilares_str, ibov):
    from collections import defaultdict
    MAX_TAGS = 3; OFFSET = 50
    def _tag(nome):
        mapa = {"MAX GEX | GAMMA WALL | MM VENDE":"GW(VENDE)","MAX GEX | GAMMA WALL | MM COMPRA":"GW(COMPRA)",
                "GAMMA FLIP":"Γ-FLIP","DELTA FLIP":"Δ-FLIP","VOL TRIGGER":"VOL-TRIG","MAX VOL":"MAX-VOL",
                "CALL WALL (OI)":"CW-OI","PUT WALL (OI)":"PW-OI","CALL WALL (VOL)":"CW-VOL","PUT WALL (VOL)":"PW-VOL",
                "VANNA +":"VANNA+","VANNA -":"VANNA-","GAMMA POS (OI)":"GEX-POS-OI","GAMMA NEG (OI)":"GEX-NEG-OI",
                "DELTA POS (OI)":"DEX-POS-OI","DELTA NEG (OI)":"DEX-NEG-OI",
                "GAMMA POS (VOL)":"GEX-POS-VOL","GAMMA NEG (VOL)":"GEX-NEG-VOL",
                "DELTA POS (VOL)":"DEX-POS-VOL","DELTA NEG (VOL)":"DEX-NEG-VOL","SPOT":"SPOT"}
        for chave, abrev in mapa.items():
            if chave in nome: return abrev
        return nome.split("|")[0].strip()[:15]

    por_pts = defaultdict(list)
    for n in niveis: por_pts[n["win_pts"]].append(n)
    linhas = []
    for pts in sorted(por_pts.keys(), reverse=True):
        itens = por_pts[pts]
        if len(itens) == 1:
            n = itens[0]
            linha = "        create_indicator('{}', {}, {}, '{}')".format(
                n["nome"], pts, n["cor_pine"], n["estilo"])
            linhas.append(linha)
        elif len(itens) <= MAX_TAGS:
            label = " + ".join(_tag(it["nome"]) for it in itens)
            linha = "        create_indicator('{}', {}, {}, '{}')".format(
                label, pts, itens[0]["cor_pine"], itens[0]["estilo"])
            linhas.append(linha)
        else:
            for gi, g in enumerate([itens[i:i+MAX_TAGS] for i in range(0, len(itens), MAX_TAGS)]):
                label = " + ".join(_tag(it["nome"]) for it in g)
                linha = "        create_indicator('{}', {}, {}, '{}')".format(
                    label, pts + gi*OFFSET, g[0]["cor_pine"], g[0]["estilo"])
                linhas.append(linha)
    return "\n".join(linhas)


def _gerar_pine_script_completo(niveis, frames_norm, ibov, pilares_str):
    arrays_str = _arrays_pine(frames_norm, ibov, pilares_str) if frames_norm else "// Sem dados de arrays."
    display_body = _niveis_to_pine(niveis, pilares_str, ibov)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    script = f"""//@version=6
// ═══════════════════════════════════════════════════════════════
// GAMMA-LEVELS / GEX / DEX — ÍNDICE WIN
// Gerado automaticamente pelo Dashboard WIN Agregado
// Pilares: {pilares_str}  |  Spot WIN: {fmt_win(ibov)}
// {ts}
// ═══════════════════════════════════════════════════════════════
indicator(\'GAMMA-LEVELS/GEX/DEX – ÍNDICE WIN\', overlay=true, max_bars_back=1000, max_labels_count=500, max_lines_count=500, max_boxes_count=1000)

// ===============================================
// VARIÁVEIS GLOBAIS
// ===============================================
var line[]  lines  = array.new_line()
var label[] labels = array.new_label()
var box[]   boxes  = array.new_box()

// ===============================================
// PARÂMETROS VISUAIS — GEX/Volume (G/V)
// ===============================================
grpGV = "Visual - GEX/Volume (G/V)"
gv_escala_maxima = input.float(50.0, "Escala Máxima das Barras (G/V)", group=grpGV)
gv_offset_barras = input.int(50, "Distância horizontal (G/V)", group=grpGV, tooltip="Distância a partir da borda esquerda.")
gv_dist_y        = input.int(50, "Meia-altura da barra G/V (pts WIN)", group=grpGV)
gv_opacidade     = input.int(20, "Opacidade (G/V)", minval=0, maxval=100, group=grpGV)
gv_cor_net_pos   = input.color(color.rgb(131, 20, 196), "Cor NET GEX + (esquerda)", group=grpGV)
gv_cor_net_neg   = input.color(color.new(#ea0c0c, 0),   "Cor NET GEX - (esquerda)", group=grpGV)
gv_cor_vol_call  = input.color(color.new(color.red, 0),   "Cor Volume CALL (direita)", group=grpGV)
gv_cor_vol_put   = input.color(color.new(color.green, 0), "Cor Volume PUT (direita)", group=grpGV)
gv_min_volume    = input.float(0.0, "Volume mínimo por strike (G/V)", minval=0, group=grpGV)

// ===============================================
// PARÂMETROS VISUAIS — DEX (Δ)
// ===============================================
grpDEX = "Visual - DEX (Δ)"
dex_escala_maxima = input.float(50.0, "Escala Máxima das Barras (Δ)", group=grpDEX)
dex_offset_barras = input.int(125, "Distância horizontal (Δ)", group=grpDEX)
dex_dist_y        = input.int(50, "Meia-altura da barra DEX (pts WIN)", group=grpDEX)
dex_opacidade     = input.int(20, "Transparência (Δ)", minval=0, maxval=100, group=grpDEX)
dex_cor_delta_pos = input.color(color.rgb(20, 160, 60),  "Cor Δ POSITIVO", group=grpDEX)
dex_cor_delta_neg = input.color(color.rgb(234, 12, 12),  "Cor Δ NEGATIVO", group=grpDEX)

// ===============================================
// PARÂMETROS VISUAIS — Camada OI
// ===============================================
grpOI = "Visual - Camada OI (Transparente)"
oi_opacidade = input.int(65, "Opacidade OI", minval=0, maxval=100, group=grpOI)

// ===============================================
// FUNÇÕES AUXILIARES
// ===============================================
f_ts_brt(y, m, d, hh, mm) =>
    timestamp("America/Sao_Paulo", y, m, d, hh, mm)

get_open_day_window() =>
    yBR = year(time, "America/Sao_Paulo")
    mBR = month(time, "America/Sao_Paulo")
    dBR = dayofmonth(time, "America/Sao_Paulo")
    todayOpenBR = f_ts_brt(yBR, mBR, dBR, 19, 0)
    lastOpenTs  = time >= todayOpenBR ? todayOpenBR : (todayOpenBR - 24 * 60 * 60 * 1000)
    dayEnd      = time
    [lastOpenTs, dayEnd]

getLineStyle(styleStr) =>
    styleStr == "Sólido" ? line.style_solid : styleStr == "Tracejado" ? line.style_dashed : line.style_dotted

clear_objects() =>
    for l in lines
        line.delete(l)
    array.clear(lines)
    for lb in labels
        label.delete(lb)
    array.clear(labels)

create_indicator(name, yValue, lineColor, lineStyleInput) =>
    [dayStart, dayEnd] = get_open_day_window()
    ls = getLineStyle(lineStyleInput)
    l  = line.new(x1=dayStart, y1=yValue, x2=dayEnd, y2=yValue, color=lineColor, width=2, style=ls, xloc=xloc.bar_time)
    array.push(lines, l)
    lb = label.new(x=dayEnd, y=yValue, text=name + \' (\' + str.tostring(yValue) + \')\'  , style=label.style_label_left, color=color.new(lineColor, 100), textcolor=lineColor, xloc=xloc.bar_time)
    array.push(labels, lb)

// ===============================================
// ARRAYS — WIN UNIFICADO (gerados automaticamente)
// ===============================================
{arrays_str}

// ===============================================
// SELEÇÃO DE ARRAYS
// ===============================================
is_win = str.contains(str.upper(syminfo.ticker), \'BRA50\')

gex_strikes        = is_win ? win_unified_gex_strikes        : array.new_float(0)
gex_call_values    = is_win ? win_unified_gex_call_values    : array.new_float(0)
gex_put_values     = is_win ? win_unified_gex_put_values     : array.new_float(0)
gex_oi_call_values = is_win ? win_unified_gex_oi_call_values : array.new_float(0)
gex_oi_put_values  = is_win ? win_unified_gex_oi_put_values  : array.new_float(0)
vol_strikes        = is_win ? win_unified_vol_strikes        : array.new_float(0)
vol_call_values    = is_win ? win_unified_vol_call_values    : array.new_float(0)
vol_put_values     = is_win ? win_unified_vol_put_values     : array.new_float(0)
dex_strikes        = is_win ? win_unified_dex_strikes        : array.new_float(0)
dex_call_values    = is_win ? win_unified_dex_call_values    : array.new_float(0)
dex_put_values     = is_win ? win_unified_dex_put_values     : array.new_float(0)
dex_oi_call_values = is_win ? win_unified_dex_oi_call_values : array.new_float(0)
dex_oi_put_values  = is_win ? win_unified_dex_oi_put_values  : array.new_float(0)

// ===============================================
// NÍVEIS INSTITUCIONAIS
// ===============================================
display_levels() =>
    if is_win
{display_body}

// ===============================================
// PRÉ-CÁLCULO: posição horizontal das barras
// ===============================================
left_time  = chart.left_visible_bar_time
cond       = not na(left_time) ? time >= left_time : true
left_index = ta.valuewhen(cond, bar_index, 0)

// ===============================================
// DESENHO DAS BARRAS (GEX, VOLUME, DEX)
// ===============================================
if barstate.islast
    sz = array.size(boxes)
    if sz > 0
        for b = 0 to sz - 1
            box.delete(array.get(boxes, b))
        array.clear(boxes)

    x_base_gv  = left_index + gv_offset_barras
    x_base_dex = left_index + dex_offset_barras

    valid_gex = math.min(array.size(gex_strikes), array.size(gex_call_values))
    valid_gex := math.min(valid_gex, array.size(gex_put_values))
    if valid_gex > 0
        abs_nets_vol = array.new_float()
        for i = 0 to valid_gex - 1
            n = array.get(gex_call_values, i) + array.get(gex_put_values, i)
            if n != 0
                array.push(abs_nets_vol, math.abs(n))
        max_gex_vol = array.size(abs_nets_vol) > 0 ? array.percentile_linear_interpolation(abs_nets_vol, 95) : 1.0
        max_gex_vol := max_gex_vol == 0 ? 1.0 : max_gex_vol
        abs_nets_oi = array.new_float()
        for i = 0 to valid_gex - 1
            n = array.get(gex_oi_call_values, i) + array.get(gex_oi_put_values, i)
            if n != 0
                array.push(abs_nets_oi, math.abs(n))
        max_gex_oi = array.size(abs_nets_oi) > 0 ? array.percentile_linear_interpolation(abs_nets_oi, 95) : 1.0
        max_gex_oi := max_gex_oi == 0 ? 1.0 : max_gex_oi
        for i = 0 to valid_gex - 1
            sk      = array.get(gex_strikes, i)
            net_vol = array.get(gex_call_values, i)    + array.get(gex_put_values, i)
            net_oi  = array.get(gex_oi_call_values, i) + array.get(gex_oi_put_values, i)
            if net_oi != 0
                norm_oi = math.min(math.abs(net_oi) / max_gex_oi, 1.0) * gv_escala_maxima
                cor_oi  = net_oi > 0 ? color.new(gv_cor_net_pos, oi_opacidade) : color.new(gv_cor_net_neg, oi_opacidade)
                array.push(boxes, box.new(left=x_base_gv - int(norm_oi), top=int(sk) + gv_dist_y, right=x_base_gv, bottom=int(sk) - gv_dist_y, xloc=xloc.bar_index, bgcolor=cor_oi, border_color=na, border_width=0))
            if net_vol != 0
                norm_vol = math.min(math.abs(net_vol) / max_gex_vol, 1.0) * gv_escala_maxima
                cor_vol  = net_vol > 0 ? color.new(gv_cor_net_pos, gv_opacidade) : color.new(gv_cor_net_neg, gv_opacidade)
                array.push(boxes, box.new(left=x_base_gv - int(norm_vol), top=int(sk) + gv_dist_y, right=x_base_gv, bottom=int(sk) - gv_dist_y, xloc=xloc.bar_index, bgcolor=cor_vol, border_color=na, border_width=0))

    valid_vol = math.min(array.size(vol_strikes), array.size(vol_call_values))
    valid_vol := math.min(valid_vol, array.size(vol_put_values))
    if valid_vol > 0
        max_vol = 0.0
        for i = 0 to valid_vol - 1
            max_vol := math.max(max_vol, math.max(array.get(vol_call_values, i), array.get(vol_put_values, i)))
        max_vol := max_vol == 0 ? 1.0 : max_vol
        opa_v = int(math.min(gv_opacidade + 10, 100))
        for i = 0 to valid_vol - 1
            sk  = array.get(vol_strikes, i)
            cv  = array.get(vol_call_values, i)
            pv  = array.get(vol_put_values, i)
            dom = math.max(cv, pv)
            if dom >= gv_min_volume
                norm  = (dom / max_vol) * gv_escala_maxima
                cor_v = cv >= pv ? color.new(gv_cor_vol_call, opa_v) : color.new(gv_cor_vol_put, opa_v)
                array.push(boxes, box.new(left=x_base_gv, top=int(sk) + gv_dist_y, right=x_base_gv + int(norm), bottom=int(sk) - gv_dist_y, xloc=xloc.bar_index, bgcolor=cor_v, border_color=na, border_width=0))

    valid_dex = math.min(array.size(dex_strikes), array.size(dex_call_values))
    valid_dex := math.min(valid_dex, array.size(dex_put_values))
    if valid_dex > 0
        abs_nets_dex_vol = array.new_float()
        for i = 0 to valid_dex - 1
            n = array.get(dex_call_values, i) + array.get(dex_put_values, i)
            if n != 0
                array.push(abs_nets_dex_vol, math.abs(n))
        max_dex_vol = array.size(abs_nets_dex_vol) > 0 ? array.percentile_linear_interpolation(abs_nets_dex_vol, 95) : 1.0
        max_dex_vol := max_dex_vol == 0 ? 1.0 : max_dex_vol
        abs_nets_dex_oi = array.new_float()
        for i = 0 to valid_dex - 1
            n = array.get(dex_oi_call_values, i) + array.get(dex_oi_put_values, i)
            if n != 0
                array.push(abs_nets_dex_oi, math.abs(n))
        max_dex_oi = array.size(abs_nets_dex_oi) > 0 ? array.percentile_linear_interpolation(abs_nets_dex_oi, 95) : 1.0
        max_dex_oi := max_dex_oi == 0 ? 1.0 : max_dex_oi
        for i = 0 to valid_dex - 1
            sk      = array.get(dex_strikes, i)
            net_vol = array.get(dex_call_values, i)    + array.get(dex_put_values, i)
            net_oi  = array.get(dex_oi_call_values, i) + array.get(dex_oi_put_values, i)
            if net_oi != 0
                norm_oi = math.min(math.abs(net_oi) / max_dex_oi, 1.0) * dex_escala_maxima
                cor_oi  = net_oi > 0 ? color.new(dex_cor_delta_pos, oi_opacidade) : color.new(dex_cor_delta_neg, oi_opacidade)
                array.push(boxes, box.new(left=x_base_dex - int(norm_oi), top=int(sk) + dex_dist_y, right=x_base_dex, bottom=int(sk) - dex_dist_y, xloc=xloc.bar_index, bgcolor=cor_oi, border_color=na, border_width=0))
            if net_vol != 0
                norm_vol = math.min(math.abs(net_vol) / max_dex_vol, 1.0) * dex_escala_maxima
                cor_vol  = net_vol > 0 ? color.new(dex_cor_delta_pos, dex_opacidade) : color.new(dex_cor_delta_neg, dex_opacidade)
                array.push(boxes, box.new(left=x_base_dex - int(norm_vol), top=int(sk) + dex_dist_y, right=x_base_dex, bottom=int(sk) - dex_dist_y, xloc=xloc.bar_index, bgcolor=cor_vol, border_color=na, border_width=0))

// ===============================================
// LINHAS E RÓTULOS
// ===============================================
clear_objects()
display_levels()

plot(na, title="__dummy__", display=display.none)
"""
    return script


def _arrays_pine(frames_norm, ibov, pilares_str):
    if not frames_norm: return "// Sem dados."
    all_df = pd.concat(frames_norm, ignore_index=True)
    agg = (all_df.groupby(["strike_win","opt_type"])
           .agg(gex_vol_norm=("gex_vol_norm","sum"),gex_oi_norm=("gex_oi_norm","sum"),
                dex_vol_norm=("dex_vol_norm","sum"),dex_oi_norm=("dex_oi_norm","sum"),
                vol_norm=("vol_norm","sum"),oi_norm=("oi_norm","sum"))
           .reset_index().sort_values("strike_win"))
    calls = agg[agg["opt_type"]=="Call"].set_index("strike_win")
    puts  = agg[agg["opt_type"]=="Put"].set_index("strike_win")
    all_strikes = sorted(set(calls.index)|set(puts.index))
    def fmt(v): return str(float(v))
    p = "win_unified_"
    strikes,g_calls,g_puts,g_oi_c,g_oi_p = [],[],[],[],[]
    v_calls,v_puts,d_calls,d_puts,d_oi_c,d_oi_p,d_net = [],[],[],[],[],[],[]
    for sk in all_strikes:
        c = calls.loc[sk] if sk in calls.index else None
        pu = puts.loc[sk]  if sk in puts.index  else None
        strikes.append(fmt(sk))
        g_calls.append(fmt(_clean(c["gex_vol_norm"] if c is not None else 0)))
        g_puts.append( fmt(_clean(pu["gex_vol_norm"] if pu is not None else 0)))
        g_oi_c.append( fmt(_clean(c["gex_oi_norm"]  if c is not None else 0)))
        g_oi_p.append( fmt(_clean(pu["gex_oi_norm"]  if pu is not None else 0)))
        v_calls.append(fmt(_clean(c["vol_norm"]      if c is not None else 0)))
        v_puts.append( fmt(_clean(pu["vol_norm"]      if pu is not None else 0)))
        dc = _clean(c["dex_vol_norm"]  if c is not None else 0)
        dp = _clean(pu["dex_vol_norm"] if pu is not None else 0)
        d_calls.append(fmt(dc)); d_puts.append(fmt(dp))
        d_oi_c.append(fmt(_clean(c["dex_oi_norm"]  if c is not None else 0)))
        d_oi_p.append(fmt(_clean(pu["dex_oi_norm"]  if pu is not None else 0)))
        d_net.append(fmt(dc+dp))
    header = (f"// ARRAYS UNIFICADOS — 6 PILARES\n// Pilares: {pilares_str}  |  Ibov: {fmt_win(ibov)}\n"
              f"// Strikes: {len(all_strikes)}  |  Gerado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    return "\n".join([header,
        f"{p}gex_strikes        = array.from({', '.join(strikes)})",
        f"{p}gex_call_values    = array.from({', '.join(g_calls)})",
        f"{p}gex_put_values     = array.from({', '.join(g_puts)})",
        f"{p}gex_oi_call_values = array.from({', '.join(g_oi_c)})",
        f"{p}gex_oi_put_values  = array.from({', '.join(g_oi_p)})",
        f"{p}vol_strikes        = array.from({', '.join(strikes)})",
        f"{p}vol_call_values    = array.from({', '.join(v_calls)})",
        f"{p}vol_put_values     = array.from({', '.join(v_puts)})",
        f"{p}dex_strikes        = array.from({', '.join(strikes)})",
        f"{p}dex_call_values    = array.from({', '.join(d_calls)})",
        f"{p}dex_put_values     = array.from({', '.join(d_puts)})",
        f"{p}dex_oi_call_values = array.from({', '.join(d_oi_c)})",
        f"{p}dex_oi_put_values  = array.from({', '.join(d_oi_p)})",
        f"{p}dex_net_values     = array.from({', '.join(d_net)})"])

# ══════════════════════════════════════════════════════════════════
# 16 · SIDEBAR
# ══════════════════════════════════════════════════════════════════

with st.sidebar:
    # ── Configurações GitHub (ocultas — sem exibição na sidebar) ──
    GITHUB_USER   = "fclfrancis"
    GITHUB_REPO   = "dashboard-etf"
    GITHUB_BRANCH = "main"
    GITHUB_PASTA  = "dados"
    _API_URL  = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_PASTA}?ref={GITHUB_BRANCH}"
    _RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/{GITHUB_PASTA}"

    @st.cache_data(ttl=60)
    def listar_arquivos_github_win():
        try:
            r = requests.get(_API_URL, timeout=10)
            if r.status_code == 200:
                return [f["name"] for f in r.json() if f["name"].endswith(".json")]
        except:
            pass
        return []

    @st.cache_data(ttl=60)
    def baixar_json_github_win(nome_arquivo):
        url = f"{_RAW_BASE}/{nome_arquivo}"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                return r.json()
        except:
            pass
        return None

    nomes_disponiveis = listar_arquivos_github_win()
    arquivos_encontrados = nomes_disponiveis
    tickers_encontrados = {}

    if nomes_disponiveis:
        tickers_encontrados = agrupar_por_ticker(nomes_disponiveis)

    # Snapshot: seletor oculto via CSS — funcional mas invisível
    snapshots = {}
    if nomes_disponiveis: snapshots = agrupar_snapshots(nomes_disponiveis)

    # CSS para ocultar tudo acima de PARÂMETROS WIN na sidebar
    st.markdown("""
    <style>
    /* Oculta o seletor de snapshot mas mantém funcional via key */
    div[data-testid='stSidebar'] div[data-testid='stSelectbox'] { display: none !important; }
    </style>""", unsafe_allow_html=True)

    if snapshots: momento = st.selectbox("Snapshot:", list(snapshots.keys()), key="snapshot_hidden", label_visibility="collapsed")
    else: momento = None

    # ── Único elemento visível: PARÂMETROS WIN ────────────────────
    st.markdown("<div style='color:#ffb400;font-size:14px;font-weight:700;letter-spacing:2px;"
                "padding:16px 0 8px;text-shadow:0 0 4px #ffb400;'>🎯 PARÂMETROS WIN</div>", unsafe_allow_html=True)

    ibov_input = st.number_input("📊 WIN Atual (pts):", value=0, step=100, format="%d")

    st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
<<<<<<< HEAD
    st.markdown("<div style='color:#ffb400;font-size:13px;font-weight:700;letter-spacing:2px;"
                "padding:6px 0;text-shadow:0 0 4px #ffb400;'>🎯 PARÂMETROS WIN</div>", unsafe_allow_html=True)

    ibov_input    = st.number_input("📊 WIN Atual (pts):", value=0, step=100, format="%d")

    st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
=======
>>>>>>> b04ecfa7ce3cfe251b4276b48d8e23c494e1514e

    pilares_ativos = {}
    pilares_ativos["EWZ"]  = True
    pilares_ativos["VALE"] = True
    pilares_ativos["PBR"]  = True
    pilares_ativos["SPY"]  = True
    pilares_ativos["USO"]  = True
    pilares_ativos["EEM"]  = True

    st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
    min_fin       = 0
    multiplicador = 100
<<<<<<< HEAD
    focus_pct     = 0.03  # ±3% ao redor do spot
=======
    focus_pct     = 0.03
>>>>>>> b04ecfa7ce3cfe251b4276b48d8e23c494e1514e

# ══════════════════════════════════════════════════════════════════
# 17 · HEADER
# ══════════════════════════════════════════════════════════════════

ibov_val = int(ibov_input)

st.markdown(
    f"<div style='display:flex;justify-content:space-between;align-items:baseline;margin-bottom:4px;'>"
    f"<h3 style='margin:0;'>📡 PAINEL WIN AGREGADO • MARKET MAKER</h3>"
    f"<span style='color:#8a9bb5;font-size:13px;'>⏱️ {datetime.now().strftime('%H:%M:%S')} | V9.6-WIN-v4.2</span>"
    f"</div>", unsafe_allow_html=True)

_pilares_str = " · ".join([tk for tk, ativo in pilares_ativos.items() if ativo])
st.markdown(
    f"<div style='display:flex;gap:20px;padding:8px 12px;background:rgba(255,180,0,0.06);"
    f"border:1px solid rgba(255,180,0,0.2);border-radius:8px;margin-bottom:8px;"
    f"font-family:JetBrains Mono,monospace;font-size:13px;'>"
    f"<span>🎯 <b style='color:#ffb400;'>WIN SPOT</b> <span class='text-win'>{fmt_win(ibov_val) if ibov_val else '—'}</span></span>"
    f"</div>", unsafe_allow_html=True)
st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# 18 · GUARDS
# ══════════════════════════════════════════════════════════════════

if not momento:
    st.markdown(alert_box("⬆ Aguardando arquivos JSON na pasta 'dados/' do repositório GitHub.", "info"), unsafe_allow_html=True)
    st.stop()
if ibov_val == 0:
    st.markdown(alert_box("⬆ Informe o valor atual do WIN (pts) na sidebar.", "warning"), unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════════════════════
# 19 · PROCESSAMENTO
# ══════════════════════════════════════════════════════════════════

frames_win   = []
frames_norm  = []
frames_bruto = []
pilares_ok   = []

_spot_ref    = 0.0
_v9_ref_df   = pd.DataFrame()

def _get_arqs_github(tk):
    # ── Correção 1: filtra por data do pregão mais recente ──────
    # Cada arquivo tem a data no nome (ex: ETF_EWZ_2026-05-29_...).
    # Só carrega arquivos cuja data bate com o snapshot selecionado
    # (variável `momento`), evitando misturar pregões diferentes.
    nomes_tk = tickers_encontrados.get(tk, [])
    nomes = [n for n in nomes_tk if momento and momento in n]
    if not nomes:
        # fallback: usa qualquer arquivo disponível do ticker
        nomes = nomes_tk
    arqs = []
    for nome in nomes:
        js = baixar_json_github_win(nome)
        if js:
            arqs.append(io.StringIO(json.dumps(js)))
    return arqs

with st.spinner("⚙️ Processando pilares..."):
    for tk in TICKERS_PILARES:
        if not pilares_ativos.get(tk, True): continue
        arqs = _get_arqs_github(tk)
        if not arqs: continue
        peso = _PESOS_CORR[tk]

        df_win_pilar = _carregar_pilar_win(tk, arqs, ibov_val, peso)
        if not df_win_pilar.empty:
            frames_win.append(df_win_pilar); pilares_ok.append(tk)

        df_norm_pilar = _calcular_pilar_normalizado(tk, arqs, ibov_val, peso)
        if not df_norm_pilar.empty:
            frames_norm.append(df_norm_pilar)

        df_bruto = _carregar_pilar_bruto(tk, arqs, float(multiplicador))
        if not df_bruto.empty:
            frames_bruto.append(df_bruto)

        if tk == "EWZ" and arqs:
            frs_ref = [parse_json(a) for a in arqs]
            frs_ref = [f for f in frs_ref if f is not None and not f.empty]
            if frs_ref:
                df_ref_raw = pd.concat(frs_ref, ignore_index=True)
                _spot_ref  = _detectar_spot_pcp(df_ref_raw) or detectar_spot(df_ref_raw)
                if _spot_ref > 0:
                    _v9_ref_df = calcular_v9(df_ref_raw, _spot_ref, float(multiplicador))

if not frames_win:
    st.markdown(alert_box("❌ Nenhum dado válido. Verifique a pasta e os pilares ativos.", "danger"), unsafe_allow_html=True)
    st.stop()

pilares_str  = " · ".join(pilares_ok)
df_win_all   = pd.concat(frames_win, ignore_index=True)

_s_lo = int(ibov_val * (1 - focus_pct))
_s_hi = int(ibov_val * (1 + focus_pct))
df_win_plot = df_win_all[
    (df_win_all["strike_win"] >= _s_lo) &
    (df_win_all["strike_win"] <= _s_hi)
].copy()

if df_win_plot.empty:
    df_win_plot = df_win_all.copy()

m            = _calcular_metricas_win(df_win_plot, ibov_val)

if not m:
    st.markdown(alert_box("⚠ Não foi possível calcular métricas.", "warning"), unsafe_allow_html=True)
    st.stop()

# ── Correção 2: alerta de convicção derivado dos 6 pilares WIN ──
# Usa net_gex e net_dex de _calcular_metricas_win (já calculado em m)
# em vez de processar_inteligencia(EWZ). Mantém _v9_ref_df só para
# o Radar Institucional (whales por z-score em espaço USD do EWZ).

def _alerta_agregado_win(m: dict, ibov: int) -> tuple:
    """
    Deriva o alerta de convicção a partir das métricas WIN agregadas.
    Lógica espelhada de processar_inteligencia, mas usando:
      - net_gex  (GEX dos 6 pilares, espaço WIN)  como indicador de regime
      - net_dex  (DEX dos 6 pilares, espaço WIN)  como indicador direcional
      - gamma_flip WIN                             como divisor de regime
    Retorna (status, mensagem) para exibição no alerta principal.
    """
    net_gex    = m["net_gex"]
    net_dex    = m["net_dex"]
    gamma_flip = m["gamma_flip"]
    gamma_wall = m["gamma_wall"]

    # Regime: Long Gamma (spot acima do flip) vs Short Gamma (abaixo)
    spot_acima_flip = ibov > gamma_flip

    if spot_acima_flip and net_dex > 0 and net_gex > 0:
        return "success", "🔥 ALTA CONVICÇÃO (Safe Zone) — Long Gamma + fluxo altista. MMs provêm liquidez para a subida."
    elif spot_acima_flip and net_dex > 0 and net_gex < 0:
        return "warning", f"⚡ ATENÇÃO: Fluxo altista mas MM em Short Gamma — volatilidade elevada. Gamma Wall: {fmt_win(gamma_wall)}"
    elif spot_acima_flip and net_dex <= 0:
        return "info", f"⚖️ DIVERGÊNCIA: Spot acima do Flip ({fmt_win(gamma_flip)}) mas fluxo vendedor. Aguarde confirmação."
    elif not spot_acima_flip and net_dex < 0 and net_gex < 0:
        return "danger", "💀 CASCATA (Falling Knife) — Short Gamma + fluxo baixista. Zona de aceleração negativa."
    elif not spot_acima_flip and net_dex < 0 and net_gex > 0:
        return "warning", f"🚀 RISCO DE SQUEEZE! Spot abaixo do Flip ({fmt_win(gamma_flip)}) com fluxo vendedor — reversão possível."
    elif not spot_acima_flip and net_dex >= 0:
        return "info", f"🔄 RECUPERAÇÃO TENTATIVA: Fluxo comprador abaixo do Flip ({fmt_win(gamma_flip)}). Confirme rompimento."
    else:
        return "info", "⚖️ MERCADO EM EQUILÍBRIO / CONSOLIDAÇÃO — Aguarde confirmação."

_alerta_stat, _alerta_msg = _alerta_agregado_win(m, ibov_val)

# Radar Institucional: mantém EWZ v9 para whales por z-score
res_intel, g_flip_usd = processar_inteligencia(_v9_ref_df, _spot_ref) if not _v9_ref_df.empty else (None, 0.0)

if res_intel:
    strikes_agg_ref = (_v9_ref_df.groupby(["strikePrice","optionType"])
                       .agg(gex_total=("gex_total","sum"), dex_total=("dex_total","sum"),
                            vanna_total=("vanna_total","sum"), volume=("volume","sum"),
                            financial_flow=("financial_flow","sum"))
                       .reset_index())
    w_calls_ref = res_intel["whales"][res_intel["whales"]["optionType"]=="Call"] if not res_intel["whales"].empty else pd.DataFrame()
    w_puts_ref  = res_intel["whales"][res_intel["whales"]["optionType"]=="Put"]  if not res_intel["whales"].empty else pd.DataFrame()

df_temporal = _build_temporal_df(frames_bruto)

# ══════════════════════════════════════════════════════════════════
# 20 · LAYOUT PRINCIPAL — 30% | 70%
# ══════════════════════════════════════════════════════════════════

col_left, col_right = st.columns([3, 7])

# ─── COLUNA ESQUERDA (30%) ────────────────────────────────────────
with col_left:

    # ── Correção 3: alerta unificado — fonte: 6 pilares WIN ────────
    st.markdown(alert_box(_alerta_msg, _alerta_stat), unsafe_allow_html=True)

    st.markdown(
        f"<div style='font-family:JetBrains Mono,monospace;font-size:13px;color:#0ff;"
        f"margin:12px 0 2px;letter-spacing:1px;text-shadow:0 0 5px #0ff;'>"
        f"⚡ SPOT WIN: <b style='color:#ffb400;font-size:15px;'>{fmt_win(ibov_val)}</b></div>",
        unsafe_allow_html=True)

    k1, k2 = st.columns(2)
    k1.markdown(kpi("SENTIMENTO",   m["bias"],     m["bias_cls"],   f"Net DEX {fmt_M(m['net_dex'])}"), unsafe_allow_html=True)
    k2.markdown(kpi("C/P MOMENTUM", f"{m['mom_val']:.2f}x", "neutral", f"C:{fmt_M(m['net_vol_c'])}  P:{fmt_M(m['net_vol_p'])}"), unsafe_allow_html=True)
    k3, k4 = st.columns(2)
    k3.markdown(kpi("NET GEX (MM)",   fmt_M(m["net_gex"]),   "neutral", "Long+=estabil. Short−=aceler."), unsafe_allow_html=True)
    k4.markdown(kpi("NET DEX (flow)", fmt_M(m["net_dex"]),   m["bias_cls"], "Delta flow agregado"), unsafe_allow_html=True)

    section("ESTRUTURA GAMA & RISCO")

    def _desc_gwall(pts, ibov):
        d = dist_win(pts, ibov); lado = "acima" if pts > ibov else "abaixo"
        return (f"Gamma Wall {lado} do spot ({d}). "
                + ("MM vai vender delta se preço subir. Difícil de romper." if pts > ibov
                   else "MM vai comprar delta se preço cair. Suporte estrutural forte."))

    def _desc_gflip(pts, ibov):
        d = dist_win(pts, ibov); lado = "acima" if pts > ibov else "abaixo"
        return f"Gamma Flip {lado} do spot ({d}). MM muda de regime de gamma aqui."

    gw_val  = float(m["gex_s"].get(m["gamma_wall"], 0))
    gw_sign = "Long" if gw_val >= 0 else "Short"
    gw_acao = "⛔ Teto" if m["gamma_wall"] > ibov_val else "🟢 Piso"
    gw_cor  = "#FF4444" if m["gamma_wall"] > ibov_val else "#00FF00"

    rows_struct = (
        f"<tr title='{_desc_gwall(m['gamma_wall'], ibov_val)}' style='cursor:help;border-bottom:1px solid rgba(255,255,255,0.05);'>"
        f"<td style='font-size:13px;'>🧱 Gamma Wall</td>"
        f"<td class='text-win'><b>{fmt_win(m['gamma_wall'])}</b></td>"
        f"<td style='color:#0ff;font-size:13px;'>{gw_sign} {fmt_M(gw_val)}</td>"
        f"<td style='color:{gw_cor};font-size:13px;'>{gw_acao}</td>"
        f"<td style='color:#8a9bb5;font-size:13px;'>{dist_win(m['gamma_wall'], ibov_val)}</td></tr>"

        f"<tr title='{_desc_gflip(m['gamma_flip'], ibov_val)}' style='cursor:help;border-bottom:1px solid rgba(255,255,255,0.05);'>"
        f"<td style='font-size:13px;'>⚡ Gamma Flip</td>"
        f"<td class='text-win'><b>{fmt_win(m['gamma_flip'])}</b></td>"
        f"<td class='text-dim' style='font-size:13px;'>Zero-crossing GEX</td>"
        f"<td style='color:#ffa500;font-size:13px;'>🔄 Transição</td>"
        f"<td style='color:#8a9bb5;font-size:13px;'>{dist_win(m['gamma_flip'], ibov_val)}</td></tr>"

        f"<tr title='Strike com maior concentração de volume — age como imã de preço.' style='cursor:help;'>"
        f"<td style='font-size:13px;'>🎯 Max Volume</td>"
        f"<td class='text-win'><b>{fmt_win(m['max_vol_win'])}</b></td>"
        f"<td class='text-dim' style='font-size:13px;'>Pico VOL</td>"
        f"<td style='color:#ffd700;font-size:13px;'>🧲 Magnético</td>"
        f"<td style='color:#8a9bb5;font-size:13px;'>{dist_win(m['max_vol_win'], ibov_val)}</td></tr>"
    )
    if m["delta_flip"]:
        rows_struct += (
            f"<tr title='Ponto onde pressão direcional muda de sinal (DEX zero-crossing).' style='cursor:help;'>"
            f"<td style='font-size:13px;'>⚡ Delta Flip</td>"
            f"<td class='text-win'><b>{fmt_win(m['delta_flip'])}</b></td>"
            f"<td class='text-dim' style='font-size:13px;'>Zero-crossing DEX</td>"
            f"<td style='color:#ffa500;font-size:13px;'>🔄 Inversão</td>"
            f"<td style='color:#8a9bb5;font-size:13px;'>{dist_win(m['delta_flip'], ibov_val)}</td></tr>"
        )
    if m["vol_trigger"]:
        rows_struct += (
            f"<tr title='75% do range entre Gamma Wall e Gamma Flip. MM perde controle direcional acima daqui.' style='cursor:help;'>"
            f"<td style='font-size:13px;'>🔥 Vol Trigger</td>"
            f"<td class='text-win'><b>{fmt_win(m['vol_trigger'])}</b></td>"
            f"<td class='text-dim' style='font-size:13px;'>75% GW-GF</td>"
            f"<td style='color:#fa0;font-size:13px;'>⚠ Perda Controle</td>"
            f"<td style='color:#8a9bb5;font-size:13px;'>{dist_win(m['vol_trigger'], ibov_val)}</td></tr>"
        )

    st.markdown(
        f"<div class='dashboard-card'><table class='hud-table'>"
        f"<tr><th>NÍVEL</th><th>WIN (pts)</th><th>VALOR</th><th>AÇÃO</th><th>DIST</th></tr>"
        f"{rows_struct}</table>"
        f"<div style='font-size:11px;color:#3a7a8a;margin-top:6px;font-family:JetBrains Mono;'>"
        f"💡 Passe o mouse nas linhas para ver a interpretação operacional.</div></div>",
        unsafe_allow_html=True)

    if any([m["cw_vol"], m["cw_oi"], m["pw_vol"], m["pw_oi"]]):
        walls_rows = ""
        if m["cw_vol"]: walls_rows += (
            f"<tr title='Call Wall por Volume. Resistência de fluxo acima do spot.' style='cursor:help;'>"
            f"<td style='font-size:13px;'>📞 Call Wall VOL</td>"
            f"<td class='text-win'><b>{fmt_win(m['cw_vol'])}</b></td>"
            f"<td style='color:#FF4444;'>⛔ Resistência</td>"
            f"<td style='color:#8a9bb5;'>{dist_win(m['cw_vol'], ibov_val)}</td></tr>")
        if m["cw_oi"]: walls_rows += (
            f"<tr title='Call Wall por OI. Teto estrutural persistente.' style='cursor:help;'>"
            f"<td style='font-size:13px;'>📞 Call Wall OI</td>"
            f"<td class='text-win'><b>{fmt_win(m['cw_oi'])}</b></td>"
            f"<td style='color:#FF4444;'>⛔ Teto Estrutural</td>"
            f"<td style='color:#8a9bb5;'>{dist_win(m['cw_oi'], ibov_val)}</td></tr>")
        if m["pw_vol"]: walls_rows += (
            f"<tr title='Put Wall por Volume. Defesa de fluxo abaixo do spot.' style='cursor:help;'>"
            f"<td style='font-size:13px;'>📢 Put Wall VOL</td>"
            f"<td class='text-win'><b>{fmt_win(m['pw_vol'])}</b></td>"
            f"<td style='color:#00FF00;'>🟢 Defesa</td>"
            f"<td style='color:#8a9bb5;'>{dist_win(m['pw_vol'], ibov_val)}</td></tr>")
        if m["pw_oi"]: walls_rows += (
            f"<tr title='Put Wall por OI. Muro estrutural que sustenta o piso.' style='cursor:help;'>"
            f"<td style='font-size:13px;'>📢 Put Wall OI</td>"
            f"<td class='text-win'><b>{fmt_win(m['pw_oi'])}</b></td>"
            f"<td style='color:#00FF00;'>🟢 Muro Estrutural</td>"
            f"<td style='color:#8a9bb5;'>{dist_win(m['pw_oi'], ibov_val)}</td></tr>")
        st.markdown(
            f"<div class='dashboard-card'><table class='hud-table'>"
            f"<tr><th>WALL</th><th>WIN (pts)</th><th>AÇÃO</th><th>DIST</th></tr>"
            f"{walls_rows}</table></div>", unsafe_allow_html=True)

    section("ZONAS DE IMPACTO DELTA")

    ic_win = m.get("ic_win", pd.DataFrame())
    ip_win = m.get("ip_win", pd.DataFrame())

    ri = ""
    if not ic_win.empty:
        for sw in ic_win.index:
            acima = sw > ibov_val
            tipo_lbl = "<span style='color:#FF4444;'>⛔ Resistência</span>" if acima else "<span style='color:#00FF00;'>🟢 Suporte</span>"
            motivo = ("Call OTM acima do spot. MM vai vender delta se preço subir até aqui." if acima
                      else "Call ITM abaixo do spot. MM já comprou futuros para hedge.")
            ri += (f"<tr title='{motivo}' style='cursor:help;'>"
                   f"<td>{tipo_lbl}</td>"
                   f"<td class='text-win' style='font-size:13px;'><b>{fmt_win(sw)}</b> C</td>"
                   f"<td style='color:#8a9bb5;font-size:13px;'>{dist_win(sw, ibov_val)}</td></tr>")

    if not ip_win.empty:
        for sw in ip_win.index:
            abaixo = sw < ibov_val
            tipo_lbl = "<span style='color:#00FF00;'>🟢 Suporte</span>" if abaixo else "<span style='color:#FF4444;'>⛔ Pressão Vend.</span>"
            motivo = ("Put OTM abaixo do spot. MM vai comprar futuros se preço cair até aqui." if abaixo
                      else "Put ITM acima do spot. MM já vendeu futuros para hedge.")
            ri += (f"<tr title='{motivo}' style='cursor:help;'>"
                   f"<td>{tipo_lbl}</td>"
                   f"<td class='text-win' style='font-size:13px;'><b>{fmt_win(sw)}</b> P</td>"
                   f"<td style='color:#8a9bb5;font-size:13px;'>{dist_win(sw, ibov_val)}</td></tr>")

    delta_flip_html = ""
    if m["delta_flip"]:
        d = dist_win(m["delta_flip"], ibov_val); lado = "acima" if m["delta_flip"] > ibov_val else "abaixo"
        msg_flip = ("MM passa de vendido para comprado acima desse nível." if m["delta_flip"] > ibov_val
                    else "MM passa de comprado para vendido abaixo desse nível.")
        delta_flip_html = (
            f"<tr style='border-top:1px solid rgba(255,165,0,0.4);'>"
            f"<td colspan='3' style='padding-top:8px;'>"
            f"<span style='color:#ffa500;font-family:JetBrains Mono;font-size:13px;'>"
            f"🔄 DELTA FLIP &nbsp;<b class='text-win'>{fmt_win(m['delta_flip'])}</b>"
            f"&nbsp;<span style='color:#8a9bb5;'>({d} · {lado} do spot)</span><br>"
            f"<span style='color:#8a9bb5;font-size:11px;'>Pressão direcional muda de sinal. {msg_flip}</span>"
            f"</span></td></tr>")

    st.markdown(
        f"<div class='dashboard-card'><table class='hud-table'>"
        f"<tr><th>TIPO</th><th>WIN (pts)</th><th>DIST.</th></tr>"
        f"{ri}{delta_flip_html}</table>"
        f"<div style='font-size:11px;color:#3a7a8a;margin-top:6px;font-family:JetBrains Mono;'>"
        f"💡 Passe o mouse para ver o motivo da classificação.</div></div>",
        unsafe_allow_html=True)

    section("VANNA & VOLATILIDADE")
    vol_status_w = "LONG VOL" if m["net_vanna"] > 0 else "SHORT VOL"
    vol_color_w  = "#0f0" if m["net_vanna"] > 0 else "#f44"
    tag_vol_w    = "tag-bull" if m["net_vanna"] > 0 else "tag-bear"
    shock_act_w  = "MM COMPRA" if m["net_vanna"] > 0 else "MM VENDE"
    shock_col_w  = "#0f0" if m["net_vanna"] > 0 else "#f44"
    st.markdown(
        f"<div class='dashboard-card' style='border-left:4px solid {vol_color_w};'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
        f"<span class='kpi-label' style='font-size:13px;'>{vol_status_w}</span>"
        f"<span class='tag {tag_vol_w}'>{vol_status_w}</span></div>"
        f"<div style='font-family:JetBrains Mono,monospace;font-size:18px;color:#f0f3fa;"
        f"margin:6px 0;text-shadow:0 0 5px rgba(0,255,255,0.4);'>{fmt_M(m['net_vanna'])}</div>"
        f"<div style='background:rgba(0,255,255,0.04);padding:6px;"
        f"border-left:3px solid {shock_col_w};border-radius:6px;font-size:13px;font-family:JetBrains Mono;'>"
        f"<span class='text-dim'>VANNA LÍQUIDA:</span> "
        f"<span style='color:{shock_col_w};font-weight:bold;'>{shock_act_w} {fmt_M(m['net_vanna'])}</span>"
        f"</div></div>", unsafe_allow_html=True)

    section("TOP VANNA POINTS — WIN")
    vanna_s = m["vanna_s"]
    vrows = ""
    for sw in m["top_vanna"]:
        val = float(vanna_s.get(sw, 0))
        nv, dc = legenda_vanna_ctx(val, vanna_s, sw, ibov_val)
        act = "COMPRA" if val > 0 else "VENDE"; clr = "#0f0" if val > 0 else "#f44"
        vrows += (f"<tr title='{dc}' style='cursor:help;'>"
                  f"<td class='text-win' style='font-size:13px;'>🐳 {fmt_win(sw)}</td>"
                  f"<td style='color:{clr};font-weight:bold;font-size:13px;'>{act}</td>"
                  f"<td class='text-gold' style='font-size:13px;'>{fmt_M(val)}</td>"
                  f"<td style='color:#8a9bb5;font-size:11px;'>{nv}</td></tr>")
    st.markdown(
        f"<div class='dashboard-card'><table class='hud-table'>"
        f"<tr><th>WIN (pts)</th><th>AÇÃO IV↑</th><th>FLUXO</th><th>NÍVEL</th></tr>"
        f"{vrows}</table>"
        f"<div style='font-size:11px;color:#3a7a8a;margin-top:6px;font-family:JetBrains Mono;'>"
        f"💡 Passe o mouse nas linhas para ver a interpretação.</div></div>",
        unsafe_allow_html=True)

    st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
    section("DIAGNÓSTICO ESTRATÉGICO")

    d1, d2 = st.columns(2)
    d1.markdown(kpi("REGIME GAMMA", m["regime"], m["regime_cls"],
                    "Estabilidade" if m["net_gex"] > 0 else "Aceleração"), unsafe_allow_html=True)
    d2.markdown(kpi("BIAS DIRECIONAL", m["bias"], m["bias_cls"],
                    f"Net DEX {fmt_M(m['net_dex'])}"), unsafe_allow_html=True)

    notas = []
    # ── Correção 3b: avisa sobre pilares sem dados no snapshot ──
    _pilares_esperados = set(TICKERS_PILARES)
    _pilares_carregados = set(pilares_ok)
    _pilares_faltando = _pilares_esperados - _pilares_carregados
    if _pilares_faltando:
        notas.append(("warning",
            f"⚠ Pilares sem dados no snapshot '{momento}': "
            f"{', '.join(sorted(_pilares_faltando))} — "
            f"carregue arquivos com a mesma data para todos os pilares."))
    if m["net_gex"] < 0 and m["net_dex"] < 0:
        notas.append(("danger",  "⚠ PERIGO: MM em Short Gamma com bias baixista → Queda Acelerada"))
    if m["net_gex"] > 0 and m["net_dex"] > 0:
        notas.append(("warning", "✅ ANCORAGEM: Long Gamma com bias altista → Topo em formação"))
    if m["alerta_flip"]:
        notas.append(("info", f"🎯 ZONA CRÍTICA: Spot próximo ao Gamma Flip ({fmt_win(m['gamma_flip'])} pts)"))
    for kind, msg_nota in notas:
        st.markdown(alert_box(msg_nota, kind), unsafe_allow_html=True)

# ─── COLUNA DIREITA (70%) ────────────────────────────────────────
with col_right:
    section("TERMINAL WIN — VOLUME · OPEN INTEREST")
    fig_vol = build_vol_oi_chart_win(df_win_plot, ibov_val, focus_pct)
    st.plotly_chart(fig_vol, use_container_width=True)

    st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
    section("TRIPLE PRESSURE MAP WIN  —  DEX · GEX · VANNA")
    fig_press = build_pressure_chart_win(df_win_plot, ibov_val, focus_pct)
    st.plotly_chart(fig_press, use_container_width=True)

    # ══════════════════════════════════════════════════════════════
    # 20-B · MOMENTUM REAL — Vol/OI por Strike WIN (6 Pilares)
    # Lógica idêntica ao momentum_real.py, adaptada para strike_win
<<<<<<< HEAD
=======
    #
    # CORREÇÕES v4.1:
    #   Bug 1 — OI estrutural: usa df_win_all (todos os strikes, inclusive
    #            vol=0) como denominador, não apenas os strikes com vol>0.
    #            VALE/EWZ perdiam até 64% do OI por esse filtro.
    #
    #   Bug 2 — Vol/OI por row: ratio calculada APÓS o groupby
    #            (vol_sum / oi_sum), nunca como soma de ratios individuais.
    #            A soma de ratios pode inflar o sinal em +38.000% (SPY).
>>>>>>> b04ecfa7ce3cfe251b4276b48d8e23c494e1514e
    # ══════════════════════════════════════════════════════════════
    st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
    section("MOMENTUM REAL — VOL/OI  (urgência do fluxo por strike WIN)")

<<<<<<< HEAD
    _df_mom = df_win_plot[df_win_plot["openInterest"] > 10].copy()

    if not _df_mom.empty:
        _df_mom["Vol_OI"] = _df_mom["volume"] / _df_mom["openInterest"].replace(0, 1)
=======
    # Bug 1 fix: OI estrutural vem de df_win_all (vol >= 0)
    # Agrupa volume do dia (só strikes com vol>0, já filtrados em df_win_plot)
    _vol_day = (
        df_win_plot
        .groupby(["strike_win", "optionType"])["volume"]
        .sum()
        .reset_index()
        .rename(columns={"volume": "_vol_sum"})
    )

    # Agrupa OI estrutural de TODOS os strikes (df_win_all inclui vol=0)
    _oi_struct = (
        df_win_all
        .groupby(["strike_win", "optionType"])["openInterest"]
        .sum()
        .reset_index()
        .rename(columns={"openInterest": "_oi_sum"})
    )

    # Merge: mantém apenas strikes que tiveram volume no dia,
    # mas usa o OI completo como denominador
    _df_mom = _vol_day.merge(_oi_struct, on=["strike_win", "optionType"], how="left")
    _df_mom["_oi_sum"] = _df_mom["_oi_sum"].fillna(0)

    # Filtra strikes sem OI estrutural relevante (denominador mínimo)
    _df_mom = _df_mom[_df_mom["_oi_sum"] > 10].copy()

    if not _df_mom.empty:
        # Bug 2 fix: ratio calculada sobre o agregado, nunca por row
        _df_mom["Vol_OI"] = _df_mom["_vol_sum"] / _df_mom["_oi_sum"].replace(0, 1)
>>>>>>> b04ecfa7ce3cfe251b4276b48d8e23c494e1514e

        _urg_threshold = (
            _df_mom["Vol_OI"][_df_mom["Vol_OI"] > 0].quantile(0.75)
            if not _df_mom.empty else 1.0
        )

        def _classif_urgencia_win(vol_oi, tipo, threshold):
            if vol_oi < 0.3:
                return "⚪ POSIÇÃO ESTÁTICA",  "Strike sem atividade relevante no momento."
            elif vol_oi < 1.0:
                return "🔵 FLUXO NORMAL",      "Nada fora do comum. MM operando normalmente."
            elif vol_oi < threshold:
                return "🟡 FLUXO ELEVADO",     "Movimento acima do normal. Fique atento."
            elif vol_oi < threshold * 2:
                if tipo == "Call":
                    return "🟠 URGÊNCIA DETECTADA", "Grandes players comprando. Pressão de alta."
                else:
                    return "🟠 URGÊNCIA DETECTADA", "Grandes players se protegendo. Pressão de baixa."
            else:
                if tipo == "Call":
                    return "🔴 ALERTA MÁXIMO", "Muita compra aqui. Preço pode subir rápido e forte."
                else:
                    return "🔴 ALERTA MÁXIMO", "Muita proteção aqui. Preço pode cair rápido e forte."

<<<<<<< HEAD
        _niveis_mom        = []
=======
        _niveis_mom         = []
>>>>>>> b04ecfa7ce3cfe251b4276b48d8e23c494e1514e
        _comportamentos_mom = []
        for _, _row in _df_mom.iterrows():
            _nv, _comp = _classif_urgencia_win(_row["Vol_OI"], _row["optionType"], _urg_threshold)
            _niveis_mom.append(_nv)
            _comportamentos_mom.append(_comp)
        _df_mom["nivel"]         = _niveis_mom
        _df_mom["comportamento"] = _comportamentos_mom

        # Ticks WIN — range idêntico ao dos outros gráficos (focus_pct)
        _s_lo_m = int(ibov_val * (1 - focus_pct))
        _s_hi_m = int(ibov_val * (1 + focus_pct))
        _strikes_mom = sorted(_df_mom["strike_win"].unique())
        _tick_vals_m = [s for s in _strikes_mom if _s_lo_m <= s <= _s_hi_m] or _strikes_mom
        _tick_text_m = [_fmt_win_tick(s) for s in _tick_vals_m]

        fig_mom = go.Figure()
        for _tipo, _color, _label in zip(
<<<<<<< HEAD
            ["Call",       "Put"],
            [COLOR_CALL,   COLOR_PUT],
            ["CALL",       "PUT"],
        ):
            _df_v = (
                _df_mom[_df_mom["optionType"] == _tipo]
                .groupby("strike_win")[["Vol_OI", "nivel", "comportamento"]]
                .agg({"Vol_OI": "sum", "nivel": "first", "comportamento": "first"})
                .reset_index()
=======
            ["Call",     "Put"],
            [COLOR_CALL, COLOR_PUT],
            ["CALL",     "PUT"],
        ):
            # Bug 2 fix: cada strike_win/optionType já tem uma linha única
            # após o merge — Vol_OI já é a ratio do agregado, não soma de ratios
            _df_v = (
                _df_mom[_df_mom["optionType"] == _tipo]
                [["strike_win", "Vol_OI", "nivel", "comportamento",
                  "_vol_sum", "_oi_sum"]]
                .copy()
                .reset_index(drop=True)
>>>>>>> b04ecfa7ce3cfe251b4276b48d8e23c494e1514e
            )
            if _df_v.empty:
                continue

            fig_mom.add_trace(go.Bar(
                x=_df_v["strike_win"],
                y=_df_v["Vol_OI"],
                marker_color=_color,
                marker_line_width=0,
                name=_label,
<<<<<<< HEAD
                customdata=np.stack([_df_v["nivel"], _df_v["comportamento"]], axis=1),
                hovertemplate=(
                    "<b>Strike WIN: %{x:,.0f}</b><br>"
                    "Vol/OI: %{y:.2f}x<br>"
=======
                customdata=np.stack(
                    [_df_v["nivel"], _df_v["comportamento"],
                     _df_v["_vol_sum"], _df_v["_oi_sum"]],
                    axis=1
                ),
                hovertemplate=(
                    "<b>Strike WIN: %{x:,.0f}</b><br>"
                    "Vol/OI: %{y:.2f}x<br>"
                    "Vol dia: %{customdata[2]:,.0f}  |  OI estrutural: %{customdata[3]:,.0f}<br>"
>>>>>>> b04ecfa7ce3cfe251b4276b48d8e23c494e1514e
                    f"Tipo: {_label}<br>"
                    "──────────────────<br>"
                    "%{customdata[0]}<br>"
                    "<i>%{customdata[1]}</i>"
                    "<extra></extra>"
                ),
            ))

        # Linha de urgência (p75)
        fig_mom.add_hline(
            y=_urg_threshold,
            line_dash="dash", line_color="#ffa500", line_width=1.5, opacity=0.9,
            annotation_text=f"URGÊNCIA MM ({_urg_threshold:.2f}x)",
            annotation_position="top right",
            annotation_font=dict(color="#ffa500", size=11, family="JetBrains Mono"),
        )
        # Linha neutra 1.0×
        fig_mom.add_hline(
            y=1.0,
            line_dash="dot", line_color="#ffffff", line_width=1, opacity=0.35,
            annotation_text="neutro 1.0x",
            annotation_position="bottom right",
            annotation_font=dict(color="#888", size=10, family="JetBrains Mono"),
        )
        # Linha do spot WIN
        fig_mom.add_vline(
            x=ibov_val,
            line_dash="dot", line_color=COLOR_NEON, line_width=1.5,
        )
        fig_mom.add_annotation(
            x=ibov_val, y=1.0, xref="x", yref="paper",
            text=f"SPOT {fmt_win(ibov_val)}",
            showarrow=False, yshift=8,
            font=dict(color=COLOR_NEON, size=10, family="JetBrains Mono"),
            xanchor="center",
        )

        fig_mom.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(8,12,20,0.6)",
            height=420,
            barmode="group",
            showlegend=True,
            legend=dict(
                orientation="h", y=1.02, x=1, xanchor="right",
                font=dict(size=11, family="JetBrains Mono"),
                bgcolor="rgba(0,0,0,0)",
            ),
            margin=dict(l=10, r=10, t=20, b=20),
            font=dict(family="JetBrains Mono", size=11, color="#ccddf8"),
            xaxis=dict(
                gridcolor="rgba(0,255,255,0.06)",
                tickvals=_tick_vals_m, ticktext=_tick_text_m,
                tickangle=-45, tickfont=dict(size=11),
            ),
            yaxis=dict(
                gridcolor="rgba(0,255,255,0.06)",
                title="Vol/OI ratio",
            ),
            hoverlabel=dict(
                font_size=13,
                font_family="JetBrains Mono",
                bgcolor="#0a1a20",
                bordercolor=COLOR_NEON,
            ),
        )
        st.plotly_chart(fig_mom, use_container_width=True)

        # Resumo textual de urgência máxima detectada
        _mom_max = _df_mom.sort_values("Vol_OI", ascending=False).head(1)
        if not _mom_max.empty:
            _mx = _mom_max.iloc[0]
            _mx_cor = "#ffa500" if _mx["Vol_OI"] >= _urg_threshold else "#8a9bb5"
            st.markdown(
                f"<div style='font-family:JetBrains Mono,monospace;font-size:13px;"
                f"color:{_mx_cor};padding:6px 10px;background:rgba(255,165,0,0.05);"
                f"border-left:3px solid {_mx_cor};border-radius:4px;margin-top:4px;'>"
                f"⚡ Máx. urgência: <b>WIN {fmt_win(_mx['strike_win'])}</b> · "
                f"{_mx['optionType']} · <b>{_mx['Vol_OI']:.2f}x</b> · {_mx['nivel']}"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
<<<<<<< HEAD
            alert_box("⚠ Dados insuficientes para calcular Vol/OI (OI > 10 em nenhum strike).", "warning"),
=======
            alert_box("⚠ Dados insuficientes para calcular Vol/OI (OI estrutural > 10 em nenhum strike).", "warning"),
>>>>>>> b04ecfa7ce3cfe251b4276b48d8e23c494e1514e
            unsafe_allow_html=True,
        )

# ══════════════════════════════════════════════════════════════════
# 21 · RADAR INSTITUCIONAL
# ══════════════════════════════════════════════════════════════════

if res_intel and not res_intel["whales"].empty:
    st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
    section("🐋 RADAR INSTITUCIONAL — EWZ (Z > 2.5σ)")

    def agg_whales(wdf):
        if wdf.empty: return wdf
        return (wdf.groupby("strikePrice")
                .agg(z_score=("z_score", lambda x: x.abs().max()),
                     d_flow=("d_flow","sum"), volume=("volume","sum"),
                     financial_flow=("financial_flow","sum"), optionType=("optionType","first"))
                .reset_index().sort_values("z_score", ascending=False).head(8))

    def legenda_whale_ctx(sk, opt, spot):
        acima = sk > spot; dist_pct = (sk-spot)/spot*100 if spot > 0 else 0
        if opt == "Call":
            if acima: return "⛔ Resistência", "#FF4444", "Call OTM. MM vai vender delta se preço subir até aqui.", f"{dist_pct:+.1f}%"
            else:     return "🟢 Suporte",     "#00FF00", "Call ITM. MM já comprou futuros — age como piso.", f"{dist_pct:+.1f}%"
        else:
            if not acima: return "🟢 Suporte",       "#00FF00", "Put OTM. MM vai comprar futuros se preço cair até aqui.", f"{dist_pct:+.1f}%"
            else:         return "⛔ Press. Vend.", "#FF4444", "Put ITM. MM já vendeu futuros — pressiona para baixo.", f"{dist_pct:+.1f}%"

    w_calls_agg = agg_whales(w_calls_ref) if not w_calls_ref.empty else pd.DataFrame()
    w_puts_agg  = agg_whales(w_puts_ref)  if not w_puts_ref.empty  else pd.DataFrame()
    wc1, wc2 = st.columns(2)

    with wc1:
        st.markdown("<div style='color:#0f0;font-size:13px;font-weight:bold;letter-spacing:1px;"
                    "margin-bottom:8px;font-family:JetBrains Mono;'>🟢 CALLS — IMPACTO MM</div>", unsafe_allow_html=True)
        if not w_calls_agg.empty:
            for _, row in w_calls_agg.iterrows():
                sk = row["strikePrice"]; acao, cor, desc, dist_fmt = legenda_whale_ctx(sk, "Call", _spot_ref)
                w_sk = strike_to_win(sk, _spot_ref, ibov_val)
                st.markdown(
                    f"<div class='whale-card' title='{desc}'>"
                    f"<b class='text-win' style='font-size:13px;'>{fmt_win(w_sk)}</b> "
                    f"<span style='color:#8a9bb5;font-size:11px;'>(${_fmt_strike(sk)})</span> "
                    f"<span style='color:{cor};font-size:13px;font-weight:bold;'>{acao}</span>"
                    f"<span class='text-dim' style='float:right;font-size:13px;'>{dist_fmt} spot USD</span><br>"
                    f"<span class='text-green' style='font-size:13px;'>z={row['z_score']:.1f}σ</span>"
                    f"<span class='text-dim' style='font-size:13px;'> · ΔFlow {fmt_M(row['d_flow'])}"
                    f" · Vol {row['volume']:,.0f} · Fin {fmt_M(row.get('financial_flow',0))}</span>"
                    f"</div>", unsafe_allow_html=True)
        else: st.caption("Sem anomalias em calls.")

    with wc2:
        st.markdown("<div style='color:#f44;font-size:13px;font-weight:bold;letter-spacing:1px;"
                    "margin-bottom:8px;font-family:JetBrains Mono;'>🔴 PUTS — IMPACTO MM</div>", unsafe_allow_html=True)
        if not w_puts_agg.empty:
            for _, row in w_puts_agg.iterrows():
                sk = row["strikePrice"]; acao, cor, desc, dist_fmt = legenda_whale_ctx(sk, "Put", _spot_ref)
                w_sk = strike_to_win(sk, _spot_ref, ibov_val)
                st.markdown(
                    f"<div class='whale-card' title='{desc}'>"
                    f"<b class='text-win' style='font-size:13px;'>{fmt_win(w_sk)}</b> "
                    f"<span style='color:#8a9bb5;font-size:11px;'>(${_fmt_strike(sk)})</span> "
                    f"<span style='color:{cor};font-size:13px;font-weight:bold;'>{acao}</span>"
                    f"<span class='text-dim' style='float:right;font-size:13px;'>{dist_fmt} spot USD</span><br>"
                    f"<span class='text-red' style='font-size:13px;'>z={row['z_score']:.1f}σ</span>"
                    f"<span class='text-dim' style='font-size:13px;'> · ΔFlow {fmt_M(abs(row['d_flow']))}"
                    f" · Vol {row['volume']:,.0f} · Fin {fmt_M(row.get('financial_flow',0))}</span>"
                    f"</div>", unsafe_allow_html=True)
        else: st.caption("Sem anomalias em puts.")

# ══════════════════════════════════════════════════════════════════
# 22 · FLOW EVOLUTION
# ══════════════════════════════════════════════════════════════════

st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
section("FLOW EVOLUTION — HIRO · DELTA FLOW · GAMMA FLOW")

if df_temporal.empty:
    st.markdown(
        alert_box("⚠ Sem dados temporais intraday. Os arquivos não contêm timestamps Unix válidos.", "warning"),
        unsafe_allow_html=True)
else:
    t_min_str = df_temporal["dt"].min().strftime("%Y-%m-%d %H:%M")
    t_max_str = df_temporal["dt"].max().strftime("%H:%M")
    _tks_flow = " · ".join(sorted(df_temporal["tk"].unique())) if "tk" in df_temporal.columns else pilares_str
    st.markdown(
        f"<div style='font-family:JetBrains Mono,monospace;font-size:13px;color:#8a9bb5;margin-bottom:8px;'>"
        f"◈ {len(df_temporal)} registros · {t_min_str} → {t_max_str} · Pilares: {_tks_flow}"
        f"<br><span style='font-size:11px;'>Fluxo bruto em USD — sem pesos de correlação, sem conversão WIN</span></div>",
        unsafe_allow_html=True)

    hiro_final  = df_temporal["hiro_cum"].iloc[-1]
    delta_final = df_temporal["d_flow_cum"].iloc[-1]
    is_absorbing = (hiro_final > 0) and (delta_final < 0)
    lookback  = max(10, len(df_temporal)//5)
    hiro_rec  = df_temporal["hiro"].tail(lookback).sum()
    hiro_med  = df_temporal["hiro"].abs().mean()
    intens    = abs(hiro_rec)/(hiro_med*lookback) if hiro_med > 0 else 0
    sent_h    = "COMPRADOR 🟢" if hiro_rec > 0 else "VENDEDOR 🔴"
    int_lbl   = "FORTE 🔥" if intens > 1.8 else "FRACO 😴" if intens < 0.8 else "NORMAL"

    ta1,ta2,ta3,ta4 = st.columns(4)
    ta1.markdown(kpi("HIRO ACUM.",   fmt_M(hiro_final),  "bull" if hiro_final > 0 else "bear",
                     "MM compra futuros" if hiro_final > 0 else "MM vende futuros"), unsafe_allow_html=True)
    ta2.markdown(kpi("DEX ACUM.",    fmt_M(delta_final), "bull" if delta_final > 0 else "bear",
                     "Delta flow cumulativo"), unsafe_allow_html=True)
    ta3.markdown(kpi("SENTIMENTO",   sent_h, "", f"Intens.: {intens:.2f}x — {int_lbl}"), unsafe_allow_html=True)
    ta4.markdown(kpi("ABSORÇÃO", "DETECTADA ⚠" if is_absorbing else "NÃO",
                     "bear" if is_absorbing else "neutral",
                     "HIRO+ com DEX−" if is_absorbing else "Fluxo coerente"), unsafe_allow_html=True)

    df_temporal["hiro_call_cum"] = df_temporal.apply(
        lambda r: r["hiro"] if r["opt"]=="Call" else 0.0, axis=1).cumsum()
    df_temporal["hiro_put_cum"]  = df_temporal.apply(
        lambda r: r["hiro"] if r["opt"]=="Put"  else 0.0, axis=1).cumsum()

    st.plotly_chart(_flow_fig(df_temporal, "hiro_cum",
                              "HIRO TOTAL  (+ = MM compra futuros  |  − = MM vende futuros)",
                              "#00ffe7", "#ff6b35",
                              extras=[("hiro_call_cum","#ff6b35","Calls"),("hiro_put_cum","#00FF00","Puts")]),
                    use_container_width=True)
    st.plotly_chart(_flow_fig(df_temporal, "d_flow_cum",
                              "DELTA FLOW ACUMULADO  (zero para BRUTO)",
                              "#00ffe7", "#ff6b35"), use_container_width=True)
    st.plotly_chart(_flow_fig(df_temporal, "g_flow_cum",
                              "GAMMA FLOW ACUMULADO  (+ Long Gamma  |  − Short Gamma)",
                              "#7b2fff", "#ff6b35"), use_container_width=True)

    if is_absorbing:
        st.markdown(alert_box("🚨 ABSORÇÃO DETECTADA — HIRO positivo com Delta Flow negativo: "
                               "institucionais segurando contra agressão vendedora.", "warning"),
                    unsafe_allow_html=True)
import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from psycopg2.pool import SimpleConnectionPool
import json
from io import BytesIO
import os
import re

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="PriceDesk",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500&family=Outfit:wght@300;400;500;600;700&display=swap');

:root {
    --primary:      #1E40AF;
    --primary-lt:   #EFF6FF;
    --primary-mid:  #BFDBFE;
    --primary-glow: rgba(30,64,175,0.15);
    --accent:       #0EA5E9;
    --accent2:      #6366F1;
    --success:      #059669;
    --success-lt:   #ECFDF5;
    --success-mid:  #A7F3D0;
    --danger:       #DC2626;
    --danger-lt:    #FEF2F2;
    --danger-mid:   #FECACA;
    --text:         #0F172A;
    --text-2:       #1E293B;
    --muted:        #475569;
    --muted-lt:     #94A3B8;
    --border:       #CBD5E1;
    --border-lt:    #E2E8F0;
    --card:         rgba(255,255,255,0.82);
    --card-solid:   #FFFFFF;
    --bg:           #EEF2FF;
}

* { box-sizing: border-box; }

/* ── RICH BACKGROUND — all pages ── */
.stApp {
    font-family: 'Outfit', sans-serif;
    color: var(--text);
    background: #dde8f8 !important;
    background-image:
        radial-gradient(ellipse 900px 600px at 10% 10%,  rgba(99,102,241,0.18) 0%, transparent 70%),
        radial-gradient(ellipse 700px 500px at 90% 80%,  rgba(14,165,233,0.16) 0%, transparent 70%),
        radial-gradient(ellipse 600px 400px at 50% 50%,  rgba(30,64,175,0.10) 0%, transparent 70%),
        radial-gradient(ellipse 400px 300px at 80% 20%,  rgba(167,243,208,0.22) 0%, transparent 60%),
        linear-gradient(160deg, #dde8f8 0%, #e8eeff 40%, #ddf3fb 100%) !important;
    min-height: 100vh;
    background-attachment: fixed !important;
}

/* subtle grid overlay */
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(30,64,175,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(30,64,175,0.03) 1px, transparent 1px);
    background-size: 44px 44px;
    pointer-events: none;
    z-index: 0;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding: 2rem 2.4rem 3rem !important;
    max-width: 1340px;
    position: relative;
    z-index: 1;
}

/* ── Sidebar — styled but FULLY COLLAPSIBLE ── */
section[data-testid="stSidebar"] {
    width: 256px !important;
    background: rgba(255,255,255,0.94) !important;
    backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(203,213,225,0.6) !important;
    box-shadow: 4px 0 24px rgba(30,64,175,0.07) !important;
}
section[data-testid="stSidebar"] > div { width: 256px !important; }

/* Style the collapse/expand toggle button — keep it visible and on-brand */
button[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    pointer-events: auto !important;
    background: white !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    box-shadow: 0 2px 8px rgba(30,64,175,0.10) !important;
    color: var(--primary) !important;
    transition: box-shadow .2s !important;
}
button[data-testid="collapsedControl"]:hover {
    box-shadow: 0 4px 16px rgba(30,64,175,0.18) !important;
}

/* ── Typography ── */
h1, h2, h3 {
    font-family: 'Sora', sans-serif;
    color: var(--text);
    font-weight: 700;
}

/* ── Glassmorphism Cards ── */
.metric-row { display:flex; gap:14px; margin-bottom:1.5rem; flex-wrap:wrap; }
.metric-card {
    background: var(--card);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.9);
    border-radius: 16px;
    padding: 20px 22px;
    min-width: 155px;
    flex: 1;
    box-shadow: 0 2px 16px rgba(30,64,175,0.08), 0 0 0 1px rgba(99,102,241,0.06);
    transition: transform .2s, box-shadow .2s;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #1E40AF, #0EA5E9, #6366F1);
    border-radius: 16px 16px 0 0;
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 28px rgba(30,64,175,0.14);
}
.metric-card .mc-label {
    font-size: 0.66rem;
    font-weight: 700;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 8px;
}
.metric-card .mc-value {
    font-size: 1.65rem;
    font-weight: 800;
    color: var(--text);
    font-family: 'Sora', sans-serif;
    line-height: 1;
    background: linear-gradient(135deg, #1E40AF, #0EA5E9);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.metric-card .mc-sub {
    font-size: 0.71rem;
    color: var(--muted-lt);
    margin-top: 5px;
}

/* ── Section Card ── */
.section-card {
    background: var(--card);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.9);
    border-radius: 16px;
    padding: 22px 24px 24px;
    margin-bottom: 1.3rem;
    box-shadow: 0 2px 16px rgba(30,64,175,0.07), 0 0 0 1px rgba(99,102,241,0.04);
}
.section-label {
    font-size: 0.67rem;
    font-weight: 700;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border-lt);
    display: flex;
    align-items: center;
    gap: 7px;
}

/* ── Page Header ── */
.page-header {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 1.8rem;
    padding-bottom: 1.2rem;
    border-bottom: 1px solid rgba(203,213,225,0.5);
}
.ph-icon {
    width: 46px; height: 46px;
    background: linear-gradient(135deg, #1E40AF 0%, #0EA5E9 100%);
    border-radius: 13px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem;
    box-shadow: 0 4px 16px rgba(30,64,175,0.28);
    flex-shrink: 0;
}
.ph-title { font-size: 1.5rem !important; margin: 0 !important; line-height: 1.2; font-family: 'Sora', sans-serif !important; }
.ph-sub   { margin: 0; color: var(--muted); font-size: 0.79rem; margin-top: 3px; }

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #1E40AF 0%, #0EA5E9 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 0.5rem 1.4rem !important;
    box-shadow: 0 3px 12px rgba(30,64,175,0.25) !important;
    transition: all .2s !important;
    letter-spacing: .01em !important;
}
.stButton > button:hover {
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(30,64,175,0.32) !important;
}
.stDownloadButton > button {
    background: linear-gradient(135deg, #059669 0%, #0EA5E9 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    box-shadow: 0 3px 12px rgba(5,150,105,0.22) !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div {
    border-radius: 10px !important;
    border: 1.5px solid var(--border) !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.88rem !important;
    background: rgba(255,255,255,0.85) !important;
    transition: border-color .18s, box-shadow .18s !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(30,64,175,0.12) !important;
    background: #fff !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    background: rgba(255,255,255,0.85) !important;
    border-radius: 10px !important;
}

/* ── File Uploader ── */
[data-testid="stFileUploader"] {
    border: 2px dashed var(--primary-mid) !important;
    border-radius: 14px !important;
    background: rgba(239,246,255,0.7) !important;
    padding: 0.6rem !important;
}

/* ── Alerts ── */
.stSuccess, .stError, .stWarning, .stInfo {
    border-radius: 12px !important;
    font-size: 0.86rem !important;
    backdrop-filter: blur(8px);
}

/* ── Dataframe ── */
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid var(--border-lt) !important;
}

/* ── Badge ── */
.badge {
    display: inline-block;
    padding: 3px 11px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: .05em;
    margin: 2px 3px 2px 0;
}
.badge-blue  { background: var(--primary-lt); color: var(--primary); border: 1px solid var(--primary-mid); }
.badge-green { background: var(--success-lt); color: var(--success); border: 1px solid var(--success-mid); }
.badge-red   { background: var(--danger-lt);  color: var(--danger);  border: 1px solid var(--danger-mid);  }

/* ── Sidebar Logo & Nav ── */
.sidebar-logo-wrap {
    padding: 24px 18px 16px;
    border-bottom: 1px solid var(--border-lt);
    margin-bottom: 10px;
}
.sidebar-brand {
    font-family: 'Sora', sans-serif;
    font-size: 1.4rem;
    font-weight: 800;
    background: linear-gradient(135deg, #1E40AF, #0EA5E9);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -.02em;
}
.sidebar-tagline {
    font-size: 0.68rem;
    color: var(--muted-lt);
    letter-spacing: .04em;
    margin-top: 1px;
}
.sidebar-user-chip {
    background: linear-gradient(135deg, rgba(239,246,255,0.9), rgba(224,242,254,0.9));
    border-radius: 10px;
    padding: 10px 14px;
    margin: 0 10px 16px;
    border: 1px solid var(--primary-mid);
}
.sidebar-user-chip .sup-label {
    font-size: 0.62rem;
    color: var(--muted);
    font-weight: 700;
    letter-spacing: .09em;
    text-transform: uppercase;
    margin-bottom: 2px;
}
.sidebar-user-chip .sup-name {
    font-size: 0.9rem;
    font-weight: 700;
    color: var(--primary);
    font-family: 'Sora', sans-serif;
}

/* ── LOGIN PAGE ── */
.login-outer {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
}
.login-card {
    background: rgba(255,255,255,0.88);
    backdrop-filter: blur(24px);
    border: 1px solid rgba(255,255,255,0.95);
    border-radius: 22px;
    padding: 0 0 36px 0;
    box-shadow:
        0 24px 64px rgba(30,64,175,0.14),
        0 2px 8px rgba(0,0,0,0.04),
        inset 0 1px 0 rgba(255,255,255,0.8);
    max-width: 420px;
    width: 100%;
    overflow: hidden;
}
.login-header-band {
    background: linear-gradient(135deg, #1E40AF 0%, #0EA5E9 60%, #6366F1 100%);
    padding: 36px 40px 32px;
    text-align: center;
    position: relative;
}
.login-header-band::after {
    content: '';
    position: absolute;
    bottom: -1px; left: 0; right: 0;
    height: 20px;
    background: rgba(255,255,255,0.88);
    border-radius: 20px 20px 0 0;
}
.login-logo-circle {
    width: 64px; height: 64px;
    background: rgba(255,255,255,0.22);
    border-radius: 18px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.8rem;
    margin: 0 auto 14px;
    border: 2px solid rgba(255,255,255,0.4);
    box-shadow: 0 4px 20px rgba(0,0,0,0.12);
    backdrop-filter: blur(8px);
}
.login-app-name {
    font-family: 'Sora', sans-serif;
    font-size: 1.8rem;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 4px;
    letter-spacing: -.03em;
}
.login-tagline {
    color: rgba(255,255,255,0.78);
    font-size: 0.78rem;
    font-weight: 500;
    letter-spacing: .03em;
}
.login-body {
    padding: 28px 36px 0;
}
.login-welcome {
    font-family: 'Sora', sans-serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 4px;
}
.login-sub {
    color: var(--muted);
    font-size: 0.78rem;
    margin-bottom: 22px;
}

/* ── Part Input Form Rows ── */
.part-row-grid {
    display: grid;
    grid-template-columns: 1fr 1.6fr 0.5fr auto;
    gap: 8px;
    align-items: end;
    margin-bottom: 8px;
}
.part-row-header {
    display: grid;
    grid-template-columns: 1fr 1.6fr 0.5fr auto;
    gap: 8px;
    margin-bottom: 4px;
}
.part-col-label {
    font-size: 0.67rem;
    font-weight: 700;
    letter-spacing: .08em;
    text-transform: uppercase;
    color: var(--muted);
    padding-left: 2px;
}
.part-row-divider {
    height: 1px;
    background: var(--border-lt);
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  DB POOL
# ─────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    st.error("DATABASE_URL environment variable is not set.")
    st.stop()


@st.cache_resource
def get_pool():
    return SimpleConnectionPool(1, 5, DATABASE_URL)


pool = get_pool()

def get_conn():  return pool.getconn()
def release(c):  pool.putconn(c)


# ─────────────────────────────────────────────
#  SCHEMA INIT
# ─────────────────────────────────────────────
@st.cache_resource
def init_schema():
    c = get_conn()
    cur = c.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS parts_table (
                id SERIAL PRIMARY KEY, part_no TEXT, brand TEXT,
                price NUMERIC, supplier TEXT
            );
            ALTER TABLE parts_table ADD COLUMN IF NOT EXISTS supplier TEXT;
            DO $$
            BEGIN
              IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname='unique_part_supplier'
              ) THEN
                ALTER TABLE parts_table
                  ADD CONSTRAINT unique_part_supplier UNIQUE(part_no, brand, supplier);
              END IF;
            END$$;
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY, username TEXT UNIQUE, password TEXT
            );
            CREATE TABLE IF NOT EXISTS saved_offers (
                id SERIAL PRIMARY KEY, username TEXT,
                data JSONB, created_at TIMESTAMP DEFAULT NOW()
            );
            INSERT INTO users(username, password)
            SELECT 'admin','admin'
            WHERE NOT EXISTS (SELECT 1 FROM users WHERE username='admin');
        """)
        c.commit()
    except Exception as e:
        c.rollback()
        raise e
    finally:
        release(c)

init_schema()


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def clean_col(name):
    return re.sub(r'[^a-z0-9]', '', name.strip().lower())


@st.cache_data(ttl=120, show_spinner=False)
def fetch_brands():
    c = get_conn()
    cur = c.cursor()
    try:
        cur.execute("SELECT DISTINCT brand FROM parts_table ORDER BY brand")
        rows = [x[0] for x in cur.fetchall()]
    finally:
        release(c)
    return rows


def lookup_prices(items):
    c = get_conn()
    cur = c.cursor()
    results = []
    try:
        for r in items:
            part  = r["part_no"].strip()
            brand = r["brand"].strip()
            qty   = max(int(r.get("qty") or 1), 1)
            if not part or not brand:
                continue
            cur.execute("""
                SELECT supplier, price FROM parts_table
                WHERE TRIM(LOWER(part_no)) = TRIM(LOWER(%s))
                  AND TRIM(LOWER(brand))   = TRIM(LOWER(%s))
                ORDER BY price ASC
            """, (part, brand))
            rows = cur.fetchall()
            if rows:
                for supplier, price in rows:
                    results.append({
                        "Brand": brand, "Part No": part, "Supplier": supplier,
                        "Qty": qty, "Unit Price (JPY)": float(price),
                        "Amount (JPY)": qty * float(price),
                    })
            else:
                results.append({
                    "Brand": brand, "Part No": part, "Supplier": "Not Found",
                    "Qty": qty, "Unit Price (JPY)": 0.0, "Amount (JPY)": 0.0,
                })
    finally:
        release(c)
    return results


def logo_sidebar():
    st.markdown("""
    <div class="sidebar-logo-wrap">
        <div class="sidebar-brand">📋 PriceDesk</div>
        <div class="sidebar-tagline">PARTS PRICING PLATFORM</div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  SESSION
# ─────────────────────────────────────────────
for k, v in {
    "user": None,
    "table_data": pd.DataFrame(),
    "num_rows": 3,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────
#  LOGIN
# ─────────────────────────────────────────────
def check_login(u, p):
    c = get_conn()
    cur = c.cursor()
    try:
        cur.execute("SELECT id FROM users WHERE username=%s AND password=%s", (u, p))
        row = cur.fetchone()
    finally:
        release(c)
    return row

if st.session_state.user is None:
    st.markdown(
        "<style>section[data-testid='stSidebar']{display:none!important;}"
        ".block-container{padding:3rem 1rem!important;}</style>",
        unsafe_allow_html=True
    )
    _, mid, _ = st.columns([1, 1.1, 1])
    with mid:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)

        # Header band with logo
        st.markdown("""
        <div class="login-header-band">
            <div class="login-logo-circle">📋</div>
            <div class="login-app-name">PriceDesk</div>
            <div class="login-tagline">PARTS PRICING PLATFORM</div>
        </div>
        <div style="height:18px;"></div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="login-body">', unsafe_allow_html=True)
        st.markdown("""
            <div class="login-welcome">Welcome back</div>
            <div class="login-sub">Sign in to continue to your workspace</div>
        """, unsafe_allow_html=True)

        u_in = st.text_input("Username", placeholder="Enter your username")
        p_in = st.text_input("Password", type="password", placeholder="Enter your password")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("Sign In →", use_container_width=True):
            if check_login(u_in, p_in):
                st.session_state.user = {"username": u_in}
                st.rerun()
            else:
                st.error("Invalid username or password.")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

username = st.session_state.user["username"]


# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    logo_sidebar()

    st.markdown(f"""
    <div class="sidebar-user-chip">
        <div class="sup-label">Logged in as</div>
        <div class="sup-name">{username}</div>
    </div>
    """, unsafe_allow_html=True)

    pages = (
        ["Price Lookup", "Saved Quotations", "Data Upload", "Access Control"]
        if username == "admin" else
        ["Price Lookup", "Saved Quotations"]
    )
    page = st.radio("", pages, label_visibility="collapsed")
    st.markdown("<hr style='border-color:#E2E8F0;margin:14px 0;'>", unsafe_allow_html=True)
    if st.button("Sign Out", use_container_width=True):
        st.session_state.clear()
        st.rerun()


# ═══════════════════════════════════════════
#  PRICE LOOKUP  — form-based, no lag
# ═══════════════════════════════════════════
if page == "Price Lookup":

    st.markdown("""
    <div class="page-header">
        <div class="ph-icon">📊</div>
        <div>
            <div class="ph-title">Price Lookup</div>
            <div class="ph-sub">Search parts across all suppliers instantly</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    brand_list = fetch_brands()

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Enter Parts to Search</div>', unsafe_allow_html=True)

    # Controls for number of rows — outside form so it's instant
    col_plus, col_minus, col_clear, col_spacer = st.columns([0.8, 0.8, 0.9, 5])
    with col_plus:
        if st.button("＋ Add Row"):
            st.session_state.num_rows = min(st.session_state.num_rows + 1, 20)
            st.rerun()
    with col_minus:
        if st.button("－ Remove"):
            st.session_state.num_rows = max(st.session_state.num_rows - 1, 1)
            st.rerun()
    with col_clear:
        if st.button("✕ Clear All"):
            st.session_state.num_rows = 3
            st.session_state.table_data = pd.DataFrame()
            for i in range(25):
                for k in [f"brand_{i}", f"part_{i}", f"qty_{i}"]:
                    if k in st.session_state:
                        del st.session_state[k]
            st.rerun()

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Column headers
    h1, h2, h3, h4 = st.columns([1.6, 2.2, 0.8, 0.6])
    with h1: st.markdown('<div class="part-col-label">Brand</div>', unsafe_allow_html=True)
    with h2: st.markdown('<div class="part-col-label">Part Number</div>', unsafe_allow_html=True)
    with h3: st.markdown('<div class="part-col-label">Qty</div>', unsafe_allow_html=True)
    with h4: st.markdown('<div class="part-col-label">&nbsp;</div>', unsafe_allow_html=True)

    n = st.session_state.num_rows
    for i in range(n):
        c1, c2, c3, c4 = st.columns([1.6, 2.2, 0.8, 0.6])
        with c1:
            st.selectbox("", [""] + brand_list, key=f"brand_{i}", label_visibility="collapsed")
        with c2:
            st.text_input("", placeholder="e.g. 04152-YZZA6", key=f"part_{i}", label_visibility="collapsed")
        with c3:
            st.number_input("", min_value=1, value=1, step=1, key=f"qty_{i}", label_visibility="collapsed")
        with c4:
            st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    b1, b2, _ = st.columns([1.2, 1, 6])
    with b1:
        go = st.button("🔍 Get Pricing", use_container_width=True)

    if go:
        items = []
        for i in range(n):
            b = st.session_state.get(f"brand_{i}", "")
            p = st.session_state.get(f"part_{i}", "").strip()
            q = st.session_state.get(f"qty_{i}", 1)
            if b and b != "" and p:
                items.append({"brand": b, "part_no": p, "qty": q})
        if items:
            with st.spinner("Fetching prices…"):
                results = lookup_prices(items)
            st.session_state.table_data = pd.DataFrame(results)
        else:
            st.warning("Please enter at least one Brand and Part No.")

    df = st.session_state.table_data

    if not df.empty:
        found       = df[df["Supplier"] != "Not Found"]
        n_parts     = int(df["Part No"].nunique())
        n_suppliers = int(found["Supplier"].nunique()) if not found.empty else 0
        best_price  = float(found["Unit Price (JPY)"].min()) if not found.empty else 0.0
        n_records   = int(len(found))

        st.markdown(f"""
        <div class="metric-row">
            <div class="metric-card">
                <div class="mc-label">Parts Searched</div>
                <div class="mc-value">{n_parts}</div>
                <div class="mc-sub">unique part numbers</div>
            </div>
            <div class="metric-card">
                <div class="mc-label">Suppliers Found</div>
                <div class="mc-value">{n_suppliers}</div>
                <div class="mc-sub">across all parts</div>
            </div>
            <div class="metric-card">
                <div class="mc-label">Best Unit Price</div>
                <div class="mc-value">¥{best_price:,.0f}</div>
                <div class="mc-sub">lowest unit price</div>
            </div>
            <div class="metric-card">
                <div class="mc-label">Price Records</div>
                <div class="mc-value">{n_records}</div>
                <div class="mc-sub">supplier rows returned</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">All Supplier Prices</div>', unsafe_allow_html=True)

        def highlight_rows(row):
            if row["Supplier"] == "Not Found":
                return ["background-color:#FEF2F2; color:#991B1B"] * len(row)
            mask  = (df["Part No"] == row["Part No"]) & (df["Brand"] == row["Brand"])
            valid = df.loc[mask & (df["Supplier"] != "Not Found"), "Unit Price (JPY)"]
            if not valid.empty and row["Unit Price (JPY)"] == valid.min():
                return ["background-color:#F0FDF4; color:#065F46; font-weight:600"] * len(row)
            return [""] * len(row)

        styled = (
            df.style
            .apply(highlight_rows, axis=1)
            .format({"Unit Price (JPY)": "¥{:,.0f}", "Amount (JPY)": "¥{:,.0f}"})
        )
        st.dataframe(styled, use_container_width=True, hide_index=True, height=360)

        st.markdown("""
        <div style="display:flex;gap:16px;margin-top:10px;font-size:0.74rem;color:#64748B;">
            <span><span class="badge badge-green">Green</span> Cheapest supplier for that part</span>
            <span><span class="badge badge-red">Red</span> Part not found in database</span>
        </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        a1, a2, _ = st.columns([1.3, 1.3, 5])
        with a1:
            if st.button("💾 Save Quotation", use_container_width=True):
                c = get_conn()
                cur = c.cursor()
                try:
                    cur.execute(
                        "INSERT INTO saved_offers(username, data) VALUES(%s, %s)",
                        (username, json.dumps(df.to_dict(orient="records")))
                    )
                    c.commit()
                    st.success("Quotation saved successfully.")
                except Exception as e:
                    c.rollback()
                    st.error(f"Could not save quotation: {e}")
                finally:
                    release(c)
        with a2:
            buf = BytesIO()
            df.to_excel(buf, index=False)
            buf.seek(0)
            st.download_button(
                "📥 Export Excel", buf, file_name="price_lookup.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )


# ═══════════════════════════════════════════
#  SAVED QUOTATIONS
# ═══════════════════════════════════════════
elif page == "Saved Quotations":

    st.markdown("""
    <div class="page-header">
        <div class="ph-icon">📁</div>
        <div>
            <div class="ph-title">Saved Quotations</div>
            <div class="ph-sub">View, download and manage past quotations</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c = get_conn()
    cur = c.cursor()
    try:
        cur.execute("""
            SELECT id, username, data, created_at::date
            FROM saved_offers ORDER BY created_at DESC
        """)
        rows = cur.fetchall()
    finally:
        release(c)

    if not rows:
        st.markdown("""
        <div class="section-card" style="text-align:center;padding:60px 24px;">
            <div style="font-size:2.8rem;margin-bottom:12px;">📭</div>
            <div style="font-size:1rem;font-weight:700;color:#0F172A;font-family:'Sora',sans-serif;">No saved quotations yet</div>
            <div style="color:#64748B;font-size:0.82rem;margin-top:8px;">
                Go to Price Lookup and save your first quotation.
            </div>
        </div>""", unsafe_allow_html=True)
        st.stop()

    # Build display dataframe — carry offer id as a column for reliable deletion
    all_data = []
    for oid, user, data, date_only in rows:
        df_o = pd.DataFrame(json.loads(data) if isinstance(data, str) else data)
        df_o["Employee"] = user
        df_o["Saved On"] = str(date_only)
        df_o["_offer_id"] = oid
        all_data.append(df_o)

    final_df = pd.concat(all_data, ignore_index=True)

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card">
            <div class="mc-label">Total Quotations</div>
            <div class="mc-value">{len(rows)}</div>
            <div class="mc-sub">saved records</div>
        </div>
        <div class="metric-card">
            <div class="mc-label">Employees</div>
            <div class="mc-value">{final_df["Employee"].nunique()}</div>
            <div class="mc-sub">contributors</div>
        </div>
        <div class="metric-card">
            <div class="mc-label">Latest Save</div>
            <div class="mc-value" style="font-size:1.05rem;">{str(rows[0][3])}</div>
            <div class="mc-sub">most recent date</div>
        </div>
    </div>""", unsafe_allow_html=True)

    # Build the display copy — keep _offer_id hidden but include Select checkbox
    display_df = final_df.drop(columns=["_offer_id"], errors="ignore").copy()
    display_df.insert(0, "Select", False)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">All Records</div>', unsafe_allow_html=True)
    edited_df = st.data_editor(
        display_df, use_container_width=True,
        hide_index=True, height=400, key="saved_editor"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    b1, b2, _ = st.columns([1.3, 1.3, 5])
    with b1:
        buf = BytesIO()
        final_df.drop(columns=["_offer_id"], errors="ignore").to_excel(buf, index=False)
        buf.seek(0)
        st.download_button(
            "📥 Download All", buf, file_name="all_quotations.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with b2:
        if st.button("🗑 Delete Selected", use_container_width=True):
            selected_mask = edited_df["Select"] == True
            if selected_mask.any():
                # Determine which offer IDs correspond to selected rows by position
                selected_indices = edited_df[selected_mask].index.tolist()
                ids_to_delete = list(final_df.loc[selected_indices, "_offer_id"].unique())
                if ids_to_delete:
                    conn = get_conn()
                    cur2 = conn.cursor()
                    try:
                        cur2.execute(
                            "DELETE FROM saved_offers WHERE id = ANY(%s)",
                            (ids_to_delete,)
                        )
                        conn.commit()
                        st.success(f"Deleted {len(ids_to_delete)} quotation(s).")
                    except Exception as e:
                        conn.rollback()
                        st.error(f"Delete failed: {e}")
                    finally:
                        release(conn)
                    st.rerun()
            else:
                st.warning("Select at least one row to delete.")


# ═══════════════════════════════════════════
#  DATA UPLOAD
# ═══════════════════════════════════════════
elif page == "Data Upload":

    st.markdown("""
    <div class="page-header">
        <div class="ph-icon">📤</div>
        <div>
            <div class="ph-title">Master Data Upload</div>
            <div class="ph-sub">Upload Excel price sheets to update the parts database</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="section-card">
        <div class="section-label">Required Column Names</div>
        <div>
            <span class="badge badge-blue">Make / Brand</span>
            <span class="badge badge-blue">Part Number</span>
            <span class="badge badge-blue">JPY Price</span>
            <span class="badge badge-blue">Supplier</span>
        </div>
        <div style="font-size:0.79rem;color:#64748B;margin-top:12px;line-height:1.7;">
            Column names are <strong>case-insensitive</strong> and extra spaces are handled automatically.
            Uploading the same part again will <strong>update</strong> the price — no duplicates.
        </div>
    </div>""", unsafe_allow_html=True)

    file = st.file_uploader("Upload Excel file (.xlsx)", type=["xlsx"])

    if file:
        df_raw = pd.read_excel(file, dtype=str)
        col_map = {clean_col(c): c for c in df_raw.columns}

        ALIASES = {
            "brand":    ["make", "brand", "manufacturer"],
            "part_no":  ["partnumber", "partno", "part", "partnum", "partnumbers"],
            "price":    ["jpyprice", "price", "unitprice", "jpy", "jprice"],
            "supplier": ["supplier", "vendor", "source"],
        }
        rename = {}
        for target, aliases in ALIASES.items():
            for alias in aliases:
                if alias in col_map:
                    rename[col_map[alias]] = target
                    break

        df_raw.rename(columns=rename, inplace=True)
        missing = [c for c in ["brand","part_no","price","supplier"] if c not in df_raw.columns]
        if missing:
            st.error(f"Could not map columns: **{missing}**\n\nDetected headers: `{list(df_raw.columns)}`")
            st.stop()

        df_raw["brand"]    = df_raw["brand"].astype(str).str.replace(r'[\n"\r]', '', regex=True).str.strip()
        df_raw["part_no"]  = df_raw["part_no"].astype(str).str.replace(r'[\n"\r]', '', regex=True).str.strip()
        df_raw["supplier"] = df_raw["supplier"].astype(str).str.strip()
        df_raw["price"]    = pd.to_numeric(df_raw["price"], errors="coerce").fillna(0)
        df_raw = df_raw[
            (df_raw["part_no"] != "") & (df_raw["brand"] != "") &
            (df_raw["supplier"] != "") &
            (df_raw["part_no"] != "nan") & (df_raw["brand"] != "nan")
        ]

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown(
            f'<div class="section-label">Preview — {len(df_raw):,} valid rows detected</div>',
            unsafe_allow_html=True
        )
        st.dataframe(
            df_raw[["brand","part_no","price","supplier"]].head(30),
            use_container_width=True, hide_index=True, height=280,
        )
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button(f"⬆ Upload {len(df_raw):,} Rows to Database"):
            values = list(
                df_raw[["part_no","brand","price","supplier"]].itertuples(index=False, name=None)
            )
            c = get_conn()
            cur = c.cursor()
            try:
                execute_values(cur, """
                    INSERT INTO parts_table(part_no, brand, price, supplier) VALUES %s
                    ON CONFLICT(part_no, brand, supplier)
                    DO UPDATE SET price = EXCLUDED.price
                """, values, page_size=500)
                c.commit()
                fetch_brands.clear()
                st.success(f"Successfully uploaded {len(values):,} rows.")
            except Exception as e:
                c.rollback()
                st.error(f"Upload failed: {e}")
            finally:
                release(c)
            st.rerun()


# ═══════════════════════════════════════════
#  ACCESS CONTROL
# ═══════════════════════════════════════════
elif page == "Access Control":

    st.markdown("""
    <div class="page-header">
        <div class="ph-icon">🔐</div>
        <div>
            <div class="ph-title">Access Control</div>
            <div class="ph-sub">Manage user accounts and permissions</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns(2, gap="large")

    with col_a:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Create New User</div>', unsafe_allow_html=True)
        nu  = st.text_input("Username", placeholder="e.g. john.doe", key="nu")
        np_ = st.text_input("Password", type="password", placeholder="Secure password", key="np")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("✚ Create User", use_container_width=True):
            if nu and np_:
                c = get_conn()
                cur = c.cursor()
                try:
                    cur.execute("INSERT INTO users(username, password) VALUES(%s,%s)", (nu, np_))
                    c.commit()
                    st.success(f"User '{nu}' created.")
                except Exception as e:
                    c.rollback()
                    st.error(f"Could not create user: {e}")
                finally:
                    release(c)
            else:
                st.warning("Please fill in both fields.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Remove Employee</div>', unsafe_allow_html=True)

        # BUG FIX: fetch users and release connection BEFORE rendering delete button
        c = get_conn()
        cur = c.cursor()
        try:
            cur.execute("SELECT username FROM users WHERE username != 'admin' ORDER BY username")
            users = [x[0] for x in cur.fetchall()]
        finally:
            release(c)

        if users:
            del_u = st.selectbox("Select employee to remove", users)
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            if st.button("🗑 Delete Employee", use_container_width=True):
                c = get_conn()
                cur = c.cursor()
                try:
                    cur.execute("DELETE FROM users WHERE username=%s", (del_u,))
                    c.commit()
                    st.success(f"User '{del_u}' removed.")
                except Exception as e:
                    c.rollback()
                    st.error(f"Could not delete user: {e}")
                finally:
                    release(c)
                st.rerun()
        else:
            st.info("No other users found.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">All Users</div>', unsafe_allow_html=True)
    c = get_conn()
    cur = c.cursor()
    try:
        cur.execute("SELECT username FROM users ORDER BY username")
        all_u = pd.DataFrame(cur.fetchall(), columns=["Username"])
    finally:
        release(c)
    all_u["Role"] = all_u["Username"].apply(lambda x: "🔑 Admin" if x == "admin" else "👤 Employee")
    st.dataframe(all_u, use_container_width=True, hide_index=True, height=220)
    st.markdown('</div>', unsafe_allow_html=True)

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
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
#  GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
    --nav-w:      240px;
    --primary:    #2563EB;
    --primary-d:  #1D4ED8;
    --primary-lt: #EFF6FF;
    --primary-md: #BFDBFE;
    --sky:        #0EA5E9;
    --indigo:     #6366F1;
    --success:    #10B981;
    --success-lt: #ECFDF5;
    --success-md: #6EE7B7;
    --danger:     #EF4444;
    --danger-lt:  #FEF2F2;
    --danger-md:  #FECACA;
    --text:       #0F172A;
    --text2:      #334155;
    --muted:      #64748B;
    --muted-lt:   #94A3B8;
    --border:     #E2E8F0;
    --border-md:  #CBD5E1;
    --card:       rgba(255,255,255,0.88);
    --font:       'Plus Jakarta Sans', sans-serif;
    --r:          14px;
    --r-sm:       9px;
    --sh:         0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(37,99,235,0.07);
    --sh-md:      0 4px 24px rgba(37,99,235,0.13), 0 1px 4px rgba(0,0,0,0.05);
    --sh-lg:      0 12px 48px rgba(37,99,235,0.18), 0 2px 8px rgba(0,0,0,0.06);
}

/* ── Hide Streamlit native chrome completely ── */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"],
section[data-testid="stSidebar"],
button[kind="header"],
[data-testid="stHeader"] {
    display: none !important;
    visibility: hidden !important;
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
}

/* ── Background ── */
.stApp {
    font-family: var(--font) !important;
    background: #e8effe !important;
    background-image:
        radial-gradient(ellipse 80vw 55vh at 12% 8%,  rgba(99,102,241,0.14) 0%, transparent 65%),
        radial-gradient(ellipse 65vw 50vh at 88% 88%,  rgba(14,165,233,0.13) 0%, transparent 65%),
        radial-gradient(ellipse 55vw 40vh at 55% 48%,  rgba(37,99,235,0.07) 0%, transparent 60%),
        linear-gradient(158deg, #e5edff 0%, #edf5ff 48%, #e2f4ff 100%) !important;
    background-attachment: fixed !important;
    min-height: 100vh;
}
.stApp::before {
    content: '';
    position: fixed; inset: 0;
    background-image: radial-gradient(rgba(37,99,235,0.055) 1.2px, transparent 1.2px);
    background-size: 26px 26px;
    pointer-events: none; z-index: 0;
}

.block-container {
    max-width: 100% !important;
    padding: 0 0 0 var(--nav-w) !important;
    position: relative; z-index: 1;
}

/* ── Custom sidebar ── */
.pd-sidebar {
    position: fixed;
    top: 0; left: 0; bottom: 0;
    width: var(--nav-w);
    background: rgba(255,255,255,0.97);
    backdrop-filter: blur(28px);
    border-right: 1px solid rgba(226,232,240,0.85);
    box-shadow: 4px 0 36px rgba(37,99,235,0.07);
    display: flex; flex-direction: column;
    z-index: 1000;
    overflow: hidden;
}

.sb-brand {
    padding: 24px 18px 18px;
    border-bottom: 1px solid var(--border);
    flex-shrink: 0;
}
.sb-logo-row {
    display: flex; align-items: center; gap: 10px; margin-bottom: 3px;
}
.sb-icon {
    width: 38px; height: 38px;
    background: linear-gradient(135deg, #2563EB, #0EA5E9);
    border-radius: 11px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.05rem;
    box-shadow: 0 3px 14px rgba(37,99,235,0.30);
    flex-shrink: 0;
}
.sb-name {
    font-size: 1.22rem; font-weight: 800;
    color: var(--text); letter-spacing: -.03em; line-height: 1;
}
.sb-tag {
    font-size: 0.58rem; color: var(--muted-lt);
    font-weight: 700; letter-spacing: .12em;
    text-transform: uppercase; margin-left: 48px;
}

.sb-user {
    margin: 14px 12px 2px;
    background: linear-gradient(135deg, #EFF6FF, #E0F2FE);
    border: 1px solid var(--primary-md);
    border-radius: 10px; padding: 10px 13px;
    flex-shrink: 0;
}
.sb-user-lbl {
    font-size: 0.57rem; font-weight: 800;
    letter-spacing: .11em; text-transform: uppercase;
    color: var(--muted); margin-bottom: 3px;
}
.sb-user-name {
    font-size: 0.9rem; font-weight: 800; color: var(--primary);
}

.sb-nav { padding: 12px 10px 10px; flex: 1; overflow-y: auto; }
.sb-nav-lbl {
    font-size: 0.57rem; font-weight: 800;
    letter-spacing: .13em; text-transform: uppercase;
    color: var(--muted-lt); padding: 0 8px; margin-bottom: 8px;
    display: block;
}

.sb-btn {
    display: flex; align-items: center; gap: 10px;
    width: 100%; padding: 10px 12px;
    border-radius: 9px; border: none; background: transparent;
    font-family: var(--font); font-size: 0.85rem; font-weight: 600;
    color: var(--muted); cursor: pointer; text-align: left;
    margin-bottom: 3px; transition: all .15s;
    line-height: 1.2;
}
.sb-btn:hover { background: var(--primary-lt); color: var(--primary); }
.sb-btn.active {
    background: linear-gradient(135deg, rgba(37,99,235,0.10), rgba(14,165,233,0.07));
    color: var(--primary);
    box-shadow: inset 3px 0 0 var(--primary);
    font-weight: 700;
}
.sb-btn .ic { font-size: 1rem; width: 22px; text-align: center; flex-shrink: 0; }

.sb-footer {
    padding: 12px;
    border-top: 1px solid var(--border);
    flex-shrink: 0;
}
.sb-signout {
    display: flex; align-items: center; gap: 9px;
    width: 100%; padding: 10px 14px;
    border-radius: 9px; border: 1px solid #FECACA;
    background: #FEF2F2; color: #DC2626;
    font-family: var(--font); font-size: 0.84rem; font-weight: 700;
    cursor: pointer; transition: all .15s; text-align: left;
}
.sb-signout:hover { background: #DC2626; color: #fff; border-color: #DC2626; }

/* ── Main content ── */
.pd-main {
    padding: 34px 38px 52px;
    min-height: 100vh;
}

/* Page header */
.page-header {
    display: flex; align-items: flex-start; gap: 16px;
    margin-bottom: 28px; padding-bottom: 20px;
    border-bottom: 1px solid rgba(226,232,240,0.75);
}
.ph-icon {
    width: 52px; height: 52px;
    background: linear-gradient(135deg, #2563EB, #0EA5E9);
    border-radius: 14px; display: flex; align-items: center;
    justify-content: center; font-size: 1.35rem;
    box-shadow: 0 4px 20px rgba(37,99,235,0.27); flex-shrink: 0;
}
.ph-title {
    font-size: 1.6rem; font-weight: 800;
    color: var(--text); letter-spacing: -.035em; line-height: 1.2;
    margin-bottom: 5px;
}
.ph-sub { font-size: 0.78rem; color: var(--muted); font-weight: 500; }

/* Metric cards */
.metric-row { display: flex; gap: 14px; margin-bottom: 24px; flex-wrap: wrap; }
.metric-card {
    background: var(--card); backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.92);
    border-radius: var(--r); padding: 20px 22px 18px;
    min-width: 150px; flex: 1;
    box-shadow: var(--sh); position: relative; overflow: hidden;
    transition: transform .2s, box-shadow .2s;
}
.metric-card:hover { transform: translateY(-2px); box-shadow: var(--sh-md); }
.metric-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #2563EB, #0EA5E9, #6366F1);
}
.mc-label {
    font-size: 0.62rem; font-weight: 800; letter-spacing: .11em;
    text-transform: uppercase; color: var(--muted); margin-bottom: 9px;
}
.mc-value {
    font-size: 1.75rem; font-weight: 800; letter-spacing: -.04em; line-height: 1;
    background: linear-gradient(135deg, #1D4ED8, #0EA5E9);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.mc-sub { font-size: 0.67rem; color: var(--muted-lt); margin-top: 6px; font-weight: 500; }

/* Section card */
.sc {
    background: var(--card); backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.92);
    border-radius: var(--r); padding: 22px 24px 24px;
    margin-bottom: 18px; box-shadow: var(--sh);
}
.sc-lbl {
    font-size: 0.62rem; font-weight: 800; letter-spacing: .13em;
    text-transform: uppercase; color: var(--muted);
    margin-bottom: 16px; padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
}

/* Column header labels */
.col-hdr {
    font-size: 0.61rem; font-weight: 800; letter-spacing: .11em;
    text-transform: uppercase; color: var(--muted); padding-left: 2px;
}

/* Badges */
.badge {
    display: inline-flex; align-items: center;
    padding: 3px 10px; border-radius: 20px;
    font-size: 0.67rem; font-weight: 700;
    letter-spacing: .04em; margin: 2px 3px 2px 0;
}
.b-blue  { background: var(--primary-lt); color: var(--primary); border: 1px solid var(--primary-md); }
.b-green { background: var(--success-lt); color: #065F46; border: 1px solid var(--success-md); }
.b-red   { background: var(--danger-lt);  color: #991B1B; border: 1px solid var(--danger-md); }

/* ── Streamlit widget overrides ── */
.stButton > button {
    background: linear-gradient(135deg, #2563EB, #0EA5E9) !important;
    color: #fff !important; border: none !important;
    border-radius: var(--r-sm) !important;
    font-family: var(--font) !important; font-weight: 700 !important;
    font-size: 0.84rem !important; letter-spacing: .01em !important;
    padding: 0.52rem 1.3rem !important;
    box-shadow: 0 3px 12px rgba(37,99,235,0.28) !important;
    transition: all .18s !important;
}
.stButton > button:hover {
    opacity: 0.86 !important; transform: translateY(-1px) !important;
    box-shadow: 0 6px 22px rgba(37,99,235,0.34) !important;
}
.stDownloadButton > button {
    background: linear-gradient(135deg, #10B981, #0EA5E9) !important;
    color: #fff !important; border: none !important;
    border-radius: var(--r-sm) !important;
    font-family: var(--font) !important; font-weight: 700 !important;
    font-size: 0.84rem !important;
    box-shadow: 0 3px 12px rgba(16,185,129,0.25) !important;
}
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    border-radius: var(--r-sm) !important;
    border: 1.5px solid var(--border-md) !important;
    font-family: var(--font) !important; font-size: 0.87rem !important;
    background: rgba(255,255,255,0.85) !important; color: var(--text) !important;
    transition: border-color .18s, box-shadow .18s !important;
    padding: 0.46rem 0.78rem !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.12) !important;
    background: #fff !important; outline: none !important;
}
.stSelectbox > div > div {
    border-radius: var(--r-sm) !important;
    border: 1.5px solid var(--border-md) !important;
    font-family: var(--font) !important; font-size: 0.87rem !important;
    background: rgba(255,255,255,0.85) !important;
}
[data-testid="stFileUploader"] {
    border: 2px dashed var(--primary-md) !important;
    border-radius: var(--r) !important;
    background: rgba(239,246,255,0.55) !important;
    padding: 0.6rem !important;
}
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {
    border-radius: 10px !important; overflow: hidden !important;
    border: 1px solid var(--border) !important;
}
.stSuccess > div, .stError > div, .stWarning > div, .stInfo > div {
    border-radius: 10px !important; font-size: 0.84rem !important;
    font-family: var(--font) !important;
}
label[data-testid="stWidgetLabel"] p {
    font-family: var(--font) !important;
    font-size: 0.77rem !important; font-weight: 700 !important;
    color: var(--text2) !important;
}

/* Login */
.login-wrap {
    min-height: 100vh; display: flex;
    align-items: center; justify-content: center; padding: 24px;
}
.login-card {
    background: rgba(255,255,255,0.92); backdrop-filter: blur(28px);
    border: 1px solid rgba(255,255,255,0.97);
    border-radius: 22px; max-width: 420px; width: 100%;
    box-shadow: var(--sh-lg); overflow: hidden;
}
.login-top {
    background: linear-gradient(135deg, #1D4ED8 0%, #2563EB 35%, #0EA5E9 75%, #6366F1 100%);
    padding: 38px 36px 30px; text-align: center; position: relative;
}
.login-top::after {
    content: ''; position: absolute;
    bottom: -18px; left: 0; right: 0;
    height: 36px; background: rgba(255,255,255,0.92);
    border-radius: 22px 22px 0 0;
}
.login-top-icon {
    width: 72px; height: 72px;
    background: rgba(255,255,255,0.18);
    border: 2px solid rgba(255,255,255,0.40);
    border-radius: 22px; display: flex;
    align-items: center; justify-content: center;
    font-size: 2.2rem; margin: 0 auto 18px;
    box-shadow: 0 8px 28px rgba(0,0,0,0.14); backdrop-filter: blur(8px);
}
.login-name {
    font-size: 2.1rem; font-weight: 800; color: #fff;
    letter-spacing: -.045em; line-height: 1;
}
.login-tagline {
    font-size: 0.63rem; font-weight: 700;
    letter-spacing: .15em; text-transform: uppercase;
    color: rgba(255,255,255,0.68); margin-top: 7px;
}
.login-body { padding: 38px 36px 30px; }
.login-greet {
    font-size: 1.12rem; font-weight: 800; color: var(--text);
    letter-spacing: -.025em; margin-bottom: 5px;
}
.login-greet-sub {
    font-size: 0.78rem; color: var(--muted);
    font-weight: 500; margin-bottom: 24px;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  DB POOL
# ─────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    st.error("⚠️ DATABASE_URL environment variable is not set.")
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
    c = get_conn(); cur = c.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS parts_table (
            id SERIAL PRIMARY KEY, part_no TEXT, brand TEXT,
            price NUMERIC, supplier TEXT
        );
        ALTER TABLE parts_table ADD COLUMN IF NOT EXISTS supplier TEXT;
        DO $$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='unique_part_supplier') THEN
            ALTER TABLE parts_table ADD CONSTRAINT unique_part_supplier UNIQUE(part_no, brand, supplier);
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
        SELECT 'admin','admin' WHERE NOT EXISTS (SELECT 1 FROM users WHERE username='admin');
    """)
    c.commit(); release(c)

init_schema()


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def clean_col(name):
    return re.sub(r'[^a-z0-9]', '', name.strip().lower())


@st.cache_data(ttl=120, show_spinner=False)
def fetch_brands():
    c = get_conn(); cur = c.cursor()
    cur.execute("SELECT DISTINCT brand FROM parts_table ORDER BY brand")
    rows = [x[0] for x in cur.fetchall()]
    release(c); return rows


def lookup_prices(items):
    c = get_conn(); cur = c.cursor()
    results = []
    for r in items:
        part  = r["part_no"].strip()
        brand = r["brand"].strip()
        qty   = max(int(r.get("qty") or 1), 1)
        if not part or not brand: continue
        cur.execute("""
            SELECT supplier, price FROM parts_table
            WHERE TRIM(LOWER(part_no))=TRIM(LOWER(%s)) AND TRIM(LOWER(brand))=TRIM(LOWER(%s))
            ORDER BY price ASC
        """, (part, brand))
        rows_db = cur.fetchall()
        if rows_db:
            for supplier, price in rows_db:
                results.append({"Brand": brand, "Part No": part, "Supplier": supplier,
                    "Qty": qty, "Unit Price (JPY)": float(price), "Amount (JPY)": qty*float(price)})
        else:
            results.append({"Brand": brand, "Part No": part, "Supplier": "Not Found",
                "Qty": qty, "Unit Price (JPY)": 0.0, "Amount (JPY)": 0.0})
    release(c); return results


# ─────────────────────────────────────────────
#  SESSION
# ─────────────────────────────────────────────
for k, v in {"user": None, "page": "Price Lookup",
              "table_data": pd.DataFrame(), "num_rows": 3}.items():
    if k not in st.session_state: st.session_state[k] = v


# ─────────────────────────────────────────────
#  LOGIN
# ─────────────────────────────────────────────
def check_login(u, p):
    c = get_conn(); cur = c.cursor()
    cur.execute("SELECT id FROM users WHERE username=%s AND password=%s", (u, p))
    row = cur.fetchone(); release(c); return row

if st.session_state.user is None:
    st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.1, 1])
    with mid:
        st.markdown("""
        <div class="login-card">
            <div class="login-top">
                <div class="login-top-icon">📋</div>
                <div class="login-name">PriceDesk</div>
                <div class="login-tagline">Parts Pricing Platform</div>
            </div>
            <div style="height:24px;"></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="login-body" style="background:rgba(255,255,255,0.92);border-radius:0 0 22px 22px;padding:8px 36px 32px;">', unsafe_allow_html=True)
        st.markdown('<div class="login-greet">Welcome back 👋</div><div class="login-greet-sub">Sign in to access your workspace</div>', unsafe_allow_html=True)
        u_in = st.text_input("Username", placeholder="Enter your username", key="login_u")
        p_in = st.text_input("Password", type="password", placeholder="Enter your password", key="login_p")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("Sign In  →", use_container_width=True, key="signin_btn"):
            if check_login(u_in, p_in):
                st.session_state.user = {"username": u_in}
                st.rerun()
            else:
                st.error("Invalid username or password.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()


# ─────────────────────────────────────────────
#  CUSTOM SIDEBAR  (always visible, always there)
# ─────────────────────────────────────────────
username = st.session_state.user["username"]
is_admin = (username == "admin")
user_pages = (["Price Lookup", "Saved Quotations", "Data Upload", "Access Control"]
              if is_admin else ["Price Lookup", "Saved Quotations"])
NAV = {"Price Lookup": "🔍", "Saved Quotations": "📁",
       "Data Upload": "📤", "Access Control": "🔐"}

nav_html = ""
for p in user_pages:
    cls   = "sb-btn active" if st.session_state.page == p else "sb-btn"
    icon  = NAV[p]
    # Each nav item is a real button that submits a hidden Streamlit form
    nav_html += f'<button class="{cls}" data-page="{p}"><span class="ic">{icon}</span>{p}</button>\n'

st.markdown(f"""
<div class="pd-sidebar">
    <div class="sb-brand">
        <div class="sb-logo-row">
            <div class="sb-icon">📋</div>
            <span class="sb-name">PriceDesk</span>
        </div>
        <div class="sb-tag">Parts Pricing Platform</div>
    </div>
    <div class="sb-user">
        <div class="sb-user-lbl">Logged in as</div>
        <div class="sb-user-name">{'⭐ ' if is_admin else '👤 '}{username}</div>
    </div>
    <div class="sb-nav">
        <span class="sb-nav-lbl">Navigation</span>
        {nav_html}
    </div>
    <div class="sb-footer">
        <button class="sb-signout" data-action="signout">🚪&nbsp; Sign Out</button>
    </div>
</div>

<script>
(function() {{
    function clickST(label) {{
        var btns = window.parent.document.querySelectorAll('button[data-testid="baseButton-secondary"]');
        btns.forEach(function(b) {{
            if (b.getAttribute('data-pd') === label) b.click();
        }});
    }}
    document.querySelectorAll('.sb-btn').forEach(function(el) {{
        el.addEventListener('click', function() {{
            clickST('nav:' + el.getAttribute('data-page'));
        }});
    }});
    var so = document.querySelector('.sb-signout');
    if (so) so.addEventListener('click', function() {{ clickST('signout'); }});
}})();
</script>
""", unsafe_allow_html=True)

# Hidden Streamlit buttons wired to the sidebar JS
col_nav = st.columns(len(user_pages) + 1)
for idx, p in enumerate(user_pages):
    with col_nav[idx]:
        btn = st.button(f"nav:{p}", key=f"__nav_{p}", help="")
        if btn:
            st.session_state.page = p
            st.rerun()
with col_nav[-1]:
    if st.button("signout", key="__signout", help=""):
        st.session_state.clear()
        st.rerun()

# Hide those helper buttons visually
st.markdown("""
<style>
/* Hide the hidden nav trigger buttons from view */
div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] > div[data-testid="element-container"] > div[data-testid="stButton"] > button {
    position: absolute !important;
    opacity: 0 !important;
    pointer-events: none !important;
    width: 1px !important; height: 1px !important;
    overflow: hidden !important;
    clip: rect(0,0,0,0) !important;
}
/* Wire the sidebar JS to find them by data-pd attribute */
</style>
<script>
(function() {
    // Add data-pd attributes to Streamlit hidden buttons after render
    function tagButtons() {
        var allBtns = window.parent.document.querySelectorAll('button');
        allBtns.forEach(function(b) {
            var txt = b.innerText ? b.innerText.trim() : '';
            if (txt.startsWith('nav:') || txt === 'signout') {
                b.setAttribute('data-pd', txt);
                b.style.cssText = 'position:absolute!important;opacity:0!important;pointer-events:none!important;width:1px!important;height:1px!important;';
            }
        });
    }
    setTimeout(tagButtons, 400);
    setTimeout(tagButtons, 1200);
})();
</script>
""", unsafe_allow_html=True)

page = st.session_state.page

# ─────────────────────────────────────────────
#  LAYOUT HELPERS
# ─────────────────────────────────────────────
def ph(icon, title, sub):
    st.markdown(f"""
    <div class="page-header">
        <div class="ph-icon">{icon}</div>
        <div><div class="ph-title">{title}</div><div class="ph-sub">{sub}</div></div>
    </div>""", unsafe_allow_html=True)

def sc_open(label):
    st.markdown(f'<div class="sc"><div class="sc-lbl">{label}</div>', unsafe_allow_html=True)

def sc_close():
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════
#  PRICE LOOKUP
# ══════════════════════════════════════════════
if page == "Price Lookup":
    ph("🔍", "Price Lookup", "Search parts across all suppliers instantly")
    brand_list = fetch_brands()

    sc_open("Enter Parts to Search")

    r1, r2, r3, _ = st.columns([0.65, 0.65, 0.75, 6])
    with r1:
        if st.button("＋ Add", key="add_row"): st.session_state.num_rows = min(st.session_state.num_rows+1,20); st.rerun()
    with r2:
        if st.button("－ Remove", key="rem_row"): st.session_state.num_rows = max(st.session_state.num_rows-1,1); st.rerun()
    with r3:
        if st.button("✕ Clear", key="clr_rows"):
            st.session_state.num_rows = 3; st.session_state.table_data = pd.DataFrame()
            for i in range(25):
                for s in ["brand","part","qty"]: st.session_state.pop(f"{s}_{i}", None)
            st.rerun()

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    h1, h2, h3 = st.columns([1.5, 2.2, 0.65])
    with h1: st.markdown('<div class="col-hdr">Brand</div>', unsafe_allow_html=True)
    with h2: st.markdown('<div class="col-hdr">Part Number</div>', unsafe_allow_html=True)
    with h3: st.markdown('<div class="col-hdr">Qty</div>', unsafe_allow_html=True)

    n = st.session_state.num_rows
    for i in range(n):
        c1, c2, c3 = st.columns([1.5, 2.2, 0.65])
        with c1: st.selectbox("B", [""] + brand_list, key=f"brand_{i}", label_visibility="collapsed")
        with c2: st.text_input("P", placeholder="e.g. 04152-YZZA6", key=f"part_{i}", label_visibility="collapsed")
        with c3: st.number_input("Q", min_value=1, value=1, step=1, key=f"qty_{i}", label_visibility="collapsed")

    sc_close()

    b1, _ = st.columns([1.2, 7])
    with b1:
        go = st.button("🔍  Get Pricing", use_container_width=True, key="go_btn")

    if go:
        items = []
        for i in range(n):
            b = st.session_state.get(f"brand_{i}", "")
            p = (st.session_state.get(f"part_{i}", "") or "").strip()
            q = st.session_state.get(f"qty_{i}", 1)
            if b and b != "" and p:
                items.append({"brand": b, "part_no": p, "qty": q})
        if items:
            with st.spinner("Fetching prices…"):
                st.session_state.table_data = pd.DataFrame(lookup_prices(items))
        else:
            st.warning("Please enter at least one Brand and Part No.")

    df = st.session_state.table_data
    if not df.empty:
        found = df[df["Supplier"] != "Not Found"]
        st.markdown(f"""
        <div class="metric-row">
            <div class="metric-card">
                <div class="mc-label">Parts Searched</div>
                <div class="mc-value">{df["Part No"].nunique()}</div>
                <div class="mc-sub">unique part numbers</div>
            </div>
            <div class="metric-card">
                <div class="mc-label">Suppliers Found</div>
                <div class="mc-value">{found["Supplier"].nunique() if not found.empty else 0}</div>
                <div class="mc-sub">across all parts</div>
            </div>
            <div class="metric-card">
                <div class="mc-label">Best Unit Price</div>
                <div class="mc-value">¥{found["Unit Price (JPY)"].min():,.0f if not found.empty else 0}</div>
                <div class="mc-sub">lowest available</div>
            </div>
            <div class="metric-card">
                <div class="mc-label">Price Records</div>
                <div class="mc-value">{len(found)}</div>
                <div class="mc-sub">supplier rows returned</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        sc_open("All Supplier Prices")
        def hi(row):
            if row["Supplier"] == "Not Found":
                return ["background-color:#FEF2F2;color:#991B1B"]*len(row)
            mask  = (df["Part No"]==row["Part No"]) & (df["Brand"]==row["Brand"])
            valid = df.loc[mask & (df["Supplier"]!="Not Found"), "Unit Price (JPY)"]
            if not valid.empty and row["Unit Price (JPY)"] == valid.min():
                return ["background-color:#ECFDF5;color:#065F46;font-weight:600"]*len(row)
            return [""]*len(row)

        st.dataframe(df.style.apply(hi,axis=1).format({"Unit Price (JPY)":"¥{:,.0f}","Amount (JPY)":"¥{:,.0f}"}),
                     use_container_width=True, hide_index=True, height=360)
        st.markdown("""
        <div style="display:flex;gap:14px;margin-top:10px;font-size:0.72rem;color:#64748B;align-items:center;">
            <span><span class="badge b-green">Green</span> Cheapest supplier</span>
            <span><span class="badge b-red">Red</span> Not found in DB</span>
        </div>""", unsafe_allow_html=True)
        sc_close()

        a1, a2, _ = st.columns([1.4, 1.5, 5])
        with a1:
            if st.button("💾  Save Quotation", use_container_width=True, key="save_q"):
                c = get_conn(); cur = c.cursor()
                cur.execute("INSERT INTO saved_offers(username,data) VALUES(%s,%s)",
                            (username, json.dumps(df.to_dict(orient="records"))))
                c.commit(); release(c)
                st.success("Quotation saved!")
        with a2:
            buf = BytesIO(); df.to_excel(buf, index=False); buf.seek(0)
            st.download_button("📥  Export Excel", buf, file_name="price_lookup.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True, key="dl_xl")


# ══════════════════════════════════════════════
#  SAVED QUOTATIONS
# ══════════════════════════════════════════════
elif page == "Saved Quotations":
    ph("📁", "Saved Quotations", "View, download and manage past quotations")

    c = get_conn(); cur = c.cursor()
    cur.execute("SELECT id,username,data,created_at::date FROM saved_offers ORDER BY created_at DESC")
    rows = cur.fetchall(); release(c)

    if not rows:
        st.markdown("""<div class="sc" style="text-align:center;padding:64px 24px;">
            <div style="font-size:3rem;margin-bottom:14px;">📭</div>
            <div style="font-size:1.05rem;font-weight:800;color:#0F172A;letter-spacing:-.02em;">No saved quotations yet</div>
            <div style="color:#64748B;font-size:0.82rem;margin-top:8px;">Go to Price Lookup and save your first quotation.</div>
        </div>""", unsafe_allow_html=True)
        st.stop()

    all_data = []
    for oid, user, data, date_only in rows:
        df_o = pd.DataFrame(json.loads(data) if isinstance(data, str) else data)
        df_o["Employee"] = user; df_o["Saved On"] = str(date_only); df_o["_offer_id"] = oid
        all_data.append(df_o)
    final_df = pd.concat(all_data, ignore_index=True)

    st.markdown(f"""<div class="metric-row">
        <div class="metric-card"><div class="mc-label">Total Quotations</div><div class="mc-value">{len(rows)}</div><div class="mc-sub">saved records</div></div>
        <div class="metric-card"><div class="mc-label">Employees</div><div class="mc-value">{final_df["Employee"].nunique()}</div><div class="mc-sub">contributors</div></div>
        <div class="metric-card"><div class="mc-label">Latest Save</div><div class="mc-value" style="font-size:1.1rem;">{str(rows[0][3])}</div><div class="mc-sub">most recent</div></div>
    </div>""", unsafe_allow_html=True)

    display_df = final_df.drop(columns=["_offer_id"], errors="ignore").copy()
    display_df.insert(0, "Select", False)
    sc_open("All Records")
    edited_df = st.data_editor(display_df, use_container_width=True, hide_index=True, height=400, key="saved_ed")
    sc_close()

    b1, b2, _ = st.columns([1.4, 1.5, 5])
    with b1:
        buf = BytesIO(); final_df.drop(columns=["_offer_id"], errors="ignore").to_excel(buf, index=False); buf.seek(0)
        st.download_button("📥  Download All", buf, file_name="all_quotations.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True, key="dl_all")
    with b2:
        if st.button("🗑  Delete Selected", use_container_width=True, key="del_sel"):
            sel = edited_df[edited_df["Select"]==True]
            if not sel.empty:
                keys = set(zip(sel["Employee"].astype(str), sel["Saved On"].astype(str)))
                ids  = [oid for oid, user, _, d in rows if (str(user), str(d)) in keys]
                if ids:
                    c = get_conn(); cur = c.cursor()
                    cur.execute("DELETE FROM saved_offers WHERE id=ANY(%s)", (ids,))
                    c.commit(); release(c)
                    st.success(f"Deleted {len(ids)} record(s)."); st.rerun()
            else:
                st.warning("Select at least one row to delete.")


# ══════════════════════════════════════════════
#  DATA UPLOAD
# ══════════════════════════════════════════════
elif page == "Data Upload":
    ph("📤", "Master Data Upload", "Upload Excel price sheets to update the parts database")

    st.markdown("""<div class="sc">
        <div class="sc-lbl">Required Column Names</div>
        <div style="margin-bottom:12px;">
            <span class="badge b-blue">Make / Brand</span>
            <span class="badge b-blue">Part Number</span>
            <span class="badge b-blue">JPY Price</span>
            <span class="badge b-blue">Supplier</span>
        </div>
        <div style="font-size:0.79rem;color:#64748B;line-height:1.8;font-weight:500;">
            Column names are <strong style="color:#334155;">case-insensitive</strong> — extra spaces handled automatically.<br>
            Re-uploading the same part will <strong style="color:#334155;">update</strong> the price (no duplicates).
        </div>
    </div>""", unsafe_allow_html=True)

    file = st.file_uploader("Upload Excel file (.xlsx)", type=["xlsx"])
    if file:
        df_raw = pd.read_excel(file, dtype=str)
        col_map = {clean_col(c): c for c in df_raw.columns}
        ALIASES = {
            "brand":    ["make","brand","manufacturer"],
            "part_no":  ["partnumber","partno","part","partnum","partnumbers"],
            "price":    ["jpyprice","price","unitprice","jpy","jprice"],
            "supplier": ["supplier","vendor","source"],
        }
        rename = {}
        for target, aliases in ALIASES.items():
            for alias in aliases:
                if alias in col_map: rename[col_map[alias]] = target; break
        df_raw.rename(columns=rename, inplace=True)
        missing = [c for c in ["brand","part_no","price","supplier"] if c not in df_raw.columns]
        if missing:
            st.error(f"Could not map: **{missing}** — Found: `{list(df_raw.columns)}`"); st.stop()
        df_raw["brand"]    = df_raw["brand"].astype(str).str.replace(r'[\n"\r]','',regex=True).str.strip()
        df_raw["part_no"]  = df_raw["part_no"].astype(str).str.replace(r'[\n"\r]','',regex=True).str.strip()
        df_raw["supplier"] = df_raw["supplier"].astype(str).str.strip()
        df_raw["price"]    = pd.to_numeric(df_raw["price"], errors="coerce").fillna(0)
        df_raw = df_raw[(df_raw["part_no"]!="")&(df_raw["brand"]!="")&
                        (df_raw["supplier"]!="")&(df_raw["part_no"]!="nan")&(df_raw["brand"]!="nan")]

        sc_open(f"Preview — {len(df_raw):,} valid rows detected")
        st.dataframe(df_raw[["brand","part_no","price","supplier"]].head(30),
                     use_container_width=True, hide_index=True, height=280)
        sc_close()

        if st.button(f"⬆  Upload {len(df_raw):,} Rows to Database", key="upload_btn"):
            values = list(df_raw[["part_no","brand","price","supplier"]].itertuples(index=False, name=None))
            c = get_conn(); cur = c.cursor()
            execute_values(cur, """
                INSERT INTO parts_table(part_no,brand,price,supplier) VALUES %s
                ON CONFLICT(part_no,brand,supplier) DO UPDATE SET price=EXCLUDED.price
            """, values, page_size=500)
            c.commit(); release(c); fetch_brands.clear()
            st.success(f"✅ Uploaded {len(values):,} rows successfully."); st.rerun()


# ══════════════════════════════════════════════
#  ACCESS CONTROL
# ══════════════════════════════════════════════
elif page == "Access Control":
    ph("🔐", "Access Control", "Manage user accounts and permissions")

    col_a, col_b = st.columns(2, gap="large")
    with col_a:
        sc_open("Create New User")
        nu  = st.text_input("Username", placeholder="e.g. john.doe",      key="nu_inp")
        np_ = st.text_input("Password", type="password", placeholder="Secure password", key="np_inp")
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        if st.button("✚  Create User", use_container_width=True, key="create_u"):
            if nu and np_:
                try:
                    c = get_conn(); cur = c.cursor()
                    cur.execute("INSERT INTO users(username,password) VALUES(%s,%s)", (nu, np_))
                    c.commit(); release(c); st.success(f"User '{nu}' created.")
                except Exception as e:
                    c.rollback(); release(c); st.error(f"Error: {e}")
            else:
                st.warning("Fill in both fields.")
        sc_close()

    with col_b:
        sc_open("Remove Employee")
        c = get_conn(); cur = c.cursor()
        cur.execute("SELECT username FROM users WHERE username!='admin' ORDER BY username")
        users = [x[0] for x in cur.fetchall()]; release(c)
        if users:
            del_u = st.selectbox("Select employee", users, key="del_u_sel")
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            if st.button("🗑  Delete Employee", use_container_width=True, key="del_u_btn"):
                c = get_conn(); cur = c.cursor()
                cur.execute("DELETE FROM users WHERE username=%s", (del_u,))
                c.commit(); release(c); st.success(f"User '{del_u}' removed."); st.rerun()
        else:
            st.info("No other users found.")
        sc_close()

    sc_open("All Users")
    c = get_conn(); cur = c.cursor()
    cur.execute("SELECT username FROM users ORDER BY username")
    all_u = pd.DataFrame(cur.fetchall(), columns=["Username"]); release(c)
    all_u["Role"] = all_u["Username"].apply(lambda x: "⭐ Admin" if x=="admin" else "👤 Employee")
    st.dataframe(all_u, use_container_width=True, hide_index=True, height=220)
    sc_close()

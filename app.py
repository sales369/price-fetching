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
#  PAGE CONFIG  — collapse native sidebar; we build our own
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="PriceDesk",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
#  SESSION DEFAULTS
# ─────────────────────────────────────────────
for k, v in {
    "user": None,
    "page": "Price Lookup",
    "table_data": pd.DataFrame(),
    "num_rows": 3,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
#  GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&family=Outfit:wght@300;400;500;600;700&display=swap');

:root {
    --primary:     #1E40AF;
    --primary-lt:  #EFF6FF;
    --primary-mid: #BFDBFE;
    --accent:      #0EA5E9;
    --success:     #059669;
    --success-lt:  #ECFDF5;
    --success-mid: #A7F3D0;
    --danger:      #DC2626;
    --danger-lt:   #FEF2F2;
    --danger-mid:  #FECACA;
    --text:        #0F172A;
    --muted:       #475569;
    --muted-lt:    #94A3B8;
    --border:      #CBD5E1;
    --border-lt:   #E2E8F0;
    --card:        rgba(255,255,255,0.82);
    --sb-w:        252px;
}

/* ── Hide EVERYTHING native Streamlit sidebar ── */
section[data-testid="stSidebar"],
[data-testid="collapsedControl"],
button[data-testid="collapsedControl"] {
    display: none !important;
    visibility: hidden !important;
    pointer-events: none !important;
    width: 0 !important;
}

#MainMenu, footer, header { visibility: hidden; }
* { box-sizing: border-box; }

.stApp {
    font-family: 'Outfit', sans-serif;
    color: var(--text);
    background: #dde8f8 !important;
    background-image:
        radial-gradient(ellipse 900px 600px at 10% 10%,  rgba(99,102,241,0.18) 0%, transparent 70%),
        radial-gradient(ellipse 700px 500px at 90% 80%,  rgba(14,165,233,0.16) 0%, transparent 70%),
        radial-gradient(ellipse 600px 400px at 50% 50%,  rgba(30,64,175,0.10) 0%, transparent 70%),
        linear-gradient(160deg, #dde8f8 0%, #e8eeff 40%, #ddf3fb 100%) !important;
    min-height: 100vh;
    background-attachment: fixed !important;
}
.stApp::before {
    content: '';
    position: fixed; inset: 0;
    background-image:
        linear-gradient(rgba(30,64,175,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(30,64,175,0.03) 1px, transparent 1px);
    background-size: 44px 44px;
    pointer-events: none; z-index: 0;
}

/* Main content area — pushed by sidebar */
.block-container {
    padding: 1rem 2rem 3rem !important;
    max-width: 100% !important;
    position: relative; z-index: 1;
    transition: padding-left 0.32s cubic-bezier(0.4,0,0.2,1);
}

/* ════════════════════════════════════════
   CUSTOM SLIDING SIDEBAR
════════════════════════════════════════ */
#pd-sidebar {
    position: fixed;
    top: 0; left: 0; bottom: 0;
    width: var(--sb-w);
    background: rgba(255,255,255,0.97);
    backdrop-filter: blur(20px);
    border-right: 1px solid rgba(203,213,225,0.65);
    box-shadow: 4px 0 32px rgba(30,64,175,0.10);
    z-index: 9999;
    display: flex; flex-direction: column;
    transform: translateX(0);
    transition: transform 0.32s cubic-bezier(0.4,0,0.2,1);
    overflow-y: auto;
}
#pd-sidebar.sb-closed {
    transform: translateX(calc(0px - var(--sb-w)));
    box-shadow: none;
}

/* Hamburger button — always visible */
#pd-toggle {
    position: fixed;
    top: 12px; left: 12px;
    z-index: 10000;
    width: 40px; height: 40px;
    background: white;
    border: 1.5px solid var(--border);
    border-radius: 11px;
    cursor: pointer;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    gap: 5px;
    box-shadow: 0 2px 14px rgba(30,64,175,0.14);
    transition: left 0.32s cubic-bezier(0.4,0,0.2,1), box-shadow .2s;
    padding: 0; outline: none;
}
#pd-toggle.tog-open { left: calc(var(--sb-w) + 10px); }
#pd-toggle:hover    { box-shadow: 0 4px 22px rgba(30,64,175,0.24); }
#pd-toggle .bar {
    display: block; width: 18px; height: 2.5px;
    background: var(--primary); border-radius: 2px;
    transition: transform .25s, opacity .25s;
}

/* Backdrop for mobile */
#pd-overlay {
    display: none;
    position: fixed; inset: 0;
    background: rgba(15,23,42,0.22);
    z-index: 9998;
    backdrop-filter: blur(2px);
}

/* ── Sidebar internals ── */
.sb-logo {
    padding: 22px 18px 14px;
    border-bottom: 1px solid var(--border-lt);
    flex-shrink: 0;
}
.sb-brand {
    font-family: 'Sora', sans-serif;
    font-size: 1.32rem; font-weight: 800;
    background: linear-gradient(135deg, #1E40AF, #0EA5E9);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    letter-spacing: -.02em;
}
.sb-tagline { font-size: 0.62rem; color: var(--muted-lt); letter-spacing: .08em; text-transform: uppercase; margin-top: 1px; }

.sb-chip {
    margin: 14px 12px 4px;
    background: linear-gradient(135deg, #EFF6FF, #E0F2FE);
    border-radius: 10px; padding: 10px 13px;
    border: 1px solid var(--primary-mid);
}
.sb-chip .chip-lbl { font-size: 0.59rem; font-weight: 700; letter-spacing: .09em; text-transform: uppercase; color: var(--muted); margin-bottom: 2px; }
.sb-chip .chip-name { font-size: 0.88rem; font-weight: 700; color: var(--primary); font-family: 'Sora', sans-serif; }

.sb-nav { padding: 10px 10px; flex: 1; }
.sb-item {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 13px; border-radius: 10px; margin-bottom: 3px;
    font-size: 0.88rem; font-weight: 600; color: var(--muted);
    cursor: pointer; transition: background .15s, color .15s;
    border: 1px solid transparent; user-select: none;
}
.sb-item:hover { background: var(--primary-lt); color: var(--primary); }
.sb-item.active {
    background: linear-gradient(135deg, #EFF6FF, #DBEAFE);
    color: var(--primary); border-color: var(--primary-mid);
}
.sb-item .ni { font-size: 1rem; width: 20px; text-align: center; flex-shrink: 0; }

.sb-divider { height: 1px; background: var(--border-lt); margin: 8px 12px; }
.sb-signout {
    margin: 0 10px 16px; padding: 10px 13px;
    background: var(--danger-lt); color: var(--danger);
    border: 1px solid var(--danger-mid); border-radius: 10px;
    font-size: 0.83rem; font-weight: 700;
    cursor: pointer; text-align: center;
    transition: background .15s; user-select: none;
}
.sb-signout:hover { background: #FEE2E2; }

/* ── Cards & layout ── */
.metric-row { display:flex; gap:12px; margin-bottom:1.4rem; flex-wrap:wrap; }
.metric-card {
    background: var(--card); backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.9); border-radius: 16px;
    padding: 18px 20px; min-width: 140px; flex: 1;
    box-shadow: 0 2px 16px rgba(30,64,175,0.08);
    position: relative; overflow: hidden;
    transition: transform .2s, box-shadow .2s;
}
.metric-card::before {
    content: ''; position: absolute; top:0; left:0; right:0; height:3px;
    background: linear-gradient(90deg,#1E40AF,#0EA5E9,#6366F1);
    border-radius: 16px 16px 0 0;
}
.metric-card:hover { transform: translateY(-2px); box-shadow: 0 8px 28px rgba(30,64,175,0.14); }
.metric-card .mc-label { font-size:.63rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:var(--muted); margin-bottom:7px; }
.metric-card .mc-value { font-size:1.6rem; font-weight:800; font-family:'Sora',sans-serif; line-height:1; background:linear-gradient(135deg,#1E40AF,#0EA5E9); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.metric-card .mc-sub   { font-size:.69rem; color:var(--muted-lt); margin-top:5px; }

.section-card {
    background: var(--card); backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.9); border-radius: 16px;
    padding: 20px 22px 22px; margin-bottom: 1.2rem;
    box-shadow: 0 2px 16px rgba(30,64,175,0.07);
}
.section-label {
    font-size:.65rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase;
    color:var(--muted); margin-bottom:14px; padding-bottom:10px;
    border-bottom:1px solid var(--border-lt);
}
.page-header {
    display:flex; align-items:center; gap:14px;
    margin-bottom:1.6rem; padding-bottom:1rem;
    border-bottom:1px solid rgba(203,213,225,0.5);
}
.ph-icon {
    width:44px; height:44px;
    background:linear-gradient(135deg,#1E40AF,#0EA5E9);
    border-radius:12px; display:flex; align-items:center; justify-content:center;
    font-size:1.1rem; box-shadow:0 4px 16px rgba(30,64,175,0.25); flex-shrink:0;
}
.ph-title { font-size:1.4rem!important; margin:0!important; font-family:'Sora',sans-serif!important; font-weight:700!important; }
.ph-sub   { margin:0; color:var(--muted); font-size:0.77rem; margin-top:3px; }

.stButton>button {
    background:linear-gradient(135deg,#1E40AF,#0EA5E9)!important;
    color:#fff!important; border:none!important; border-radius:10px!important;
    font-family:'Outfit',sans-serif!important; font-weight:600!important;
    font-size:0.85rem!important; padding:0.5rem 1.3rem!important;
    box-shadow:0 3px 12px rgba(30,64,175,0.25)!important; transition:all .2s!important;
}
.stButton>button:hover { opacity:.88!important; transform:translateY(-1px)!important; }
.stDownloadButton>button {
    background:linear-gradient(135deg,#059669,#0EA5E9)!important;
    color:#fff!important; border:none!important; border-radius:10px!important;
    font-family:'Outfit',sans-serif!important; font-weight:600!important; font-size:0.85rem!important;
}
.stTextInput>div>div>input,
.stNumberInput>div>div>input,
.stSelectbox>div>div {
    border-radius:10px!important; border:1.5px solid var(--border)!important;
    font-family:'Outfit',sans-serif!important; font-size:0.87rem!important;
    background:rgba(255,255,255,0.85)!important;
}
.stTextInput>div>div>input:focus {
    border-color:var(--primary)!important;
    box-shadow:0 0 0 3px rgba(30,64,175,0.12)!important; background:#fff!important;
}
[data-testid="stFileUploader"] {
    border:2px dashed var(--primary-mid)!important;
    border-radius:14px!important; background:rgba(239,246,255,0.7)!important;
}
[data-testid="stDataFrame"],[data-testid="stDataEditor"] {
    border-radius:12px; overflow:hidden; border:1px solid var(--border-lt)!important;
}

.badge { display:inline-block; padding:3px 10px; border-radius:20px; font-size:.68rem; font-weight:700; letter-spacing:.05em; margin:2px; }
.badge-blue  { background:var(--primary-lt); color:var(--primary); border:1px solid var(--primary-mid); }
.badge-green { background:var(--success-lt); color:var(--success); border:1px solid var(--success-mid); }
.badge-red   { background:var(--danger-lt);  color:var(--danger);  border:1px solid var(--danger-mid);  }
.part-col-label { font-size:.65rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); padding-left:2px; }

/* Login */
.login-card { background:rgba(255,255,255,0.9); backdrop-filter:blur(24px); border:1px solid rgba(255,255,255,0.95); border-radius:22px; padding:0 0 34px; box-shadow:0 24px 64px rgba(30,64,175,0.14); max-width:420px; width:100%; overflow:hidden; }
.login-hdr  { background:linear-gradient(135deg,#1E40AF,#0EA5E9 60%,#6366F1); padding:34px 40px 30px; text-align:center; position:relative; }
.login-hdr::after { content:''; position:absolute; bottom:-1px; left:0; right:0; height:20px; background:rgba(255,255,255,0.9); border-radius:20px 20px 0 0; }
.login-ico  { width:60px; height:60px; background:rgba(255,255,255,0.22); border-radius:16px; display:flex; align-items:center; justify-content:center; font-size:1.7rem; margin:0 auto 12px; border:2px solid rgba(255,255,255,0.4); }
.login-name { font-family:'Sora',sans-serif; font-size:1.7rem; font-weight:800; color:#fff; margin-bottom:4px; }
.login-tag  { color:rgba(255,255,255,0.75); font-size:.76rem; }
.login-body { padding:26px 34px 0; }
.login-hi   { font-family:'Sora',sans-serif; font-size:1rem; font-weight:700; color:var(--text); margin-bottom:3px; }
.login-sub  { color:var(--muted); font-size:.77rem; margin-bottom:20px; }
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
    c = get_conn(); cur = c.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS parts_table (
                id SERIAL PRIMARY KEY, part_no TEXT, brand TEXT, price NUMERIC, supplier TEXT
            );
            ALTER TABLE parts_table ADD COLUMN IF NOT EXISTS supplier TEXT;
            DO $$
            BEGIN
              IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='unique_part_supplier') THEN
                ALTER TABLE parts_table ADD CONSTRAINT unique_part_supplier UNIQUE(part_no,brand,supplier);
              END IF;
            END$$;
            CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username TEXT UNIQUE, password TEXT);
            CREATE TABLE IF NOT EXISTS saved_offers (
                id SERIAL PRIMARY KEY, username TEXT, data JSONB, created_at TIMESTAMP DEFAULT NOW()
            );
            INSERT INTO users(username,password) SELECT 'admin','admin'
            WHERE NOT EXISTS (SELECT 1 FROM users WHERE username='admin');
        """)
        c.commit()
    except Exception as e:
        c.rollback(); raise e
    finally:
        release(c)

init_schema()


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def clean_col(name):
    return re.sub(r'[^a-z0-9]','', name.strip().lower())

@st.cache_data(ttl=120, show_spinner=False)
def fetch_brands():
    c = get_conn(); cur = c.cursor()
    try:
        cur.execute("SELECT DISTINCT brand FROM parts_table ORDER BY brand")
        return [x[0] for x in cur.fetchall()]
    finally:
        release(c)

def lookup_prices(items):
    c = get_conn(); cur = c.cursor(); results = []
    try:
        for r in items:
            part=r["part_no"].strip(); brand=r["brand"].strip(); qty=max(int(r.get("qty") or 1),1)
            if not part or not brand: continue
            cur.execute("""
                SELECT supplier,price FROM parts_table
                WHERE TRIM(LOWER(part_no))=TRIM(LOWER(%s)) AND TRIM(LOWER(brand))=TRIM(LOWER(%s))
                ORDER BY price ASC
            """, (part,brand))
            rows=cur.fetchall()
            if rows:
                for supplier,price in rows:
                    results.append({"Brand":brand,"Part No":part,"Supplier":supplier,
                                    "Qty":qty,"Unit Price (JPY)":float(price),"Amount (JPY)":qty*float(price)})
            else:
                results.append({"Brand":brand,"Part No":part,"Supplier":"Not Found",
                                "Qty":qty,"Unit Price (JPY)":0.0,"Amount (JPY)":0.0})
    finally:
        release(c)
    return results

def check_login(u, p):
    c = get_conn(); cur = c.cursor()
    try:
        cur.execute("SELECT id FROM users WHERE username=%s AND password=%s",(u,p))
        return cur.fetchone()
    finally:
        release(c)


# ─────────────────────────────────────────────
#  LOGIN
# ─────────────────────────────────────────────
if st.session_state.user is None:
    _, mid, _ = st.columns([1,1.1,1])
    with mid:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="login-hdr">
            <div class="login-ico">📋</div>
            <div class="login-name">PriceDesk</div>
            <div class="login-tag">PARTS PRICING PLATFORM</div>
        </div>
        <div style="height:16px;"></div>""", unsafe_allow_html=True)
        st.markdown('<div class="login-body">', unsafe_allow_html=True)
        st.markdown('<div class="login-hi">Welcome back</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-sub">Sign in to continue to your workspace</div>', unsafe_allow_html=True)
        u_in = st.text_input("Username", placeholder="Enter your username", key="li_u")
        p_in = st.text_input("Password", type="password", placeholder="Enter your password", key="li_p")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("Sign In →", use_container_width=True):
            if check_login(u_in, p_in):
                st.session_state.user = {"username": u_in}
                st.rerun()
            else:
                st.error("Invalid username or password.")
        st.markdown('</div></div>', unsafe_allow_html=True)
    st.stop()


# ─────────────────────────────────────────────
#  CUSTOM SIDEBAR  (HTML + JS, no Streamlit sidebar)
# ─────────────────────────────────────────────
username   = st.session_state.user["username"]
is_admin   = (username == "admin")
cur_page   = st.session_state.page

nav_pages  = ["Price Lookup","Saved Quotations"] + (["Data Upload","Access Control"] if is_admin else [])
nav_icons  = {"Price Lookup":"📊","Saved Quotations":"📁","Data Upload":"📤","Access Control":"🔐"}

items_html = "".join(
    f'<div class="sb-item{" active" if p==cur_page else ""}" '
    f'onclick="choosePage({json.dumps(p)})">'
    f'<span class="ni">{nav_icons[p]}</span>{p}</div>'
    for p in nav_pages
)

st.markdown(f"""
<div id="pd-sidebar">
  <div class="sb-logo">
    <div class="sb-brand">📋 PriceDesk</div>
    <div class="sb-tagline">Parts Pricing Platform</div>
  </div>
  <div class="sb-chip">
    <div class="chip-lbl">Logged in as</div>
    <div class="chip-name">{username}</div>
  </div>
  <nav class="sb-nav">{items_html}</nav>
  <div class="sb-divider"></div>
  <div class="sb-signout" onclick="doSignOut()">⏏&nbsp; Sign Out</div>
</div>

<button id="pd-toggle" class="tog-open" onclick="toggleSB()">
  <span class="bar"></span>
  <span class="bar"></span>
  <span class="bar"></span>
</button>
<div id="pd-overlay" onclick="closeSB()"></div>

<script>
(function(){{
  var SB_W = 252;

  function getSB()  {{ return document.getElementById('pd-sidebar'); }}
  function getTog() {{ return document.getElementById('pd-toggle'); }}
  function getOvl() {{ return document.getElementById('pd-overlay'); }}
  function getBC()  {{
    return window.parent.document.querySelector('.block-container')
        || window.parent.document.querySelector('[data-testid="stAppViewBlockContainer"]');
  }}

  function isOpen() {{ return !getSB().classList.contains('sb-closed'); }}

  function openSB() {{
    getSB().classList.remove('sb-closed');
    getTog().classList.add('tog-open');
    getOvl().style.display = 'block';
    var bc = getBC(); if(bc) bc.style.paddingLeft = (SB_W+16)+'px';
  }}
  function closeSB() {{
    getSB().classList.add('sb-closed');
    getTog().classList.remove('tog-open');
    getOvl().style.display = 'none';
    var bc = getBC(); if(bc) bc.style.paddingLeft = '56px';
  }}
  window.closeSB = closeSB;

  window.toggleSB = function() {{ isOpen() ? closeSB() : openSB(); }};

  // Set initial padding
  setTimeout(function(){{
    var bc = getBC();
    if(bc) {{
      bc.style.transition = 'padding-left 0.32s cubic-bezier(0.4,0,0.2,1)';
      bc.style.paddingLeft = (SB_W+16)+'px';
    }}
  }}, 100);

  // Nav page selection — change hidden selectbox in parent frame
  window.choosePage = function(pageName) {{
    var doc = window.parent.document;
    // Find ALL select elements and look for one with our page options
    var sels = doc.querySelectorAll('select');
    sels.forEach(function(sel) {{
      for(var i=0;i<sel.options.length;i++) {{
        if(sel.options[i].text.trim()===pageName) {{
          sel.selectedIndex = i;
          sel.dispatchEvent(new Event('change',{{bubbles:true}}));
          // Also trigger React synthetic event
          var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype,'value').set;
          nativeInputValueSetter.call(sel, sel.options[i].value);
          sel.dispatchEvent(new Event('input',{{bubbles:true}}));
          break;
        }}
      }}
    }});
  }};

  // Sign out — click the hidden Streamlit button
  window.doSignOut = function() {{
    var doc = window.parent.document;
    var btns = doc.querySelectorAll('button');
    btns.forEach(function(b) {{
      if(b.innerText && b.innerText.trim()==='__SIGNOUT__') b.click();
    }});
  }};
}})();
</script>
""", unsafe_allow_html=True)

# ── Hidden Streamlit controls for nav & sign-out ──
with st.container():
    st.markdown("<div style='position:fixed;left:-9999px;top:-9999px;width:1px;height:1px;overflow:hidden;'>", unsafe_allow_html=True)
    nav_sel = st.selectbox("__nav__", nav_pages,
                           index=nav_pages.index(cur_page),
                           key="__nav_sel__",
                           label_visibility="collapsed")
    so_btn  = st.button("__SIGNOUT__", key="__so__")
    st.markdown("</div>", unsafe_allow_html=True)

if so_btn:
    st.session_state.clear(); st.rerun()
if nav_sel != cur_page:
    st.session_state.page = nav_sel; st.rerun()

page = st.session_state.page

# Top spacer (hamburger button height)
st.markdown("<div style='height:50px'></div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════
#  PAGE: PRICE LOOKUP
# ═══════════════════════════════════════════
if page == "Price Lookup":

    st.markdown("""
    <div class="page-header">
      <div class="ph-icon">📊</div>
      <div><div class="ph-title">Price Lookup</div>
           <div class="ph-sub">Search parts across all suppliers instantly</div></div>
    </div>""", unsafe_allow_html=True)

    brand_list = fetch_brands()

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Enter Parts to Search</div>', unsafe_allow_html=True)

    ca, cb, cc, _ = st.columns([0.9,0.9,1,5])
    with ca:
        if st.button("＋ Add Row"):
            st.session_state.num_rows = min(st.session_state.num_rows+1, 20); st.rerun()
    with cb:
        if st.button("－ Remove"):
            st.session_state.num_rows = max(st.session_state.num_rows-1, 1); st.rerun()
    with cc:
        if st.button("✕ Clear All"):
            st.session_state.num_rows = 3; st.session_state.table_data = pd.DataFrame()
            for i in range(25):
                for k in [f"brand_{i}",f"part_{i}",f"qty_{i}"]:
                    if k in st.session_state: del st.session_state[k]
            st.rerun()

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    h1,h2,h3,_ = st.columns([1.6,2.2,0.8,0.6])
    with h1: st.markdown('<div class="part-col-label">Brand</div>', unsafe_allow_html=True)
    with h2: st.markdown('<div class="part-col-label">Part Number</div>', unsafe_allow_html=True)
    with h3: st.markdown('<div class="part-col-label">Qty</div>', unsafe_allow_html=True)

    n = st.session_state.num_rows
    for i in range(n):
        r1,r2,r3,_ = st.columns([1.6,2.2,0.8,0.6])
        with r1: st.selectbox("",[""] + brand_list, key=f"brand_{i}", label_visibility="collapsed")
        with r2: st.text_input("", placeholder="e.g. 04152-YZZA6", key=f"part_{i}", label_visibility="collapsed")
        with r3: st.number_input("", min_value=1, value=1, step=1, key=f"qty_{i}", label_visibility="collapsed")

    st.markdown('</div>', unsafe_allow_html=True)

    b1,_,__ = st.columns([1.2,1,6])
    with b1:
        go = st.button("🔍 Get Pricing", use_container_width=True)

    if go:
        items=[]
        for i in range(n):
            b=st.session_state.get(f"brand_{i}",""); p=st.session_state.get(f"part_{i}","").strip()
            q=st.session_state.get(f"qty_{i}",1)
            if b and b!="" and p: items.append({"brand":b,"part_no":p,"qty":q})
        if items:
            with st.spinner("Fetching prices…"):
                results=lookup_prices(items)
            st.session_state.table_data=pd.DataFrame(results)
        else:
            st.warning("Please enter at least one Brand and Part No.")

    df = st.session_state.table_data

    if not df.empty:
        found=df[df["Supplier"]!="Not Found"]
        n_parts=int(df["Part No"].nunique()); n_suppliers=int(found["Supplier"].nunique()) if not found.empty else 0
        best_price=float(found["Unit Price (JPY)"].min()) if not found.empty else 0.0; n_records=int(len(found))

        st.markdown(f"""
        <div class="metric-row">
          <div class="metric-card"><div class="mc-label">Parts Searched</div><div class="mc-value">{n_parts}</div><div class="mc-sub">unique part numbers</div></div>
          <div class="metric-card"><div class="mc-label">Suppliers Found</div><div class="mc-value">{n_suppliers}</div><div class="mc-sub">across all parts</div></div>
          <div class="metric-card"><div class="mc-label">Best Unit Price</div><div class="mc-value">¥{best_price:,.0f}</div><div class="mc-sub">lowest unit price</div></div>
          <div class="metric-card"><div class="mc-label">Price Records</div><div class="mc-value">{n_records}</div><div class="mc-sub">supplier rows returned</div></div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">All Supplier Prices</div>', unsafe_allow_html=True)

        def highlight_rows(row):
            if row["Supplier"]=="Not Found": return ["background-color:#FEF2F2;color:#991B1B"]*len(row)
            mask=(df["Part No"]==row["Part No"])&(df["Brand"]==row["Brand"])
            valid=df.loc[mask&(df["Supplier"]!="Not Found"),"Unit Price (JPY)"]
            if not valid.empty and row["Unit Price (JPY)"]==valid.min():
                return ["background-color:#F0FDF4;color:#065F46;font-weight:600"]*len(row)
            return [""]*len(row)

        styled=(df.style.apply(highlight_rows,axis=1)
                  .format({"Unit Price (JPY)":"¥{:,.0f}","Amount (JPY)":"¥{:,.0f}"}))
        st.dataframe(styled, use_container_width=True, hide_index=True, height=360)
        st.markdown("""
        <div style="display:flex;gap:16px;margin-top:10px;font-size:.74rem;color:#64748B;">
          <span><span class="badge badge-green">Green</span> Cheapest for that part</span>
          <span><span class="badge badge-red">Red</span> Not found in database</span>
        </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        a1,a2,_ = st.columns([1.3,1.3,5])
        with a1:
            if st.button("💾 Save Quotation", use_container_width=True):
                c=get_conn(); cur=c.cursor()
                try:
                    cur.execute("INSERT INTO saved_offers(username,data) VALUES(%s,%s)",
                                (username, json.dumps(df.to_dict(orient="records"))))
                    c.commit(); st.success("Quotation saved.")
                except Exception as e:
                    c.rollback(); st.error(f"Save failed: {e}")
                finally:
                    release(c)
        with a2:
            buf=BytesIO(); df.to_excel(buf,index=False); buf.seek(0)
            st.download_button("📥 Export Excel", buf, file_name="price_lookup.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)


# ═══════════════════════════════════════════
#  PAGE: SAVED QUOTATIONS
# ═══════════════════════════════════════════
elif page == "Saved Quotations":

    st.markdown("""
    <div class="page-header">
      <div class="ph-icon">📁</div>
      <div><div class="ph-title">Saved Quotations</div>
           <div class="ph-sub">View, download and manage past quotations</div></div>
    </div>""", unsafe_allow_html=True)

    c=get_conn(); cur=c.cursor()
    try:
        cur.execute("SELECT id,username,data,created_at::date FROM saved_offers ORDER BY created_at DESC")
        rows=cur.fetchall()
    finally:
        release(c)

    if not rows:
        st.markdown("""
        <div class="section-card" style="text-align:center;padding:60px 24px;">
          <div style="font-size:2.8rem;margin-bottom:12px;">📭</div>
          <div style="font-size:1rem;font-weight:700;font-family:'Sora',sans-serif;">No saved quotations yet</div>
          <div style="color:#64748B;font-size:.82rem;margin-top:8px;">Go to Price Lookup and save your first quotation.</div>
        </div>""", unsafe_allow_html=True)
        st.stop()

    all_data=[]
    for oid,user,data,date_only in rows:
        df_o=pd.DataFrame(json.loads(data) if isinstance(data,str) else data)
        df_o["Employee"]=user; df_o["Saved On"]=str(date_only); df_o["_offer_id"]=oid
        all_data.append(df_o)
    final_df=pd.concat(all_data,ignore_index=True)

    st.markdown(f"""
    <div class="metric-row">
      <div class="metric-card"><div class="mc-label">Total Quotations</div><div class="mc-value">{len(rows)}</div><div class="mc-sub">saved records</div></div>
      <div class="metric-card"><div class="mc-label">Employees</div><div class="mc-value">{final_df["Employee"].nunique()}</div><div class="mc-sub">contributors</div></div>
      <div class="metric-card"><div class="mc-label">Latest Save</div><div class="mc-value" style="font-size:1rem;">{str(rows[0][3])}</div><div class="mc-sub">most recent</div></div>
    </div>""", unsafe_allow_html=True)

    display_df=final_df.drop(columns=["_offer_id"],errors="ignore").copy()
    display_df.insert(0,"Select",False)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">All Records</div>', unsafe_allow_html=True)
    edited_df=st.data_editor(display_df, use_container_width=True, hide_index=True, height=400, key="saved_editor")
    st.markdown('</div>', unsafe_allow_html=True)

    b1,b2,_ = st.columns([1.3,1.3,5])
    with b1:
        buf=BytesIO(); final_df.drop(columns=["_offer_id"],errors="ignore").to_excel(buf,index=False); buf.seek(0)
        st.download_button("📥 Download All", buf, file_name="all_quotations.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)
    with b2:
        if st.button("🗑 Delete Selected", use_container_width=True):
            sel_mask=edited_df["Select"]==True
            if sel_mask.any():
                ids_to_del=list(final_df.loc[sel_mask[sel_mask].index,"_offer_id"].unique())
                if ids_to_del:
                    conn=get_conn(); cur2=conn.cursor()
                    try:
                        cur2.execute("DELETE FROM saved_offers WHERE id=ANY(%s)",(ids_to_del,))
                        conn.commit(); st.success(f"Deleted {len(ids_to_del)} quotation(s).")
                    except Exception as e:
                        conn.rollback(); st.error(f"Delete failed: {e}")
                    finally:
                        release(conn)
                    st.rerun()
            else:
                st.warning("Select at least one row to delete.")


# ═══════════════════════════════════════════
#  PAGE: DATA UPLOAD
# ═══════════════════════════════════════════
elif page == "Data Upload":

    st.markdown("""
    <div class="page-header">
      <div class="ph-icon">📤</div>
      <div><div class="ph-title">Master Data Upload</div>
           <div class="ph-sub">Upload Excel price sheets to update the parts database</div></div>
    </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="section-card">
      <div class="section-label">Required Column Names</div>
      <span class="badge badge-blue">Make / Brand</span>
      <span class="badge badge-blue">Part Number</span>
      <span class="badge badge-blue">JPY Price</span>
      <span class="badge badge-blue">Supplier</span>
      <div style="font-size:.79rem;color:#64748B;margin-top:12px;line-height:1.7;">
        Column names are <strong>case-insensitive</strong>. Same part uploaded again will <strong>update</strong> price — no duplicates.
      </div>
    </div>""", unsafe_allow_html=True)

    file=st.file_uploader("Upload Excel file (.xlsx)",type=["xlsx"])
    if file:
        df_raw=pd.read_excel(file,dtype=str)
        col_map={clean_col(c):c for c in df_raw.columns}
        ALIASES={"brand":["make","brand","manufacturer"],"part_no":["partnumber","partno","part","partnum","partnumbers"],
                 "price":["jpyprice","price","unitprice","jpy","jprice"],"supplier":["supplier","vendor","source"]}
        rename={}
        for target,aliases in ALIASES.items():
            for alias in aliases:
                if alias in col_map: rename[col_map[alias]]=target; break
        df_raw.rename(columns=rename,inplace=True)
        missing=[c for c in ["brand","part_no","price","supplier"] if c not in df_raw.columns]
        if missing:
            st.error(f"Could not map: **{missing}**  Detected: `{list(df_raw.columns)}`"); st.stop()
        for col in ["brand","part_no","supplier"]:
            df_raw[col]=df_raw[col].astype(str).str.replace(r'[\n"\r]','',regex=True).str.strip()
        df_raw["price"]=pd.to_numeric(df_raw["price"],errors="coerce").fillna(0)
        df_raw=df_raw[(df_raw["part_no"]!="")&(df_raw["brand"]!="")&(df_raw["supplier"]!="")
                      &(df_raw["part_no"]!="nan")&(df_raw["brand"]!="nan")]

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="section-label">Preview — {len(df_raw):,} valid rows</div>', unsafe_allow_html=True)
        st.dataframe(df_raw[["brand","part_no","price","supplier"]].head(30),
                     use_container_width=True, hide_index=True, height=280)
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button(f"⬆ Upload {len(df_raw):,} Rows to Database"):
            values=list(df_raw[["part_no","brand","price","supplier"]].itertuples(index=False,name=None))
            c=get_conn(); cur=c.cursor()
            try:
                execute_values(cur,"""
                    INSERT INTO parts_table(part_no,brand,price,supplier) VALUES %s
                    ON CONFLICT(part_no,brand,supplier) DO UPDATE SET price=EXCLUDED.price
                """,values,page_size=500)
                c.commit(); fetch_brands.clear(); st.success(f"Uploaded {len(values):,} rows.")
            except Exception as e:
                c.rollback(); st.error(f"Upload failed: {e}")
            finally:
                release(c)
            st.rerun()


# ═══════════════════════════════════════════
#  PAGE: ACCESS CONTROL
# ═══════════════════════════════════════════
elif page == "Access Control":

    st.markdown("""
    <div class="page-header">
      <div class="ph-icon">🔐</div>
      <div><div class="ph-title">Access Control</div>
           <div class="ph-sub">Manage user accounts and permissions</div></div>
    </div>""", unsafe_allow_html=True)

    col_a,col_b=st.columns(2,gap="large")

    with col_a:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Create New User</div>', unsafe_allow_html=True)
        nu =st.text_input("Username",placeholder="e.g. john.doe",key="nu")
        np_=st.text_input("Password",type="password",placeholder="Secure password",key="np")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("✚ Create User",use_container_width=True):
            if nu and np_:
                c=get_conn(); cur=c.cursor()
                try:
                    cur.execute("INSERT INTO users(username,password) VALUES(%s,%s)",(nu,np_))
                    c.commit(); st.success(f"User '{nu}' created.")
                except Exception as e:
                    c.rollback(); st.error(f"Error: {e}")
                finally:
                    release(c)
            else:
                st.warning("Fill in both fields.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Remove Employee</div>', unsafe_allow_html=True)
        c=get_conn(); cur=c.cursor()
        try:
            cur.execute("SELECT username FROM users WHERE username!='admin' ORDER BY username")
            users=[x[0] for x in cur.fetchall()]
        finally:
            release(c)
        if users:
            del_u=st.selectbox("Select employee to remove",users)
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            if st.button("🗑 Delete Employee",use_container_width=True):
                c=get_conn(); cur=c.cursor()
                try:
                    cur.execute("DELETE FROM users WHERE username=%s",(del_u,))
                    c.commit(); st.success(f"User '{del_u}' removed.")
                except Exception as e:
                    c.rollback(); st.error(f"Error: {e}")
                finally:
                    release(c)
                st.rerun()
        else:
            st.info("No other users found.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">All Users</div>', unsafe_allow_html=True)
    c=get_conn(); cur=c.cursor()
    try:
        cur.execute("SELECT username FROM users ORDER BY username")
        all_u=pd.DataFrame(cur.fetchall(),columns=["Username"])
    finally:
        release(c)
    all_u["Role"]=all_u["Username"].apply(lambda x:"🔑 Admin" if x=="admin" else "👤 Employee")
    st.dataframe(all_u,use_container_width=True,hide_index=True,height=220)
    st.markdown('</div>', unsafe_allow_html=True)

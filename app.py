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
    --primary:     #C9A84C;
    --primary-dk:  #A8833A;
    --primary-lt:  rgba(201,168,76,0.12);
    --primary-mid: #EDD98A;
    --accent:      #38BDF8;
    --navy:        #060d1a;
    --success:     #22C55E;
    --danger:      #EF4444;
    --text:        #E8EEF6;
    --muted:       #7A90AB;
    --muted-lt:    #4A607A;
    --border:      rgba(201,168,76,0.18);
    --border-lt:   rgba(201,168,76,0.08);
    --card:        rgba(10,20,40,0.75);
}

/* ════════════════════════════════════
   KEYFRAME ANIMATIONS — LIVE THEME
════════════════════════════════════ */
@keyframes auroraShift {
  0%   { transform: translate(0%, 0%)   scale(1);    opacity: 0.55; }
  25%  { transform: translate(8%, -6%)  scale(1.08); opacity: 0.70; }
  50%  { transform: translate(-5%, 10%) scale(0.95); opacity: 0.50; }
  75%  { transform: translate(-10%, -4%)scale(1.05); opacity: 0.65; }
  100% { transform: translate(0%, 0%)   scale(1);    opacity: 0.55; }
}
@keyframes auroraShift2 {
  0%   { transform: translate(0%, 0%)   scale(1.05); opacity: 0.45; }
  33%  { transform: translate(-9%, 8%)  scale(0.92); opacity: 0.65; }
  66%  { transform: translate(7%, -9%)  scale(1.10); opacity: 0.40; }
  100% { transform: translate(0%, 0%)   scale(1.05); opacity: 0.45; }
}
@keyframes auroraShift3 {
  0%   { transform: translate(0%, 0%)   scale(0.98); opacity: 0.35; }
  40%  { transform: translate(6%, 6%)   scale(1.06); opacity: 0.55; }
  80%  { transform: translate(-7%, -5%) scale(0.94); opacity: 0.30; }
  100% { transform: translate(0%, 0%)   scale(0.98); opacity: 0.35; }
}
@keyframes gridPulse {
  0%, 100% { opacity: 0.18; }
  50%       { opacity: 0.32; }
}
@keyframes particleDrift {
  0%   { transform: translateY(0px)   translateX(0px);   opacity: 0; }
  10%  { opacity: 1; }
  90%  { opacity: 1; }
  100% { transform: translateY(-120px) translateX(40px); opacity: 0; }
}
@keyframes orbitRing {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
@keyframes shimmerLine {
  0%   { opacity: 0; transform: scaleX(0); }
  50%  { opacity: 1; transform: scaleX(1); }
  100% { opacity: 0; transform: scaleX(0); }
}

#MainMenu, footer, header { visibility: hidden; }
* { box-sizing: border-box; }

section[data-testid="stSidebar"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"] { display: none !important; }

/* ════ BASE APP — solid dark foundation ════ */
.stApp {
    font-family: 'Outfit', sans-serif;
    color: var(--text);
    background: var(--navy) !important;
    min-height: 100vh;
    position: relative;
    overflow-x: hidden;
}

/* ════ LIVE ANIMATED CANVAS LAYER ════ */
.stApp::before {
    content: '';
    position: fixed; inset: 0; z-index: 0;
    background:
        /* Aurora blob 1 — gold */
        radial-gradient(ellipse 900px 700px at 15% 20%,
            rgba(201,168,76,0.22) 0%, transparent 65%),
        /* Aurora blob 2 — electric blue */
        radial-gradient(ellipse 750px 600px at 85% 75%,
            rgba(56,189,248,0.20) 0%, transparent 65%),
        /* Aurora blob 3 — deep indigo */
        radial-gradient(ellipse 650px 550px at 55% 50%,
            rgba(99,60,180,0.18) 0%, transparent 65%),
        /* Base gradient */
        linear-gradient(160deg, #060d1a 0%, #0a1628 50%, #060f20 100%);
    animation: auroraShift 14s ease-in-out infinite;
    pointer-events: none;
}

/* Aurora layer 2 — counter-motion */
.stApp::after {
    content: '';
    position: fixed; inset: 0; z-index: 0;
    background:
        radial-gradient(ellipse 600px 500px at 80% 15%,
            rgba(56,189,248,0.14) 0%, transparent 60%),
        radial-gradient(ellipse 700px 450px at 10% 80%,
            rgba(201,168,76,0.13) 0%, transparent 60%),
        radial-gradient(ellipse 500px 400px at 50% 90%,
            rgba(99,60,180,0.12) 0%, transparent 60%);
    animation: auroraShift2 18s ease-in-out infinite;
    pointer-events: none;
}

/* ════ MOVING GRID OVERLAY ════ */
#pd-grid-overlay {
    position: fixed; inset: 0; z-index: 1;
    background-image:
        linear-gradient(rgba(201,168,76,0.07) 1px, transparent 1px),
        linear-gradient(90deg, rgba(201,168,76,0.07) 1px, transparent 1px);
    background-size: 56px 56px;
    animation: gridPulse 6s ease-in-out infinite;
    pointer-events: none;
}

/* ════ FLOATING PARTICLES ════ */
.pd-particle {
    position: fixed;
    width: 3px; height: 3px;
    border-radius: 50%;
    background: rgba(201,168,76,0.7);
    box-shadow: 0 0 6px rgba(201,168,76,0.5);
    pointer-events: none;
    z-index: 2;
    animation: particleDrift linear infinite;
}

/* ════ TOP NAVBAR ════ */
.top-navbar {
    display: flex; align-items: center; justify-content: space-between;
    background: rgba(6,13,26,0.88);
    backdrop-filter: blur(28px); -webkit-backdrop-filter: blur(28px);
    border-bottom: 1px solid rgba(201,168,76,0.22);
    box-shadow: 0 1px 40px rgba(0,0,0,0.6), 0 1px 0 rgba(201,168,76,0.15);
    padding: 0 28px; height: 66px;
    position: relative; z-index: 100;
}
.navbar-brand { display:flex; align-items:center; gap:13px; }
.navbar-logo {
    width:38px; height:38px;
    background: linear-gradient(135deg,#C9A84C,#EDD98A);
    border-radius:10px; display:flex; align-items:center; justify-content:center;
    font-size:1rem; box-shadow:0 4px 18px rgba(201,168,76,0.45); flex-shrink:0;
}
.navbar-title {
    font-family:'Sora',sans-serif; font-size:1.18rem; font-weight:800;
    background: linear-gradient(135deg,#EDD98A 0%,#C9A84C 50%,#F5E6A3 100%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
    letter-spacing:-0.01em; line-height:1.1;
}
.navbar-sub { font-size:0.54rem; color:#3A5070; letter-spacing:0.13em; text-transform:uppercase; }
.navbar-user-chip {
    display:flex; align-items:center; gap:10px;
    padding:5px 15px 5px 6px;
    background: rgba(201,168,76,0.10);
    border:1px solid rgba(201,168,76,0.28); border-radius:40px;
}
.navbar-avatar {
    width:28px; height:28px;
    background: linear-gradient(135deg,#C9A84C,#EDD98A);
    border-radius:50%; display:flex; align-items:center; justify-content:center;
    font-size:0.68rem; color:#060d1a; font-weight:800; font-family:'Sora',sans-serif;
}
.navbar-uname { font-size:0.8rem; font-weight:700; color:#C9A84C; font-family:'Sora',sans-serif; }

/* ════ NAV BUTTON ROW ════ */
.nav-row-wrap {
    background: rgba(6,13,26,0.82);
    backdrop-filter: blur(20px);
    border-bottom: 1px solid rgba(201,168,76,0.10);
    padding: 8px 20px; margin-bottom: 24px;
    display:flex; align-items:center; gap:4px;
    position: relative; z-index: 99;
}

/* ════ NAV PILL BUTTONS ════ */
.nav-pill > div > button,
.nav-pill-active > div > button {
    border-radius: 8px !important; font-family: 'Outfit', sans-serif !important;
    font-size: 0.85rem !important; font-weight: 600 !important;
    padding: 0px 18px !important; height: 40px !important; min-height: 40px !important;
    white-space: nowrap !important; letter-spacing: 0.01em !important;
    transition: all 0.18s ease !important;
}
.nav-pill > div > button {
    background: transparent !important; color: #7A90AB !important;
    border: 1.5px solid rgba(201,168,76,0.14) !important; box-shadow: none !important;
}
.nav-pill > div > button:hover {
    background: rgba(201,168,76,0.10) !important; color: #C9A84C !important;
    border-color: rgba(201,168,76,0.35) !important; opacity: 1 !important;
}
.nav-pill-active > div > button {
    background: linear-gradient(135deg,#C9A84C 0%,#EDD98A 100%) !important;
    color: #060d1a !important; border: none !important;
    box-shadow: 0 4px 18px rgba(201,168,76,0.42) !important; font-weight: 700 !important;
}
.nav-pill-active > div > button:hover { opacity: 0.9 !important; }

/* ════ SIGN OUT PILL ════ */
.signout-pill > div > button {
    background: transparent !important; color: #F87171 !important;
    border: 1.5px solid rgba(239,68,68,0.30) !important; border-radius: 8px !important;
    font-family: 'Outfit', sans-serif !important; font-size: 0.83rem !important;
    font-weight: 600 !important; padding: 0px 14px !important;
    height: 40px !important; min-height: 40px !important;
    box-shadow: none !important; white-space: nowrap !important;
}
.signout-pill > div > button:hover {
    background: rgba(239,68,68,0.12) !important;
    border-color: rgba(239,68,68,0.55) !important;
    color: #FCA5A5 !important; opacity: 1 !important;
}

/* ════ REFRESH PILL ════ */
.refresh-pill > div > button {
    background: transparent !important; color: #7A90AB !important;
    border: 1.5px solid rgba(201,168,76,0.14) !important; border-radius: 8px !important;
    font-family: 'Outfit', sans-serif !important; font-size: 0.83rem !important;
    font-weight: 600 !important; padding: 0px 12px !important;
    height: 40px !important; min-height: 40px !important; box-shadow: none !important;
}
.refresh-pill > div > button:hover {
    background: rgba(201,168,76,0.10) !important; color: #C9A84C !important;
    border-color: rgba(201,168,76,0.35) !important; opacity: 1 !important;
}

/* ════ MAIN ACTION BUTTONS ════ */
.block-container .stButton > button {
    background: linear-gradient(135deg,#C9A84C,#EDD98A) !important;
    color: #060d1a !important; border: none !important; border-radius: 10px !important;
    font-family: 'Outfit', sans-serif !important; font-weight: 700 !important;
    font-size: 0.85rem !important; padding: 0.5rem 1.3rem !important;
    box-shadow: 0 4px 16px rgba(201,168,76,0.35) !important; transition: all .2s !important;
}
.block-container .stButton > button:hover {
    opacity: .88 !important; transform: translateY(-1px) !important;
    box-shadow: 0 6px 22px rgba(201,168,76,0.50) !important;
}
.stDownloadButton > button {
    background: linear-gradient(135deg,#059669,#38BDF8) !important;
    color: #fff !important; border: none !important; border-radius: 10px !important;
    font-family: 'Outfit', sans-serif !important; font-weight: 700 !important;
    font-size: 0.85rem !important;
    box-shadow: 0 4px 14px rgba(34,197,94,0.30) !important;
}

/* ════ MAIN CONTENT ════ */
.block-container {
    padding: 0 2rem 3rem !important; max-width: 100% !important;
    position: relative; z-index: 10;
}

/* ════ METRIC CARDS ════ */
.metric-row { display:flex; gap:12px; margin-bottom:1.4rem; flex-wrap:wrap; }
.metric-card {
    background: rgba(10,20,40,0.72);
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(201,168,76,0.20); border-radius: 16px;
    padding: 18px 20px; min-width: 140px; flex: 1;
    box-shadow: 0 4px 24px rgba(0,0,0,0.40), inset 0 1px 0 rgba(201,168,76,0.08);
    position: relative; overflow: hidden; transition: transform .22s, box-shadow .22s;
}
.metric-card::before {
    content: ''; position: absolute; top:0; left:0; right:0; height:2px;
    background: linear-gradient(90deg, transparent, #C9A84C, #EDD98A, #C9A84C, transparent);
    animation: shimmerLine 3.5s ease-in-out infinite;
}
.metric-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 36px rgba(0,0,0,0.50), 0 0 20px rgba(201,168,76,0.12);
    border-color: rgba(201,168,76,0.35);
}
.metric-card .mc-label { font-size:.63rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:#4A607A; margin-bottom:7px; }
.metric-card .mc-value { font-size:1.6rem; font-weight:800; font-family:'Sora',sans-serif; line-height:1;
    background:linear-gradient(135deg,#EDD98A,#C9A84C); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.metric-card .mc-sub   { font-size:.69rem; color:#3A5070; margin-top:5px; }

/* ════ SECTION CARDS ════ */
.section-card {
    background: rgba(10,20,40,0.72);
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(201,168,76,0.16); border-radius: 16px;
    padding: 20px 22px 22px; margin-bottom: 1.2rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.35), inset 0 1px 0 rgba(201,168,76,0.06);
}
.section-label {
    font-size:.65rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase;
    color:#4A607A; margin-bottom:14px; padding-bottom:10px;
    border-bottom:1px solid rgba(201,168,76,0.10);
}

/* ════ PAGE HEADER ════ */
.page-header {
    display:flex; align-items:center; gap:14px;
    margin-bottom:1.6rem; padding-bottom:1rem;
    border-bottom:1px solid rgba(201,168,76,0.12);
}
.ph-icon {
    width:46px; height:46px;
    background: linear-gradient(135deg,#C9A84C,#EDD98A);
    border-radius:13px; display:flex; align-items:center; justify-content:center;
    font-size:1.2rem; box-shadow:0 4px 18px rgba(201,168,76,0.38); flex-shrink:0;
}
.ph-title { font-size:1.4rem!important; margin:0!important; font-family:'Sora',sans-serif!important; font-weight:700!important; color:#E8EEF6!important; }
.ph-sub   { margin:0; color:#4A607A; font-size:0.77rem; margin-top:3px; }

/* ════ INPUTS ════ */
.stTextInput>div>div>input,
.stNumberInput>div>div>input,
.stSelectbox>div>div {
    border-radius:10px!important; border:1.5px solid rgba(201,168,76,0.18)!important;
    font-family:'Outfit',sans-serif!important; font-size:0.87rem!important;
    background:rgba(10,20,40,0.80)!important; color:#E8EEF6!important;
}
.stTextInput>div>div>input:focus {
    border-color:rgba(201,168,76,0.55)!important;
    box-shadow:0 0 0 3px rgba(201,168,76,0.12)!important;
}
[data-testid="stFileUploader"] {
    border:2px dashed rgba(201,168,76,0.28)!important;
    border-radius:14px!important; background:rgba(201,168,76,0.04)!important;
}
[data-testid="stDataFrame"],[data-testid="stDataEditor"] {
    border-radius:12px; overflow:hidden; border:1px solid rgba(201,168,76,0.12)!important;
}

/* ════ BADGES ════ */
.badge { display:inline-block; padding:3px 10px; border-radius:20px; font-size:.68rem; font-weight:700; letter-spacing:.05em; margin:2px; }
.badge-blue  { background:rgba(201,168,76,0.12); color:#C9A84C;  border:1px solid rgba(201,168,76,0.28); }
.badge-green { background:rgba(34,197,94,0.12);  color:#4ADE80;  border:1px solid rgba(34,197,94,0.30); }
.badge-red   { background:rgba(239,68,68,0.12);  color:#F87171;  border:1px solid rgba(239,68,68,0.28); }
.part-col-label { font-size:.65rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:#4A607A; padding-left:2px; }

/* ════ LOGIN CARD ════ */
.login-card {
    background: rgba(10,20,40,0.80);
    backdrop-filter:blur(32px); -webkit-backdrop-filter:blur(32px);
    border:1px solid rgba(201,168,76,0.25); border-radius:22px;
    padding:0 0 34px; box-shadow:0 32px 80px rgba(0,0,0,0.60), 0 0 40px rgba(201,168,76,0.08);
    max-width:420px; width:100%; overflow:hidden;
}
.login-hdr {
    background: linear-gradient(135deg,#0a1628 0%,#1a2a48 50%,#0a1628 100%);
    border-bottom:1px solid rgba(201,168,76,0.20);
    padding:34px 40px 30px; text-align:center; position:relative;
}
.login-hdr::before {
    content:''; position:absolute; inset:0;
    background: radial-gradient(ellipse 300px 200px at 50% 60%, rgba(201,168,76,0.15) 0%, transparent 70%);
}
.login-hdr::after {
    content:''; position:absolute; bottom:0; left:20%; right:20%; height:1px;
    background: linear-gradient(90deg, transparent, rgba(201,168,76,0.5), transparent);
}
.login-ico  { width:64px; height:64px; background:rgba(201,168,76,0.14); border-radius:18px; display:flex; align-items:center; justify-content:center; font-size:1.8rem; margin:0 auto 14px; border:1px solid rgba(201,168,76,0.30); position:relative; }
.login-name { font-family:'Sora',sans-serif; font-size:1.8rem; font-weight:800;
    background:linear-gradient(135deg,#EDD98A,#C9A84C,#F5E6A3);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
    margin-bottom:4px; position:relative; }
.login-tag  { color:#3A5070; font-size:.73rem; letter-spacing:0.12em; text-transform:uppercase; position:relative; }
.login-body { padding:28px 34px 0; }
.login-hi   { font-family:'Sora',sans-serif; font-size:1.05rem; font-weight:700; color:#E8EEF6; margin-bottom:4px; }
.login-sub  { color:#4A607A; font-size:.77rem; margin-bottom:22px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  ANIMATED LIVE BACKGROUND INJECTION
# ─────────────────────────────────────────────
st.markdown("""
<div id="pd-grid-overlay"></div>
<div id="pd-particles"></div>
<script>
(function() {
  // Floating particles
  var container = document.getElementById('pd-particles');
  if (!container) return;
  container.style.cssText = 'position:fixed;inset:0;z-index:2;pointer-events:none;overflow:hidden;';
  var colors = [
    'rgba(201,168,76,0.8)',
    'rgba(237,217,138,0.6)',
    'rgba(56,189,248,0.6)',
    'rgba(201,168,76,0.5)',
    'rgba(255,255,255,0.3)'
  ];
  for (var i = 0; i < 28; i++) {
    var p = document.createElement('div');
    var size = Math.random() * 3 + 1.5;
    var left = Math.random() * 100;
    var bottom = Math.random() * 30;
    var duration = Math.random() * 18 + 12;
    var delay = Math.random() * 16;
    var color = colors[Math.floor(Math.random() * colors.length)];
    p.style.cssText = [
      'position:absolute',
      'width:' + size + 'px',
      'height:' + size + 'px',
      'border-radius:50%',
      'background:' + color,
      'box-shadow:0 0 ' + (size*3) + 'px ' + color,
      'left:' + left + '%',
      'bottom:' + bottom + '%',
      'animation:particleDrift ' + duration + 's ' + delay + 's linear infinite'
    ].join(';');
    container.appendChild(p);
  }
})();
</script>
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
            ALTER TABLE parts_table ADD COLUMN IF NOT EXISTS currency TEXT;
            ALTER TABLE parts_table ADD COLUMN IF NOT EXISTS delivery_time TEXT;
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
                SELECT supplier,price,currency,delivery_time FROM parts_table
                WHERE TRIM(LOWER(part_no))=TRIM(LOWER(%s)) AND TRIM(LOWER(brand))=TRIM(LOWER(%s))
                ORDER BY price ASC
            """, (part,brand))
            rows=cur.fetchall()
            if rows:
                for supplier,price,currency,delivery_time in rows:
                    results.append({"Brand":brand,"Part No":part,"Supplier":supplier,
                                    "Currency":currency or "","Delivery Time":delivery_time or "",
                                    "Qty":qty,"Unit Price":float(price),"Amount":qty*float(price)})
            else:
                results.append({"Brand":brand,"Part No":part,"Supplier":"Not Found",
                                "Currency":"","Delivery Time":"",
                                "Qty":qty,"Unit Price":0.0,"Amount":0.0})
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
#  LOGIN PAGE
# ─────────────────────────────────────────────
if st.session_state.user is None:
    _, mid, _ = st.columns([1,1.1,1])
    with mid:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="login-hdr">
            <img src="https://raw.githubusercontent.com/sales369/price-fetching/main/logo.png"
                 style="width:90px;height:auto;margin:0 auto 10px;display:block;filter:drop-shadow(0 4px 12px rgba(0,0,0,0.18));"
                 alt="PriceDesk Logo" />
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
#  TOP NAVBAR
# ─────────────────────────────────────────────
username  = st.session_state.user["username"]
is_admin  = (username == "admin")
cur_page  = st.session_state.page
nav_pages = ["Price Lookup","Saved Quotations"] + (["Data Upload","Access Control"] if is_admin else [])
nav_icons = {"Price Lookup":"📊","Saved Quotations":"📁","Data Upload":"📤","Access Control":"🔐"}
user_initials = username[:2].upper()

# ── Static brand bar (HTML only — no interactivity needed here) ──
st.markdown(f"""
<div class="top-navbar">
  <div class="navbar-brand">
    <img src="https://raw.githubusercontent.com/sales369/price-fetching/main/logo.png"
         style="height:40px;width:auto;object-fit:contain;filter:drop-shadow(0 2px 6px rgba(30,64,175,0.18));"
         alt="PriceDesk Logo" />
    <div>
      <div class="navbar-title">PriceDesk</div>
      <div class="navbar-sub">Parts Pricing Platform</div>
    </div>
  </div>
  <div class="navbar-user-chip">
    <div class="navbar-avatar">{user_initials}</div>
    <div class="navbar-uname">{username}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Interactive nav buttons row ──
# Build columns: [nav buttons...] [spacer] [refresh] [signout]
n_nav = len(nav_pages)
# each nav pill ~150px, refresh ~52px, signout ~110px, rest is spacer
col_widths = [1.5] * n_nav + [4, 0.6, 1.1]
cols = st.columns(col_widths)

for i, p in enumerate(nav_pages):
    css_cls = "nav-pill-active" if p == cur_page else "nav-pill"
    with cols[i]:
        st.markdown(f'<div class="{css_cls}">', unsafe_allow_html=True)
        if st.button(f"{nav_icons[p]}  {p}", key=f"nav_{p}", use_container_width=True):
            st.session_state.page = p
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# spacer col does nothing
with cols[n_nav + 1]:
    st.markdown('<div class="refresh-pill">', unsafe_allow_html=True)
    if st.button("🔄", key="refresh_btn", help="Refresh brands"):
        fetch_brands.clear()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with cols[n_nav + 2]:
    st.markdown('<div class="signout-pill">', unsafe_allow_html=True)
    if st.button("⏏ Sign Out", key="signout_btn", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

page = st.session_state.page


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
        best_price=float(found["Unit Price"].min()) if not found.empty else 0.0; n_records=int(len(found))

        st.markdown(f"""
        <div class="metric-row">
          <div class="metric-card"><div class="mc-label">Parts Searched</div><div class="mc-value">{n_parts}</div><div class="mc-sub">unique part numbers</div></div>
          <div class="metric-card"><div class="mc-label">Suppliers Found</div><div class="mc-value">{n_suppliers}</div><div class="mc-sub">across all parts</div></div>
          <div class="metric-card"><div class="mc-label">Best Unit Price</div><div class="mc-value">{best_price:,.0f}</div><div class="mc-sub">lowest unit price</div></div>
          <div class="metric-card"><div class="mc-label">Price Records</div><div class="mc-value">{n_records}</div><div class="mc-sub">supplier rows returned</div></div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">All Supplier Prices</div>', unsafe_allow_html=True)

        def highlight_rows(row):
            if row["Supplier"]=="Not Found": return ["background-color:#FEF2F2;color:#991B1B"]*len(row)
            mask=(df["Part No"]==row["Part No"])&(df["Brand"]==row["Brand"])
            valid=df.loc[mask&(df["Supplier"]!="Not Found"),"Unit Price"]
            if not valid.empty and row["Unit Price"]==valid.min():
                return ["background-color:#F0FDF4;color:#065F46;font-weight:600"]*len(row)
            return [""]*len(row)

        styled=(df.style.apply(highlight_rows,axis=1)
                  .format({"Unit Price":"{:,.0f}","Amount":"{:,.0f}"}))
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
                    conn2=get_conn(); cur2=conn2.cursor()
                    try:
                        cur2.execute("DELETE FROM saved_offers WHERE id=ANY(%s)",(ids_to_del,))
                        conn2.commit(); st.success(f"Deleted {len(ids_to_del)} quotation(s).")
                    except Exception as e:
                        conn2.rollback(); st.error(f"Delete failed: {e}")
                    finally:
                        release(conn2)
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
      <span class="badge badge-blue">Currency</span>
      <span class="badge badge-blue">Delivery Time</span>
      <div style="font-size:.79rem;color:#64748B;margin-top:12px;line-height:1.7;">
        Column names are <strong>case-insensitive</strong>. Same part uploaded again will <strong>update</strong> price — no duplicates. Currency and Delivery Time are optional.
      </div>
    </div>""", unsafe_allow_html=True)

    file=st.file_uploader("Upload Excel file (.xlsx)",type=["xlsx"])
    if file:
        df_raw=pd.read_excel(file,dtype=str)
        col_map={clean_col(c):c for c in df_raw.columns}
        ALIASES={"brand":["make","brand","manufacturer"],"part_no":["partnumber","partno","part","partnum","partnumbers"],
                 "price":["jpyprice","price","unitprice","jpy","jprice","unitrate"],"supplier":["supplier","vendor","source"],
                 "currency":["currency","cur","ccy"],"delivery_time":["deliverytime","delivery","leadtime","deliverydays"]}
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
        for col in ["currency","delivery_time"]:
            if col not in df_raw.columns: df_raw[col]=""
            else: df_raw[col]=df_raw[col].astype(str).str.replace(r'[\n"\r]','',regex=True).str.strip()
        df_raw["price"]=pd.to_numeric(df_raw["price"],errors="coerce").fillna(0)
        df_raw=df_raw[(df_raw["part_no"]!="")&(df_raw["brand"]!="")&(df_raw["supplier"]!="")
                      &(df_raw["part_no"]!="nan")&(df_raw["brand"]!="nan")]

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="section-label">Preview — {len(df_raw):,} valid rows</div>', unsafe_allow_html=True)
        preview_cols=[c for c in ["brand","part_no","price","currency","delivery_time","supplier"] if c in df_raw.columns]
        st.dataframe(df_raw[preview_cols].head(30),
                     use_container_width=True, hide_index=True, height=280)
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button(f"⬆ Upload {len(df_raw):,} Rows to Database"):
            values=list(df_raw[["part_no","brand","price","supplier","currency","delivery_time"]].itertuples(index=False,name=None))
            c=get_conn(); cur=c.cursor()
            try:
                execute_values(cur,"""
                    INSERT INTO parts_table(part_no,brand,price,supplier,currency,delivery_time) VALUES %s
                    ON CONFLICT(part_no,brand,supplier) DO UPDATE SET price=EXCLUDED.price,currency=EXCLUDED.currency,delivery_time=EXCLUDED.delivery_time
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

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
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   KEYFRAMES — rich live animations
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
@keyframes aurora1 {
  0%   { transform:translate(0,0) scale(1);      }
  25%  { transform:translate(80px,-60px) scale(1.10); }
  55%  { transform:translate(-55px,70px) scale(0.92); }
  80%  { transform:translate(40px,-20px) scale(1.05); }
  100% { transform:translate(0,0) scale(1);      }
}
@keyframes aurora2 {
  0%   { transform:translate(0,0) scale(1.05);   }
  30%  { transform:translate(-85px,55px) scale(0.90); }
  65%  { transform:translate(65px,-70px) scale(1.12); }
  100% { transform:translate(0,0) scale(1.05);   }
}
@keyframes aurora3 {
  0%   { transform:translate(0,0) scale(0.95);   }
  40%  { transform:translate(50px,60px) scale(1.08); }
  75%  { transform:translate(-40px,-30px) scale(0.97); }
  100% { transform:translate(0,0) scale(0.95);   }
}
@keyframes gridFlow {
  0%   { background-position:0 0;    opacity:0.22; }
  50%  { background-position:26px 26px; opacity:0.40; }
  100% { background-position:0 0;    opacity:0.22; }
}
@keyframes floatUp {
  0%     { transform:translateY(0) translateX(0) scale(1);   opacity:0; }
  8%     { opacity:1; }
  50%    { transform:translateY(-80px) translateX(15px) scale(1.2); }
  90%    { opacity:0.6; }
  100%   { transform:translateY(-170px) translateX(-10px) scale(0.8); opacity:0; }
}
@keyframes shimmer {
  0%   { background-position:-400% center; }
  100% { background-position: 400% center; }
}
@keyframes slideInUp {
  from { opacity:0; transform:translateY(24px); }
  to   { opacity:1; transform:translateY(0); }
}
@keyframes fadeIn {
  from { opacity:0; } to { opacity:1; }
}
@keyframes pulseGlow {
  0%,100% { box-shadow:0 0 0 0 rgba(30,64,175,0.20); }
  50%     { box-shadow:0 0 0 8px rgba(30,64,175,0); }
}
@keyframes rotateRing {
  from { transform:rotate(0deg); }
  to   { transform:rotate(360deg); }
}
@keyframes waveX {
  0%,100% { transform:scaleX(1);   }
  50%     { transform:scaleX(1.04); }
}
@keyframes navbarShimmer {
  0%   { background-position:-200% center; }
  100% { background-position: 200% center; }
}

/* ━━━━ RESET & BASE ━━━━ */
#MainMenu,footer,header { visibility:hidden; }
*, *::before, *::after { box-sizing:border-box; margin:0; padding:0; }
section[data-testid="stSidebar"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"] { display:none !important; }

/* ━━━━ APP SHELL ━━━━ */
.stApp {
  font-family:'Inter',sans-serif;
  color:#0F172A;
  background:#e8f2ff !important;
  min-height:100vh;
  position:relative;
  overflow-x:hidden;
}

/* ━━━━ AURORA LAYER 1 ━━━━ */
.stApp::before {
  content:''; position:fixed; inset:0; z-index:0; pointer-events:none;
  background:
    radial-gradient(ellipse 1100px 850px at  5% 10%, rgba(147,197,253,0.65) 0%, transparent 62%),
    radial-gradient(ellipse  900px 750px at 92% 85%, rgba(196,181,253,0.55) 0%, transparent 62%),
    radial-gradient(ellipse  750px 600px at 50% 50%, rgba(125,211,252,0.40) 0%, transparent 62%),
    linear-gradient(150deg, #dbeafe 0%, #ede9fe 42%, #e0f2fe 75%, #fce7f3 100%);
  animation:aurora1 18s ease-in-out infinite;
}

/* ━━━━ AURORA LAYER 2 ━━━━ */
.stApp::after {
  content:''; position:fixed; inset:0; z-index:0; pointer-events:none;
  background:
    radial-gradient(ellipse 750px 600px at 82%  8%, rgba(167,243,208,0.45) 0%, transparent 60%),
    radial-gradient(ellipse 680px 540px at 10% 88%, rgba(254,215,170,0.40) 0%, transparent 60%),
    radial-gradient(ellipse 580px 460px at 40% 95%, rgba(147,197,253,0.35) 0%, transparent 60%);
  animation:aurora2 25s ease-in-out infinite;
}

/* ━━━━ MOVING GRID ━━━━ */
#pd-grid {
  position:fixed; inset:0; z-index:1; pointer-events:none;
  background-image:
    linear-gradient(rgba(99,102,241,0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(99,102,241,0.07) 1px, transparent 1px);
  background-size:52px 52px;
  animation:gridFlow 10s ease-in-out infinite;
}

/* ━━━━ DIAGONAL ACCENT LINES ━━━━ */
#pd-lines {
  position:fixed; inset:0; z-index:1; pointer-events:none;
  background-image:
    repeating-linear-gradient(
      -45deg,
      transparent,
      transparent 80px,
      rgba(30,64,175,0.018) 80px,
      rgba(30,64,175,0.018) 81px
    );
  animation:waveX 12s ease-in-out infinite;
}

/* ━━━━ NAVBAR ━━━━ */
.top-navbar {
  display:flex; align-items:center; justify-content:space-between;
  background:rgba(255,255,255,0.92);
  backdrop-filter:blur(32px); -webkit-backdrop-filter:blur(32px);
  border-bottom:1px solid rgba(30,64,175,0.10);
  box-shadow:0 1px 0 rgba(255,255,255,0.8), 0 4px 32px rgba(30,64,175,0.10);
  padding:0 32px; height:68px;
  position:relative; z-index:300;
}
.top-navbar::after {
  content:''; position:absolute; bottom:0; left:0; right:0; height:2px;
  background:linear-gradient(90deg,#1E40AF,#0EA5E9,#6366F1,#8B5CF6,#0EA5E9,#1E40AF);
  background-size:300% 100%;
  animation:navbarShimmer 4s linear infinite;
}
.navbar-brand  { display:flex; align-items:center; gap:14px; }
.navbar-title  {
  font-family:'Sora',sans-serif; font-size:1.22rem; font-weight:800;
  background:linear-gradient(135deg,#1E40AF 0%,#0EA5E9 60%,#6366F1 100%);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
  letter-spacing:-.02em; line-height:1.1;
}
.navbar-sub { font-size:0.52rem; color:#94A3B8; letter-spacing:0.15em; text-transform:uppercase; }
.navbar-right { display:flex; align-items:center; gap:12px; }
.navbar-user-chip {
  display:flex; align-items:center; gap:10px;
  padding:6px 16px 6px 7px;
  background:linear-gradient(135deg,#EFF6FF,#F0F4FF);
  border:1px solid rgba(30,64,175,0.18); border-radius:40px;
  box-shadow:0 2px 8px rgba(30,64,175,0.08);
}
.navbar-avatar {
  width:32px; height:32px;
  background:linear-gradient(135deg,#1E40AF,#0EA5E9);
  border-radius:50%; display:flex; align-items:center; justify-content:center;
  font-size:.72rem; color:#fff; font-weight:800; font-family:'Sora',sans-serif;
  animation:pulseGlow 3s ease-in-out infinite;
  box-shadow:0 2px 10px rgba(30,64,175,0.32);
}
.navbar-uname { font-size:.83rem; font-weight:700; color:#1E40AF; font-family:'Sora',sans-serif; }

/* ━━━━ NAV PILLS ━━━━ */
.nav-pill > div > button,
.nav-pill-active > div > button,
.signout-pill > div > button,
.refresh-pill > div > button {
  height:36px !important; min-height:36px !important;
  border-radius:9px !important;
  font-family:'Inter',sans-serif !important;
  font-size:.82rem !important; font-weight:600 !important;
  white-space:nowrap !important; letter-spacing:.01em !important;
  padding:0 16px !important;
  transition:all .18s cubic-bezier(.4,0,.2,1) !important;
  display:flex !important; align-items:center !important;
}
.nav-pill > div > button {
  background:rgba(255,255,255,0.7) !important; color:#475569 !important;
  border:1.5px solid rgba(203,213,225,0.8) !important; box-shadow:none !important;
}
.nav-pill > div > button:hover {
  background:rgba(239,246,255,0.95) !important; color:#1E40AF !important;
  border-color:#BFDBFE !important; opacity:1 !important;
  transform:translateY(-1px) !important; box-shadow:0 4px 12px rgba(30,64,175,0.12) !important;
}
.nav-pill-active > div > button {
  background:linear-gradient(135deg,#1E40AF,#0EA5E9) !important;
  color:#fff !important; border:none !important;
  box-shadow:0 4px 16px rgba(30,64,175,0.38) !important; font-weight:700 !important;
}
.nav-pill-active > div > button:hover { opacity:.92 !important; transform:translateY(-1px) !important; }
.signout-pill > div > button {
  background:rgba(255,245,245,0.85) !important; color:#DC2626 !important;
  border:1.5px solid rgba(254,202,202,0.9) !important; box-shadow:none !important;
}
.signout-pill > div > button:hover {
  background:#FEE2E2 !important; border-color:#F87171 !important;
  color:#B91C1C !important; opacity:1 !important; transform:translateY(-1px) !important;
}
.refresh-pill > div > button {
  background:rgba(255,255,255,0.7) !important; color:#64748B !important;
  border:1.5px solid rgba(203,213,225,0.8) !important; box-shadow:none !important;
  padding:0 12px !important;
}
.refresh-pill > div > button:hover {
  background:rgba(239,246,255,0.95) !important; color:#1E40AF !important;
  border-color:#BFDBFE !important; opacity:1 !important;
}
.nav-pill > div,.nav-pill-active > div,
.signout-pill > div,.refresh-pill > div { padding:0 !important; margin:0 !important; }

/* ━━━━ MAIN CONTENT AREA ━━━━ */
.block-container {
  padding:0 2.5rem 3rem !important; max-width:100% !important;
  position:relative; z-index:10;
}

/* ━━━━ ACTION BUTTONS ━━━━ */
.block-container .stButton > button {
  background:linear-gradient(135deg,#1E40AF,#0EA5E9) !important;
  color:#fff !important; border:none !important; border-radius:11px !important;
  font-family:'Inter',sans-serif !important; font-weight:700 !important;
  font-size:.85rem !important; padding:0 22px !important;
  height:42px !important; min-height:42px !important;
  box-shadow:0 4px 16px rgba(30,64,175,0.28) !important;
  transition:all .22s cubic-bezier(.4,0,.2,1) !important;
  letter-spacing:.01em !important;
}
.block-container .stButton > button:hover {
  transform:translateY(-2px) !important;
  box-shadow:0 8px 24px rgba(30,64,175,0.42) !important; opacity:1 !important;
}
.block-container .stButton > button:active { transform:translateY(0) !important; }
.stDownloadButton > button {
  background:linear-gradient(135deg,#059669,#10B981) !important;
  color:#fff !important; border:none !important; border-radius:11px !important;
  font-family:'Inter',sans-serif !important; font-weight:700 !important;
  font-size:.85rem !important; height:42px !important; min-height:42px !important;
  box-shadow:0 4px 16px rgba(5,150,105,0.28) !important;
  transition:all .22s !important;
}
.stDownloadButton > button:hover { transform:translateY(-2px) !important; opacity:1 !important; }

/* ━━━━ GLASS CARDS ━━━━ */
.metric-row { display:flex; gap:16px; margin-bottom:1.8rem; flex-wrap:wrap; }
.metric-card {
  background:rgba(255,255,255,0.80);
  backdrop-filter:blur(20px); -webkit-backdrop-filter:blur(20px);
  border:1px solid rgba(255,255,255,0.95);
  border-radius:20px; padding:22px 24px; min-width:150px; flex:1;
  box-shadow:0 4px 24px rgba(30,64,175,0.09), inset 0 1px 0 rgba(255,255,255,0.9);
  position:relative; overflow:hidden;
  transition:transform .25s cubic-bezier(.4,0,.2,1), box-shadow .25s;
  animation:slideInUp .5s ease both;
}
.metric-card::before {
  content:''; position:absolute; top:0; left:0; right:0; height:3px;
  background:linear-gradient(90deg,#1E40AF,#0EA5E9,#6366F1,#8B5CF6,#0EA5E9,#1E40AF);
  background-size:400% 100%; animation:shimmer 4s linear infinite;
}
.metric-card::after {
  content:''; position:absolute; inset:0; border-radius:20px;
  background:radial-gradient(ellipse 80% 60% at 50% 0%, rgba(147,197,253,0.15) 0%, transparent 70%);
  pointer-events:none;
}
.metric-card:hover {
  transform:translateY(-5px) scale(1.01);
  box-shadow:0 16px 40px rgba(30,64,175,0.18), inset 0 1px 0 rgba(255,255,255,0.9);
  border-color:rgba(191,219,254,0.8);
}
.mc-label { font-size:.60rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:#94A3B8; margin-bottom:10px; }
.mc-value {
  font-size:1.75rem; font-weight:800; font-family:'Sora',sans-serif; line-height:1;
  background:linear-gradient(135deg,#1E40AF,#0EA5E9);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
}
.mc-sub { font-size:.68rem; color:#CBD5E1; margin-top:6px; font-weight:500; }

/* ━━━━ SECTION CARDS ━━━━ */
.section-card {
  background:rgba(255,255,255,0.80);
  backdrop-filter:blur(20px); -webkit-backdrop-filter:blur(20px);
  border:1px solid rgba(255,255,255,0.95); border-radius:20px;
  padding:24px 26px 26px; margin-bottom:1.4rem;
  box-shadow:0 4px 24px rgba(30,64,175,0.08), inset 0 1px 0 rgba(255,255,255,0.9);
  animation:slideInUp .45s ease both;
  transition:box-shadow .25s;
}
.section-card:hover { box-shadow:0 8px 32px rgba(30,64,175,0.13), inset 0 1px 0 rgba(255,255,255,0.9); }
.section-label {
  font-size:.62rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase;
  color:#94A3B8; margin-bottom:16px; padding-bottom:12px;
  border-bottom:1px solid rgba(241,245,249,1);
  display:flex; align-items:center; gap:8px;
}

/* ━━━━ PAGE HEADER ━━━━ */
.page-header {
  display:flex; align-items:center; gap:16px;
  margin-bottom:1.8rem; padding-bottom:1.2rem;
  border-bottom:1px solid rgba(30,64,175,0.08);
  animation:fadeIn .4s ease both;
}
.ph-icon {
  width:52px; height:52px;
  background:linear-gradient(135deg,#1E40AF,#0EA5E9);
  border-radius:16px; display:flex; align-items:center; justify-content:center;
  font-size:1.4rem; flex-shrink:0;
  box-shadow:0 6px 20px rgba(30,64,175,0.32);
  transition:transform .2s; cursor:default;
}
.ph-icon:hover { transform:rotate(-8deg) scale(1.08); }
.ph-title { font-size:1.5rem !important; margin:0 !important; font-family:'Sora',sans-serif !important; font-weight:800 !important; color:#0F172A !important; }
.ph-sub   { margin:0; color:#64748B; font-size:.80rem; margin-top:4px; font-weight:400; }

/* ━━━━ INPUTS ━━━━ */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div {
  border-radius:11px !important; border:1.5px solid #E2E8F0 !important;
  font-family:'Inter',sans-serif !important; font-size:.88rem !important;
  background:rgba(255,255,255,0.92) !important; color:#0F172A !important;
  transition:all .18s !important;
}
.stTextInput > div > div > input:focus {
  border-color:#1E40AF !important; background:#fff !important;
  box-shadow:0 0 0 3px rgba(30,64,175,0.12) !important;
}
label, .stTextInput label, .stSelectbox label, .stNumberInput label, .stFileUploader label {
  color:#374151 !important; font-weight:600 !important; font-size:.82rem !important;
}
[data-testid="stFileUploader"] {
  border:2px dashed #BFDBFE !important; border-radius:16px !important;
  background:rgba(239,246,255,0.70) !important;
  transition:all .2s !important;
}
[data-testid="stFileUploader"]:hover {
  border-color:#93C5FD !important; background:rgba(219,234,254,0.50) !important;
}
[data-testid="stDataFrame"],[data-testid="stDataEditor"] {
  border-radius:14px !important; overflow:hidden !important;
  border:1px solid #E2E8F0 !important;
}

/* ━━━━ BADGES ━━━━ */
.badge { display:inline-block; padding:4px 12px; border-radius:20px; font-size:.67rem; font-weight:700; letter-spacing:.05em; margin:2px; transition:transform .15s; cursor:default; }
.badge:hover { transform:scale(1.06); }
.badge-blue  { background:#EFF6FF; color:#1E40AF; border:1px solid #BFDBFE; }
.badge-green { background:#ECFDF5; color:#059669; border:1px solid #A7F3D0; }
.badge-red   { background:#FEF2F2; color:#DC2626; border:1px solid #FECACA; }
.part-col-label { font-size:.63rem; font-weight:700; letter-spacing:.10em; text-transform:uppercase; color:#64748B; padding-left:2px; }

/* ━━━━ LOGIN ━━━━ */
.login-card {
  background:#fff; border-radius:28px; overflow:hidden; width:100%; max-width:430px;
  box-shadow:0 32px 80px rgba(30,64,175,0.22), 0 0 0 1px rgba(255,255,255,0.9);
  animation:slideInUp .65s cubic-bezier(.34,1.56,.64,1) both;
}
.login-hdr {
  background:linear-gradient(145deg,#1a3799 0%,#1E40AF 40%,#0EA5E9 75%,#38BDF8 100%);
  padding:48px 40px 44px; text-align:center; position:relative; overflow:hidden;
}
.login-hdr::before {
  content:''; position:absolute; width:300px; height:300px; border-radius:50%;
  background:rgba(255,255,255,0.06); top:-100px; right:-100px;
  animation:rotateRing 18s linear infinite;
}
.login-hdr::after {
  content:''; position:absolute; width:220px; height:220px; border-radius:50%;
  background:rgba(255,255,255,0.05); bottom:-80px; left:-70px;
  animation:rotateRing 25s linear infinite reverse;
}
.login-logo-wrap {
  width:100px; height:100px; margin:0 auto 22px;
  background:rgba(255,255,255,0.18); border:2px solid rgba(255,255,255,0.38);
  border-radius:26px; display:flex; align-items:center; justify-content:center;
  position:relative; z-index:1;
  box-shadow:0 16px 40px rgba(0,0,0,0.18), inset 0 1px 0 rgba(255,255,255,0.3);
  backdrop-filter:blur(10px); transition:transform .3s;
}
.login-logo-wrap:hover { transform:scale(1.06) rotate(-3deg); }
.login-name {
  font-family:'Sora',sans-serif; font-size:2.1rem; font-weight:800;
  color:#fff; margin-bottom:6px; letter-spacing:-.02em; position:relative; z-index:1;
  text-shadow:0 2px 20px rgba(0,0,0,0.15);
}
.login-tag {
  color:rgba(255,255,255,0.72); font-size:.64rem;
  letter-spacing:.20em; text-transform:uppercase; position:relative; z-index:1;
}
.login-body { padding:38px 38px 42px; background:#fff; }
.login-hi   { font-family:'Sora',sans-serif; font-size:1.25rem; font-weight:700; color:#0F172A; margin-bottom:5px; }
.login-sub  { color:#94A3B8; font-size:.80rem; margin-bottom:30px; }
.login-divider {
  height:1px; background:linear-gradient(90deg,transparent,#E2E8F0,transparent); margin-bottom:26px;
}
.login-body .stTextInput label {
  font-size:.70rem !important; font-weight:700 !important; color:#374151 !important;
  letter-spacing:.08em !important; text-transform:uppercase !important;
}
.login-body .stTextInput > div > div > input {
  border-radius:12px !important; border:1.5px solid #E5E7EB !important;
  background:#F8FAFC !important; color:#111827 !important;
  font-size:.93rem !important; height:50px !important; padding:0 16px !important;
  transition:all .20s !important;
}
.login-body .stTextInput > div > div > input:focus {
  border-color:#1E40AF !important; background:#fff !important;
  box-shadow:0 0 0 4px rgba(30,64,175,0.12) !important;
}
.login-body .stButton > button {
  background:linear-gradient(135deg,#1E40AF,#0EA5E9) !important;
  color:#fff !important; border:none !important; border-radius:14px !important;
  height:54px !important; font-size:1rem !important; font-weight:700 !important;
  letter-spacing:.04em !important; box-shadow:0 8px 28px rgba(30,64,175,0.42) !important;
  transition:all .22s cubic-bezier(.4,0,.2,1) !important; margin-top:12px !important;
}
.login-body .stButton > button:hover {
  transform:translateY(-3px) !important; opacity:1 !important;
  box-shadow:0 14px 36px rgba(30,64,175,0.52) !important;
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
    st.markdown('''
<div id="pd-grid"></div><div id="pd-lines"></div>
<div id="pd-particles"></div>
<script>
(function(){
  var c=document.getElementById("pd-particles");
  if(!c)return;
  c.style.cssText="position:fixed;inset:0;z-index:2;pointer-events:none;overflow:hidden;";
  var cols=["rgba(30,64,175,.18)","rgba(14,165,233,.24)","rgba(99,102,241,.18)",
            "rgba(167,243,208,.30)","rgba(196,181,253,.26)","rgba(254,215,170,.28)"];
  for(var i=0;i<45;i++){
    var p=document.createElement("div");
    var sz=Math.random()*6+1.5, lf=Math.random()*100, bt=Math.random()*25;
    var dr=Math.random()*22+12, dl=Math.random()*22;
    var cl=cols[Math.floor(Math.random()*cols.length)];
    p.style.cssText="position:absolute;width:"+sz+"px;height:"+sz+"px;border-radius:50%;"+
      "background:"+cl+";box-shadow:0 0 "+(sz*3)+"px "+cl+";"+
      "left:"+lf+"%;bottom:"+bt+"%;animation:floatUp "+dr+"s "+dl+"s linear infinite";
    c.appendChild(p);
  }
})();
</script>
''', unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 1.05, 1])
    with mid:
        st.markdown('''
        <div class="login-card">
          <div class="login-hdr">
            <div class="login-logo-wrap">
              <img src="https://raw.githubusercontent.com/sales369/price-fetching/main/logo.png"
                   style="width:72px;height:auto;object-fit:contain;" alt="FIAPL" />
            </div>
            <div class="login-name">PriceDesk</div>
            <div class="login-tag">Parts Pricing Platform &nbsp;·&nbsp; FIAPL</div>
          </div>
          <div class="login-body">
            <div class="login-hi">Welcome back 👋</div>
            <div class="login-sub">Sign in to continue to your workspace</div>
            <div class="login-divider"></div>
        ''', unsafe_allow_html=True)
        u_in = st.text_input("USERNAME", placeholder="Enter your username", key="li_u")
        p_in = st.text_input("PASSWORD", type="password", placeholder="Enter your password", key="li_p")
        if st.button("Sign In  →", use_container_width=True):
            if check_login(u_in, p_in):
                st.session_state.user = {"username": u_in}
                st.rerun()
            else:
                st.error("Invalid username or password.")
        st.markdown("</div></div>", unsafe_allow_html=True)
    st.stop()




# inject live background for main app
st.markdown('''<div id="pd-grid"></div><div id="pd-lines"></div><div id="pd-particles"></div>
<script>
(function(){
  if(window._pdParticlesDone)return; window._pdParticlesDone=true;
  var c=document.getElementById("pd-particles");
  if(!c)return;
  c.style.cssText="position:fixed;inset:0;z-index:2;pointer-events:none;overflow:hidden;";
  var cols=["rgba(30,64,175,.16)","rgba(14,165,233,.20)","rgba(99,102,241,.16)",
            "rgba(167,243,208,.26)","rgba(196,181,253,.22)","rgba(254,215,170,.24)"];
  for(var i=0;i<38;i++){
    var p=document.createElement("div");
    var sz=Math.random()*5+1.5,lf=Math.random()*100,bt=Math.random()*20;
    var dr=Math.random()*20+13,dl=Math.random()*20;
    var cl=cols[Math.floor(Math.random()*cols.length)];
    p.style.cssText="position:absolute;width:"+sz+"px;height:"+sz+"px;border-radius:50%;"+
      "background:"+cl+";box-shadow:0 0 "+(sz*3)+"px "+cl+";"+
      "left:"+lf+"%;bottom:"+bt+"%;animation:floatUp "+dr+"s "+dl+"s linear infinite";
    c.appendChild(p);
  }
})();
</script>''', unsafe_allow_html=True)

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

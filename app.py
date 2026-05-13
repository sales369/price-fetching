import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from psycopg2.pool import SimpleConnectionPool
import json
from io import BytesIO
import os
import re
import time

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

/* ━━━ KEYFRAMES ━━━ */
@keyframes aurora1{0%{transform:translate(0,0) scale(1)}30%{transform:translate(90px,-70px) scale(1.12)}65%{transform:translate(-60px,80px) scale(0.91)}100%{transform:translate(0,0) scale(1)}}
@keyframes aurora2{0%{transform:translate(0,0) scale(1.06)}35%{transform:translate(-90px,60px) scale(0.88)}70%{transform:translate(70px,-80px) scale(1.14)}100%{transform:translate(0,0) scale(1.06)}}
@keyframes aurora3{0%{transform:translate(0,0) scale(0.96)}50%{transform:translate(55px,65px) scale(1.10)}100%{transform:translate(0,0) scale(0.96)}}
@keyframes gridFlow{0%{background-position:0 0;opacity:.18}50%{background-position:26px 26px;opacity:.34}100%{background-position:0 0;opacity:.18}}
@keyframes diagFlow{0%{background-position:0 0;opacity:.6}100%{background-position:200px 200px;opacity:.6}}
@keyframes floatUp{0%{transform:translateY(0) translateX(0) scale(1);opacity:0}8%{opacity:.85}50%{transform:translateY(-85px) translateX(18px) scale(1.25)}90%{opacity:.5}100%{transform:translateY(-180px) translateX(-12px) scale(.7);opacity:0}}
@keyframes shimmerBar{0%{background-position:-400% center}100%{background-position:400% center}}
@keyframes navLine{0%{background-position:-200% center}100%{background-position:200% center}}
@keyframes slideUp{from{opacity:0;transform:translateY(22px)}to{opacity:1;transform:translateY(0)}}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
@keyframes pulseRing{0%,100%{box-shadow:0 0 0 0 rgba(30,64,175,.30)}50%{box-shadow:0 0 0 9px rgba(30,64,175,0)}}
@keyframes spinSlow{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
@keyframes btnShimmer{0%{background-position:-200% center}100%{background-position:200% center}}
@keyframes badgePop{0%{transform:scale(1)}50%{transform:scale(1.12)}100%{transform:scale(1)}}
@keyframes cardHover{from{transform:translateY(0) scale(1)}to{transform:translateY(-5px) scale(1.015)}}

/* ━━━ RESET ━━━ */
#MainMenu,footer,header{visibility:hidden}
*,*::before,*::after{box-sizing:border-box}
section[data-testid="stSidebar"],[data-testid="collapsedControl"],[data-testid="stSidebarCollapseButton"]{display:none!important}

/* ━━━ ZOOM-OUT VIEWPORT SCALE ━━━ */
html{font-size:14px}
body{zoom:0.92}

/* ━━━ APP BASE ━━━ */
.stApp{
  font-family:'Inter',sans-serif;
  color:#0F172A;
  background:#e4eeff!important;
  min-height:100vh;
  position:relative;
  overflow-x:hidden;
}

/* ━━━ AURORA LAYER 1 ━━━ */
.stApp::before{
  content:'';position:fixed;inset:0;z-index:0;pointer-events:none;
  background:
    radial-gradient(ellipse 1200px 900px at  4%  8%, rgba(147,197,253,.68) 0%,transparent 62%),
    radial-gradient(ellipse  950px 800px at 94% 88%, rgba(196,181,253,.58) 0%,transparent 62%),
    radial-gradient(ellipse  800px 650px at 52% 52%, rgba(125,211,252,.42) 0%,transparent 62%),
    linear-gradient(148deg,#dbeafe 0%,#ede9fe 40%,#e0f2fe 72%,#fce7f3 100%);
  animation:aurora1 20s ease-in-out infinite;
}

/* ━━━ AURORA LAYER 2 ━━━ */
.stApp::after{
  content:'';position:fixed;inset:0;z-index:0;pointer-events:none;
  background:
    radial-gradient(ellipse 800px 650px at 84%  6%, rgba(167,243,208,.48) 0%,transparent 60%),
    radial-gradient(ellipse 720px 580px at  8% 90%, rgba(254,215,170,.44) 0%,transparent 60%),
    radial-gradient(ellipse 600px 480px at 38% 98%, rgba(147,197,253,.38) 0%,transparent 60%);
  animation:aurora2 28s ease-in-out infinite;
}

/* ━━━ MOVING GRID ━━━ */
#pd-grid{
  position:fixed;inset:0;z-index:1;pointer-events:none;
  background-image:
    linear-gradient(rgba(99,102,241,.07) 1px,transparent 1px),
    linear-gradient(90deg,rgba(99,102,241,.07) 1px,transparent 1px);
  background-size:52px 52px;
  animation:gridFlow 12s ease-in-out infinite;
}

/* ━━━ DIAGONAL LINES ━━━ */
#pd-diag{
  position:fixed;inset:0;z-index:1;pointer-events:none;
  background-image:repeating-linear-gradient(
    -55deg,transparent,transparent 90px,
    rgba(30,64,175,.015) 90px,rgba(30,64,175,.015) 91px
  );
  animation:diagFlow 30s linear infinite;
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   NAVBAR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
.top-navbar{
  display:flex;align-items:center;justify-content:space-between;
  background:rgba(255,255,255,.95);
  backdrop-filter:blur(32px);-webkit-backdrop-filter:blur(32px);
  border-bottom:1px solid rgba(30,64,175,.08);
  box-shadow:0 1px 0 rgba(255,255,255,.8),0 4px 28px rgba(30,64,175,.10);
  padding:0 28px;height:64px;
  position:relative;z-index:300;
}
.top-navbar::after{
  content:'';position:absolute;bottom:0;left:0;right:0;height:2.5px;
  background:linear-gradient(90deg,#1E40AF,#0EA5E9,#6366F1,#8B5CF6,#EC4899,#0EA5E9,#1E40AF);
  background-size:300% 100%;
  animation:navLine 5s linear infinite;
}
.navbar-brand{display:flex;align-items:center;gap:12px}
.navbar-title{
  font-family:'Sora',sans-serif;font-size:1.15rem;font-weight:800;
  background:linear-gradient(135deg,#1E40AF,#0EA5E9,#6366F1);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
  letter-spacing:-.02em;line-height:1.1;
}
.navbar-sub{font-size:.52rem;color:#94A3B8;letter-spacing:.14em;text-transform:uppercase}
.navbar-user-chip{
  display:flex;align-items:center;gap:10px;
  padding:6px 16px 6px 7px;
  background:linear-gradient(135deg,#EFF6FF,#F0F4FF);
  border:1px solid rgba(30,64,175,.18);border-radius:40px;
  box-shadow:0 2px 8px rgba(30,64,175,.08);
  transition:transform .2s,box-shadow .2s;cursor:default;
}
.navbar-user-chip:hover{transform:scale(1.03);box-shadow:0 4px 14px rgba(30,64,175,.14)}
.navbar-avatar{
  width:30px;height:30px;
  background:linear-gradient(135deg,#1E40AF,#0EA5E9);
  border-radius:50%;display:flex;align-items:center;justify-content:center;
  font-size:.70rem;color:#fff;font-weight:800;font-family:'Sora',sans-serif;
  animation:pulseRing 3.5s ease-in-out infinite;
  box-shadow:0 2px 10px rgba(30,64,175,.32);
}
.navbar-uname{font-size:.82rem;font-weight:700;color:#1E40AF;font-family:'Sora',sans-serif}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   NAV PILLS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
.nav-pill > div > button,
.nav-pill-active > div > button,
.signout-pill > div > button,
.refresh-pill > div > button {
  height:36px!important;min-height:36px!important;
  border-radius:10px!important;
  font-family:'Inter',sans-serif!important;
  font-size:.82rem!important;font-weight:600!important;
  white-space:nowrap!important;letter-spacing:.01em!important;
  padding:0 16px!important;
  transition:all .20s cubic-bezier(.4,0,.2,1)!important;
  display:flex!important;align-items:center!important;
  position:relative!important;overflow:hidden!important;
}
.nav-pill > div > button::after,
.nav-pill-active > div > button::after,
.signout-pill > div > button::after,
.refresh-pill > div > button::after {
  content:'';position:absolute;inset:0;
  background:linear-gradient(90deg,transparent 0%,rgba(255,255,255,.3) 50%,transparent 100%);
  background-size:200% 100%;background-position:-200% center;
  transition:background-position .5s ease;border-radius:10px;
}
.nav-pill > div > button:hover::after,
.nav-pill-active > div > button:hover::after { background-position:200% center; }

.nav-pill > div > button{
  background:rgba(255,255,255,.75)!important;color:#475569!important;
  border:1.5px solid rgba(203,213,225,.9)!important;box-shadow:none!important;
}
.nav-pill > div > button:hover{
  background:rgba(239,246,255,.95)!important;color:#1E40AF!important;
  border-color:#93C5FD!important;opacity:1!important;
  transform:translateY(-2px)!important;
  box-shadow:0 6px 16px rgba(30,64,175,.15)!important;
}
.nav-pill-active > div > button{
  background:linear-gradient(135deg,#1E40AF,#0EA5E9)!important;
  color:#fff!important;border:none!important;
  box-shadow:0 4px 18px rgba(30,64,175,.40)!important;font-weight:700!important;
}
.nav-pill-active > div > button:hover{
  opacity:1!important;transform:translateY(-2px)!important;
  box-shadow:0 8px 24px rgba(30,64,175,.50)!important;
}
.signout-pill > div > button{
  background:rgba(255,245,245,.85)!important;color:#DC2626!important;
  border:1.5px solid rgba(254,202,202,.9)!important;box-shadow:none!important;
}
.signout-pill > div > button:hover{
  background:#FEE2E2!important;border-color:#F87171!important;
  color:#B91C1C!important;opacity:1!important;
  transform:translateY(-2px)!important;box-shadow:0 6px 14px rgba(220,38,38,.20)!important;
}
.refresh-pill > div > button{
  background:rgba(255,255,255,.75)!important;color:#64748B!important;
  border:1.5px solid rgba(203,213,225,.9)!important;box-shadow:none!important;
  padding:0 12px!important;
}
.refresh-pill > div > button:hover{
  background:rgba(239,246,255,.95)!important;color:#1E40AF!important;
  border-color:#93C5FD!important;opacity:1!important;
  transform:translateY(-2px)!important;box-shadow:0 6px 16px rgba(30,64,175,.15)!important;
}
.nav-pill>div,.nav-pill-active>div,
.signout-pill>div,.refresh-pill>div{padding:0!important;margin:0!important}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   MAIN CONTENT BUTTONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
.block-container{
  padding:0 2.5rem 3rem!important;max-width:100%!important;
  position:relative;z-index:10;
}
.block-container .stButton > button{
  background:linear-gradient(135deg,#1E40AF 0%,#2563EB 40%,#0EA5E9 100%)!important;
  background-size:200% 100%!important;
  color:#fff!important;border:none!important;
  border-radius:12px!important;
  font-family:'Inter',sans-serif!important;font-weight:700!important;
  font-size:.86rem!important;padding:0 22px!important;
  height:42px!important;min-height:42px!important;
  box-shadow:0 4px 16px rgba(30,64,175,.30),inset 0 1px 0 rgba(255,255,255,.20)!important;
  transition:all .22s cubic-bezier(.4,0,.2,1)!important;
  letter-spacing:.02em!important;
  position:relative!important;overflow:hidden!important;
}
.block-container .stButton > button::before{
  content:'';position:absolute;inset:0;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,.18),transparent);
  background-size:200% 100%;background-position:-200% center;
  transition:background-position .55s ease;
}
.block-container .stButton > button:hover{
  transform:translateY(-3px) scale(1.02)!important;
  box-shadow:0 10px 28px rgba(30,64,175,.42),inset 0 1px 0 rgba(255,255,255,.20)!important;
  opacity:1!important;
}
.block-container .stButton > button:hover::before{ background-position:200% center; }
.block-container .stButton > button:active{
  transform:translateY(-1px) scale(1.00)!important;
  box-shadow:0 4px 14px rgba(30,64,175,.30)!important;
}
.stDownloadButton > button{
  background:linear-gradient(135deg,#059669,#10B981,#34D399)!important;
  background-size:200% 100%!important;
  color:#fff!important;border:none!important;border-radius:12px!important;
  font-family:'Inter',sans-serif!important;font-weight:700!important;
  font-size:.86rem!important;height:42px!important;min-height:42px!important;
  box-shadow:0 4px 16px rgba(5,150,105,.30),inset 0 1px 0 rgba(255,255,255,.18)!important;
  transition:all .22s!important;position:relative!important;overflow:hidden!important;
}
.stDownloadButton > button:hover{
  transform:translateY(-3px) scale(1.02)!important;
  box-shadow:0 10px 28px rgba(5,150,105,.42)!important;opacity:1!important;
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   GLASS CARDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
.metric-row{display:flex;gap:16px;margin-bottom:1.8rem;flex-wrap:wrap}
.metric-card{
  background:rgba(255,255,255,.78);
  backdrop-filter:blur(22px);-webkit-backdrop-filter:blur(22px);
  border:1px solid rgba(255,255,255,.96);border-radius:20px;
  padding:22px 24px;min-width:150px;flex:1;
  box-shadow:0 4px 24px rgba(30,64,175,.09),inset 0 1px 0 rgba(255,255,255,.9);
  position:relative;overflow:hidden;
  transition:transform .25s cubic-bezier(.4,0,.2,1),box-shadow .25s,border-color .25s;
  animation:slideUp .5s ease both;
}
.metric-card::before{
  content:'';position:absolute;top:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,#1E40AF,#0EA5E9,#6366F1,#8B5CF6,#EC4899,#0EA5E9,#1E40AF);
  background-size:400% 100%;animation:shimmerBar 4.5s linear infinite;
}
.metric-card::after{
  content:'';position:absolute;inset:0;border-radius:20px;
  background:radial-gradient(ellipse 70% 50% at 50% -10%,rgba(147,197,253,.18) 0%,transparent 70%);
  pointer-events:none;
}
.metric-card:hover{
  transform:translateY(-6px) scale(1.02);
  box-shadow:0 18px 44px rgba(30,64,175,.18),inset 0 1px 0 rgba(255,255,255,.9);
  border-color:rgba(147,197,253,.7);
}
.mc-label{font-size:.59rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#94A3B8;margin-bottom:10px}
.mc-value{
  font-size:1.75rem;font-weight:800;font-family:'Sora',sans-serif;line-height:1;
  background:linear-gradient(135deg,#1E40AF,#0EA5E9);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
}
.mc-sub{font-size:.67rem;color:#CBD5E1;margin-top:6px;font-weight:500}

.section-card{
  background:rgba(255,255,255,.78);
  backdrop-filter:blur(22px);-webkit-backdrop-filter:blur(22px);
  border:1px solid rgba(255,255,255,.96);border-radius:20px;
  padding:24px 26px 26px;margin-bottom:1.4rem;
  box-shadow:0 4px 24px rgba(30,64,175,.08),inset 0 1px 0 rgba(255,255,255,.9);
  animation:slideUp .45s ease both;
  transition:box-shadow .25s,border-color .25s;
}
.section-card:hover{
  box-shadow:0 8px 32px rgba(30,64,175,.13),inset 0 1px 0 rgba(255,255,255,.9);
  border-color:rgba(191,219,254,.6);
}
.section-label{
  font-size:.61rem;font-weight:700;letter-spacing:.15em;text-transform:uppercase;
  color:#94A3B8;margin-bottom:16px;padding-bottom:12px;
  border-bottom:1px solid rgba(241,245,249,1);
}

/* ━━━ PAGE HEADER ━━━ */
.page-header{
  display:flex;align-items:center;gap:16px;
  margin-bottom:1.8rem;padding-bottom:1.2rem;
  border-bottom:1px solid rgba(30,64,175,.08);
  animation:fadeIn .4s ease both;
}
.ph-icon{
  width:50px;height:50px;
  background:linear-gradient(135deg,#1E40AF,#0EA5E9);
  border-radius:15px;display:flex;align-items:center;justify-content:center;
  font-size:1.35rem;flex-shrink:0;
  box-shadow:0 6px 20px rgba(30,64,175,.32);
  transition:transform .25s cubic-bezier(.34,1.56,.64,1),box-shadow .25s;cursor:default;
}
.ph-icon:hover{transform:rotate(-10deg) scale(1.12);box-shadow:0 10px 28px rgba(30,64,175,.44)}
.ph-title{font-size:1.45rem!important;margin:0!important;font-family:'Sora',sans-serif!important;font-weight:800!important;color:#0F172A!important}
.ph-sub{margin:0;color:#64748B;font-size:.79rem;margin-top:4px}

/* ━━━ INPUTS ━━━ */
.stTextInput>div>div>input,
.stNumberInput>div>div>input,
.stSelectbox>div>div{
  border-radius:11px!important;border:1.5px solid #E2E8F0!important;
  font-family:'Inter',sans-serif!important;font-size:.88rem!important;
  background:rgba(255,255,255,.92)!important;color:#0F172A!important;
  transition:all .18s!important;
}
.stTextInput>div>div>input:focus{
  border-color:#1E40AF!important;background:#fff!important;
  box-shadow:0 0 0 3px rgba(30,64,175,.12)!important;
}
label,.stTextInput label,.stSelectbox label,.stNumberInput label,.stFileUploader label{
  color:#374151!important;font-weight:600!important;font-size:.82rem!important;
}
[data-testid="stFileUploader"]{
  border:2px dashed #BFDBFE!important;border-radius:16px!important;
  background:rgba(239,246,255,.70)!important;transition:all .2s!important;
}
[data-testid="stFileUploader"]:hover{
  border-color:#93C5FD!important;background:rgba(219,234,254,.50)!important;
}
[data-testid="stDataFrame"],[data-testid="stDataEditor"]{
  border-radius:14px!important;overflow:hidden!important;border:1px solid #E2E8F0!important;
}

/* ━━━ BADGES ━━━ */
.badge{
  display:inline-block;padding:4px 12px;border-radius:20px;
  font-size:.66rem;font-weight:700;letter-spacing:.05em;margin:2px;
  transition:transform .18s,box-shadow .18s;cursor:default;
}
.badge:hover{transform:scale(1.08) translateY(-1px);box-shadow:0 4px 10px rgba(0,0,0,.10)}
.badge-blue{background:#EFF6FF;color:#1E40AF;border:1px solid #BFDBFE}
.badge-green{background:#ECFDF5;color:#059669;border:1px solid #A7F3D0}
.badge-red{background:#FEF2F2;color:#DC2626;border:1px solid #FECACA}
.badge-purple{background:#F5F3FF;color:#7C3AED;border:1px solid #DDD6FE}
.part-col-label{font-size:.62rem;font-weight:700;letter-spacing:.10em;text-transform:uppercase;color:#64748B;padding-left:2px}

/* ━━━ FORMAT TABS (upload page) ━━━ */
.format-tab-row{display:flex;gap:10px;margin-bottom:18px}
.format-tab{
  flex:1;padding:14px 16px;border-radius:14px;cursor:pointer;
  border:2px solid #E2E8F0;background:rgba(255,255,255,.7);
  transition:all .18s;text-align:center;
}
.format-tab.active{
  border-color:#1E40AF;background:linear-gradient(135deg,#EFF6FF,#F0F4FF);
  box-shadow:0 4px 14px rgba(30,64,175,.12);
}
.format-tab-title{font-size:.82rem;font-weight:700;color:#0F172A;margin-bottom:3px}
.format-tab-sub{font-size:.70rem;color:#94A3B8}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   LOGIN CARD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
.login-card{
  background:#fff;border-radius:28px;overflow:hidden;
  width:100%;max-width:430px;
  box-shadow:0 36px 90px rgba(30,64,175,.24),0 0 0 1px rgba(255,255,255,.9);
  animation:slideUp .7s cubic-bezier(.34,1.56,.64,1) both;
}
.login-hdr{
  background:linear-gradient(148deg,#1a3799 0%,#1E40AF 38%,#0EA5E9 72%,#38BDF8 100%);
  padding:50px 40px 46px;text-align:center;position:relative;overflow:hidden;
}
.login-hdr::before{
  content:'';position:absolute;width:320px;height:320px;border-radius:50%;
  background:rgba(255,255,255,.055);top:-110px;right:-110px;
  animation:spinSlow 22s linear infinite;
}
.login-hdr::after{
  content:'';position:absolute;width:240px;height:240px;border-radius:50%;
  background:rgba(255,255,255,.045);bottom:-90px;left:-80px;
  animation:spinSlow 30s linear infinite reverse;
}
.login-logo-wrap{
  width:104px;height:104px;margin:0 auto 24px;
  background:rgba(255,255,255,.18);border:2px solid rgba(255,255,255,.38);
  border-radius:28px;display:flex;align-items:center;justify-content:center;
  position:relative;z-index:1;
  box-shadow:0 18px 44px rgba(0,0,0,.18),inset 0 1px 0 rgba(255,255,255,.28);
  backdrop-filter:blur(10px);
  transition:transform .32s cubic-bezier(.34,1.56,.64,1),box-shadow .3s;
}
.login-logo-wrap:hover{transform:scale(1.08) rotate(-4deg);box-shadow:0 24px 54px rgba(0,0,0,.24),inset 0 1px 0 rgba(255,255,255,.28)}
.login-name{
  font-family:'Sora',sans-serif;font-size:2.2rem;font-weight:800;
  color:#fff;margin-bottom:6px;letter-spacing:-.025em;
  position:relative;z-index:1;text-shadow:0 2px 20px rgba(0,0,0,.14);
}
.login-tag{
  color:rgba(255,255,255,.70);font-size:.63rem;
  letter-spacing:.22em;text-transform:uppercase;position:relative;z-index:1;
}
.login-body{padding:40px 40px 44px;background:#fff}
.login-hi{font-family:'Sora',sans-serif;font-size:1.28rem;font-weight:700;color:#0F172A;margin-bottom:5px}
.login-sub{color:#94A3B8;font-size:.80rem;margin-bottom:30px}
.login-divider{height:1px;background:linear-gradient(90deg,transparent,#E2E8F0,transparent);margin-bottom:28px}
.login-body .stTextInput label{
  font-size:.70rem!important;font-weight:700!important;color:#374151!important;
  letter-spacing:.08em!important;text-transform:uppercase!important;
}
.login-body .stTextInput>div>div>input{
  border-radius:13px!important;border:1.5px solid #E5E7EB!important;
  background:#F8FAFC!important;color:#111827!important;
  font-size:.93rem!important;height:52px!important;padding:0 18px!important;
  transition:all .20s!important;
}
.login-body .stTextInput>div>div>input:focus{
  border-color:#1E40AF!important;background:#fff!important;
  box-shadow:0 0 0 4px rgba(30,64,175,.12)!important;
}
.login-body .stButton>button{
  background:linear-gradient(135deg,#1E40AF 0%,#2563EB 45%,#0EA5E9 100%)!important;
  background-size:200% 100%!important;
  color:#fff!important;border:none!important;border-radius:14px!important;
  height:56px!important;font-size:1.02rem!important;font-weight:700!important;
  letter-spacing:.04em!important;
  box-shadow:0 8px 28px rgba(30,64,175,.42)!important;
  transition:all .24s cubic-bezier(.4,0,.2,1)!important;margin-top:14px!important;
  position:relative!important;overflow:hidden!important;
}
.login-body .stButton>button::before{
  content:'';position:absolute;inset:0;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,.22),transparent);
  background-size:200% 100%;background-position:-200% center;
  transition:background-position .55s ease;
}
.login-body .stButton>button:hover{
  transform:translateY(-3px)!important;opacity:1!important;
  box-shadow:0 16px 40px rgba(30,64,175,.52)!important;
}
.login-body .stButton>button:hover::before{background-position:200% center}
.login-body .stButton>button:active{transform:translateY(0)!important}
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
            if not brand: continue
            
            # UPDATED: Logical switch for Brand-only vs Part+Brand
            if part:
                cur.execute("""
                    SELECT part_no, supplier, price, currency, delivery_time FROM parts_table
                    WHERE TRIM(LOWER(part_no))=TRIM(LOWER(%s)) AND TRIM(LOWER(brand))=TRIM(LOWER(%s))
                    ORDER BY price ASC
                """, (part,brand))
            else:
                cur.execute("""
                    SELECT part_no, supplier, price, currency, delivery_time FROM parts_table
                    WHERE TRIM(LOWER(brand))=TRIM(LOWER(%s))
                    ORDER BY part_no ASC, price ASC
                """, (brand,))
                
            rows=cur.fetchall()
            if rows:
                for db_part, supplier,price,currency,delivery_time in rows:
                    results.append({
                        "Brand": brand,
                        "Part No": db_part, # Use actual part number from DB
                        "Supplier": supplier,
                        "Currency": currency or "",
                        "Delivery Time": delivery_time or "",
                        "Qty": qty,
                        "Unit Price": float(price),
                        "Amount": qty * float(price)
                    })
            else:
                # Handle Not Found Case
                results.append({
                    "Brand": brand,
                    "Part No": part if part else "N/A",
                    "Supplier": "Not Found",
                    "Currency": "",
                    "Delivery Time": "",
                    "Qty": qty,
                    "Unit Price": 0.0,
                    "Amount": 0.0
                })
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
#  ★ COLUMN & BRAND NORMALISATION
# ─────────────────────────────────────────────
COLUMN_ALIASES = {
    "brand": [
        "make", "brand", "manufacturer",
        "makebrand", "brandmake", "brandorname",
        "brandormodel", "brandbymake",
    ],
    "part_no": [
        "partnumber", "partno", "part", "partnum",
        "partnumbers", "itemcode", "itemno",
    ],
    "price": [
        "jpyprice", "price", "unitprice", "jpy",
        "jprice", "unitrate", "rate", "cost",
    ],
    "supplier": [
        "supplier", "vendor", "source",
        "suppliername", "vendorname",
    ],
    "currency": ["currency", "cur", "ccy"],
    "delivery_time": [
        "deliverytime", "delivery", "leadtime",
        "deliverydays", "lead", "leadtimedelivery",
    ],
}

# Add any new brands and their misspellings here
BRAND_ALIASES = {
    "SCHNEIDER": ["schiner", "schneder", "schneider electric"],
    "SIEMENS":   ["sieman", "seimens"],
    "ABB":       ["ab b", "a b b"],
}

def normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename df columns to internal names using COLUMN_ALIASES."""
    col_map = {clean_col(c): c for c in df.columns}
    rename = {}
    for target, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in col_map:
                rename[col_map[alias]] = target
                break
    df.rename(columns=rename, inplace=True)
    return df

def normalise_brands(df: pd.DataFrame) -> pd.DataFrame:
    """Force brands to uppercase and fix known typos."""
    if "brand" not in df.columns:
        return df
    
    # 1. Force everything to UPPERCASE and remove extra spaces
    df["brand"] = df["brand"].astype(str).str.strip().str.upper()
    
    # 2. Build mapping dictionary for exact matches
    replace_dict = {}
    for true_brand, typos in BRAND_ALIASES.items():
        true_brand_upper = true_brand.upper()
        for typo in typos:
            replace_dict[typo.strip().upper()] = true_brand_upper
            
    # 3. Apply corrections
    df["brand"] = df["brand"].replace(replace_dict)
    return df


def load_upload_file(file) -> pd.DataFrame:
    """Load either .xlsx or .csv and return a raw DataFrame."""
    name = file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(file, dtype=str)
    else:
        return pd.read_excel(file, dtype=str)


# ─────────────────────────────────────────────
#  LOGIN PAGE
# ─────────────────────────────────────────────
if st.session_state.user is None:
    st.markdown('''<div id="pd-grid"></div><div id="pd-diag"></div>
<div id="pd-particles"></div>
<script>
(function(){
  var c=document.getElementById("pd-particles");
  if(!c)return;
  c.style.cssText="position:fixed;inset:0;z-index:2;pointer-events:none;overflow:hidden;";
  var cols=["rgba(30,64,175,.16)","rgba(14,165,233,.22)","rgba(99,102,241,.16)",
            "rgba(167,243,208,.28)","rgba(196,181,253,.24)","rgba(254,215,170,.26)"];
  for(var i=0;i<50;i++){
    var p=document.createElement("div");
    var sz=Math.random()*7+1.5,lf=Math.random()*100,bt=Math.random()*30;
    var dr=Math.random()*24+12,dl=Math.random()*24;
    var cl=cols[Math.floor(Math.random()*cols.length)];
    p.style.cssText="position:absolute;width:"+sz+"px;height:"+sz+"px;border-radius:50%;"+
      "background:"+cl+";box-shadow:0 0 "+(sz*3)+"px "+cl+";"+
      "left:"+lf+"%;bottom:"+bt+"%;animation:floatUp "+dr+"s "+dl+"s linear infinite";
    c.appendChild(p);
  }
})();
</script>''', unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.05, 1])
    with mid:
        st.markdown('''
        <div class="login-card">
          <div class="login-hdr">
            <div class="login-logo-wrap">
              <img src="https://raw.githubusercontent.com/sales369/price-fetching/main/logo.png"
                   style="width:74px;height:auto;object-fit:contain;" alt="FIAPL" />
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


# inject live animated background elements
st.markdown('''<div id="pd-grid"></div><div id="pd-diag"></div><div id="pd-particles"></div>
<script>
(function(){
  if(window._pd)return; window._pd=true;
  var c=document.getElementById("pd-particles");
  if(!c)return;
  c.style.cssText="position:fixed;inset:0;z-index:2;pointer-events:none;overflow:hidden;";
  var cols=["rgba(30,64,175,.14)","rgba(14,165,233,.18)","rgba(99,102,241,.14)",
            "rgba(167,243,208,.24)","rgba(196,181,253,.20)","rgba(254,215,170,.22)"];
  for(var i=0;i<42;i++){
    var p=document.createElement("div");
    var sz=Math.random()*6+1.5,lf=Math.random()*100,bt=Math.random()*22;
    var dr=Math.random()*22+13,dl=Math.random()*22;
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

n_nav = len(nav_pages)
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
           <div class="ph-sub">Search specific parts or browse entire brands instantly</div></div>
    </div>""", unsafe_allow_html=True)

    brand_list = fetch_brands()

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Enter Brands or Parts to Search</div>', unsafe_allow_html=True)

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
    with h2: st.markdown('<div class="part-col-label">Part Number (Leave blank to see all)</div>', unsafe_allow_html=True)
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
            # Accept even if part number is empty to allow brand search
            if b and b!="": items.append({"brand":b,"part_no":p,"qty":q})
            
        if items:
            with st.spinner("Fetching prices…"):
                results=lookup_prices(items)
            st.session_state.table_data=pd.DataFrame(results)
        else:
            st.warning("Please select at least one Brand.")

    df = st.session_state.table_data

    if not df.empty:
        found=df[df["Supplier"]!="Not Found"]
        n_parts=int(df["Part No"].nunique()); n_suppliers=int(found["Supplier"].nunique()) if not found.empty else 0
        best_price=float(found["Unit Price"].min()) if not found.empty else 0.0; n_records=int(len(found))

        st.markdown(f"""
        <div class="metric-row">
          <div class="metric-card"><div class="mc-label">Unique Items</div><div class="mc-value">{n_parts}</div><div class="mc-sub">different part numbers</div></div>
          <div class="metric-card"><div class="mc-label">Suppliers Found</div><div class="mc-value">{n_suppliers}</div><div class="mc-sub">across selection</div></div>
          <div class="metric-card"><div class="mc-label">Best Unit Price</div><div class="mc-value">{best_price:,.0f}</div><div class="mc-sub">lowest unit price</div></div>
          <div class="metric-card"><div class="mc-label">Offer Records</div><div class="mc-value">{n_records}</div><div class="mc-sub">total supplier rows</div></div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">All Supplier Prices</div>', unsafe_allow_html=True)

        def highlight_rows(row):
            if row["Supplier"]=="Not Found": return ["background-color:#FEF2F2;color:#991B1B"]*len(row)
            # Find cheapest price for this specific part number
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
          <span><span class="badge badge-green">Green</span> Cheapest version of that specific part</span>
          <span><span class="badge badge-red">Red</span> Brand/Part not found in database</span>
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
           <div class="ph-sub">Upload price sheets (Excel or CSV) to update the parts database</div></div>
    </div>""", unsafe_allow_html=True)

    # ── Accepted column guide ──
    import streamlit.components.v1 as components
    components.html("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
      * { box-sizing: border-box; font-family: 'Inter', sans-serif; }
      .guide-card {
        background: rgba(255,255,255,0.85);
        border: 1px solid rgba(255,255,255,0.96);
        border-radius: 20px;
        padding: 20px 24px 22px;
        box-shadow: 0 4px 24px rgba(30,64,175,0.08);
      }
      .guide-label {
        font-size: 10px; font-weight: 700; letter-spacing: .15em;
        text-transform: uppercase; color: #94A3B8;
        margin-bottom: 14px; padding-bottom: 10px;
        border-bottom: 1px solid #F1F5F9;
      }
      .cols-row { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 6px; }
      .badge {
        display: inline-block; padding: 5px 14px; border-radius: 20px;
        font-size: 12px; font-weight: 700; margin: 3px 3px 4px 0;
      }
      .badge-blue  { background:#EFF6FF; color:#1E40AF; border:1px solid #BFDBFE; }
      .req  { background:#FFF7ED; color:#C2410C; border:1px solid #FED7AA; }
      .opt  { background:#F0FDF4; color:#15803D; border:1px solid #BBF7D0; }
      .col-table { width:100%; border-collapse:collapse; margin-top:4px; }
      .col-table th {
        text-align:left; font-size:10px; font-weight:700; letter-spacing:.10em;
        text-transform:uppercase; color:#94A3B8; padding:0 8px 8px 0;
      }
      .col-table td { padding: 5px 8px 5px 0; font-size:12px; vertical-align:middle; }
      .col-table tr:not(:last-child) td { border-bottom: 1px solid #F1F5F9; }
      .col-name { font-weight:700; color:#0F172A; font-family:monospace; font-size:13px; }
      .col-desc { color:#64748B; }
      .info-box {
        font-size: 12px; color: #64748B; margin-top: 16px; line-height: 1.75;
        padding: 10px 14px; background: rgba(241,245,249,0.8); border-radius: 10px;
      }
      .info-box strong { color: #374151; }
    </style>
    <div class="guide-card">
      <div class="guide-label">Required Excel Column Headers</div>
      <table class="col-table">
        <tr>
          <th>Column Header (exact)</th>
          <th>Type</th>
          <th>Description</th>
        </tr>
        <tr>
          <td><span class="col-name">Supplier Name</span></td>
          <td><span class="badge req">Required</span></td>
          <td class="col-desc">Name of the vendor / supplier</td>
        </tr>
        <tr>
          <td><span class="col-name">Brand / Make</span></td>
          <td><span class="badge req">Required</span></td>
          <td class="col-desc">Brand or manufacturer of the part</td>
        </tr>
        <tr>
          <td><span class="col-name">Part Number</span></td>
          <td><span class="badge req">Required</span></td>
          <td class="col-desc">Unique part / item code</td>
        </tr>
        <tr>
          <td><span class="col-name">Unit Price</span></td>
          <td><span class="badge req">Required</span></td>
          <td class="col-desc">Price per unit (numeric)</td>
        </tr>
        <tr>
          <td><span class="col-name">Currency</span></td>
          <td><span class="badge opt">Optional</span></td>
          <td class="col-desc">e.g. INR, USD, EUR</td>
        </tr>
        <tr>
          <td><span class="col-name">Lead Time</span></td>
          <td><span class="badge opt">Optional</span></td>
          <td class="col-desc">Delivery / lead time details</td>
        </tr>
      </table>
      <div class="info-box">
        ✅ &nbsp;Column names are <strong>case-insensitive</strong> — spacing variations are handled automatically.<br>
        ✅ &nbsp;Same part + supplier uploaded again will <strong>update</strong> the price, not create a duplicate.<br>
        ✅ &nbsp;Both <strong>.xlsx</strong> and <strong>.csv</strong> files are accepted.
      </div>
    </div>
    """, height=320)

    # ── File uploader ──
    file = st.file_uploader(
        "Upload Excel (.xlsx) or CSV (.csv) file",
        type=["xlsx", "csv"]
    )

    if file:
        # Load file based on extension
        try:
            df_raw = load_upload_file(file)
        except Exception as e:
            st.error(f"Could not read file: {e}")
            st.stop()

        # Normalise column names
        df_raw = normalise_columns(df_raw)

        # Check required columns are present
        required = ["brand", "part_no", "price", "supplier"]
        missing = [c for c in required if c not in df_raw.columns]
        if missing:
            st.error(
                f"Could not map these required columns: **{missing}**\n\n"
                f"Columns detected in file: `{list(df_raw.columns)}`\n\n"
                "Please check the column names match one of the accepted formats above."
            )
            st.stop()

        # Apply Brand Normalisation Fix
        df_raw = normalise_brands(df_raw)

        # Clean string columns
        for col in ["brand", "part_no", "supplier"]:
            df_raw[col] = (df_raw[col].astype(str)
                           .str.replace(r'[\n"\r]', '', regex=True)
                           .str.strip())

        for col in ["currency", "delivery_time"]:
            if col not in df_raw.columns:
                df_raw[col] = ""
            else:
                df_raw[col] = (df_raw[col].astype(str)
                               .str.replace(r'[\n"\r]', '', regex=True)
                               .str.strip()
                               .replace("nan", ""))

        # Parse price
        df_raw["price"] = pd.to_numeric(df_raw["price"], errors="coerce").fillna(0)

        # Drop rows with blank key fields
        df_raw = df_raw[
            (df_raw["part_no"] != "") & (df_raw["part_no"] != "nan") &
            (df_raw["brand"]   != "") & (df_raw["brand"]   != "nan") &
            (df_raw["supplier"]!= "") & (df_raw["supplier"]!= "nan")
        ]

        # FIX: Prevent ON CONFLICT DO UPDATE duplicate row error
        df_raw = df_raw.drop_duplicates(subset=["part_no", "brand", "supplier"], keep="last")

        # ── Preview ──
        st.markdown('<div class="section-card">', unsafe_allow_html=True)

        file_type_label = "CSV" if file.name.lower().endswith(".csv") else "Excel"
        st.markdown(
            f'<div class="section-label">Preview — {len(df_raw):,} valid rows '
            f'<span class="badge badge-{"green" if file_type_label=="CSV" else "blue"}" '
            f'style="margin-left:8px;">{file_type_label}</span></div>',
            unsafe_allow_html=True
        )

        preview_cols = [c for c in ["brand","part_no","price","currency","delivery_time","supplier"]
                        if c in df_raw.columns]
        friendly_names = {
            "brand": "Brand / Make", "part_no": "Part Number", "price": "Unit Price",
            "currency": "Currency", "delivery_time": "Lead Time", "supplier": "Supplier Name"
        }
        st.dataframe(
            df_raw[preview_cols].rename(columns=friendly_names).head(30),
            use_container_width=True, hide_index=True, height=280
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # ── Upload button ──
        if st.button(f"⬆ Upload {len(df_raw):,} Rows to Database"):
            values = list(
                df_raw[["part_no","brand","price","supplier","currency","delivery_time"]]
                .itertuples(index=False, name=None)
            )
            total   = len(values)
            chunk   = 50  # Reduced for smoother updates
            chunks  = [values[i:i+chunk] for i in range(0, total, chunk)]
            n_chunks = len(chunks)

            st.markdown("""
            <div style="font-size:.82rem;font-weight:600;color:#1E40AF;margin-bottom:6px;">
              📤 Uploading to database…
            </div>""", unsafe_allow_html=True)
            progress_bar = st.progress(0)
            status_text  = st.empty()

            c = get_conn(); cur = c.cursor()
            uploaded = 0
            failed   = False
            try:
                for idx, chunk_vals in enumerate(chunks):
                    execute_values(cur, """
                        INSERT INTO parts_table(part_no,brand,price,supplier,currency,delivery_time)
                        VALUES %s
                        ON CONFLICT(part_no,brand,supplier)
                        DO UPDATE SET
                            price         = EXCLUDED.price,
                            currency      = EXCLUDED.currency,
                            delivery_time = EXCLUDED.delivery_time
                    """, chunk_vals, page_size=chunk)
                    
                    uploaded += len(chunk_vals)
                    pct = int((idx + 1) / n_chunks * 100)
                    progress_bar.progress(pct)
                    status_text.markdown(
                        f"<div style='font-size:.78rem;color:#64748B;'>"
                        f"Processed <strong>{uploaded:,}</strong> of <strong>{total:,}</strong> rows "
                        f"({pct}%)</div>",
                        unsafe_allow_html=True
                    )
                    time.sleep(0.02)
                    
                c.commit()
                fetch_brands.clear()
                progress_bar.progress(100)
                status_text.empty()
                st.success(f"✅ Successfully uploaded {uploaded:,} rows to the database.")
            except Exception as e:
                c.rollback()
                progress_bar.empty()
                status_text.empty()
                st.error(f"Upload failed: {e}")
                failed = True
            finally:
                release(c)
            if not failed:
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

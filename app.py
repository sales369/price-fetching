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
#  PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="PriceDesk Pro",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Sora:wght@400;600;700&display=swap');

:root {
    --primary:    #4F6EF7;
    --primary-lt: #EEF1FF;
    --accent:     #7C3AED;
    --success:    #059669;
    --success-lt: #D1FAE5;
    --danger:     #DC2626;
    --danger-lt:  #FEE2E2;
    --warn:       #D97706;
    --warn-lt:    #FEF3C7;
    --text:       #1E293B;
    --muted:      #64748B;
    --border:     #E2E8F0;
    --card:       rgba(255,255,255,0.85);
    --sidebar-bg: #0F172A;
}

.stApp {
    background: linear-gradient(135deg, #EEF2FF 0%, #F0F9FF 40%, #F5F3FF 100%);
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: var(--text);
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.8rem 2.2rem 2rem; max-width: 1280px; }

section[data-testid="stSidebar"] {
    width: 260px !important;
    background: var(--sidebar-bg) !important;
}
section[data-testid="stSidebar"] > div { width: 260px !important; }
section[data-testid="stSidebar"] * { color: #CBD5E1 !important; }
section[data-testid="stSidebar"] hr { border-color: #1E293B !important; }

h1 {
    font-family: 'Sora', sans-serif;
    font-size: 1.7rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 0;
}

.metric-row { display: flex; gap: 14px; margin-bottom: 1.4rem; flex-wrap: wrap; }
.metric-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 16px 22px;
    min-width: 150px;
    flex: 1;
    backdrop-filter: blur(12px);
    box-shadow: 0 2px 12px rgba(79,110,247,.07);
    transition: transform .2s, box-shadow .2s;
}
.metric-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(79,110,247,.13); }
.metric-card .label { font-size: 0.7rem; font-weight: 600; letter-spacing: .07em; text-transform: uppercase; color: var(--muted); margin-bottom: 4px; }
.metric-card .value { font-size: 1.5rem; font-weight: 700; color: var(--text); font-family: 'Sora', sans-serif; }
.metric-card .sub   { font-size: 0.73rem; color: var(--muted); margin-top: 2px; }

.section-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 22px 24px;
    margin-bottom: 1.2rem;
    backdrop-filter: blur(12px);
    box-shadow: 0 2px 10px rgba(0,0,0,.04);
}
.section-title {
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: .08em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 14px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
}

.stButton > button {
    background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.86rem !important;
    padding: 0.5rem 1.4rem !important;
    box-shadow: 0 3px 12px rgba(79,110,247,.25) !important;
    transition: opacity .2s, transform .15s !important;
}
.stButton > button:hover { opacity: 0.88 !important; transform: translateY(-1px) !important; }

.stDownloadButton > button {
    background: linear-gradient(135deg, #059669 0%, #0891B2 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.86rem !important;
    box-shadow: 0 3px 12px rgba(5,150,105,.2) !important;
}

.stTextInput > div > div > input {
    border-radius: 10px !important;
    border: 1.5px solid var(--border) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.88rem !important;
}

[data-testid="stFileUploader"] {
    border: 2px dashed #4F6EF7 !important;
    border-radius: 14px !important;
    background: #EEF1FF !important;
}

.badge {
    display: inline-block;
    padding: 3px 11px;
    border-radius: 20px;
    font-size: 0.73rem;
    font-weight: 600;
    letter-spacing: .04em;
    margin-right: 4px;
}
.badge-blue { background: #EEF1FF; color: #4F6EF7; }

.page-header {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 1.4rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border);
}
.page-header .icon {
    width: 44px; height: 44px;
    background: linear-gradient(135deg, #4F6EF7 0%, #7C3AED 100%);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.3rem;
    box-shadow: 0 4px 12px rgba(79,110,247,.3);
    flex-shrink: 0;
}
.page-header h1 { margin: 0 !important; font-size: 1.5rem !important; line-height:1.2; }
.page-header p  { margin: 0; color: var(--muted); font-size: 0.82rem; }

.login-wrap {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 22px;
    padding: 42px 38px 36px;
    backdrop-filter: blur(16px);
    box-shadow: 0 8px 40px rgba(79,110,247,.12);
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  DB POOL  — cached for lifetime of server
# ─────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    st.error("❌ DATABASE_URL environment variable not set.")
    st.stop()


@st.cache_resource
def get_pool():
    return SimpleConnectionPool(1, 5, DATABASE_URL)


pool = get_pool()

def get_conn():  return pool.getconn()
def release(c):  pool.putconn(c)


# ─────────────────────────────────────────────
#  SCHEMA — run once per server lifetime
# ─────────────────────────────────────────────
@st.cache_resource
def init_schema():
    c = get_conn()
    cur = c.cursor()
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
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY, username TEXT UNIQUE, password TEXT
        );
        CREATE TABLE IF NOT EXISTS saved_offers (
            id SERIAL PRIMARY KEY, username TEXT, data JSONB, created_at TIMESTAMP DEFAULT NOW()
        );
        INSERT INTO users(username,password)
        SELECT 'admin','admin' WHERE NOT EXISTS(SELECT 1 FROM users WHERE username='admin');
    """)
    c.commit()
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
    cur.execute("SELECT DISTINCT brand FROM parts_table ORDER BY brand")
    rows = [x[0] for x in cur.fetchall()]
    release(c)
    return rows


def lookup_prices(items):
    c = get_conn()
    cur = c.cursor()
    results = []
    for r in items:
        part  = r["part_no"].strip()
        brand = r["brand"].strip()
        qty   = max(int(r.get("qty") or 1), 1)
        if not part or not brand:
            continue
        cur.execute("""
            SELECT supplier, price FROM parts_table
            WHERE TRIM(LOWER(part_no))=TRIM(LOWER(%s))
              AND TRIM(LOWER(brand))=TRIM(LOWER(%s))
            ORDER BY price ASC
        """, (part, brand))
        rows = cur.fetchall()
        if rows:
            for supplier, price in rows:
                results.append({"Brand": brand, "Part No": part, "Supplier": supplier,
                                 "Qty": qty, "Unit Price (JPY)": float(price),
                                 "Amount (JPY)": qty * float(price)})
        else:
            results.append({"Brand": brand, "Part No": part, "Supplier": "Not Found",
                             "Qty": qty, "Unit Price (JPY)": 0, "Amount (JPY)": 0})
    release(c)
    return results


# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────
for k, v in {
    "user": None,
    "table_data": pd.DataFrame(),
    "input_table": pd.DataFrame(columns=["Brand","Part No","Qty"]),
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────
#  LOGIN
# ─────────────────────────────────────────────
def check_login(u, p):
    c = get_conn()
    cur = c.cursor()
    cur.execute("SELECT id FROM users WHERE username=%s AND password=%s", (u, p))
    row = cur.fetchone()
    release(c)
    return row

if st.session_state.user is None:
    st.markdown("<style>section[data-testid='stSidebar']{display:none!important;}</style>",
                unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.05, 1])
    with mid:
        st.markdown("""
        <div class="login-wrap">
            <div style="text-align:center; margin-bottom:24px;">
                <div style="font-size:2rem; margin-bottom:6px;">💎</div>
                <div style="font-family:'Sora',sans-serif; font-size:1.65rem; font-weight:700; color:#1E293B;">
                    PriceDesk Pro
                </div>
                <div style="color:#64748B; font-size:0.83rem; margin-top:4px;">
                    Parts Price Intelligence Platform
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        u = st.text_input("Username", placeholder="Enter username")
        p = st.text_input("Password", type="password", placeholder="••••••••")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("Sign In →", use_container_width=True):
            if check_login(u, p):
                st.session_state.user = {"username": u}
                st.rerun()
            else:
                st.error("Invalid username or password.")
    st.stop()

username = st.session_state.user["username"]


# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding:20px 12px 6px; text-align:center;">
        <div style="font-size:1.4rem;">💎</div>
        <div style="font-family:'Sora',sans-serif; font-size:1.1rem; font-weight:700;
                    color:#F1F5F9; letter-spacing:.03em;">PriceDesk</div>
        <div style="font-size:0.68rem; color:#475569; letter-spacing:.08em; margin-top:1px;">
            PARTS INTELLIGENCE
        </div>
    </div>
    <div style="height:1px; background:#1E293B; margin:10px 0 14px;"></div>
    <div style="padding:0 10px 14px;">
        <div style="background:#1E293B; border-radius:10px; padding:10px 12px;">
            <div style="font-size:0.68rem; color:#475569; text-transform:uppercase;
                        letter-spacing:.07em; margin-bottom:3px;">Logged in as</div>
            <div style="font-size:0.88rem; font-weight:600; color:#E2E8F0;">👤 {username}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    pages = (["📊 Price Lookup","📁 Saved Quotations","📤 Data Upload","🛠 Access Control"]
             if username == "admin" else
             ["📊 Price Lookup","📁 Saved Quotations"])

    page = st.radio("", pages, label_visibility="collapsed")
    st.markdown("<div style='height:1px; background:#1E293B; margin:12px 0;'></div>",
                unsafe_allow_html=True)
    if st.button("⎋  Sign Out", use_container_width=True):
        st.session_state.clear()
        st.rerun()


# ═══════════════════════════════════════════
#  PRICE LOOKUP
# ═══════════════════════════════════════════
if page == "📊 Price Lookup":
    st.markdown("""
    <div class="page-header">
        <div class="icon">📊</div>
        <div><h1>Price Lookup</h1><p>Search parts across all suppliers instantly</p></div>
    </div>""", unsafe_allow_html=True)

    brand_list = fetch_brands()

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🔍 Enter Parts to Search</div>', unsafe_allow_html=True)
    input_df = st.data_editor(
        st.session_state.input_table, num_rows="dynamic",
        use_container_width=True, height=210,
        column_config={
            "Brand":   st.column_config.SelectboxColumn("Brand", options=brand_list, width="medium"),
            "Part No": st.column_config.TextColumn("Part No", width="large"),
            "Qty":     st.column_config.NumberColumn("Qty", min_value=1, default=1, width="small"),
        }, key="input_editor",
    )
    st.markdown('</div>', unsafe_allow_html=True)

    c1, c2, _ = st.columns([1, 1, 5])
    with c1:
        go = st.button("🔍 Get Pricing", use_container_width=True)
    with c2:
        if st.button("✖ Clear", use_container_width=True):
            st.session_state.input_table = pd.DataFrame(columns=["Brand","Part No","Qty"])
            st.session_state.table_data  = pd.DataFrame()
            st.rerun()

    if go:
        items = [
            {"brand": str(r.get("Brand","")).strip(),
             "part_no": str(r.get("Part No","")).strip(),
             "qty": r.get("Qty", 1)}
            for _, r in input_df.iterrows()
            if str(r.get("Brand","")).strip() not in ("","nan")
            and str(r.get("Part No","")).strip() not in ("","nan")
        ]
        if items:
            with st.spinner("Fetching prices…"):
                st.session_state.table_data  = pd.DataFrame(lookup_prices(items))
                st.session_state.input_table = input_df
        else:
            st.warning("Add at least one Brand + Part No row.")

    df = st.session_state.table_data

    if not df.empty:
        found = df[df["Supplier"] != "Not Found"]
        st.markdown(f"""
        <div class="metric-row">
            <div class="metric-card">
                <div class="label">Parts Searched</div>
                <div class="value">{df["Part No"].nunique()}</div>
                <div class="sub">unique part numbers</div>
            </div>
            <div class="metric-card">
                <div class="label">Suppliers Found</div>
                <div class="value">{found["Supplier"].nunique() if not found.empty else 0}</div>
                <div class="sub">across all parts</div>
            </div>
            <div class="metric-card">
                <div class="label">Best Price</div>
                <div class="value">¥{found["Amount (JPY)"].min():,.0f if not found.empty else 0}</div>
                <div class="sub">lowest amount</div>
            </div>
            <div class="metric-card">
                <div class="label">Price Records</div>
                <div class="value">{len(found)}</div>
                <div class="sub">supplier rows returned</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">💹 Supplier Prices — All Results</div>',
                    unsafe_allow_html=True)

        def highlight_rows(row):
            if row["Supplier"] == "Not Found":
                return ["background-color:#FEE2E2;color:#991B1B"] * len(row)
            mask  = (df["Part No"]==row["Part No"]) & (df["Brand"]==row["Brand"])
            valid = df.loc[mask & (df["Supplier"]!="Not Found"), "Unit Price (JPY)"]
            if not valid.empty and row["Unit Price (JPY)"] == valid.min():
                return ["background-color:#D1FAE5;color:#065F46;font-weight:600"] * len(row)
            return [""] * len(row)

        styled = (df.style
                  .apply(highlight_rows, axis=1)
                  .format({"Unit Price (JPY)":"¥{:,.0f}","Amount (JPY)":"¥{:,.0f}"}))
        st.dataframe(styled, use_container_width=True, hide_index=True, height=380)

        st.markdown("""
        <div style="font-size:0.76rem;color:#64748B;margin-top:6px;display:flex;gap:18px;">
            <span>🟢 Green = cheapest supplier</span>
            <span>🔴 Red = not found in database</span>
        </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        a1, a2 = st.columns([1, 1])
        with a1:
            if st.button("💾 Save Quotation", use_container_width=True):
                c = get_conn()
                cur = c.cursor()
                cur.execute("INSERT INTO saved_offers(username,data) VALUES(%s,%s)",
                            (username, json.dumps(df.to_dict(orient="records"))))
                c.commit(); release(c)
                st.success("✅ Quotation saved!")
        with a2:
            buf = BytesIO()
            df.to_excel(buf, index=False); buf.seek(0)
            st.download_button("⬇ Export Excel", buf, file_name="price_lookup.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)


# ═══════════════════════════════════════════
#  SAVED QUOTATIONS
# ═══════════════════════════════════════════
elif page == "📁 Saved Quotations":
    st.markdown("""
    <div class="page-header">
        <div class="icon">📁</div>
        <div><h1>Saved Quotations</h1><p>View, download and manage past quotations</p></div>
    </div>""", unsafe_allow_html=True)

    c = get_conn(); cur = c.cursor()
    cur.execute("SELECT id,username,data,created_at::date FROM saved_offers ORDER BY created_at DESC")
    rows = cur.fetchall(); release(c)

    if not rows:
        st.markdown("""
        <div class="section-card" style="text-align:center;padding:48px 24px;">
            <div style="font-size:2.8rem;margin-bottom:10px;">📭</div>
            <div style="font-size:1rem;font-weight:600;">No saved quotations yet</div>
            <div style="color:#64748B;font-size:0.83rem;margin-top:6px;">
                Go to Price Lookup and save your first quotation.
            </div>
        </div>""", unsafe_allow_html=True)
        st.stop()

    all_data = []
    for oid, user, data, date_only in rows:
        df_o = pd.DataFrame(json.loads(data) if isinstance(data, str) else data)
        df_o["Employee"] = user
        df_o["Saved On"] = str(date_only)
        df_o["Offer ID"] = oid
        all_data.append(df_o)

    final_df = pd.concat(all_data, ignore_index=True)

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card">
            <div class="label">Quotations</div>
            <div class="value">{len(rows)}</div>
            <div class="sub">total saved</div>
        </div>
        <div class="metric-card">
            <div class="label">Employees</div>
            <div class="value">{final_df["Employee"].nunique()}</div>
            <div class="sub">contributors</div>
        </div>
        <div class="metric-card">
            <div class="label">Latest Save</div>
            <div class="value" style="font-size:1.05rem;">{str(rows[0][3])}</div>
            <div class="sub">most recent date</div>
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📋 All Records</div>', unsafe_allow_html=True)

    display_cols = final_df.drop(columns=["Offer ID"], errors="ignore").copy()
    display_cols.insert(0, "Select", False)
    edited_df = st.data_editor(display_cols, use_container_width=True,
                                hide_index=True, height=400, key="saved_editor")
    st.markdown('</div>', unsafe_allow_html=True)

    b1, b2 = st.columns([1, 1])
    with b1:
        buf = BytesIO()
        final_df.drop(columns=["Offer ID"], errors="ignore").to_excel(buf, index=False); buf.seek(0)
        st.download_button("⬇ Download All", buf, file_name="all_quotations.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)
    with b2:
        if st.button("🗑 Delete Selected", use_container_width=True):
            sel = edited_df[edited_df["Select"] == True]
            if not sel.empty:
                keys = set(zip(sel["Employee"], sel["Saved On"].astype(str)))
                ids  = [oid for oid, user, _, date_only in rows if (user, str(date_only)) in keys]
                if ids:
                    c = get_conn(); cur = c.cursor()
                    cur.execute("DELETE FROM saved_offers WHERE id=ANY(%s)", (ids,))
                    c.commit(); release(c)
                    st.success(f"Deleted {len(ids)} record(s).")
                    st.rerun()
            else:
                st.warning("Tick at least one row.")


# ═══════════════════════════════════════════
#  DATA UPLOAD
# ═══════════════════════════════════════════
elif page == "📤 Data Upload":
    st.markdown("""
    <div class="page-header">
        <div class="icon">📤</div>
        <div><h1>Master Data Upload</h1><p>Upload Excel price sheets to update the parts database</p></div>
    </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="section-card">
        <div class="section-title">📋 Required Columns</div>
        <div style="margin-bottom:10px;">
            <span class="badge badge-blue">Make / Brand</span>
            <span class="badge badge-blue">Part Number</span>
            <span class="badge badge-blue">JPY Price</span>
            <span class="badge badge-blue">Supplier</span>
        </div>
        <div style="font-size:0.8rem;color:#64748B;">
            Column names are case-insensitive. Spaces, quotes and special characters are handled automatically.
            Existing records are updated on conflict — no duplicates.
        </div>
    </div>""", unsafe_allow_html=True)

    file = st.file_uploader("Drop your Excel file here", type=["xlsx"])

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
                if alias in col_map:
                    rename[col_map[alias]] = target
                    break

        df_raw.rename(columns=rename, inplace=True)
        missing = [c for c in ["brand","part_no","price","supplier"] if c not in df_raw.columns]
        if missing:
            st.error(f"❌ Could not map: **{missing}** — Found: `{list(df_raw.columns)}`")
            st.stop()

        df_raw["brand"]    = df_raw["brand"].astype(str).str.replace(r'[\n"\r]','',regex=True).str.strip()
        df_raw["part_no"]  = df_raw["part_no"].astype(str).str.replace(r'[\n"\r]','',regex=True).str.strip()
        df_raw["supplier"] = df_raw["supplier"].astype(str).str.strip()
        df_raw["price"]    = pd.to_numeric(df_raw["price"], errors="coerce").fillna(0)
        df_raw = df_raw[
            (df_raw["part_no"] != "") & (df_raw["brand"] != "") &
            (df_raw["supplier"] != "") & (df_raw["part_no"] != "nan") & (df_raw["brand"] != "nan")
        ]

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="section-title">👁 Preview — {len(df_raw):,} valid rows detected</div>',
                    unsafe_allow_html=True)
        st.dataframe(df_raw[["brand","part_no","price","supplier"]].head(30),
                     use_container_width=True, hide_index=True, height=270)
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button(f"✅ Upload {len(df_raw):,} Rows to Database", use_container_width=False):
            values = list(df_raw[["part_no","brand","price","supplier"]].itertuples(index=False, name=None))
            c = get_conn(); cur = c.cursor()
            execute_values(cur, """
                INSERT INTO parts_table(part_no,brand,price,supplier) VALUES %s
                ON CONFLICT(part_no,brand,supplier) DO UPDATE SET price=EXCLUDED.price
            """, values, page_size=500)
            c.commit(); release(c)
            fetch_brands.clear()
            st.success(f"✅ Uploaded **{len(values):,} rows** successfully!")
            st.rerun()


# ═══════════════════════════════════════════
#  ACCESS CONTROL
# ═══════════════════════════════════════════
elif page == "🛠 Access Control":
    st.markdown("""
    <div class="page-header">
        <div class="icon">🛠</div>
        <div><h1>Access Control</h1><p>Manage users and employee accounts</p></div>
    </div>""", unsafe_allow_html=True)

    col_a, col_b = st.columns(2, gap="large")

    with col_a:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">➕ Create New User</div>', unsafe_allow_html=True)
        nu = st.text_input("Username", placeholder="e.g. john.doe", key="nu")
        np_ = st.text_input("Password", type="password", placeholder="Secure password", key="np")
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        if st.button("Create User", use_container_width=True):
            if nu and np_:
                try:
                    c = get_conn(); cur = c.cursor()
                    cur.execute("INSERT INTO users(username,password) VALUES(%s,%s)", (nu, np_))
                    c.commit(); release(c)
                    st.success(f"✅ User **{nu}** created.")
                except Exception as e:
                    c.rollback(); release(c)
                    st.error(f"Error: {e}")
            else:
                st.warning("Fill in both fields.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🗑 Remove Employee</div>', unsafe_allow_html=True)
        c = get_conn(); cur = c.cursor()
        cur.execute("SELECT username FROM users WHERE username!='admin' ORDER BY username")
        users = [x[0] for x in cur.fetchall()]; release(c)
        if users:
            del_u = st.selectbox("Select employee", users)
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            if st.button("Delete Employee", use_container_width=True):
                c = get_conn(); cur = c.cursor()
                cur.execute("DELETE FROM users WHERE username=%s", (del_u,))
                c.commit(); release(c)
                st.success(f"User **{del_u}** removed.")
                st.rerun()
        else:
            st.info("No other users found.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">👥 All Users</div>', unsafe_allow_html=True)
    c = get_conn(); cur = c.cursor()
    cur.execute("SELECT username FROM users ORDER BY username")
    all_u = pd.DataFrame(cur.fetchall(), columns=["Username"]); release(c)
    all_u["Role"] = all_u["Username"].apply(lambda x: "🔑 Admin" if x=="admin" else "👤 Employee")
    st.dataframe(all_u, use_container_width=True, hide_index=True, height=200)
    st.markdown('</div>', unsafe_allow_html=True)

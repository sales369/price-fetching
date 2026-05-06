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
    page_icon="assets/logo.png" if os.path.exists("assets/logo.png") else "📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap');

:root {
    --primary:      #2563EB;
    --primary-lt:   #EFF6FF;
    --primary-mid:  #BFDBFE;
    --accent:       #0EA5E9;
    --accent-lt:    #F0F9FF;
    --success:      #16A34A;
    --success-lt:   #F0FDF4;
    --success-mid:  #BBF7D0;
    --danger:       #DC2626;
    --danger-lt:    #FEF2F2;
    --danger-mid:   #FECACA;
    --text:         #0F172A;
    --text-2:       #334155;
    --muted:        #64748B;
    --muted-lt:     #94A3B8;
    --border:       #E2E8F0;
    --border-lt:    #F1F5F9;
    --card:         #FFFFFF;
    --bg:           #F8FAFC;
}

* { box-sizing: border-box; }

.stApp {
    background: linear-gradient(160deg, #F0F7FF 0%, #F8FAFC 50%, #F5F0FF 100%);
    font-family: 'Inter', sans-serif;
    color: var(--text);
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2.4rem 3rem !important; max-width: 1300px; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    width: 250px !important;
    background: #FFFFFF !important;
    border-right: 1px solid var(--border) !important;
    box-shadow: 2px 0 12px rgba(0,0,0,.04);
}
section[data-testid="stSidebar"] > div { width: 250px !important; }

/* ── Headings ── */
h1, h2, h3 {
    font-family: 'DM Sans', sans-serif;
    color: var(--text);
    font-weight: 700;
}

/* ── Metric Cards ── */
.metric-row { display:flex; gap:12px; margin-bottom:1.4rem; flex-wrap:wrap; }
.metric-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 18px 20px;
    min-width: 148px;
    flex: 1;
    box-shadow: 0 1px 6px rgba(0,0,0,.05);
    transition: box-shadow .2s;
}
.metric-card:hover { box-shadow: 0 4px 18px rgba(37,99,235,.1); }
.metric-card .mc-label {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: .08em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 6px;
}
.metric-card .mc-value {
    font-size: 1.55rem;
    font-weight: 700;
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    line-height: 1;
}
.metric-card .mc-sub {
    font-size: 0.72rem;
    color: var(--muted-lt);
    margin-top: 4px;
}

/* ── Section Card ── */
.section-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 20px 22px 22px;
    margin-bottom: 1.2rem;
    box-shadow: 0 1px 6px rgba(0,0,0,.04);
}
.section-label {
    font-size: 0.69rem;
    font-weight: 700;
    letter-spacing: .09em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border-lt);
    display: flex;
    align-items: center;
    gap: 6px;
}

/* ── Page Header ── */
.page-header {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 1.6rem;
    padding-bottom: 1.1rem;
    border-bottom: 1px solid var(--border);
}
.ph-icon {
    width: 42px; height: 42px;
    background: linear-gradient(135deg, #2563EB 0%, #0EA5E9 100%);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.15rem;
    box-shadow: 0 3px 10px rgba(37,99,235,.22);
    flex-shrink: 0;
}
.ph-title { font-size: 1.45rem !important; margin: 0 !important; line-height: 1.2; }
.ph-sub   { margin: 0; color: var(--muted); font-size: 0.8rem; margin-top: 2px; }

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #2563EB 0%, #0EA5E9 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 9px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.84rem !important;
    padding: 0.48rem 1.3rem !important;
    box-shadow: 0 2px 8px rgba(37,99,235,.22) !important;
    transition: opacity .18s, transform .15s, box-shadow .18s !important;
    letter-spacing: .01em !important;
}
.stButton > button:hover {
    opacity: 0.87 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(37,99,235,.28) !important;
}

.stDownloadButton > button {
    background: linear-gradient(135deg, #16A34A 0%, #0EA5E9 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 9px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.84rem !important;
    box-shadow: 0 2px 8px rgba(22,163,74,.2) !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input {
    border-radius: 9px !important;
    border: 1.5px solid var(--border) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.87rem !important;
    background: #FAFAFA !important;
    transition: border-color .18s !important;
    padding: 0.45rem 0.75rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--primary) !important;
    background: #fff !important;
}

/* ── File Uploader ── */
[data-testid="stFileUploader"] {
    border: 2px dashed var(--primary-mid) !important;
    border-radius: 12px !important;
    background: var(--primary-lt) !important;
    padding: 0.5rem !important;
}

/* ── Alerts ── */
.stSuccess, .stError, .stWarning, .stInfo {
    border-radius: 10px !important;
    font-size: 0.86rem !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {
    border-radius: 10px;
    overflow: hidden;
}

/* ── Badge ── */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.71rem;
    font-weight: 600;
    letter-spacing: .04em;
    margin: 2px 3px 2px 0;
}
.badge-blue  { background: var(--primary-lt);  color: var(--primary); border: 1px solid var(--primary-mid); }
.badge-green { background: var(--success-lt);  color: var(--success); border: 1px solid var(--success-mid); }
.badge-red   { background: var(--danger-lt);   color: var(--danger);  border: 1px solid var(--danger-mid);  }

/* ── Sidebar Nav ── */
.sidebar-logo-wrap {
    padding: 20px 16px 12px;
    border-bottom: 1px solid var(--border-lt);
    margin-bottom: 8px;
}
.sidebar-user-chip {
    background: var(--primary-lt);
    border-radius: 8px;
    padding: 9px 12px;
    margin: 0 10px 14px;
    border: 1px solid var(--primary-mid);
}
.sidebar-user-chip .sup-label {
    font-size: 0.65rem;
    color: var(--muted);
    font-weight: 600;
    letter-spacing: .07em;
    text-transform: uppercase;
    margin-bottom: 2px;
}
.sidebar-user-chip .sup-name {
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--primary);
}

/* ── Login ── */
.login-outer {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
}
.login-card {
    background: #fff;
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 44px 40px 36px;
    box-shadow: 0 8px 40px rgba(37,99,235,.10), 0 1px 4px rgba(0,0,0,.04);
    max-width: 400px;
    width: 100%;
}
.login-app-name {
    font-family: 'DM Sans', sans-serif;
    font-size: 1.55rem;
    font-weight: 700;
    color: var(--text);
    text-align: center;
    margin-bottom: 2px;
    letter-spacing: -.01em;
}
.login-tagline {
    color: var(--muted);
    font-size: 0.8rem;
    text-align: center;
    margin-bottom: 26px;
}
.login-divider {
    height: 1px;
    background: var(--border-lt);
    margin: 16px 0;
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
#  SCHEMA INIT — once per server boot
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
    release(c)
    return rows


def lookup_prices(items):
    c = get_conn(); cur = c.cursor()
    results = []
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
    release(c)
    return results


def logo(width=130):
    """Render logo.png if present, else text fallback."""
    if os.path.exists("logo.png"):
        st.image("logo.png", width=width)
    else:
        st.markdown(
            f'<div style="font-family:\'DM Sans\',sans-serif;font-size:1.3rem;'
            f'font-weight:700;color:#2563EB;letter-spacing:-.01em;">PriceDesk</div>',
            unsafe_allow_html=True
        )


# ─────────────────────────────────────────────
#  SESSION
# ─────────────────────────────────────────────
for k, v in {
    "user": None,
    "table_data": pd.DataFrame(),
    "input_table": pd.DataFrame(columns=["Brand", "Part No", "Qty"]),
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────
#  LOGIN
# ─────────────────────────────────────────────
def check_login(u, p):
    c = get_conn(); cur = c.cursor()
    cur.execute("SELECT id FROM users WHERE username=%s AND password=%s", (u, p))
    row = cur.fetchone(); release(c)
    return row

if st.session_state.user is None:
    st.markdown(
        "<style>section[data-testid='stSidebar']{display:none!important;}"
        ".block-container{padding:3rem 1rem!important;}</style>",
        unsafe_allow_html=True
    )
    _, mid, _ = st.columns([1, 1, 1])
    with mid:
        logo(width=140)
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown("""
            <div class="login-app-name">Welcome back</div>
            <div class="login-tagline">Sign in to your PriceDesk account</div>
            <div class="login-divider"></div>
        """, unsafe_allow_html=True)
        u_in = st.text_input("Username", placeholder="Enter username", label_visibility="visible")
        p_in = st.text_input("Password", type="password", placeholder="Enter password")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("Sign In", use_container_width=True):
            if check_login(u_in, p_in):
                st.session_state.user = {"username": u_in}
                st.rerun()
            else:
                st.error("Invalid username or password.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

username = st.session_state.user["username"]


# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-logo-wrap">', unsafe_allow_html=True)
    logo(width=120)
    st.markdown('</div>', unsafe_allow_html=True)

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
    st.markdown("<hr style='border-color:#E2E8F0;margin:12px 0;'>", unsafe_allow_html=True)
    if st.button("Sign Out", use_container_width=True):
        st.session_state.clear()
        st.rerun()


# ═══════════════════════════════════════════
#  PRICE LOOKUP
# ═══════════════════════════════════════════
if page == "Price Lookup":

    st.markdown("""
    <div class="page-header">
        <div class="ph-icon">📊</div>
        <div>
            <div class="ph-title" style="font-family:'DM Sans',sans-serif;font-size:1.45rem;
                 font-weight:700;color:#0F172A;margin:0;line-height:1.2;">Price Lookup</div>
            <div class="ph-sub">Search parts across all suppliers instantly</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    brand_list = fetch_brands()

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Enter Parts to Search</div>', unsafe_allow_html=True)
    input_df = st.data_editor(
        st.session_state.input_table,
        num_rows="dynamic",
        use_container_width=True,
        height=210,
        column_config={
            "Brand":   st.column_config.SelectboxColumn("Brand", options=brand_list, width="medium"),
            "Part No": st.column_config.TextColumn("Part No", width="large"),
            "Qty":     st.column_config.NumberColumn("Qty", min_value=1, default=1, width="small"),
        },
        key="input_editor",
    )
    st.markdown('</div>', unsafe_allow_html=True)

    c1, c2, _ = st.columns([1.2, 1, 5])
    with c1:
        go = st.button("Get Pricing", use_container_width=True)
    with c2:
        if st.button("Clear", use_container_width=True):
            st.session_state.input_table = pd.DataFrame(columns=["Brand", "Part No", "Qty"])
            st.session_state.table_data  = pd.DataFrame()
            st.rerun()

    if go:
        items = []
        for _, row in input_df.iterrows():
            b = str(row.get("Brand",   "")).strip()
            p = str(row.get("Part No", "")).strip()
            q = row.get("Qty", 1)
            if b not in ("", "nan") and p not in ("", "nan"):
                items.append({"brand": b, "part_no": p, "qty": q})
        if items:
            with st.spinner("Fetching prices…"):
                results = lookup_prices(items)
            st.session_state.table_data  = pd.DataFrame(results)
            st.session_state.input_table = input_df
        else:
            st.warning("Please enter at least one Brand and Part No.")

    df = st.session_state.table_data

    if not df.empty:
        found      = df[df["Supplier"] != "Not Found"]
        n_parts    = int(df["Part No"].nunique())
        n_suppliers = int(found["Supplier"].nunique()) if not found.empty else 0
        best_price = float(found["Unit Price (JPY)"].min()) if not found.empty else 0.0
        n_records  = int(len(found))

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
                <div class="mc-value">&#165;{best_price:,.0f}</div>
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
                return ["background-color:#F0FDF4; color:#15803D; font-weight:600"] * len(row)
            return [""] * len(row)

        styled = (
            df.style
            .apply(highlight_rows, axis=1)
            .format({"Unit Price (JPY)": "¥{:,.0f}", "Amount (JPY)": "¥{:,.0f}"})
        )
        st.dataframe(styled, use_container_width=True, hide_index=True, height=360)

        st.markdown("""
        <div style="display:flex;gap:16px;margin-top:8px;font-size:0.75rem;color:#64748B;">
            <span><span class="badge badge-green">Green</span> Cheapest supplier for that part</span>
            <span><span class="badge badge-red">Red</span> Part not found in database</span>
        </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        a1, a2, _ = st.columns([1.2, 1.2, 5])
        with a1:
            if st.button("Save Quotation", use_container_width=True):
                c = get_conn(); cur = c.cursor()
                cur.execute(
                    "INSERT INTO saved_offers(username, data) VALUES(%s, %s)",
                    (username, json.dumps(df.to_dict(orient="records")))
                )
                c.commit(); release(c)
                st.success("Quotation saved successfully.")
        with a2:
            buf = BytesIO()
            df.to_excel(buf, index=False); buf.seek(0)
            st.download_button(
                "Export to Excel", buf, file_name="price_lookup.xlsx",
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
            <div class="ph-title" style="font-family:'DM Sans',sans-serif;font-size:1.45rem;
                 font-weight:700;color:#0F172A;margin:0;">Saved Quotations</div>
            <div class="ph-sub">View, download and manage past quotations</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c = get_conn(); cur = c.cursor()
    cur.execute("""
        SELECT id, username, data, created_at::date
        FROM saved_offers ORDER BY created_at DESC
    """)
    rows = cur.fetchall(); release(c)

    if not rows:
        st.markdown("""
        <div class="section-card" style="text-align:center;padding:52px 24px;">
            <div style="font-size:2.4rem;margin-bottom:10px;">📭</div>
            <div style="font-size:1rem;font-weight:600;color:#0F172A;">No saved quotations yet</div>
            <div style="color:#64748B;font-size:0.82rem;margin-top:6px;">
                Go to Price Lookup and save your first quotation.
            </div>
        </div>""", unsafe_allow_html=True)
        st.stop()

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
            <div class="mc-value" style="font-size:1rem;">{str(rows[0][3])}</div>
            <div class="mc-sub">most recent date</div>
        </div>
    </div>""", unsafe_allow_html=True)

    display_df = final_df.drop(columns=["_offer_id"], errors="ignore").copy()
    display_df.insert(0, "Select", False)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">All Records</div>', unsafe_allow_html=True)
    edited_df = st.data_editor(
        display_df, use_container_width=True,
        hide_index=True, height=400, key="saved_editor"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    b1, b2, _ = st.columns([1.2, 1.2, 5])
    with b1:
        buf = BytesIO()
        final_df.drop(columns=["_offer_id"], errors="ignore").to_excel(buf, index=False)
        buf.seek(0)
        st.download_button(
            "Download All", buf, file_name="all_quotations.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with b2:
        if st.button("Delete Selected", use_container_width=True):
            sel = edited_df[edited_df["Select"] == True]
            if not sel.empty:
                keys = set(zip(sel["Employee"].astype(str), sel["Saved On"].astype(str)))
                ids  = [oid for oid, user, _, date_only in rows
                        if (str(user), str(date_only)) in keys]
                if ids:
                    c = get_conn(); cur = c.cursor()
                    cur.execute("DELETE FROM saved_offers WHERE id = ANY(%s)", (ids,))
                    c.commit(); release(c)
                    st.success(f"Deleted {len(ids)} record(s).")
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
            <div class="ph-title" style="font-family:'DM Sans',sans-serif;font-size:1.45rem;
                 font-weight:700;color:#0F172A;margin:0;">Master Data Upload</div>
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
        <div style="font-size:0.79rem;color:#64748B;margin-top:10px;line-height:1.6;">
            Column names are case-insensitive and extra spaces are handled automatically.
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
            use_container_width=True, hide_index=True, height=270,
        )
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button(f"Upload {len(df_raw):,} Rows to Database"):
            values = list(
                df_raw[["part_no","brand","price","supplier"]].itertuples(index=False, name=None)
            )
            c = get_conn(); cur = c.cursor()
            execute_values(cur, """
                INSERT INTO parts_table(part_no, brand, price, supplier) VALUES %s
                ON CONFLICT(part_no, brand, supplier)
                DO UPDATE SET price = EXCLUDED.price
            """, values, page_size=500)
            c.commit(); release(c)
            fetch_brands.clear()
            st.success(f"Successfully uploaded {len(values):,} rows.")
            st.rerun()


# ═══════════════════════════════════════════
#  ACCESS CONTROL
# ═══════════════════════════════════════════
elif page == "Access Control":

    st.markdown("""
    <div class="page-header">
        <div class="ph-icon">🔐</div>
        <div>
            <div class="ph-title" style="font-family:'DM Sans',sans-serif;font-size:1.45rem;
                 font-weight:700;color:#0F172A;margin:0;">Access Control</div>
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
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        if st.button("Create User", use_container_width=True):
            if nu and np_:
                try:
                    c = get_conn(); cur = c.cursor()
                    cur.execute("INSERT INTO users(username, password) VALUES(%s,%s)", (nu, np_))
                    c.commit(); release(c)
                    st.success(f"User '{nu}' created.")
                except Exception as e:
                    c.rollback(); release(c)
                    st.error(f"Could not create user: {e}")
            else:
                st.warning("Please fill in both fields.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Remove Employee</div>', unsafe_allow_html=True)
        c = get_conn(); cur = c.cursor()
        cur.execute("SELECT username FROM users WHERE username != 'admin' ORDER BY username")
        users = [x[0] for x in cur.fetchall()]; release(c)
        if users:
            del_u = st.selectbox("Select employee to remove", users)
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            if st.button("Delete Employee", use_container_width=True):
                c = get_conn(); cur = c.cursor()
                cur.execute("DELETE FROM users WHERE username=%s", (del_u,))
                c.commit(); release(c)
                st.success(f"User '{del_u}' removed.")
                st.rerun()
        else:
            st.info("No other users found.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">All Users</div>', unsafe_allow_html=True)
    c = get_conn(); cur = c.cursor()
    cur.execute("SELECT username FROM users ORDER BY username")
    all_u = pd.DataFrame(cur.fetchall(), columns=["Username"]); release(c)
    all_u["Role"] = all_u["Username"].apply(lambda x: "Admin" if x == "admin" else "Employee")
    st.dataframe(all_u, use_container_width=True, hide_index=True, height=200)
    st.markdown('</div>', unsafe_allow_html=True)

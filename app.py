import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import json
from io import BytesIO
import os
import re

# ---------------- DB ----------------
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    st.error("❌ DATABASE_URL not set. Please configure it in environment variables.")
    st.stop()

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

st.set_page_config(layout="wide")

# ---------------- UI ----------------
st.markdown("""
<style>
section[data-testid="stSidebar"] {
    width: 280px !important;
}
section[data-testid="stSidebar"] > div {
    width: 280px !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------- BG ----------------
def set_bg(c1, c2):
    st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, {c1} 0%, {c2} 100%);
        background-attachment: fixed;
    }}
    </style>
    """, unsafe_allow_html=True)

# ---------------- TABLES ----------------
cur.execute("""
CREATE TABLE IF NOT EXISTS parts_table (
    id SERIAL PRIMARY KEY,
    part_no TEXT,
    brand TEXT,
    price NUMERIC
);
""")

cur.execute("""
ALTER TABLE parts_table
ADD COLUMN IF NOT EXISTS supplier TEXT;
""")

cur.execute("""
DO $$
BEGIN
IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'unique_part_supplier'
) THEN
    ALTER TABLE parts_table
    ADD CONSTRAINT unique_part_supplier UNIQUE (part_no, brand, supplier);
END IF;
END$$;
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS saved_offers (
    id SERIAL PRIMARY KEY,
    username TEXT,
    data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
""")

cur.execute("""
INSERT INTO users (username, password)
SELECT 'admin', 'admin'
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin')
""")

conn.commit()

# ---------------- HELPERS ----------------
def clean_col(name):
    """Aggressively normalize a column header to lowercase, no spaces/symbols."""
    return re.sub(r'[^a-z0-9]', '', name.strip().lower())

def load_brands():
    if "brands" in st.session_state:
        return st.session_state["brands"]
    cur.execute("SELECT DISTINCT brand FROM parts_table ORDER BY brand")
    return [x[0] for x in cur.fetchall()]

# ---------------- SESSION ----------------
if "table_data" not in st.session_state:
    st.session_state.table_data = pd.DataFrame()

if "input_table" not in st.session_state:
    st.session_state.input_table = pd.DataFrame(columns=["Brand", "Part No", "Qty"])

if "user" not in st.session_state:
    st.session_state.user = None

# ---------------- LOGIN ----------------
def login(u, p):
    cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (u, p))
    return cur.fetchone()

if st.session_state.user is None:
    st.markdown("<style>section[data-testid='stSidebar']{display:none;}</style>", unsafe_allow_html=True)
    set_bg("#eef4ff", "#f8fbff")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image("logo.png", width=160)
        except:
            pass
        st.markdown("### 👤 Sign In")
        u = st.text_input("Enter Username")
        p = st.text_input("Enter Password", type="password")

        if st.button("Click me to Continue"):
            if login(u, p):
                st.session_state.user = {"username": u}
                st.rerun()
            else:
                st.error("Invalid credentials")
    st.stop()

username = st.session_state.user["username"]

# ---------------- SIDEBAR ----------------
with st.sidebar:
    try:
        st.image("logo.png", width=140)
    except:
        pass
    st.markdown(f"### 👤 {username}")

    if username == "admin":
        pages = ["📊 Price Lookup", "📁 Saved Quotations", "📤 Data Upload", "🛠 Access Control"]
    else:
        pages = ["📊 Price Lookup", "📁 Saved Quotations"]

    page = st.radio("WorkSpace", pages)
    st.markdown("---")

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# ================= PRICE LOOKUP =================
if page == "📊 Price Lookup":
    set_bg("#f0f7ff", "#e6f0ff")
    st.title("Price Lookup Panel")

    brand_list = load_brands()

    st.markdown("#### Enter Parts to Look Up")
    input_df = st.data_editor(
        st.session_state.input_table,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Brand": st.column_config.SelectboxColumn("Brand", options=brand_list)
        },
        key="input_editor"
    )

    if st.button("🔍 Get Pricing"):
        all_results = []

        for _, r in input_df.iterrows():
            part = str(r.get("Part No", "")).strip()
            brand = str(r.get("Brand", "")).strip()

            if not part or not brand:
                continue

            qty = pd.to_numeric(r.get("Qty"), errors="coerce")
            if pd.isna(qty) or qty <= 0:
                qty = 1
            qty = int(qty)

            # Fetch ALL suppliers for this part+brand
            cur.execute("""
                SELECT supplier, price
                FROM parts_table
                WHERE TRIM(LOWER(part_no)) = TRIM(LOWER(%s))
                  AND TRIM(LOWER(brand))   = TRIM(LOWER(%s))
                ORDER BY price ASC
            """, (part, brand))

            matches = cur.fetchall()

            if matches:
                for supplier, price in matches:
                    all_results.append({
                        "Brand":    brand,
                        "Part No":  part,
                        "Supplier": supplier,
                        "Qty":      qty,
                        "Unit Price (JPY)": float(price),
                        "Amount (JPY)":     qty * float(price)
                    })
            else:
                all_results.append({
                    "Brand":    brand,
                    "Part No":  part,
                    "Supplier": "❌ Not Found",
                    "Qty":      qty,
                    "Unit Price (JPY)": 0,
                    "Amount (JPY)":     0
                })

        st.session_state.table_data = pd.DataFrame(all_results)

    df = st.session_state.table_data

    if not df.empty:
        st.markdown("#### Results — All Supplier Prices")

        # Highlight cheapest supplier per part
        def highlight_best(row):
            if "❌" in str(row["Supplier"]):
                return ["background-color: #ffe0e0"] * len(row)
            # Find min price for this part+brand group
            mask = (df["Part No"] == row["Part No"]) & (df["Brand"] == row["Brand"])
            min_price = df.loc[mask, "Unit Price (JPY)"].min()
            if row["Unit Price (JPY)"] == min_price and row["Unit Price (JPY)"] > 0:
                return ["background-color: #d4f7dc; font-weight: bold"] * len(row)
            return [""] * len(row)

        styled = df.style.apply(highlight_best, axis=1).format({
            "Unit Price (JPY)": "{:,.0f}",
            "Amount (JPY)":     "{:,.0f}"
        })

        st.dataframe(styled, use_container_width=True, hide_index=True)
        st.caption("🟢 Green = cheapest supplier for that part")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Save Quotation"):
                cur.execute(
                    "INSERT INTO saved_offers (username, data) VALUES (%s, %s)",
                    (username, json.dumps(df.to_dict(orient="records")))
                )
                conn.commit()
                st.success("Quotation saved successfully!")

        with col2:
            excel_buf = BytesIO()
            df.to_excel(excel_buf, index=False)
            excel_buf.seek(0)
            st.download_button(
                "⬇ Download as Excel",
                excel_buf,
                file_name="price_lookup.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("Enter brands and part numbers above, then click Get Pricing.")

# ================= SAVED =================
elif page == "📁 Saved Quotations":
    set_bg("#f0fff4", "#e6fffa")
    st.title("Saved Quotations")

    cur.execute("""
        SELECT id, username, data, created_at::date
        FROM saved_offers
        ORDER BY created_at DESC
    """)
    rows = cur.fetchall()

    if not rows:
        st.info("No saved offers yet.")
        st.stop()

    all_data = []
    for offer_id, user, data, date_only in rows:
        df = pd.DataFrame(json.loads(data) if isinstance(data, str) else data)
        df["Employee"] = user
        df["Saved On"] = date_only
        df["Offer ID"] = offer_id
        all_data.append(df)

    final_df = pd.concat(all_data, ignore_index=True)
    final_df.insert(0, "Select", False)

    edited_df = st.data_editor(final_df, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)

    with col1:
        output = BytesIO()
        final_df.drop(columns=["Select"]).to_excel(output, index=False)
        output.seek(0)
        st.download_button("⬇ Download All (Excel)", output, file_name="saved_offers.xlsx")

    with col2:
        if st.button("🗑 Delete Selected Quotations"):
            selected = edited_df[edited_df["Select"] == True]
            if not selected.empty:
                ids = selected["Offer ID"].unique().tolist()
                cur.execute("DELETE FROM saved_offers WHERE id = ANY(%s)", (ids,))
                conn.commit()
                st.success(f"Deleted {len(ids)} quotation(s).")
                st.rerun()
            else:
                st.warning("No rows selected.")

# ================= UPLOAD =================
elif page == "📤 Data Upload":
    set_bg("#f5f0ff", "#ede9fe")
    st.title("Master Data Upload")

    st.markdown("""
    **Expected Excel columns:** `Make` · `Part Number` · `JPY Price` · `Supplier`  
    *(Column names are case-insensitive and extra spaces are handled automatically)*
    """)

    file = st.file_uploader("Upload Price Sheet (.xlsx)", type=["xlsx"])

    if file:
        df_raw = pd.read_excel(file, dtype=str)

        # ── Robust column normalization ──────────────────────────────────
        # Build a mapping from cleaned header → original header
        col_map = {clean_col(c): c for c in df_raw.columns}

        # Accept multiple possible spellings for each required column
        ALIASES = {
            "brand":    ["make", "brand", "manufacturer"],
            "part_no":  ["partnumber", "partno", "part", "partnum"],
            "price":    ["jpyprice", "price", "unitprice", "jpy"],
            "supplier": ["supplier", "vendor", "source"],
        }

        rename = {}
        for target, aliases in ALIASES.items():
            for alias in aliases:
                if alias in col_map:
                    rename[col_map[alias]] = target
                    break

        df_raw.rename(columns=rename, inplace=True)

        missing = [c for c in ["brand", "part_no", "price", "supplier"] if c not in df_raw.columns]
        if missing:
            st.error(f"❌ Could not find these columns: {missing}\n\nFound: {list(df_raw.columns)}")
            st.stop()

        # ── Clean values ─────────────────────────────────────────────────
        df_raw["brand"]    = df_raw["brand"].astype(str).str.replace(r'[\n"\r]', '', regex=True).str.strip()
        df_raw["part_no"]  = df_raw["part_no"].astype(str).str.replace(r'[\n"\r]', '', regex=True).str.strip()
        df_raw["supplier"] = df_raw["supplier"].astype(str).str.strip()
        df_raw["price"]    = pd.to_numeric(df_raw["price"], errors="coerce").fillna(0)

        df_raw = df_raw[
            (df_raw["part_no"] != "") &
            (df_raw["brand"] != "") &
            (df_raw["supplier"] != "") &
            (df_raw["part_no"] != "nan") &
            (df_raw["brand"] != "nan")
        ]

        st.markdown(f"**Preview — {len(df_raw):,} valid rows found:**")
        st.dataframe(df_raw[["brand", "part_no", "price", "supplier"]].head(20), use_container_width=True)

        if st.button("✅ Confirm & Upload to Database"):
            values = list(df_raw[["part_no", "brand", "price", "supplier"]].itertuples(index=False, name=None))

            execute_values(
                cur,
                """
                INSERT INTO parts_table (part_no, brand, price, supplier)
                VALUES %s
                ON CONFLICT (part_no, brand, supplier)
                DO UPDATE SET price = EXCLUDED.price
                """,
                values
            )
            conn.commit()

            # Refresh brand cache
            cur.execute("SELECT DISTINCT brand FROM parts_table ORDER BY brand")
            st.session_state["brands"] = [x[0] for x in cur.fetchall()]

            st.success(f"✅ Uploaded {len(values):,} rows successfully!")
            st.rerun()

# ================= ADMIN =================
elif page == "🛠 Access Control":
    set_bg("#f3f6ff", "#e8edff")
    st.title("User & Access Control")

    st.markdown("#### Create New User")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Create User"):
        if u and p:
            try:
                cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (u, p))
                conn.commit()
                st.success(f"User '{u}' created.")
            except Exception as e:
                conn.rollback()
                st.error(f"Could not create user: {e}")
        else:
            st.warning("Please enter both username and password.")

    st.markdown("---")
    st.markdown("#### Remove Employee")

    cur.execute("SELECT username FROM users WHERE username != 'admin' ORDER BY username")
    users = [x[0] for x in cur.fetchall()]

    if users:
        user_to_delete = st.selectbox("Select Employee", users)
        if st.button("Delete Employee"):
            cur.execute("DELETE FROM users WHERE username=%s", (user_to_delete,))
            conn.commit()
            st.success(f"User '{user_to_delete}' deleted.")
            st.rerun()
    else:
        st.info("No other users found.")

import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import json
from io import BytesIO
import os

# ---------------- DB (SECURE) ----------------
DATABASE_URL = os.getenv("DATABASE_URL")

# ✅ safety check
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

# ✅ ensure supplier column exists
cur.execute("""
ALTER TABLE parts_table
ADD COLUMN IF NOT EXISTS supplier TEXT;
""")

# ✅ unique constraint safely
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
INSERT INTO users (username,password)
SELECT 'admin','admin'
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username='admin')
""")

conn.commit()

# ---------------- BRAND LOADER ----------------
def load_brands():
    if "brands" in st.session_state:
        return st.session_state["brands"]

    cur.execute("SELECT DISTINCT brand FROM parts_table ORDER BY brand")
    return [x[0] for x in cur.fetchall()]

# ---------------- SESSION ----------------
if "table_data" not in st.session_state:
    st.session_state.table_data = pd.DataFrame(columns=[
        "Brand","Part No","Supplier","Qty","Price","Amount"
    ])

if "input_table" not in st.session_state:
    st.session_state.input_table = pd.DataFrame(columns=["Brand","Part No","Qty"])

if "user" not in st.session_state:
    st.session_state.user = None

# ---------------- LOGIN ----------------
def login(u,p):
    cur.execute("SELECT * FROM users WHERE username=%s AND password=%s",(u,p))
    return cur.fetchone()

if st.session_state.user is None:

    st.markdown("<style>section[data-testid='stSidebar']{display:none;}</style>", unsafe_allow_html=True)
    set_bg("#eef4ff","#f8fbff")

    col1,col2,col3 = st.columns([1,2,1])
    with col2:
        st.image("logo.png", width=160)
        st.markdown("### 👤 Sign In")

        u = st.text_input("Enter Username")
        p = st.text_input("Enter Password", type="password")

        if st.button("Click me to Continue"):
            if login(u,p):
                st.session_state.user = {"username":u}
                st.rerun()
            else:
                st.error("Invalid credentials")

    st.stop()

username = st.session_state.user["username"]

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.image("logo.png", width=140)
    st.markdown(f"### 👤 {username}")

    if username == "admin":
        pages = ["📊 Price Lookup","📁 Saved Quotations","📤 Data Upload","🛠 Access Control"]
    else:
        pages = ["📊 Price Lookup","📁 Saved Quotations"]

    page = st.radio("WorkSpace", pages)

    st.markdown("---")

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# ================= PRICE LOOKUP =================
if page == "📊 Price Lookup":
    set_bg("#f0f7ff","#e6f0ff")

    st.title("Price Lookup Panel")

    brand_list = load_brands()

    input_df = st.data_editor(
        st.session_state.input_table,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Brand": st.column_config.SelectboxColumn("Brand", options=brand_list)
        }
    )

    if st.button("Get Pricing"):

        result = []

        for _, r in input_df.iterrows():

            part = str(r.get("Part No","")).strip()
            brand = str(r.get("Brand","")).strip()

            qty = pd.to_numeric(r.get("Qty"), errors="coerce")
            if pd.isna(qty) or qty <= 0:
                qty = 1

            cur.execute("""
                SELECT supplier, price
                FROM parts_table
                WHERE LOWER(part_no)=LOWER(%s)
                AND LOWER(brand)=LOWER(%s)
            """, (part, brand))

            matches = cur.fetchall()

            if matches:
                for supplier, price in matches:
                    result.append({
                        "Brand": brand,
                        "Part No": part,
                        "Supplier": supplier,
                        "Qty": qty,
                        "Price": float(price),
                        "Amount": qty * float(price)
                    })
            else:
                result.append({
                    "Brand": brand,
                    "Part No": part,
                    "Supplier": "Not Found",
                    "Qty": qty,
                    "Price": 0,
                    "Amount": 0
                })

        st.session_state.table_data = pd.DataFrame(result)

    df = st.session_state.table_data
    st.dataframe(df, use_container_width=True)

    if st.button("💾 Save Quotation"):
        if not df.empty:
            cur.execute(
                "INSERT INTO saved_offers (username,data) VALUES (%s,%s)",
                (username, json.dumps(df.to_dict(orient="records")))
            )
            conn.commit()
            st.success("Quotation saved successfully")

# ================= SAVED =================
elif page == "📁 Saved Quotations":
    set_bg("#f0fff4","#e6fffa")
    st.title("Saved Quotations")

    cur.execute("""
        SELECT id, username, data, created_at::date
        FROM saved_offers
        ORDER BY created_at DESC
    """)
    rows = cur.fetchall()

    if not rows:
        st.info("No saved offers")
        st.stop()

    all_data = []

    for offer_id, user, data, date_only in rows:
        df = pd.DataFrame(json.loads(data) if isinstance(data,str) else data)
        df["Employee"] = user
        df["Saved On"] = date_only
        df["Offer ID"] = offer_id
        all_data.append(df)

    final_df = pd.concat(all_data, ignore_index=True)

    final_df.insert(0, "Select", False)

    edited_df = st.data_editor(final_df, use_container_width=True)

    output = BytesIO()
    final_df.to_excel(output, index=False)
    output.seek(0)

    st.download_button("⬇ Download Excel", output, file_name="saved_offers.xlsx")

    if st.button("Delete Selected Quotations"):
        selected = edited_df[edited_df["Select"] == True]
        if not selected.empty:
            ids = selected["Offer ID"].unique().tolist()
            cur.execute("DELETE FROM saved_offers WHERE id = ANY(%s)", (ids,))
            conn.commit()
            st.rerun()

# ================= UPLOAD =================
elif page == "📤 Data Upload":
    set_bg("#f5f0ff","#ede9fe")
    st.title("Master Data Upload")

    file = st.file_uploader("Upload Price Sheet", type=["xlsx"])

    if file:
        df = pd.read_excel(file, dtype=str)

        df.columns = df.columns.str.strip().str.lower()

        df.rename(columns={
            "make": "brand",
            "part number": "part_no",
            "jpy price": "price",
            "supplier": "supplier"
        }, inplace=True)

        df["brand"] = df["brand"].str.replace(r'[\n"]', '', regex=True).str.strip()
        df["part_no"] = df["part_no"].str.replace(r'[\n"]', '', regex=True).str.strip()
        df["supplier"] = df["supplier"].str.strip()

        df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)

        df = df[(df["part_no"] != "") & (df["brand"] != "") & (df["supplier"] != "")]

        st.session_state["brands"] = sorted(df["brand"].unique().tolist())

        values = list(df[["part_no","brand","price","supplier"]]
                      .itertuples(index=False, name=None))

        execute_values(
            cur,
            """
            INSERT INTO parts_table (part_no,brand,price,supplier)
            VALUES %s
            ON CONFLICT (part_no, brand, supplier)
            DO UPDATE SET price = EXCLUDED.price
            """,
            values
        )

        conn.commit()

        st.success("File uploaded successfully")
        st.rerun()

# ================= ADMIN =================
elif page == "🛠 Access Control":
    set_bg("#f3f6ff", "#e8edff")
    st.title("User & Access Control")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Create User"):
        cur.execute("INSERT INTO users (username,password) VALUES (%s,%s)",(u,p))
        conn.commit()
        st.success("User Created")

    cur.execute("SELECT username FROM users WHERE username != 'admin'")
    users = [x[0] for x in cur.fetchall()]

    if users:
        user_to_delete = st.selectbox("Select Employee", users)

        if st.button("Delete Employee"):
            cur.execute("DELETE FROM users WHERE username=%s", (user_to_delete,))
            conn.commit()
            st.rerun()

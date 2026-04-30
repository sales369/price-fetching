import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import re
import json
from io import BytesIO

# ---------------- DB ----------------
DATABASE_URL = "postgresql://parts_ty2y_user:6Jiri0NZpiwj60mlHi1P4xBIikFn3A4U@dpg-d7pf3rn7f7vs739ipo7g-a.oregon-postgres.render.com/parts_ty2y"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

st.set_page_config(layout="wide")

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
    price NUMERIC,
    description TEXT,
    moq INTEGER
);
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

# ---------------- CACHE ----------------
@st.cache_data
def load_brands():
    cur.execute("SELECT DISTINCT brand FROM parts_table ORDER BY brand")
    return [x[0] for x in cur.fetchall()]

# ---------------- SESSION ----------------
if "table_data" not in st.session_state:
    st.session_state.table_data = pd.DataFrame(columns=[
        "Brand","Part No","Description","Qty","Price","Amount"
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

            # ✅ FIXED NORMALIZATION
            part = str(r.get("Part No","")).strip().replace(".0","")
            brand = str(r.get("Brand","")).strip()

            qty = pd.to_numeric(r.get("Qty"), errors="coerce")
            if pd.isna(qty) or qty <= 0:
                qty = 1

            price = 0
            desc = "Not Found"

            if part and brand:
                cur.execute("""
                    SELECT price, description
                    FROM parts_table
                    WHERE LOWER(part_no)=LOWER(%s)
                    AND LOWER(brand)=LOWER(%s)
                    LIMIT 1
                """, (part, brand))

                match = cur.fetchone()

                if match:
                    price, desc = match

            result.append({
                "Brand": brand,
                "Part No": part,
                "Description": desc,
                "Qty": qty,
                "Price": float(price),
                "Amount": qty * float(price)
            })

        st.session_state.table_data = pd.DataFrame(result)

    df = st.session_state.table_data
    st.dataframe(df, use_container_width=True)

# ================= UPLOAD =================
elif page == "📤 Data Upload":
    set_bg("#f5f0ff","#ede9fe")
    st.title("Master Data Upload")

    files = st.file_uploader("Upload Price Sheet", type=["xlsx"], accept_multiple_files=True)

    if files:
        for f in files:

            # ✅ FAST + FIX
            df = pd.read_excel(f, dtype=str)

            df.columns = df.columns.str.strip().str.lower()

            df.rename(columns={
                "part no": "part_no",
                "price [eur]": "price",
                "item description": "description",
                "moq": "moq"
            }, inplace=True)

            df = df.fillna("")

            # ✅ NORMALIZATION
            df["part_no"] = df["part_no"].str.strip().str.replace(".0","", regex=False)
            df["brand"] = df["brand"].str.strip()

            df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)
            df["moq"] = pd.to_numeric(df["moq"], errors="coerce").fillna(0).astype(int)

            df = df[(df["part_no"] != "") & (df["brand"] != "")]

            values = list(df[["part_no","brand","price","description","moq"]].itertuples(index=False, name=None))

            execute_values(
                cur,
                "INSERT INTO parts_table (part_no,brand,price,description,moq) VALUES %s",
                values
            )

            conn.commit()
            st.success(f"{f.name} uploaded successfully")

        st.cache_data.clear()
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

    # ✅ REMOVE USER
    st.markdown("---")
    st.subheader("Remove Employee")

    cur.execute("SELECT username FROM users WHERE username != 'admin'")
    users = [x[0] for x in cur.fetchall()]

    if users:
        user_to_delete = st.selectbox("Select Employee", users)

        if st.button("Delete Employee"):
            if user_to_delete == username:
                st.error("You cannot delete yourself")
            else:
                cur.execute("DELETE FROM users WHERE username=%s", (user_to_delete,))
                conn.commit()
                st.success(f"{user_to_delete} removed successfully")
                st.rerun()

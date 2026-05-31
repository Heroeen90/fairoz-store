import streamlit as st
from datetime import datetime
from database import init_db, get_connection

# تهيئة قاعدة البيانات
init_db()

st.set_page_config(page_title="محل فيروز", layout="wide")

st.title("🛒 نظام إدارة محل فيروز")
st.subheader("بإدارة الحاج تحسين عبد ديوان")

conn = get_connection()
cursor = conn.cursor()

# =========================
# 🔘 قائمة اختيار العملية
# =========================
st.sidebar.title("➕ إضافة عملية")

operation_type = st.sidebar.selectbox(
    "نوع العملية",
    [
        "مبيعات",
        "مشتريات",
        "مصروف",
        "سلفة عامل",
        "راتب عامل",
        "سحب تحسين"
    ]
)

amount = st.sidebar.number_input("المبلغ", min_value=0)

category = ""
description = ""

# =========================
# 🧾 تفاصيل حسب النوع
# =========================

if operation_type == "مشتريات":
    category = st.sidebar.text_input("تفاصيل المشتريات (مثال: شيبس، ماء...)")

elif operation_type == "مصروف":
    category = st.sidebar.selectbox(
        "نوع المصروف",
        ["كهرباء", "صيانة", "نقليات", "أدوات", "أخرى"]
    )
    description = st.sidebar.text_input("ملاحظة")

elif operation_type in ["سلفة عامل", "راتب عامل"]:
    category = st.sidebar.text_input("اسم العامل")

elif operation_type == "سحب تحسين":
    description = st.sidebar.text_input("ملاحظة (اختياري)")

elif operation_type == "مبيعات":
    description = st.sidebar.text_input("ملاحظة (اختياري)")

# =========================
# 💾 زر الحفظ
# =========================
if st.sidebar.button("💾 حفظ العملية"):

    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO transactions (type, category, amount, description, date)
        VALUES (?, ?, ?, ?, ?)
    """, (
        operation_type,
        category,
        amount,
        description,
        date
    ))

    conn.commit()

    st.success("تم حفظ العملية بنجاح ✅")

# =========================
# 📋 عرض آخر العمليات
# =========================
st.divider()

st.subheader("📋 آخر العمليات")

cursor.execute("SELECT * FROM transactions ORDER BY id DESC LIMIT 10")
rows = cursor.fetchall()

for row in rows:
    st.write(row)

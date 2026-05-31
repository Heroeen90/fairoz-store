import streamlit as st
from datetime import datetime
from database import init_db, get_connection

# =========================
# 🧱 تهيئة النظام
# =========================
init_db()

st.set_page_config(page_title="محل فيروز", layout="wide")

st.title("🛒 نظام إدارة محل فيروز")
st.subheader("بإدارة الحاج تحسين عبد ديوان")

conn = get_connection()
cursor = conn.cursor()

# =========================
# 📊 دوال الحسابات العامة
# =========================
def get_sum_by_type(op_type):
    cursor.execute(
        "SELECT SUM(amount) FROM transactions WHERE type=?",
        (op_type,)
    )
    result = cursor.fetchone()[0]
    return result if result else 0


def get_total_sales():
    return get_sum_by_type("مبيعات")


def get_total_expenses():
    cursor.execute("""
        SELECT SUM(amount) FROM transactions 
        WHERE type IN ('مشتريات','مصروف','سلفة عامل','راتب عامل','سحب تحسين')
    """)
    result = cursor.fetchone()[0]
    return result if result else 0


# =========================
# 👤 دوال العمال
# =========================
def get_employee_balance(name):
    cursor.execute("""
        SELECT type, amount FROM transactions
        WHERE category=?
    """, (name,))
    
    rows = cursor.fetchall()

    loans = 0
    salaries = 0

    for r in rows:
        if r[0] == "سلفة عامل":
            loans += r[1]
        elif r[0] == "راتب عامل":
            salaries += r[1]

    return salaries - loans


# =========================
# 📊 لوحة التحكم
# =========================
st.divider()
st.subheader("📊 لوحة التحكم المالية")

sales = get_total_sales()
expenses = get_total_expenses()
profit = sales - expenses

col1, col2, col3 = st.columns(3)

col1.metric("💰 المبيعات", f"{sales:,} IQD")
col2.metric("💸 المصروفات", f"{expenses:,} IQD")
col3.metric("📈 الربح", f"{profit:,} IQD")

st.divider()

# =========================
# ➕ إضافة العمليات
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

if operation_type == "مشتريات":
    category = st.sidebar.text_input("تفاصيل المشتريات")

elif operation_type == "مصروف":
    category = st.sidebar.selectbox(
        "نوع المصروف",
        ["كهرباء", "صيانة", "نقليات", "معدات", "أخرى"]
    )
    description = st.sidebar.text_input("ملاحظة")

elif operation_type in ["سلفة عامل", "راتب عامل"]:
    category = st.sidebar.selectbox(
        "اسم العامل",
        ["مصطفى", "حسين", "عمار", "كرار"]
    )

elif operation_type == "سحب تحسين":
    description = st.sidebar.text_input("ملاحظة")

elif operation_type == "مبيعات":
    description = st.sidebar.text_input("ملاحظة")

# =========================
# 💾 حفظ العملية
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

    st.success("تم الحفظ بنجاح ✅")
    st.rerun()

# =========================
# 👤 لوحة العمال
# =========================
st.divider()
st.subheader("👤 كشف العمال")

employees = ["مصطفى", "حسين", "عمار", "كرار"]

for emp in employees:
    balance = get_employee_balance(emp)

    st.write(f"👤 {emp} → الرصيد: {balance:,} IQD")

# =========================
# 📋 آخر العمليات
# =========================
st.divider()
st.subheader("📋 آخر العمليات")

cursor.execute("""
    SELECT type, category, amount, description, date
    FROM transactions
    ORDER BY id DESC
    LIMIT 15
""")

rows = cursor.fetchall()

for row in rows:
    st.write({
        "النوع": row[0],
        "الشخص/التصنيف": row[1],
        "المبلغ": row[2],
        "الملاحظة": row[3],
        "التاريخ": row[4],
    })

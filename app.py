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
# 📊 الدوال الأساسية
# =========================
def get_sum_by_type(op_type):
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type=?", (op_type,))
    result = cursor.fetchone()[0]
    return result if result else 0


def get_total_by_types(types):
    cursor.execute(
        f"SELECT SUM(amount) FROM transactions WHERE type IN ({','.join(['?']*len(types))})",
        types
    )
    result = cursor.fetchone()[0]
    return result if result else 0


def get_monthly_data():
    cursor.execute("""
        SELECT type, amount, date, category, description
        FROM transactions
        ORDER BY date DESC
    """)
    return cursor.fetchall()


# =========================
# 📊 لوحة التحكم الرئيسية
# =========================
st.divider()
st.subheader("📊 لوحة التحكم المالية")

sales = get_sum_by_type("مبيعات")

expenses = get_total_by_types([
    "مشتريات", "مصروف", "سلفة عامل", "راتب عامل", "سحب تحسين"
])

profit = sales - expenses

col1, col2, col3 = st.columns(3)

col1.metric("💰 المبيعات", f"{sales:,} IQD")
col2.metric("💸 المصروفات", f"{expenses:,} IQD")
col3.metric("📈 صافي الربح", f"{profit:,} IQD")

st.divider()

# =========================
# 📌 أين ذهبت الأموال؟
# =========================
st.subheader("📌 أين ذهبت الأموال؟")

cat_sales = get_sum_by_type("مبيعات")
cat_purchases = get_sum_by_type("مشتريات")
cat_expenses = get_sum_by_type("مصروف")
cat_loans = get_sum_by_type("سلفة عامل")
cat_salaries = get_sum_by_type("راتب عامل")
cat_owner = get_sum_by_type("سحب تحسين")

col1, col2, col3 = st.columns(3)

col1.metric("🛒 مبيعات", f"{cat_sales:,}")
col2.metric("📦 مشتريات", f"{cat_purchases:,}")
col3.metric("⚙️ مصروفات", f"{cat_expenses:,}")

col1, col2, col3 = st.columns(3)

col1.metric("👤 رواتب", f"{cat_salaries:,}")
col2.metric("💳 سلف", f"{cat_loans:,}")
col3.metric("🏠 سحب تحسين", f"{cat_owner:,}")

st.divider()

# =========================
# ➕ إدخال العمليات
# =========================
st.sidebar.title("➕ إضافة عملية")

operation_type = st.sidebar.selectbox(
    "نوع العملية",
    ["مبيعات", "مشتريات", "مصروف", "سلفة عامل", "راتب عامل", "سحب تحسين"]
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
# 📋 سجل العمليات
# =========================
st.divider()
st.subheader("📋 آخر العمليات")

rows = get_monthly_data()[:20]

for r in rows:
    st.write({
        "النوع": r[0],
        "المبلغ": r[1],
        "التاريخ": r[2],
        "الشخص/التصنيف": r[3],
        "الملاحظة": r[4],
    })

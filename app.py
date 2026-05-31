import streamlit as st
from datetime import datetime
from database import init_db, get_connection
import pandas as pd

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
# 📦 جلب البيانات
# =========================
def get_all_transactions():
    cursor.execute("""
        SELECT type, amount, date, category, description
        FROM transactions
        ORDER BY date DESC
    """)
    return cursor.fetchall()

def get_sum_by_type(op_type):
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type=?", (op_type,))
    res = cursor.fetchone()[0]
    return res if res else 0

def get_sum_in_list(types):
    cursor.execute(
        f"SELECT SUM(amount) FROM transactions WHERE type IN ({','.join(['?']*len(types))})",
        types
    )
    res = cursor.fetchone()[0]
    return res if res else 0

# =========================
# 📊 لوحة التحكم
# =========================
st.divider()
st.subheader("📊 لوحة التحكم")

sales = get_sum_by_type("مبيعات")
expenses = get_sum_in_list(["مشتريات","مصروف","سلفة عامل","راتب عامل","سحب تحسين"])

profit = sales - expenses

c1, c2, c3 = st.columns(3)
c1.metric("💰 المبيعات", f"{sales:,} IQD")
c2.metric("💸 المصروفات", f"{expenses:,} IQD")
c3.metric("📈 الربح", f"{profit:,} IQD")

st.divider()

# =========================
# 📅 فلترة شهرية
# =========================
st.subheader("📅 التقارير الشهرية")

all_data = get_all_transactions()

df = pd.DataFrame(all_data, columns=["type","amount","date","category","description"])

df["date"] = pd.to_datetime(df["date"])

month = st.selectbox("اختر الشهر", sorted(df["date"].dt.month.unique()))

year = st.selectbox("اختر السنة", sorted(df["date"].dt.year.unique()))

filtered = df[(df["date"].dt.month == month) & (df["date"].dt.year == year)]

st.write("عدد العمليات:", len(filtered))

st.dataframe(filtered)

# =========================
# 📌 تحليل الشهر
# =========================
st.subheader("📌 تحليل الشهر")

sales_m = filtered[filtered["type"] == "مبيعات"]["amount"].sum()
purchases_m = filtered[filtered["type"] == "مشتريات"]["amount"].sum()
expenses_m = filtered[filtered["type"] == "مصروف"]["amount"].sum()
loans_m = filtered[filtered["type"] == "سلفة عامل"]["amount"].sum()
salary_m = filtered[filtered["type"] == "راتب عامل"]["amount"].sum()
owner_m = filtered[filtered["type"] == "سحب تحسين"]["amount"].sum()

total_exp = purchases_m + expenses_m + loans_m + salary_m + owner_m
profit_m = sales_m - total_exp

col1, col2, col3 = st.columns(3)
col1.metric("💰 مبيعات الشهر", f"{sales_m:,}")
col2.metric("💸 مصروفات الشهر", f"{total_exp:,}")
col3.metric("📈 صافي الشهر", f"{profit_m:,}")

st.divider()

# =========================
# 📌 أين ذهبت الأموال؟
# =========================
st.subheader("📌 أين ذهبت أموال الشهر؟")

st.write({
    "مشتريات": purchases_m,
    "مصروفات": expenses_m,
    "رواتب": salary_m,
    "سلف": loans_m,
    "سحب تحسين": owner_m
})

# =========================
# ➕ إدخال العمليات
# =========================
st.sidebar.title("➕ إضافة عملية")

op = st.sidebar.selectbox(
    "نوع العملية",
    ["مبيعات","مشتريات","مصروف","سلفة عامل","راتب عامل","سحب تحسين"]
)

amount = st.sidebar.number_input("المبلغ", min_value=0)

cat = ""
desc = ""

if op == "مشتريات":
    cat = st.sidebar.text_input("تفاصيل")

elif op == "مصروف":
    cat = st.sidebar.selectbox("نوع المصروف",["كهرباء","صيانة","نقليات","معدات","أخرى"])
    desc = st.sidebar.text_input("ملاحظة")

elif op in ["سلفة عامل","راتب عامل"]:
    cat = st.sidebar.selectbox("العامل",["مصطفى","حسين","عمار","كرار"])

elif op == "سحب تحسين":
    desc = st.sidebar.text_input("ملاحظة")

elif op == "مبيعات":
    desc = st.sidebar.text_input("ملاحظة")

if st.sidebar.button("💾 حفظ"):

    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO transactions(type,category,amount,description,date)
        VALUES(?,?,?,?,?)
    """,(op,cat,amount,desc,date))

    conn.commit()
    st.success("تم الحفظ ✅")
    st.rerun()

# =========================
# 📋 السجل
# =========================
st.divider()
st.subheader("📋 آخر العمليات")

st.dataframe(df.head(20))

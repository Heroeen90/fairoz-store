import streamlit as st
from datetime import datetime
from database import init_db, get_connection
import pandas as pd
import io

# =========================
# 🧱 INIT
# =========================
init_db()

st.set_page_config(page_title="محل فيروز", layout="wide")

conn = get_connection()
cursor = conn.cursor()

# =========================
# 🔐 LOGIN SYSTEM (PIN)
# =========================
PIN = "1234"

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 تسجيل الدخول")

    pin_input = st.text_input("أدخل PIN", type="password")

    if st.button("دخول"):
        if pin_input == PIN:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("PIN خطأ ❌")

    st.stop()

# =========================
# 🏪 HEADER
# =========================
st.title("🛒 محل فيروز")
st.subheader("بإدارة الحاج تحسين عبد ديوان")

# =========================
# 📦 LOAD DATA
# =========================
def load_data():
    cursor.execute("""
        SELECT type, category, amount, description, date
        FROM transactions
        ORDER BY id DESC
    """)
    return cursor.fetchall()

data = load_data()
df = pd.DataFrame(data, columns=["type","category","amount","description","date"])
df["date"] = pd.to_datetime(df["date"])

# =========================
# 📊 DASHBOARD
# =========================
st.divider()
st.subheader("📊 لوحة التحكم")

def sum_type(t):
    return df[df["type"] == t]["amount"].sum()

sales = sum_type("مبيعات")
purchases = sum_type("مشتريات")
expenses = sum_type("مصروف")
loans = sum_type("سلفة عامل")
salary = sum_type("راتب عامل")
owner = sum_type("سحب تحسين")

total_exp = purchases + expenses + loans + salary + owner
profit = sales - total_exp

c1, c2, c3 = st.columns(3)
c1.metric("💰 مبيعات", f"{sales:,} IQD")
c2.metric("💸 مصروفات", f"{total_exp:,} IQD")
c3.metric("📈 ربح", f"{profit:,} IQD")

st.divider()

# =========================
# 📌 WHERE MONEY WENT
# =========================
st.subheader("📌 أين ذهبت الأموال؟")

st.write({
    "مشتريات": purchases,
    "مصروفات": expenses,
    "رواتب": salary,
    "سلف": loans,
    "سحب تحسين": owner
})

st.divider()

# =========================
# 📅 FILTER
# =========================
st.subheader("📅 التقارير")

month = st.selectbox("الشهر", sorted(df["date"].dt.month.unique()))
year = st.selectbox("السنة", sorted(df["date"].dt.year.unique()))

filtered = df[(df["date"].dt.month == month) & (df["date"].dt.year == year)]

st.dataframe(filtered)

st.divider()

# =========================
# 📤 EXPORT EXCEL
# =========================
st.subheader("📤 تصدير البيانات")

output = io.BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    filtered.to_excel(writer, index=False)

st.download_button(
    "⬇️ تحميل Excel",
    data=output.getvalue(),
    file_name="fairoz_report.xlsx"
)

# =========================
# 💾 BACKUP
# =========================
st.subheader("💾 النسخ الاحتياطي")

backup_data = df.to_csv(index=False).encode('utf-8')

st.download_button(
    "⬇️ تحميل Backup CSV",
    data=backup_data,
    file_name="fairoz_backup.csv",
    mime="text/csv"
)

# =========================
# ➕ QUICK ADD (MOBILE FRIENDLY)
# =========================
st.sidebar.title("⚡ إضافة سريعة")

op = st.sidebar.selectbox(
    "العملية",
    ["مبيعات","مشتريات","مصروف","سلفة عامل","راتب عامل","سحب تحسين"]
)

amount = st.sidebar.number_input("المبلغ", min_value=0)

cat = ""
desc = ""

if op == "مشتريات":
    cat = st.sidebar.text_input("تفاصيل")

elif op == "مصروف":
    cat = st.sidebar.selectbox("نوع",["كهرباء","صيانة","نقليات","معدات","أخرى"])

elif op in ["سلفة عامل","راتب عامل"]:
    cat = st.sidebar.selectbox("عامل",["مصطفى","حسين","عمار","كرار"])

elif op == "سحب تحسين":
    desc = st.sidebar.text_input("ملاحظة")

elif op == "مبيعات":
    desc = st.sidebar.text_input("ملاحظة")

if st.sidebar.button("💾 حفظ"):

    cursor.execute("""
        INSERT INTO transactions(type,category,amount,description,date)
        VALUES (?,?,?,?,?)
    """,(op,cat,amount,desc,datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    st.success("تم الحفظ ✅")
    st.rerun()

# =========================
# 📋 LOG
# =========================
st.divider()
st.subheader("📋 آخر العمليات")

st.dataframe(df.head(25))

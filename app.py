import streamlit as st
from datetime import datetime, timedelta
from database import init_db, get_connection
import pandas as pd
import io

# =========================
# INIT
# =========================
init_db()
st.set_page_config(page_title="محل فيروز", layout="wide")

conn = get_connection()
cursor = conn.cursor()

# =========================
# LOGIN
# =========================
PIN = "1234"

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 دخول النظام")

    pin = st.text_input("PIN", type="password")

    if st.button("دخول"):
        if pin == PIN:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("خطأ في PIN")

    st.stop()

# =========================
# LOAD DATA (مرة واحدة)
# =========================
@st.cache_data
def load_data():
    cursor.execute("""
        SELECT type, category, amount, description, date
        FROM transactions
        ORDER BY id DESC
    """)
    return pd.DataFrame(cursor.fetchall(),
        columns=["type","category","amount","description","date"]
    )

df = load_data()
df["date"] = pd.to_datetime(df["date"])

# =========================
# TABS SYSTEM
# =========================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 لوحة التحكم",
    "➕ إضافة عملية",
    "📅 التقارير",
    "📋 السجل"
])

# =========================
# 📊 DASHBOARD
# =========================
with tab1:
    st.title("📊 لوحة التحكم")

    sales = df[df["type"] == "مبيعات"]["amount"].sum()
    purchases = df[df["type"] == "مشتريات"]["amount"].sum()
    expenses = df[df["type"] == "مصروف"]["amount"].sum()
    loans = df[df["type"] == "سلفة عامل"]["amount"].sum()
    salary = df[df["type"] == "راتب عامل"]["amount"].sum()
    owner = df[df["type"] == "سحب تحسين"]["amount"].sum()

    total_exp = purchases + expenses + loans + salary + owner
    profit = sales - total_exp

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 مبيعات", f"{sales:,}")
    c2.metric("💸 مصروفات", f"{total_exp:,}")
    c3.metric("📈 ربح", f"{profit:,}")

    st.divider()

    st.subheader("📌 أين ذهبت الأموال؟")

    st.bar_chart({
        "مشتريات": [purchases],
        "مصروفات": [expenses],
        "رواتب": [salary],
        "سلف": [loans],
        "سحب": [owner]
    })

    # 🔥 Insights
    st.subheader("🧠 تحليل ذكي")

    if not df.empty:
        biggest_expense = df.groupby("type")["amount"].sum().sort_values(ascending=False)

        st.write("📌 أعلى نوع صرف:")
        st.write(biggest_expense.head(3))

# =========================
# ➕ ADD
# =========================
with tab2:
    st.title("➕ إضافة عملية")

    op = st.selectbox(
        "نوع العملية",
        ["مبيعات","مشتريات","مصروف","سلفة عامل","راتب عامل","سحب تحسين"]
    )

    amount = st.number_input("المبلغ", min_value=0)

    cat = ""
    desc = ""

    if op == "مشتريات":
        cat = st.text_input("تفاصيل")

    elif op == "مصروف":
        cat = st.selectbox("نوع",["كهرباء","صيانة","نقليات","معدات","أخرى"])

    elif op in ["سلفة عامل","راتب عامل"]:
        cat = st.selectbox("عامل",["مصطفى","حسين","عمار","كرار"])

    elif op == "سحب تحسين":
        desc = st.text_input("ملاحظة")

    elif op == "مبيعات":
        desc = st.text_input("ملاحظة")

    if st.button("💾 حفظ"):
        cursor.execute("""
            INSERT INTO transactions(type,category,amount,description,date)
            VALUES (?,?,?,?,?)
        """,(op,cat,amount,desc,datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        conn.commit()
        st.success("تم الحفظ")
        st.rerun()

# =========================
# 📅 REPORTS
# =========================
with tab3:
    st.title("📅 التقارير")

    filter_type = st.selectbox("فلترة",["اليوم","آخر 7 أيام","الشهر"])

    now = datetime.now()

    if filter_type == "اليوم":
        f = df[df["date"].dt.date == now.date()]

    elif filter_type == "آخر 7 أيام":
        f = df[df["date"] >= now - timedelta(days=7)]

    else:
        f = df[df["date"].dt.month == now.month]

    st.dataframe(f)

    st.subheader("📊 تحليل")
    st.write(f.groupby("type")["amount"].sum())

    # export
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        f.to_excel(writer, index=False)

    st.download_button("📤 Excel", output.getvalue(), "report.xlsx")

# =========================
# 📋 LOG
# =========================
with tab4:
    st.title("📋 السجل")

    search = st.text_input("بحث")

    filtered = df.copy()

    if search:
        filtered = df[df.astype(str).apply(lambda x: x.str.contains(search)).any(axis=1)]

    st.dataframe(filtered.head(50))

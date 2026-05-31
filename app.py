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
            st.error("PIN غير صحيح ❌")

    st.stop()

# =========================
# LOAD DATA
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

if df.empty:
    df = pd.DataFrame(columns=["type","category","amount","description","date"])

df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
df["date"] = pd.to_datetime(df["date"], errors="coerce")

# =========================
# TABS
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
    c1.metric("💰 مبيعات", f"{sales:,.0f}")
    c2.metric("💸 مصروفات", f"{total_exp:,.0f}")
    c3.metric("📈 ربح", f"{profit:,.0f}")

    st.divider()

    st.subheader("📌 أين ذهبت الأموال؟")

    chart_data = {
        "مشتريات": float(purchases or 0),
        "مصروفات": float(expenses or 0),
        "رواتب": float(salary or 0),
        "سلف": float(loans or 0),
        "سحب": float(owner or 0)
    }

    st.bar_chart(chart_data)

    # =========================
    # 🧠 FIXED SMART ANALYTICS
    # =========================
    st.subheader("🧠 تحليل ذكي")

    if not df.empty:

        analysis = (
            df.groupby("type")["amount"]
            .sum()
            .fillna(0)
            .sort_values(ascending=False)
            .reset_index()
        )

        analysis.columns = ["نوع العملية", "المجموع"]

        st.dataframe(analysis)

    else:
        st.info("لا توجد بيانات بعد")

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
        st.cache_data.clear()
        st.success("تم الحفظ ✅")
        st.rerun()

# =========================
# 📅 REPORTS
# =========================
with tab3:
    st.title("📅 التقارير")

    filter_type = st.selectbox("فلترة",["اليوم","آخر 7 أيام","الشهر"])

    now = datetime.now()

    if filter_type == "اليوم":
        filtered = df[df["date"].dt.date == now.date()]

    elif filter_type == "آخر 7 أيام":
        filtered = df[df["date"] >= now - timedelta(days=7)]

    else:
        filtered = df[df["date"].dt.month == now.month]

    st.dataframe(filtered)

    st.subheader("📊 تحليل")

    if not filtered.empty:
        st.write(
            filtered.groupby("type")["amount"]
            .sum()
            .fillna(0)
        )
    else:
        st.info("لا توجد بيانات")

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        filtered.to_excel(writer, index=False)

    st.download_button("📤 Excel", output.getvalue(), "report.xlsx")

# =========================
# 📋 LOG
# =========================
with tab4:
    st.title("📋 السجل")

    search = st.text_input("بحث")

    filtered = df.copy()

    if search:
        filtered = df[df.astype(str).apply(
            lambda x: x.str.contains(search, case=False, na=False)
        ).any(axis=1)]

    st.dataframe(filtered.head(50))

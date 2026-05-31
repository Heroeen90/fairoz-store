import streamlit as st
from database import init_db

# تهيئة قاعدة البيانات
init_db()

st.set_page_config(page_title="محل فيروز", layout="wide")

st.title("🛒 نظام إدارة محل فيروز")
st.subheader("بإدارة الحاج تحسين عبد ديوان")

st.write("النظام قيد التطوير - النسخة الأولى")

# اختبار بسيط
if st.button("اختبار الاتصال بالنظام"):
    st.success("النظام يعمل بنجاح 🚀")

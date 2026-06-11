import streamlit as st
import requests

# 請確保這裡貼上的是您從 Google Apps Script 取得的那串 /exec 結尾的網址
GAS_URL = "https://script.google.com/macros/s/AKfycbzR2K6nyJvCtq1JrUsAQJ1h8NjzuJU9erW3tpKX1G41GcH1xx6mLVqyU8F_8iQOqhTi8w/exec"

st.set_page_config(page_title="班級經營系統", layout="centered")
st.title("👨‍🏫 班級經營系統")

tabs = st.tabs(["📊 點名/繳費", "🎲 抽籤/發言"])

with tabs[0]:
    st.subheader("點名與繳費")
    cls = st.text_input("班級 (如 301)")
    seat = st.number_input("座號", 1, 50)
    name = st.text_input("姓名")
    status = st.selectbox("狀態", ["出席", "缺席", "遲到"])
    pay = st.selectbox("費用", ["已繳", "未繳"])
    
    if st.button("儲存點名資料"):
        data = {"action": "record_attendance", "class_name": cls, "seat": seat, "name": name, "status": status, "payment": pay}
        requests.post(GAS_URL, json=data)
        st.success("紀錄已成功送出！")

with tabs[1]:
    st.subheader("課堂互動")
    cls_d = st.text_input("班級 (如 301)")
    name_d = st.text_input("學生姓名")
    if st.button("記錄發言"):
        data = {"action": "record_draw", "class_name": cls_d, "name": name_d, "result": "發言/抽籤"}
        requests.post(GAS_URL, json=data)
        st.success("互動紀錄已成功送出！")
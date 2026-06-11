import streamlit as st
import requests

# 請確認這裡的網址是您的 GAS 網址
GAS_URL = "https://script.google.com/macros/s/AKfycbzR2K6nyJvCtq1JrUsAQJ1h8NjzuJU9erW3tpKX1G41GcH1xx6mLVqyU8F_8iQOqhTi8w/exec"

# 假設的學生名單，之後可以從 Google Sheet 讀取
student_list = ["王小明", "李小華", "張大強", "陳美美"]

st.set_page_config(page_title="班級經營系統", layout="centered")
st.title("👨‍🏫 班級經營系統")

tabs = st.tabs(["📊 點名/繳費", "🎲 抽籤/發言"])

with tabs[0]:
    st.subheader("點名與繳費記錄")
    cls = st.text_input("輸入班級", key="c1")
    name = st.selectbox("選擇學生", student_list, key="n1")
    status = st.selectbox("出席狀態", ["出席", "缺席", "遲到"], key="s1")
    pay = st.selectbox("繳費狀態", ["已繳", "未繳"], key="p1")
    
    if st.button("儲存點名資料", key="b1"):
        data = {"action": "record_attendance", "class_name": cls, "name": name, "status": status, "payment": pay}
        requests.post(GAS_URL, json=data)
        st.success(f"{name} 的點名資料已送出！")

with tabs[1]:
    st.subheader("課堂互動記錄")
    cls_d = st.text_input("輸入班級", key="c2")
    name_d = st.selectbox("選擇學生", student_list, key="n2")
    if st.button("記錄發言", key="b2"):
        data = {"action": "record_draw", "class_name": cls_d, "name": name_d, "result": "發言"}
        requests.post(GAS_URL, json=data)
        st.success(f"{name_d} 的發言已記錄！")

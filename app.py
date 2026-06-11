import streamlit as st
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheet 讀取設定 (這裡需要設定權限)
def get_student_list():
    # 這是為了讓程式能連結到您的 Sheet
    # 實際運作時，您需要將憑證 JSON 檔設定在 Streamlit 的 Secrets 中
    # 為求簡單，我們暫時先用一個模擬的讀取邏輯
    return ["王玫鈞", "田宇豪", "吳克宸", "林秉寬", "姜睿謙"] # 之後可替換為實際讀取 Sheet 的代碼

st.set_page_config(page_title="班級經營系統", layout="centered")
st.title("👨‍🏫 班級經營系統")

tabs = st.tabs(["📊 點名/繳費", "🎲 抽籤/發言"])

with tabs[0]:
    st.subheader("點名與繳費記錄")
    cls = st.text_input("輸入班級", key="c1")
    # 直接使用函數讀取名單
    name = st.selectbox("選擇學生", get_student_list(), key="n1")
    status = st.selectbox("出席狀態", ["出席", "缺席", "遲到"], key="s1")
    pay = st.selectbox("繳費狀態", ["已繳", "未繳"], key="p1")
    
    if st.button("儲存點名資料", key="b1"):
        # 請確保這裡的 GAS_URL 是您正確的網址
        GAS_URL = "https://script.google.com/macros/s/AKfycbzR2K6nyJvCtq1JrUsAQJ1h8NjzuJU9erW3tpKX1G41GcH1xx6mLVqyU8F_8iQOqhTi8w/exec"
        data = {"action": "record_attendance", "class_name": cls, "name": name, "status": status, "payment": pay}
        requests.post(GAS_URL, json=data)
        st.success(f"{name} 的資料已送出！")

with tabs[1]:
    st.subheader("課堂互動記錄")
    cls_d = st.text_input("輸入班級", key="c2")
    name_d = st.selectbox("選擇發言學生", get_student_list(), key="n2")
    if st.button("記錄發言", key="b2"):
        GAS_URL = "https://script.google.com/macros/s/AKfycbzR2K6nyJvCtq1JrUsAQJ1h8NjzuJU9erW3tpKX1G41GcH1xx6mLVqyU8F_8iQOqhTi8w/exec"
        data = {"action": "record_draw", "class_name": cls_d, "name": name_d, "result": "發言"}
        requests.post(GAS_URL, json=data)
        st.success(f"{name_d} 的發言已記錄！")

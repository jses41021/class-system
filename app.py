import streamlit as st
import pandas as pd
import requests

# 您的 GAS 網址 (請確認已更換為您實際的網址)
GAS_URL = "https://script.google.com/macros/s/AKfycbzR2K6nyJvCtq1JrUsAQJ1h8NjzuJU9erW3tpKX1G41GcH1xx6mLVqyU8F_8iQOqhTi8w/exec"

st.set_page_config(page_title="班級經營系統", layout="wide")
st.title("👨‍🏫 班級經營系統 - 快速點名")

# 模擬從 Sheet 讀取到的全班名單
# 您之後可以改寫這裡，讓它讀取您的 Google Sheet
data = {
    "座號": [1, 2, 3, 4, 5],
    "姓名": ["王玫鈞", "田宇豪", "吳克宸", "林秉寬", "姜睿謙"],
    "狀態": ["出席"] * 5  # 預設全體出席
}
df = pd.DataFrame(data)

# 使用 data_editor 呈現表格，讓您可以直接在網頁上點選修改
edited_df = st.data_editor(
    df,
    column_config={
        "狀態": st.column_config.SelectboxColumn(
            "狀態",
            options=["出席", "缺席", "遲到"],
            required=True,
        )
    },
    hide_index=True,
)

if st.button("送出整班點名紀錄"):
    # 將表格資料轉換為 JSON 發送給 GAS
    records = edited_df.to_dict(orient="records")
    for record in records:
        payload = {
            "action": "record_attendance",
            "class_name": "301",
            "seat": record["座號"],
            "name": record["姓名"],
            "status": record["狀態"],
            "payment": "已繳"
        }
        requests.post(GAS_URL, json=payload)
    st.success("整班點名紀錄已成功同步至 Google Sheet！")

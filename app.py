import streamlit as st
import pandas as pd
import requests

# 1. 設定區 (請務必更換為您的網址)
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8_2gDvKiTieAleMNeHdN1owBrEtkhhWBrg3Bpl3b8CzURHgOBouqPJ-_-LTbP8ZXJyPywXlnTKkKj/pub?gid=0&single=true&output=csv"
GAS_URL = "https://script.google.com/macros/s/AKfycbzR2K6nyJvCtq1JrUsAQJ1h8NjzuJU9erW3tpKX1G41GcH1xx6mLVqyU8F_8iQOqhTi8w/exec"

st.set_page_config(page_title="班級經營全功能系統", layout="wide")
st.title("🍎 班級經營全功能系統")

# 讀取名單功能
@st.cache_data(ttl=600) # 每10分鐘更新一次名單
def load_data():
    try:
        df = pd.read_csv(CSV_URL)
        return df
    except:
        return pd.DataFrame(columns=["班級", "座號", "姓名"])

df_all = load_data()

# 側邊欄：選擇班級
all_classes = df_all["班級"].unique() if not df_all.empty else []
selected_class = st.sidebar.selectbox("請選擇操作班級", all_classes)

# 篩選出該班級學生
if selected_class:
    class_students = df_all[df_all["班級"] == selected_class].copy()
else:
    class_students = pd.DataFrame()

# 建立分頁
tab1, tab2, tab3 = st.tabs(["📊 快速點名", "🎲 抽籤互動", "💰 繳費管理"])

# --- Tab 1: 快速點名 ---
with tab1:
    st.subheader(f"【{selected_class}】全班點名 (預設出席)")
    if not class_students.empty:
        # 準備點名表格：加入「狀態」欄位並預設出席
        class_students["狀態"] = "出席"
        
        edited_df = st.data_editor(
            class_students[["座號", "姓名", "狀態"]],
            column_config={
                "狀態": st.column_config.SelectboxColumn("狀態", options=["出席", "缺席", "遲到"], required=True)
            },
            hide_index=True,
            key="attendance_editor"
        )
        
        if st.button("送出整班點名紀錄"):
            with st.spinner("傳送中..."):
                for _, row in edited_df.iterrows():
                    payload = {
                        "action": "record_attendance",
                        "class_name": str(selected_class),
                        "seat": int(row["座號"]),
                        "name": row["姓名"],
                        "status": row["狀態"],
                        "payment": "-"
                    }
                    requests.post(GAS_URL, json=payload)
                st.success(f"{selected_class} 點名紀錄已成功同步！")
    else:
        st.warning("請先在側邊欄選擇班級或檢查名單網址。")

# --- Tab 2: 抽籤互動 ---
with tab2:
    st.subheader("隨機抽籤與發言紀錄")
    if not class_students.empty:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎲 隨機抽一位學生"):
                lucky_one = class_students.sample(1).iloc[0]
                st.balloons()
                st.header(f"中獎者：{lucky_one['座號']}號 {lucky_one['姓名']}")
                st.session_state['last_drawn'] = lucky_one['姓名']
                st.session_state['last_drawn_seat'] = lucky_one['座號']

        with col2:
            if 'last_drawn' in st.session_state:
                st.write(f"紀錄對象：{st.session_state['last_drawn']}")
                comment = st.text_input("備註 (如：回答正確、加分)")
                if st.button("確認儲存發言紀錄"):
                    payload = {
                        "action": "record_draw",
                        "class_name": str(selected_class),
                        "seat": int(st.session_state['last_drawn_seat']),
                        "name": st.session_state['last_drawn'],
                        "result": comment if comment else "抽籤發言"
                    }
                    requests.post(GAS_URL, json=payload)
                    st.success("紀錄已存入 Sheet！")

# --- Tab 3: 繳費管理 ---
with tab3:
    st.subheader("各項費用繳交狀況")
    fee_name = st.text_input("項目名稱", value="材料費")
    if not class_students.empty:
        class_students["繳費狀態"] = "未繳"
        pay_df = st.data_editor(
            class_students[["座號", "姓名", "繳費狀態"]],
            column_config={
                "繳費狀態": st.column_config.SelectboxColumn("狀態", options=["已繳", "未繳"], required=True)
            },
            hide_index=True,
            key="pay_editor"
        )
        if st.button("儲存繳費紀錄"):
            # 這裡可以根據您的 GAS 邏輯調整，通常也是傳送至 Sheet
            st.info("功能測試中：此按鈕可串接至您的收費分頁")

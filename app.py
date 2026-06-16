import streamlit as st
import pandas as pd
import datetime
import requests
import re

# --- 設定頁面 ---
st.set_page_config(layout="wide")
st.title("🍎 班級經營系統")

save_clicked = st.button("💾 儲存今日紀錄", type="primary")

# 優化手機版 CSS
st.markdown("""
    <style>
    @media screen and (max-width: 768px) {
        [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important; align-items: center !important; }
        [data-testid="stHorizontalBlock"] > div[data-testid="column"] { width: auto !important; flex: 1 1 auto !important; min-width: 0 !important; padding: 0 4px !important; }
        div.stButton > button { padding: 2px 4px !important; font-size: 13px !important; height: 32px !important; width: 100% !important; }
    }
    </style>
""", unsafe_allow_html=True)

# --- 設定網址 ---
STUDENT_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8_2gDvKiTieAleMNeHdN1owBrEtkhhWBrg3Bpl3b8CzURHgOBouqPJ-_-LTbP8ZXJyPywXlnTKkKj/pub?gid=0&single=true&output=csv"
HISTORY_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8_2gDvKiTieAleMNeHdN1owBrEtkhhWBrg3Bpl3b8CzURHgOBouqPJ-_-LTbP8ZXJyPywXlnTKkKj/pub?gid=2042566365&single=true&output=csv"
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbz6v1LiJXiMQobPT-knkNUBSZ4ut4OwUbcKpzoFiSWKMaj2s8dqsKcmYeuJP8_bVY8UYw/exec"
GROUP_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8_2gDvKiTieAleMNeHdN1owBrEtkhhWBrg3Bpl3b8CzURHgOBouqPJ-_-LTbP8ZXJyPywXlnTKkKj/pub?gid=725381119&single=true&output=csv"
HW_URL = "請在此填入『作業繳交』分頁發布到網路的_CSV_網址" 

@st.cache_data(ttl=60)
def load_data(url):
    if not url or url.startswith("請在此"): return pd.DataFrame()
    try: return pd.read_csv(url)
    except: return pd.DataFrame()

# 載入資料
all_df = load_data(STUDENT_URL)
history_df = load_data(HISTORY_URL)
group_df = load_data(GROUP_URL)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["✅ 點名", "🎲 抽籤/發言", "👥 分組", "💰 繳費", "📝 作業繳交"])

if all_df.empty:
    st.sidebar.warning("⚠️ 學生名單讀取失敗，請檢查網路或 Google Sheet 連結。")
else:
    selected_class = st.sidebar.selectbox("請選擇班級", all_df["班級"].unique())
    df_class = all_df[all_df["班級"] == selected_class].copy()
    
    if 'hw_all_df' not in st.session_state:
        st.session_state['hw_all_df'] = load_data(HW_URL)

    with tab1:
        st.subheader("點名")
        for _, row in df_class.iterrows():
            st.checkbox(f"{int(row['班級'])}-{int(row['座號'])}-{row['姓名']}")

    with tab2:
        st.subheader("🎲 抽籤與發言")
        st.info("此處為抽籤功能區。")

    with tab3:
        st.subheader("👥 分組管理")
        st.info("此處為分組紀錄顯示區。")

    with tab4:
        st.subheader("💰 繳費管理")
        st.info("此處為繳費狀態確認區。")

    with tab5:
        st.subheader("📝 作業繳交管理")
        df_hw = st.session_state['hw_all_df']
        if df_hw.empty:
            df_hw = all_df[['班級', '座號', '姓名']].copy()
            df_hw['日期'] = ""
        
        class_hw_df = df_hw[df_hw['班級'] == int(selected_class)].copy()
        class_hw_df['座號 - 姓名'] = class_hw_df['座號'].fillna(0).astype(int).astype(str) + " - " + class_hw_df['姓名']
        class_hw_df.set_index('座號 - 姓名', inplace=True)
        
        display_hw_df = class_hw_df.drop(columns=['班級', '座號', '姓名'])
        
        hw_col_config = {col: st.column_config.SelectboxColumn(col, options=["已繳", "未繳", ""]) for col in display_hw_df.columns if col != '日期'}
        edited_display_df = st.data_editor(display_hw_df, use_container_width=True, column_config=hw_col_config)

        if st.button("📤 儲存表格修改至 Google Sheet"):
            with st.spinner("正在合併並上傳..."):
                updated_df = st.session_state['hw_all_df'].copy()
                for idx, row in edited_display_df.reset_index().iterrows():
                    seat = int(str(row['座號 - 姓名']).split(" - ")[0])
                    mask = (updated_df['班級'] == int(selected_class)) & (updated_df['座號'] == seat)
                    for col in edited_display_df.columns:
                        updated_df.loc[mask, col] = row[col]
                
                payload = {"action": "update_homework_partial", "data": updated_df.fillna("").to_dict(orient="records")}
                res = requests.post(WEB_APP_URL, json=payload)
                if res.status_code == 200: st.success("✅ 更新成功！")

        st.markdown("#### 📥 批次匯入缺交名單")
        hw_input = st.text_area("格式：日期:2025/6/3\n作業名稱:健康餐盤\n班級:301\n缺交同學座號:2、3、4", height=150)
        
        if st.button("一鍵匯入"):
            try:
                date_match = re.search(r'日期[：:](.*?)(?=\n|$)', hw_input)
                name_match = re.search(r'作業名稱[：:](.*?)(?=\n|$)', hw_input)
                class_match = re.search(r'班級[：:](.*?)(?=\n|$)', hw_input)
                missing_match = re.search(r'缺交同學座號[：:](.*)', hw_input)

                hw_date = date_match.group(1).strip() if date_match else ""
                hw_name = name_match.group(1).strip() if name_match else ""
                hw_class = int(class_match.group(1).strip()) if class_match else 0
                missing_seats = [int(s) for s in re.findall(r'\d+', missing_match.group(1))] if missing_match else []
                
                df_hw = st.session_state['hw_all_df'].copy()
                if hw_name not in df_hw.columns: df_hw[hw_name] = ""
                
                mask = (df_hw['班級'] == hw_class)
                for idx, row in df_hw[mask].iterrows():
                    df_hw.at[idx, '日期'] = hw_date
                    df_hw.at[idx, hw_name] = "未繳" if int(row['座號']) in missing_seats else "已繳"
                
                st.session_state['hw_all_df'] = df_hw
                payload = {"action": "update_homework_partial", "data": df_hw.fillna("").to_dict(orient="records")}
                if requests.post(WEB_APP_URL, json=payload).status_code == 200:
                    st.success("✅ 匯入完成！")
                    st.rerun()
            except Exception as e: st.error(f"解析失敗: {e}")

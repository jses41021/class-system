import streamlit as st
import pandas as pd
import datetime
import requests
import re

# --- 設定頁面 ---
st.set_page_config(layout="wide")
st.title("🍎 班級經營系統")

save_clicked = st.button("💾 儲存今日紀錄", type="primary")

# 優化手機版 CSS (強制抽籤發言在同一行，不換行)
st.markdown("""
    <style>
    @media screen and (max-width: 768px) {
        [data-testid="stHorizontalBlock"] {
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: center !important;
        }
        [data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            width: auto !important;
            flex: 1 1 auto !important;
            min-width: 0 !important;
            padding: 0 4px !important;
        }
        [data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(1) {
            flex: 0 0 65px !important; 
        }
        div.stButton > button {
            padding: 2px 4px !important;
            font-size: 13px !important;
            height: 32px !important;
            min-height: 32px !important;
            width: 100% !important;
            margin: 0 !important;
        }
        div.stMarkdown p {
            line-height: 32px !important;
            margin: 0 !important;
            font-size: 13px !important;
            white-space: nowrap !important;
        }
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

all_df = load_data(STUDENT_URL)
history_df = load_data(HISTORY_URL)
group_df = load_data(GROUP_URL)

if not history_df.empty and '班級' in history_df.columns:
    history_df['班級'] = pd.to_numeric(history_df['班級'], errors='coerce')
if not group_df.empty and '班級' in group_df.columns:
    group_df['班級'] = pd.to_numeric(group_df['班級'], errors='coerce')
    cols_to_ffill = ['日期', '班級', '分組']
    for col in cols_to_ffill:
        if col in group_df.columns:
            group_df[col] = group_df[col].ffill()

if all_df.empty:
    st.warning("⚠️ 學生名單讀取失敗！")
else:
    selected_class = st.sidebar.selectbox("請選擇班級", all_df["班級"].unique())
    df_class = all_df[all_df["班級"] == selected_class].copy()
    
    if 'hw_all_df' not in st.session_state:
        hw_loaded = load_data(HW_URL)
        if hw_loaded.empty or '班級' not in hw_loaded.columns:
            hw_loaded = all_df[['班級', '座號', '姓名']].copy()
        st.session_state['hw_all_df'] = hw_loaded

    if f'attendance_{selected_class}' not in st.session_state:
        st.session_state[f'attendance_{selected_class}'] = {name: True for name in df_class["姓名"]}
        st.session_state[f'scores_{selected_class}'] = {name: 0 for name in df_class["姓名"]}
        st.session_state[f'draws_{selected_class}'] = {name: 0 for name in df_class["姓名"]}
        st.session_state[f'payment_{selected_class}'] = {}
        for name in df_class["姓名"]:
            has_paid = False
            if not history_df.empty and '繳費狀態' in history_df.columns:
                student_hist = history_df[(history_df["姓名"] == name) & (history_df["班級"] == int(selected_class))]
                if (student_hist["繳費狀態"] == "已繳").any():
                    has_paid = True
            st.session_state[f'payment_{selected_class}'][name] = has_paid
        st.session_state[f'last_winner_{selected_class}'] = None
        st.session_state[f'group_dict_{selected_class}'] = {name: "無" for name in df_class["姓名"]}

    if save_clicked:
        with st.spinner("正在批次同步今日紀錄..."):
            all_data = []
            for name in df_class["姓名"]:
                row = df_class[df_class['姓名'] == name].iloc[0]
                all_data.append({
                    "日期": datetime.date.today().strftime("%Y/%m/%d"),
                    "班級": int(row['班級']),
                    "座號": int(row['座號']),
                    "姓名": name,
                    "出席狀態": "出席" if st.session_state[f'attendance_{selected_class}'][name] else "缺席",
                    "繳費狀態": "已繳" if st.session_state[f'payment_{selected_class}'][name] else "未繳",
                    "發言次數": st.session_state[f'scores_{selected_class}'][name],
                    "中籤次數": st.session_state[f'draws_{selected_class}'][name],
                    "分組": st.session_state[f'group_dict_{selected_class}'].get(name, "無")
                })
            try:
                payload = {"action": "append_daily", "data": all_data}
                response = requests.post(WEB_APP_URL, json=payload, timeout=15)
                if response.status_code == 200: st.success("✅ 今日全部資料已同步完成！")
                else: st.error(f"同步發生錯誤，狀態碼: {response.status_code}")
            except Exception as e: st.error(f"同步請求失敗: {e}")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["✅ 點名", "🎲 抽籤/發言", "👥 分組", "💰 繳費", "📝 作業繳交"])

    with tab1:
        st.subheader("點名")
        for _, row in df_class.iterrows():
            name = row['姓名']
            disp = f"{int(row['班級'])}-{int(row['座號'])}-{name}"
            st.session_state[f'attendance_{selected_class}'][name] = st.checkbox(disp, value=st.session_state[f'attendance_{selected_class}'][name])

        st.divider()
        st.subheader("📊 個人累積統計表")
        if not history_df.empty:
            class_hist = history_df[history_df["班級"] == int(selected_class)].copy()
            if not class_hist.empty:
                stats = class_hist.groupby(['班級', '座號', '姓名']).agg({
                    '出席狀態': lambda x: (x == '出席').sum(),
                    '繳費狀態': lambda x: "已繳" if (x == '已繳').any() else "未繳",
                    '發言次數': 'sum', 
                    '中籤次數': 'sum'
                }).reset_index()
                
                # ✅ 將座號、姓名合併為單一 Index 達成凍結窗格，解決手機版佔用太多空間的問題
                stats['座號 - 姓名'] = stats['座號'].fillna(0).astype(int).astype(str) + " - " + stats['姓名']
                stats.set_index('座號 - 姓名', inplace=True)
                
                # 隱藏不需要重複顯示的欄位，畫面更清爽
                display_stats = stats.drop(columns=['班級', '座號', '姓名'])
                st.dataframe(display_stats, use_container_width=True)

    present_students = [name for name, present in st.session_state[f'attendance_{selected_class}'].items() if present]

    with tab2:
        st.subheader("隨機抽籤")
        eligible_students = [name for name in present_students if st.session_state[f'draws_{selected_class}'][name] + st.session_state[f'scores_{selected_class}'][name] == 0]
        if st.button("🎲 抽籤 (僅限出席且未中籤/發言者)"):
            if eligible_students:
                winner = pd.Series(eligible_students).sample(1).iloc[0]
                st.session_state[f'last_winner_{selected_class}'] = winner
                st.session_state[f'draws_{selected_class}'][winner] += 1
            else: st.warning("目前所有出席者都已經中籤或發言過了！")
        if st.session_state[f'last_winner_{selected_class}']:
            winner = st.session_state[f'last_winner_{selected_class}']
            w_row = df_class[df_class['姓名'] == winner].iloc[0]
            st.success(f"🎉 抽中：{int(w_row['班級'])}-{int(w_row['座號'])}-{winner}")
        
        for name in present_students:
            row = df_class[df_class['姓名'] == name].iloc[0]
            col1, col2 = st.columns([1.5, 8.5], gap="small")
            with col1:
                if st.button("加分", key=f"score_{name}"):
                    st.session_state[f'scores_{selected_class}'][name] += 1
                    st.rerun()
            with col2:
                st.write(f"{int(row['班級'])}-{int(row['座號'])}-{name} (中籤: {st.session_state[f'draws_{selected_class}'][name]}, 發言: {st.session_state[f'scores_{selected_class}'][name]})")

    with tab3:
        st.subheader("隨機分組")
        group_n = st.selectbox("組數", [3, 4, 5, 6, 8])
        if st.button("開始分組"):
            shuffled = pd.Series(present_students).sample(frac=1).tolist()
            groups = [shuffled[i::group_n] for i in range(group_n)]
            for name in df_class["姓名"]: st.session_state[f'group_dict_{selected_class}'][name] = "無"
            for i, g in enumerate(groups):
                group_name = f"第 {i+1} 組"
                st.write(f"{group_name}: {', '.join([f'{int(df_class.loc[df_class['姓名']==name, '座號'].values[0])} {name}' for name in g])}")
                for name in g: st.session_state[f'group_dict_{selected_class}'][name] = group_name
        
        st.divider()
        st.subheader("📅 各週次分組紀錄")
        if not group_df.empty and '班級' in group_df.columns:
            group_class = group_df[group_df["班級"] == int(selected_class)].copy()
            if not group_class.empty:
                dates = sorted(group_class["日期"].dropna().unique(), reverse=True)
                for d in dates:
                    st.markdown(f"**{d}**")
                    df_date = group_class[group_class["日期"] == d]
                    groups = df_date["分組"].dropna().unique()
                    for g in groups:
                        df_g = df_date[df_date["分組"] == g]
                        members = []
                        for _, r in df_g.iterrows():
                            seat = int(r["座號"]) if pd.notna(r["座號"]) else ""
                            name = str(r["姓名"]) if pd.notna(r["姓名"]) else ""
                            members.append(f"{seat}{name}")
                        st.write(f"{g}: {''.join(members)}")
                    st.divider()
            else: st.write("目前無此班級的分組紀錄。")
        else: st.warning("⚠️ 分組紀錄讀取失敗！")

    with tab4:
        st.subheader("繳費管理")
        for _, row in df_class.iterrows():
            name = row['姓名']
            st.session_state[f'payment_{selected_class}'][name] = st.checkbox(f"{int(row['班級'])}-{int(row['座號'])}-{name}", value=st.session_state[f'payment_{selected_class}'][name], key=f"pay_{name}")

    with tab5:
        st.subheader("📝 作業繳交管理")
        df_hw_all = st.session_state['hw_all_df']
        class_hw_df = df_hw_all[df_hw_all['班級'] == int(selected_class)].copy()
        
        # ✅ 合併座號與姓名為單一 Index 達成凍結窗格，解決 Streamlit 不支援 MultiIndex 編輯報錯的問題
        class_hw_df['座號 - 姓名'] = class_hw_df['座號'].fillna(0).astype(int).astype(str) + " - " + class_hw_df['姓名']
        class_hw_df.set_index('座號 - 姓名', inplace=True)
        
        # 將基本資料隱藏，只留下作業，讓手機版版面更乾淨
        cols_to_hide = ['班級', '座號', '姓名', '日期']
        display_hw_df = class_hw_df.drop(columns=[c for c in cols_to_hide if c in class_hw_df.columns])
        
        # ✅ 使用 column_config 讓所有的作業欄位變成「下拉式選單」
        hw_col_config = {}
        for col in display_hw_df.columns:
            hw_col_config[col] = st.column_config.SelectboxColumn(col, options=["已繳", "未繳", ""])
        
        st.markdown("👇 **學生作業狀況總表 (可往右滑動查看，點兩下儲存格可下拉修改狀態)**")
        # 顯示可修改且具備單一凍結窗格的表格
        edited_display_df = st.data_editor(display_hw_df, use_container_width=True, column_config=hw_col_config)

        if st.button("📤 儲存表格修改至 Google Sheet", type="secondary"):
            with st.spinner("正在合併最新資料並上傳紀錄..."):
                # ✅ 修正 1: 使用 session_state 中累積的資料，避免去抓到 Google 尚未更新的舊快取 CSV 而導致洗掉資料
                df_hw_all = st.session_state['hw_all_df']
                
                # 將修改的結果合併回最新版本的全校大表
                edited_reset = edited_display_df.reset_index()
                
                # 確保新作業的欄位有在總表中
                for col in edited_display_df.columns:
                    if col not in df_hw_all.columns:
                        df_hw_all[col] = ""

                for idx, row in edited_reset.iterrows():
                    # 從「座號 - 姓名」中提取座號
                    seat_val = int(str(row['座號 - 姓名']).split(" - ")[0])
                    mask = (df_hw_all['班級'] == int(selected_class)) & (df_hw_all['座號'].fillna(0).astype(int) == seat_val)
                    for col in edited_display_df.columns:
                        df_hw_all.loc[mask, col] = row[col]
                        
                st.session_state['hw_all_df'] = df_hw_all
                
                hw_payload = {"action": "overwrite_homework", "data": df_hw_all.fillna("").to_dict(orient="records")}
                try:
                    res = requests.post(WEB_APP_URL, json=hw_payload, timeout=15)
                    if res.status_code == 200: st.success("✅ 作業紀錄已成功更新！不會覆蓋掉其他人的心血囉！")
                    else: st.error(f"儲存發生錯誤，狀態碼: {res.status_code}")
                except Exception as e: st.error(f"連線失敗: {e}")

        st.divider()
        st.markdown("#### 📥 批次匯入缺交名單")
        hw_input = st.text_area("貼上缺交名單 (包含作業名稱、班級、缺交同學座號)", height=150)
        
        if st.button("一鍵匯入名單並同步至 Sheet", type="primary"):
            try:
                # ✅ 修正 2: 強化正則表達式，只要碰到「日期」、「班級」或「缺交」任何一個關鍵字就立刻停止抓取，避免內容混在一起
                hw_name_match = re.search(r'作業名稱[：:](.*?)(?=(?:日期|班級|缺交同學座號)[：:]|$)', hw_input, re.DOTALL)
                hw_class_match = re.search(r'班級[：:](.*?)(?=(?:作業名稱|日期|缺交同學座號)[：:]|$)', hw_input, re.DOTALL)
                hw_missing_match = re.search(r'缺交同學座號[：:](.*)', hw_input, re.DOTALL)

                hw_name = hw_name_match.group(1).strip() if hw_name_match else ""
                hw_class = hw_class_match.group(1).strip() if hw_class_match else ""
                missing_str = hw_missing_match.group(1).strip() if hw_missing_match else ""
                
                if not hw_name or not hw_class: st.error("❌ 格式解析錯誤。請確認有『作業名稱：』與『班級：』等關鍵字。")
                elif int(hw_class) != int(selected_class): st.error(f"⚠️ 貼上的班級 ({hw_class}) 與目前選擇的班級 ({selected_class}) 不符！")
                else:
                    parts = re.split(r'[、,，\s]+', missing_str)
                    missing_seats = [int(p) for p in parts if p.isdigit()]
                    
                    # ✅ 修正 1: 匯入時也直接使用 session_state 中累積的資料
                    df_hw_all = st.session_state['hw_all_df']

                    if hw_name not in df_hw_all.columns: df_hw_all[hw_name] = ""
                    
                    mask_class = df_hw_all['班級'] == int(selected_class)
                    for idx, row in df_hw_all[mask_class].iterrows():
                        status = "未繳" if int(row['座號']) in missing_seats else "已繳"
                        df_hw_all.at[idx, hw_name] = status
                    
                    st.session_state['hw_all_df'] = df_hw_all
                    with st.spinner("正在同步..."):
                        hw_payload = {"action": "overwrite_homework", "data": df_hw_all.fillna("").to_dict(orient="records")}
                        res = requests.post(WEB_APP_URL, json=hw_payload, timeout=15)
                        if res.status_code == 200:
                            st.success(f"✅ {hw_name} 缺交名單匯入成功！歷史紀錄也安全保留了！")
                            st.rerun()
                        else: st.error("⚠️ 同步失敗。")
            except Exception as e: st.error(f"❌ 解析錯誤：{e}")

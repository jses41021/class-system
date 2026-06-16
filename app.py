import streamlit as st
import pandas as pd
import datetime
import requests
import re

# --- 設定頁面 ---
st.set_page_config(layout="wide")
st.title("🍎 班級經營系統")

save_clicked = st.button("💾 儲存今日紀錄", type="primary")

# 優化手機版 CSS：強制按鈕與文字同行，並極大化縮小間距
st.markdown("""
    <style>
    @media screen and (max-width: 768px) {
        /* 取消 Streamlit 預設的直向排列，強制橫向 */
        div[data-testid="column"] {
            min-width: 0 !important;
            padding-left: 2px !important;
            padding-right: 2px !important;
        }
        /* 第一個欄位 (按鈕) 固定寬度縮至極限 */
        div[data-testid="column"]:nth-of-type(1) {
            flex: 0 0 55px !important; 
            width: 55px !important;
        }
        /* 第二個欄位 (文字) 填滿剩餘空間 */
        div[data-testid="column"]:nth-of-type(2) {
            flex: 1 1 auto !important;
        }
        /* 縮小按鈕本體 */
        div.stButton > button {
            padding: 2px 4px !important;
            font-size: 13px !important;
            height: 32px !important;
            min-height: 32px !important;
            width: 100% !important;
        }
        /* 文字對齊按鈕高度，避免跑版 */
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

@st.cache_data(ttl=60)
def load_data(url):
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

    # --- 執行儲存每日紀錄邏輯 ---
    if save_clicked:
        with st.spinner("正在批次同步..."):
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
                response = requests.post(WEB_APP_URL, json=all_data, timeout=15)
                if response.status_code == 200:
                    st.success("✅ 全部資料已同步完成！")
                else:
                    st.error(f"同步發生錯誤，狀態碼: {response.status_code}")
            except Exception as e:
                st.error(f"同步請求失敗: {e}")

    # 修改: 刪除原有的 tab5，替換為作業繳交
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
                st.dataframe(stats, use_container_width=True)

    present_students = [name for name, present in st.session_state[f'attendance_{selected_class}'].items() if present]

    with tab2:
        st.subheader("隨機抽籤")
        eligible_students = [
            name for name in present_students 
            if st.session_state[f'draws_{selected_class}'][name] + st.session_state[f'scores_{selected_class}'][name] == 0
        ]
        if st.button("🎲 抽籤 (僅限出席且未中籤/發言者)"):
            if eligible_students:
                winner = pd.Series(eligible_students).sample(1).iloc[0]
                st.session_state[f'last_winner_{selected_class}'] = winner
                st.session_state[f'draws_{selected_class}'][winner] += 1
            else:
                st.warning("目前所有出席者都已經中籤或發言過了！")
        if st.session_state[f'last_winner_{selected_class}']:
            winner = st.session_state[f'last_winner_{selected_class}']
            w_row = df_class[df_class['姓名'] == winner].iloc[0]
            st.success(f"🎉 抽中：{int(w_row['班級'])}-{int(w_row['座號'])}-{winner}")
        
        for name in present_students:
            row = df_class[df_class['姓名'] == name].iloc[0]
            # 使用 gap="small" 配合上方 CSS，讓手機版能完美貼合
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
        
        # 新增: 將各週次分組紀錄整合至此，並倒序排列
        st.divider()
        st.subheader("📅 各週次分組紀錄 (最新至最舊)")
        if not group_df.empty and '班級' in group_df.columns:
            group_class = group_df[group_df["班級"] == int(selected_class)].copy()
            if not group_class.empty:
                # 取得日期並反向排序 (越新的日期在越上方)
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
            else:
                st.write("目前無此班級的分組紀錄。")
        else:
            st.warning("⚠️ 分組紀錄讀取失敗或尚未建立資料！")

    with tab4:
        st.subheader("繳費管理")
        for _, row in df_class.iterrows():
            name = row['姓名']
            st.session_state[f'payment_{selected_class}'][name] = st.checkbox(f"{int(row['班級'])}-{int(row['座號'])}-{name}", value=st.session_state[f'payment_{selected_class}'][name], key=f"pay_{name}")

    # 新增: 作業繳交分頁邏輯
    with tab5:
        st.subheader("📝 作業繳交管理")
        st.markdown("請在下方貼上缺交名單：")
        
        # 預設提示文字
        placeholder_text = "作業名稱：健康餐盤\n日期：2026/6/13\n班級：301\n缺交同學座號：2、5、10"
        hw_input = st.text_area("貼上缺交名單", height=150, placeholder=placeholder_text)
        
        if st.button("📥 一鍵匯入名單"):
            try:
                # 解析輸入文字
                hw_name = re.search(r'作業名稱：(.*)', hw_input).group(1).strip()
                hw_date = re.search(r'日期：(.*)', hw_input).group(1).strip()
                hw_class = re.search(r'班級：(.*)', hw_input).group(1).strip()
                
                if int(hw_class) != int(selected_class):
                    st.error(f"⚠️ 貼上的班級 ({hw_class}) 與目前選擇的班級 ({selected_class}) 不符！")
                else:
                    missing_str_match = re.search(r'缺交同學座號：(.*)', hw_input)
                    missing_seats = []
                    if missing_str_match:
                        missing_str = missing_str_match.group(1).strip()
                        # 支援頓號、逗號、空白等多種分隔符號
                        parts = re.split(r'[、,，\s]+', missing_str)
                        missing_seats = [int(p) for p in parts if p.isdigit()]
                    
                    # 建立 DataFrame 狀態
                    hw_data = []
                    for _, row in df_class.iterrows():
                        seat = int(row['座號'])
                        name = row['姓名']
                        status = "未繳" if seat in missing_seats else ""
                        hw_data.append({"座號": seat, "姓名": name, "繳交狀態": status})
                    
                    st.session_state[f'hw_df_{selected_class}'] = pd.DataFrame(hw_data)
                    st.session_state[f'hw_name_{selected_class}'] = hw_name
                    st.session_state[f'hw_date_{selected_class}'] = hw_date
                    st.success("✅ 名單匯入成功！請在下方表格確認或修改。")
            except Exception as e:
                st.error("❌ 格式解析錯誤，請確認貼上的文字格式是否與範例完全一致（包含冒號）。")

        # 若已解析過，顯示可編輯的表格
        if f'hw_df_{selected_class}' in st.session_state:
            st.markdown(f"#### 📚 目前作業：{st.session_state[f'hw_name_{selected_class}']} ({st.session_state[f'hw_date_{selected_class}']})")
            
            # 使用 st.data_editor 讓使用者可以直接在網頁上修改「繳交狀態」
            edited_hw_df = st.data_editor(
                st.session_state[f'hw_df_{selected_class}'],
                column_config={
                    "座號": st.column_config.NumberColumn("座號", disabled=True),
                    "姓名": st.column_config.TextColumn("姓名", disabled=True),
                    "繳交狀態": st.column_config.SelectboxColumn(
                        "繳交狀態",
                        help="點擊修改：空白表示已繳交，顯示'未繳'表示缺交",
                        options=["", "未繳"],
                        required=False
                    )
                },
                hide_index=True,
                use_container_width=True
            )
            
            # 更新 session state 以保留使用者手動編輯的結果
            st.session_state[f'hw_df_{selected_class}'] = edited_hw_df
            
            if st.button("📤 儲存作業紀錄至 Google Sheet", type="secondary"):
                with st.spinner("正在上傳作業紀錄..."):
                    hw_payload = []
                    for _, row in edited_hw_df.iterrows():
                        hw_payload.append({
                            "日期": st.session_state[f'hw_date_{selected_class}'],
                            "班級": int(selected_class),
                            "座號": int(row['座號']),
                            "姓名": row['姓名'],
                            "作業名稱": st.session_state[f'hw_name_{selected_class}'],
                            "繳交狀態": row['繳交狀態']
                        })
                    try:
                        response = requests.post(WEB_APP_URL, json=hw_payload, timeout=15)
                        if response.status_code == 200:
                            st.success("✅ 作業紀錄已成功儲存至「作業繳交」分頁！")
                        else:
                            st.error(f"儲存發生錯誤，狀態碼: {response.status_code}")
                    except Exception as e:
                        st.error(f"連線失敗: {e}")

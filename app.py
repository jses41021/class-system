import streamlit as st
import pandas as pd
import datetime
import requests

# --- 設定頁面 ---
st.set_page_config(layout="wide")
st.title("🍎 班級經營系統")

# 修正儲存按鈕位置：直接放在標題下方
# 如果需要儲存，點選按鈕後會直接觸發下方的邏輯
save_clicked = st.button("💾 儲存今日紀錄", type="primary")

# 加入 CSS 來修復手機版的欄位換行問題
st.markdown("""
    <style>
    [data-testid="stHorizontalBlock"] {
        align-items: center;
    }
    @media screen and (max-width: 768px) {
        [data-testid="stHorizontalBlock"] {
            flex-direction: row !important;
            flex-wrap: nowrap !important;
        }
        [data-testid="column"] {
            width: auto !important;
        }
        [data-testid="column"]:nth-of-type(1) {
            flex: 3 !important;
        }
        [data-testid="column"]:nth-of-type(2) {
            flex: 1 !important;
        }
        [data-testid="column"]:nth-of-type(3) {
            display: none !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# --- 設定網址 ---
STUDENT_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8_2gDvKiTieAleMNeHdN1owBrEtkhhWBrg3Bpl3b8CzURHgOBouqPJ-_-LTbP8ZXJyPywXlnTKkKj/pub?gid=0&single=true&output=csv"
HISTORY_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8_2gDvKiTieAleMNeHdN1owBrEtkhhWBrg3Bpl3b8CzURHgOBouqPJ-_-LTbP8ZXJyPywXlnTKkKj/pub?gid=2042566365&single=true&output=csv"
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbz6v1LiJXiMQobPT-knkNUBSZ4ut4OwUbcKpzoFiSWKMaj2s8dqsKcmYeuJP8_bVY8UYw/exec"

@st.cache_data(ttl=60)
def load_data(url):
    try: return pd.read_csv(url)
    except: return pd.DataFrame()

all_df = load_data(STUDENT_URL)
history_df = load_data(HISTORY_URL)

if not history_df.empty and '班級' in history_df.columns:
    history_df['班級'] = pd.to_numeric(history_df['班級'], errors='coerce')

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

    # --- 執行儲存紀錄邏輯 (移至全域，確保能正確觸發) ---
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

    tab1, tab2, tab3, tab4 = st.tabs(["✅ 點名", "🎲 抽籤/發言", "👥 分組", "💰 繳費"])

    with tab1:
        st.subheader("點名")
        for _, row in df_class.iterrows():
            name = row['姓名']
            disp = f"{int(row['班級'])}-{int(row['座號'])}-{name}"
            st.session_state[f'attendance_{selected_class}'][name] = st.checkbox(disp, value=st.session_state[f'attendance_{selected_class}'][name])

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
            col1, col2, _ = st.columns([4, 1, 5])
            col1.write(f"{int(row['班級'])}-{int(row['座號'])}-{name} (中籤: {st.session_state[f'draws_{selected_class}'][name]}, 發言: {st.session_state[f'scores_{selected_class}'][name]})")
            if col2.button("加分", key=f"score_{name}"):
                st.session_state[f'scores_{selected_class}'][name] += 1
                st.rerun()

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

    with tab4:
        st.subheader("繳費管理")
        for _, row in df_class.iterrows():
            name = row['姓名']
            st.session_state[f'payment_{selected_class}'][name] = st.checkbox(f"{int(row['班級'])}-{int(row['座號'])}-{name}", value=st.session_state[f'payment_{selected_class}'][name], key=f"pay_{name}")

    st.divider()
    st.subheader("📊 個人累積統計表")
    if not history_df.empty:
        class_hist = history_df[history_df["班級"] == int(selected_class)].copy()
        if not class_hist.empty:
            stats = class_hist.groupby(['座號', '姓名']).agg({'出席狀態': lambda x: (x == '出席').sum(), '發言次數': 'sum', '中籤次數': 'sum', '分組': 'last'}).reset_index()
            st.dataframe(stats, use_container_width=True)

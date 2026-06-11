import streamlit as st
import pandas as pd

# --- 設定頁面 ---
st.set_page_config(layout="wide")
st.title("🍎 班級經營系統")

# --- 載入資料 (請務必將 CSV_URL 換成您自己的真實網址) ---
@st.cache_data(ttl=600)
def load_data():
    csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8_2gDvKiTieAleMNeHdN1owBrEtkhhWBrg3Bpl3b8CzURHgOBouqPJ-_-LTbP8ZXJyPywXlnTKkKj/pub?gid=0&single=true&output=csv" 
    try:
        return pd.read_csv(csv_url)
    except:
        return pd.DataFrame()

all_df = load_data()

if not all_df.empty:
    selected_class = st.sidebar.selectbox("請選擇班級", all_df["班級"].unique())
    df_class = all_df[all_df["班級"] == selected_class].copy()
    
    # 建立顯示名稱函式 (確保顯示為 301-1-姓名，去除 .0)
    def get_display_name(row):
        return f"{int(row['班級'])}-{int(row['座號'])}-{row['姓名']}"

    # 初始化 session_state
    if f'attendance_{selected_class}' not in st.session_state:
        st.session_state[f'attendance_{selected_class}'] = {name: True for name in df_class["姓名"]}
    if f'scores_{selected_class}' not in st.session_state:
        st.session_state[f'scores_{selected_class}'] = {name: 0 for name in df_class["姓名"]}

    tab1, tab2, tab3 = st.tabs(["✅ 點名", "🎲 抽籤/發言", "👥 分組"])

    with tab1:
        st.subheader(f"{selected_class} 點名 (打勾代表出席)")
        for _, row in df_class.iterrows():
            name = row['姓名']
            st.session_state[f'attendance_{selected_class}'][name] = st.checkbox(get_display_name(row), value=st.session_state[f'attendance_{selected_class}'][name])

    present_students = [name for name, present in st.session_state[f'attendance_{selected_class}'].items() if present]

    # 抽籤與發言統計區塊 (替換原本的 tab2 內容)
   # 抽籤與發言統計區塊
    with tab2:
        st.subheader("隨機抽籤與發言統計")
        
        # 1. 確保 session_state 記錄了最後抽中的人
        if f'last_winner_{selected_class}' not in st.session_state:
            st.session_state[f'last_winner_{selected_class}'] = None

        # 2. 抽籤按鈕
        if st.button("🎲 隨機抽籤 (僅限出席者)"):
            if present_students:
                winner_name = pd.Series(present_students).sample(1).iloc[0]
                st.session_state[f'scores_{selected_class}'][winner_name] += 1
                # 記錄抽中者的名字
                st.session_state[f'last_winner_{selected_class}'] = winner_name
                st.rerun() # 重新整理以更新顯示
            else:
                st.warning("目前沒有學生出席！")
        
        # 3. 顯示抽籤結果 (固定在抽籤按鈕下方)
        if st.session_state[f'last_winner_{selected_class}']:
            winner_name = st.session_state[f'last_winner_{selected_class}']
            winner_row = df_class[df_class['姓名'] == winner_name].iloc[0]
            st.success(f"🎉 剛剛抽中：{get_display_name(winner_row)}")
        
        st.write("---")
        
        # 4. 主動加分清單
        for name in present_students:
            col1, col2 = st.columns([3, 1])
            score = st.session_state[f'scores_{selected_class}'].get(name, 0)
            row = df_class[df_class['姓名'] == name].iloc[0]
            col1.write(f"{get_display_name(row)} (累積：{score} 次)")
            if col2.button("加分", key=f"btn_{name}"):
                st.session_state[f'scores_{selected_class}'][name] += 1
                # 當手動加分時，清除抽籤結果顯示，避免混淆
                st.session_state[f'last_winner_{selected_class}'] = None
                st.rerun()

    # 分組區塊 (替換原本的 tab3 內容)
    with tab3:
        st.subheader("隨機分組 (僅限出席者)")
        cols = st.columns(5)
        nums = [3, 4, 5, 6, 8]
        for i, n in enumerate(nums):
            if cols[i].button(f"{n} 組"):
                if len(present_students) >= n:
                    random_list = pd.Series(present_students).sample(frac=1).tolist()
                    groups = [random_list[i::n] for i in range(n)]
                    for g_idx, group in enumerate(groups):
                        # 轉換為班級-座號-姓名顯示
                        full_names = []
                        for name in group:
                            row = df_class[df_class['姓名'] == name].iloc[0]
                            full_names.append(get_display_name(row))
                        st.write(f"第 {g_idx+1} 組: {', '.join(full_names)}")
                else:
                    st.error("出席人數不足以分組")
# 繳費統計區塊 (新增 tab4)
    # 如果您原本只有 tab1~tab3，請記得將上方 st.tabs 改為 st.tabs(["✅ 點名", "🎲 抽籤/發言", "👥 分組", "💰 繳費"])
    
    with tab4:
        st.subheader(f"{selected_class} 繳費管理")
        
        # 初始化該班級的繳費狀態 (預設為 False 即 未繳)
        if f'payment_{selected_class}' not in st.session_state:
            st.session_state[f'payment_{selected_class}'] = {name: False for name in df_class["姓名"]}
            
        # 顯示繳費清單
        for _, row in df_class.iterrows():
            name = row['姓名']
            # 使用 checkbox：打勾即為「已繳費」
            is_paid = st.checkbox(f"{get_display_name(row)}", value=st.session_state[f'payment_{selected_class}'][name], key=f"pay_{name}")
            st.session_state[f'payment_{selected_class}'][name] = is_paid

        # 顯示統計結果
        paid_count = sum(st.session_state[f'payment_{selected_class}'].values())
        st.write(f"---")
        st.info(f"繳費統計：共 {len(df_class)} 人，已繳 {paid_count} 人，未繳 {len(df_class) - paid_count} 人")

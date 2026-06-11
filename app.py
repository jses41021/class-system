import streamlit as st
import pandas as pd

# --- 設定頁面 ---
st.set_page_config(layout="wide")
st.title("🍎 班級經營系統")

# --- 載入資料 ---
@st.cache_data(ttl=600)
def load_data():
    csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8_2gDvKiTieAleMNeHdN1owBrEtkhhWBrg3Bpl3b8CzURHgOBouqPJ-_-LTbP8ZXJyPywXlnTKkKj/pub?gid=0&single=true&output=csv"
    try:
        return pd.read_csv(csv_url)
    except:
        return pd.DataFrame()

all_df = load_data()
# --- 新增讀取歷史資料的功能 ---
@st.cache_data(ttl=600)
def load_history():
    # 這裡是您的「總資料庫」發布至網路的 CSV 網址
    history_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVhobz_uXg7PcjS9BJh0kKh2KosiFnPLAyQq8hiGVPxuQIwCrJVU6pcyYLOukIY2hQIB2e8qXROmBu/pub?gid=1041522227&single=true&output=csv" 
    try:
        return pd.read_csv(history_url)
    except:
        return pd.DataFrame()

history_df = load_history()
if not all_df.empty:
    selected_class = st.sidebar.selectbox("請選擇班級", all_df["班級"].unique())
    df_class = all_df[all_df["班級"] == selected_class].copy()
    
    # 統一格式化顯示名稱的函式
    def get_display_name(row):
        return f"{int(row['班級'])}-{int(row['座號'])}-{row['姓名']}"

    # 初始化 session_state
    if f'attendance_{selected_class}' not in st.session_state:
        st.session_state[f'attendance_{selected_class}'] = {name: True for name in df_class["姓名"]}
    if f'scores_{selected_class}' not in st.session_state:
        st.session_state[f'scores_{selected_class}'] = {name: 0 for name in df_class["姓名"]}
    if f'payment_{selected_class}' not in st.session_state:
        st.session_state[f'payment_{selected_class}'] = {name: False for name in df_class["姓名"]}
    if f'last_winner_{selected_class}' not in st.session_state:
        st.session_state[f'last_winner_{selected_class}'] = None

    tab1, tab2, tab3, tab4 = st.tabs(["✅ 點名", "🎲 抽籤/發言", "👥 分組", "💰 繳費"])

    with tab1:
        st.subheader(f"{selected_class} 點名 (打勾代表出席)")
        for _, row in df_class.iterrows():
            name = row['姓名']
            st.session_state[f'attendance_{selected_class}'][name] = st.checkbox(get_display_name(row), value=st.session_state[f'attendance_{selected_class}'][name])

    present_students = [name for name, present in st.session_state[f'attendance_{selected_class}'].items() if present]

    with tab2:
        st.subheader("隨機抽籤與發言統計")
        if st.button("🎲 隨機抽籤 (僅限出席者)"):
            if present_students:
                winner_name = pd.Series(present_students).sample(1).iloc[0]
                st.session_state[f'scores_{selected_class}'][winner_name] += 1
                st.session_state[f'last_winner_{selected_class}'] = winner_name
                st.rerun()
        
        if st.session_state[f'last_winner_{selected_class}']:
            w_name = st.session_state[f'last_winner_{selected_class}']
            w_row = df_class[df_class['姓名'] == w_name].iloc[0]
            st.success(f"🎉 剛剛抽中：{get_display_name(w_row)}")
        
        st.write("---")
        for name in present_students:
            col1, col2 = st.columns([3, 1])
            score = st.session_state[f'scores_{selected_class}'].get(name, 0)
            row = df_class[df_class['姓名'] == name].iloc[0]
            col1.write(f"{get_display_name(row)} (累積：{score} 次)")
            if col2.button("加分", key=f"btn_{name}"):
                st.session_state[f'scores_{selected_class}'][name] += 1
                st.session_state[f'last_winner_{selected_class}'] = None
                st.rerun()

    with tab3:
        st.subheader("隨機分組 (僅限出席者)")
        for n in [3, 4, 5, 6, 8]:
            if st.button(f"{n} 組"):
                if len(present_students) >= n:
                    random_list = pd.Series(present_students).sample(frac=1).tolist()
                    groups = [random_list[i::n] for i in range(n)]
                    for g_idx, group in enumerate(groups):
                        full_names = [get_display_name(df_class[df_class['姓名'] == name].iloc[0]) for name in group]
                        st.write(f"第 {g_idx+1} 組: {', '.join(full_names)}")
    with tab4:
        st.subheader(f"{selected_class} 繳費管理")
        
        # 顯示名單與勾選框 (這段是關鍵，必須確保在 with tab4 之下)
        for _, row in df_class.iterrows():
            name = row['姓名']
            # 使用 key 以確保每個勾選框獨立
            st.session_state[f'payment_{selected_class}'][name] = st.checkbox(
                f"{int(row['班級'])}-{int(row['座號'])}-{row['姓名']}", 
                value=st.session_state[f'payment_{selected_class}'][name], 
                key=f"pay_{name}"
            )
        
        # 計算統計數字
        paid_count = sum(st.session_state[f'payment_{selected_class}'].values())
        st.info(f"💰 繳費統計：共 {len(df_class)} 人，已繳 {paid_count} 人，未繳 {len(df_class) - paid_count} 人")
        
        st.write("---")
        
        # 匯出紀錄按鈕 (欄位已拆分)
        # 匯出紀錄按鈕 (修改處)
        if st.button("💾 匯出本週紀錄 (CSV)"):
            # ... (原本的 export_data 與 df_export 產生邏輯保持不變) ...
            
            # 取得今天的日期並格式化
            today = datetime.date.today().strftime("%Y-%m-%d")
            file_name = f"{today}_{selected_class}.csv"
            
            df_export = pd.DataFrame(export_data)
            csv = df_export.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            
            # 修改這裡：使用動態的 file_name
            st.download_button("📥 點擊下載 CSV", csv, file_name, "text/csv")
# --- 顯示歷史紀錄 ---
        st.divider()
        st.subheader("📊 20 週歷史紀錄")
        if not history_df.empty:
            st.dataframe(history_df, use_container_width=True)
        else:
            st.info("請確認「總資料庫」的 CSV 連結已設定正確，或目前尚無歷史紀錄。")

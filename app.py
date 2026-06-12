import streamlit as st
import pandas as pd
import datetime
import requests  # 確保這裡有引入

# --- 1. 定義所有函式 (只定義一次) ---
@st.cache_data(ttl=600)
def load_data():
    # 這裡放名單的 CSV 網址
    return pd.read_csv("您的名單CSV網址")

@st.cache_data(ttl=600)
def load_history():
    # 這裡放總資料庫的 CSV 網址
    return pd.read_csv("您的總資料庫CSV網址")

def save_to_google_sheet(data):
    api_url = "https://script.google.com/macros/s/AKfycbwRTMwukxZx8JBD76jWMtrGdpT6lG7gU_8qtzoNXUSSsPPEMN-TaTalZ9tTc33F0KtYvA/exec" # 請填入您的真實網址
    try:
        response = requests.post(api_url, json=data)
        return response.status_code == 200
    except:
        return False

# --- 2. 執行頁面邏輯 ---
all_df = load_data()
history_df = load_history()

if not all_df.empty:
    selected_class = st.sidebar.selectbox("請選擇班級", all_df["班級"].unique())
    # ... 後續您的 UI 程式碼 ...
    
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
       # 匯出紀錄按鈕 (修改後版本)
        if st.button("💾 匯出本週紀錄 (CSV)"):
            export_data = []
            for name in df_class["姓名"]:
                row = df_class[df_class['姓名'] == name].iloc[0]
                export_data.append({
                    "班級": int(row['班級']),
                    "座號": int(row['座號']),
                    "姓名": row['姓名'],
                    "出席": st.session_state[f'attendance_{selected_class}'][name],
                    "發言次數": st.session_state[f'scores_{selected_class}'][name],
                    "繳費狀態": "已繳" if st.session_state[f'payment_{selected_class}'][name] else "未繳"
                })
            
            df_export = pd.DataFrame(export_data)
            csv = df_export.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            
            # --- 關鍵修改處：動態產生檔名 ---
            today = datetime.date.today().strftime("%Y-%m-%d")
            file_name = f"{today}_{selected_class}.csv"
            
# --- 放在第 135 行 (st.download_button) 之後 ---
        st.divider()
        st.subheader("📊 20 週歷史紀錄與統計")
        
        history_df = load_history()
        
        if not history_df.empty:
            # 確保班級型態一致以利篩選
            history_df['班級'] = pd.to_numeric(history_df['班級'], errors='coerce')
            class_history = history_df[history_df["班級"] == int(selected_class)]
            
            if not class_history.empty:
                # 1. 顯示歷史明細
                st.write("### 歷史明細資料")
                st.dataframe(class_history, use_container_width=True)
                
                # 2. 個人累積統計總表 (自動統計)
                st.write("### 個人累積統計總表")
                
                # 計算：統計缺席與發言次數
                stats = class_history.groupby(['班級', '座號', '姓名']).agg({
                    '出席狀態': lambda x: (x == '缺席').sum(), 
                    '主動發言次數': 'sum'
                }).reset_index()
                
                # 獲取最新繳費狀態 (按日期取最後一筆)
                latest_payment = class_history.sort_values('日期').groupby('姓名').tail(1)[['姓名', '繳費狀態']]
                
                # 合併統計與繳費狀態
                final_stats = pd.merge(stats, latest_payment, on='姓名')
                
                # 重新命名欄位順序
                final_stats.columns = ['班級', '座號', '姓名', '缺席總次數', '發言總次數', '最新繳費狀態']
                
                # 顯示表格 (使用 hide_index=True 隱藏左側索引)
                st.dataframe(final_stats.sort_values('座號'), use_container_width=True, hide_index=True)
            else:
                st.info(f"{selected_class} 班目前尚無歷史紀錄。")
        else:
            st.info("尚無歷史紀錄，請確認「總資料庫」CSV 連結設定正確。")

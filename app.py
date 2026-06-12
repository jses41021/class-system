import streamlit as st
import pandas as pd
import datetime
import requests
import io  # 👈 務必確保上方有 import io
@st.cache_data(ttl=600)
def load_data():
    csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8_2gDvKiTieAleMNeHdN1owBrEtkhhWBrg3Bpl3b8CzURHgOBouqPJ-_-LTbP8ZXJyPywXlnTKkKj/pub?gid=0&single=true&output=csv" # 請務必確認這裡已替換成正確網址
    try:
        df = pd.read_csv(csv_url)
        return df  # 直接回傳上面讀取好的變數
    except:
        return pd.DataFrame()

# 在主程式中強制偵錯
all_df = load_data()
st.write("目前讀到的 DataFrame:", all_df) # 這行會把讀取結果直接印在網頁上

# 只有在資料不是空的時候，才執行後續的選單
if not all_df.empty:
    selected_class = st.sidebar.selectbox("請選擇班級", all_df["班級"].unique())
    # ... 後續程式碼 ...
else:
    st.warning("⚠️ 資料讀取為空！請檢查 CSV 網址是否正確，且 Google Sheet 是否已「發布至網路」。")

@st.cache_data(ttl=60)
def load_history():
    csv_url = "您的總資料庫CSV網址" # 請填入正確網址
    # 修改 load_data 函式，加入錯誤處理
@st.cache_data(ttl=60)
def load_data():
    # 請確保這串網址結尾有 &output=csv
    csv_url = "您的長網址..." 
    try:
        df = pd.read_csv(csv_url)
        return df
    except Exception as e:
        st.error(f"讀取失敗: {e}")
        return pd.DataFrame()

# 在呼叫時加上判斷
all_df = load_data()
if not all_df.empty:
    selected_class = st.sidebar.selectbox("請選擇班級", all_df["班級"].unique())
    # ... 後續 UI 程式碼 ...
else:
    st.warning("目前讀不到學生名單，請檢查 Google Sheet 連結與發布狀態！")
    try:
        return pd.read_csv(csv_url)
    except:
        return pd.DataFrame()

# --- 2. 執行主邏輯 (取代 Line 41 之後的邏輯) ---
all_df = load_data()
history_df = load_history()

# 強制除錯檢查
if all_df.empty:
    st.error("⚠️ 無法讀取名單！請檢查 Google Sheet 發布連結。")
else:
    # 檢查欄位是否存在
    if "班級" in all_df.columns:
        selected_class = st.sidebar.selectbox("請選擇班級", all_df["班級"].unique())
        df_class = all_df[all_df["班級"] == selected_class].copy()
        
        # 顯示介面
        st.subheader(f"目前班級: {selected_class}")
        tab1, tab2, tab3, tab4 = st.tabs(["✅ 點名", "🎲 抽籤/發言", "👥 分組", "💰 繳費"])
        
        with tab1:
            # 這裡放入您原本的點名功能代碼
            st.write("點名功能啟動中...")
            
    else:
        st.error(f"錯誤：找不到「班級」欄位。目前的欄位有：{all_df.columns.tolist()}")
    
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
     # --- 新增：整合 Google Apps Script 寫入功能 ---
        if st.button("💾 儲存今日紀錄至總資料庫"):
            # 這是你從 Google Apps Script 部署得到的網頁應用程式網址
            WEB_APP_URL = "https://script.google.com/macros/s/AKfycbz6v1LiJXiMQobPT-knkNUBSZ4ut4OwUbcKpzoFiSWKMaj2s8dqsKcmYeuJP8_bVY8UYw/exec" 
            
            with st.spinner("正在寫入資料到總資料庫..."):
                for name in df_class["姓名"]:
                    row = df_class[df_class['姓名'] == name].iloc[0]
                    # 準備要傳送的資料
                    payload = {
                        "日期": datetime.date.today().strftime("%Y/%m/%d"),
                        "班級": int(row['班級']),
                        "座號": int(row['座號']),
                        "姓名": row['姓名'],
                        "出席狀態": "出席" if st.session_state[f'attendance_{selected_class}'][name] else "缺席",
                        "繳費狀態": "已繳" if st.session_state[f'payment_{selected_class}'][name] else "未繳",
                        "發言次數": st.session_state[f'scores_{selected_class}'][name],
                        "中籤次數": 0, # 若未來有記錄抽籤功能可在此調整
                        "分組": "無" # 若未來有記錄分組功能可在此調整
                    }
                    # 發送給 Google Sheet
                    try:
                        requests.post(WEB_APP_URL, json=payload)
                    except Exception as e:
                        st.error(f"寫入失敗: {e}")
                
                st.success("✅ 紀錄已成功自動同步至總資料庫！")
            
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

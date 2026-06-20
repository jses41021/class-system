import streamlit as st
import pandas as pd
import datetime
import requests
import re

# --- 設定頁面 ---
st.set_page_config(layout="wide")
st.title("🍎 班級經營系統")

# 移除雙按鈕設計，僅保留儲存按鈕
save_clicked = st.button("💾 儲存今日紀錄", type="primary", use_container_width=True)

# 強力優化手機版 CSS
st.markdown("""
    <style>
    @media screen and (max-width: 768px) {
        [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: center !important;
            gap: 4px !important; 
            width: 100% !important;
        }
        [data-testid="stHorizontalBlock"] > div {
            flex: 1 1 30% !important; 
            min-width: 0 !important;
            max-width: 33% !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        [data-testid="stHorizontalBlock"] div[data-testid="stVerticalBlock"] {
            width: 100% !important;
            gap: 0px !important;
        }
        div.stButton { width: 100% !important; }
        div.stButton > button {
            padding: 4px 2px !important;
            font-size: 11px !important; 
            height: 36px !important;
            min-height: 36px !important;
            width: 100% !important;
            margin: 0 !important;
            white-space: nowrap !important; 
            overflow: hidden !important;
            text-overflow: ellipsis !important; 
            border-radius: 4px !important;
        }
        div.stMarkdown p {
            line-height: 32px !important;
            margin: 0 !important;
            font-size: 13px !important;
            white-space: nowrap !important;
        }
    }
    [data-testid="stDataFrame"] { width: 100%; }
    </style>
""", unsafe_allow_html=True)

# --- 設定網址 ---
STUDENT_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8_2gDvKiTieAleMNeHdN1owBrEtkhhWBrg3Bpl3b8CzURHgOBouqPJ-_-LTbP8ZXJyPywXlnTKkKj/pub?gid=0&single=true&output=csv"
HISTORY_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8_2gDvKiTieAleMNeHdN1owBrEtkhhWBrg3Bpl3b8CzURHgOBouqPJ-_-LTbP8ZXJyPywXlnTKkKj/pub?gid=2042566365&single=true&output=csv"
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbz6v1LiJXiMQobPT-knkNUBSZ4ut4OwUbcKpzoFiSWKMaj2s8dqsKcmYeuJP8_bVY8UYw/exec"
# 移除 GROUP_URL 依賴，後續直接利用 HISTORY_URL 計算分組歷史，避免錯誤
HW_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8_2gDvKiTieAleMNeHdN1owBrEtkhhWBrg3Bpl3b8CzURHgOBouqPJ-_-LTbP8ZXJyPywXlnTKkKj/pub?gid=1452088972&single=true&output=csv" 

@st.cache_data(ttl=60)
def load_data(url):
    if not url or url.startswith("請在此"): return pd.DataFrame()
    try: 
        # 加入時間戳記繞過 Google CDN 延遲
        fetch_url = f"{url}&_t={int(datetime.datetime.now().timestamp())}" if "?" in url else f"{url}?_t={int(datetime.datetime.now().timestamp())}"
        return pd.read_csv(fetch_url)
    except: return pd.DataFrame()

# 統一清理資料格式
def to_clean_str(x):
    if pd.isna(x): return ""
    x_str = str(x).strip()
    if x_str.endswith(".0"): return x_str[:-2]
    return x_str

all_df = load_data(STUDENT_URL)
base_history_df = load_data(HISTORY_URL)

# 導入樂觀更新機制(Optimistic UI)：暫存當前網頁送出的紀錄，實現秒更新
if 'optimistic_history' not in st.session_state:
    st.session_state['optimistic_history'] = pd.DataFrame()

history_df = pd.concat([base_history_df, st.session_state['optimistic_history']], ignore_index=True)

# 資料前處理
if not all_df.empty:
    for col in ['班級', '座號', '姓名']:
        if col in all_df.columns: all_df[col] = all_df[col].apply(to_clean_str)

if not history_df.empty:
    for col in ['班級', '座號', '姓名']:
        if col in history_df.columns: history_df[col] = history_df[col].apply(to_clean_str)
    # 過濾同一天、同座號的重複送出紀錄，以確保統計精準
    if '日期' in history_df.columns:
        history_df = history_df.drop_duplicates(subset=['日期', '班級', '座號', '姓名'], keep='last')

if all_df.empty:
    st.warning("⚠️ 學生名單讀取失敗！")
else:
    selected_class = str(st.sidebar.selectbox("請選擇班級", all_df["班級"].unique()))
    df_class = all_df[all_df["班級"] == selected_class].copy()
    
    if 'hw_all_df' not in st.session_state:
        hw_loaded = load_data(HW_URL)
        if not hw_loaded.empty and '班級' in hw_loaded.columns:
            for col in ['班級', '座號', '姓名']:
                if col in hw_loaded.columns: hw_loaded[col] = hw_loaded[col].apply(to_clean_str)
            # 使用 left merge 保留原本的作業紀錄，並補上剛剛新增的學生
            hw_loaded = pd.merge(all_df[['班級', '座號', '姓名']], hw_loaded, on=['班級', '座號', '姓名'], how='left')
            hw_loaded = hw_loaded.fillna("")
        else:
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
                student_hist = history_df[(history_df["姓名"] == name) & (history_df["班級"] == selected_class)]
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
                    "班級": str(row['班級']),
                    "座號": str(row['座號']),
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
                if response.status_code == 200: 
                    st.success("✅ 今日全部資料已同步完成！")
                    
                    # 將儲存的資料注入暫存區，實現無延遲的資料刷新
                    new_records = pd.DataFrame(all_data)
                    st.session_state['optimistic_history'] = pd.concat([st.session_state['optimistic_history'], new_records], ignore_index=True)
                    
                    st.cache_data.clear()
                    st.rerun()
                    
                else: st.error(f"同步發生錯誤，狀態碼: {response.status_code}")
            except Exception as e: st.error(f"同步請求失敗: {e}")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["✅ 點名", "🎲 抽籤/發言", "👥 分組", "💰 繳費", "📝 作業繳交"])

    with tab1:
        st.subheader("點名")
        for _, row in df_class.iterrows():
            name = row['姓名']
            disp = f"{row['班級']}-{row['座號']}-{name}"
            st.session_state[f'attendance_{selected_class}'][name] = st.checkbox(disp, value=st.session_state[f'attendance_{selected_class}'][name])

        st.divider()
        st.subheader("📊 個人累積統計表")
        if not history_df.empty:
            class_hist = history_df[history_df["班級"] == selected_class].copy()
            if not class_hist.empty:
                stats = class_hist.groupby(['班級', '座號', '姓名']).agg({
                    '出席狀態': lambda x: (x == '出席').sum(),
                    '繳費狀態': lambda x: "已繳" if (x == '已繳').any() else "未繳",
                    '發言次數': 'sum', 
                    '中籤次數': 'sum'
                }).reset_index()
                
                # 強制轉換為數值進行排序，解決字串排序 10 比 2 前面的問題
                stats['numeric_seat'] = pd.to_numeric(stats['座號'], errors='coerce').fillna(999)
                stats = stats.sort_values(by='numeric_seat').drop(columns=['numeric_seat'])
                
                stats['座號 - 姓名'] = stats['座號'].astype(str) + " - " + stats['姓名'].astype(str)
                stats.set_index('座號 - 姓名', inplace=True)
                display_stats = stats.drop(columns=['班級', '座號', '姓名'])
                st.dataframe(display_stats, use_container_width=True)

    present_students = [name for name, present in st.session_state[f'attendance_{selected_class}'].items() if present]

    with tab2:
        st.subheader("隨機抽籤")
        eligible_students = [name for name in present_students if st.session_state[f'draws_{selected_class}'][name] + st.session_state[f'scores_{selected_class}'][name] == 0]
        
        if st.button("🎲 抽籤 (僅限出席且未中籤/發言者)", use_container_width=True):
            if eligible_students:
                winner = pd.Series(eligible_students).sample(1).iloc[0]
                st.session_state[f'last_winner_{selected_class}'] = winner
                st.session_state[f'draws_{selected_class}'][winner] += 1
            else: st.warning("目前所有出席者都已經中籤或發言過了！")
            
        if st.session_state[f'last_winner_{selected_class}']:
            winner = st.session_state[f'last_winner_{selected_class}']
            w_row = df_class[df_class['姓名'] == winner].iloc[0]
            st.success(f"🎉 抽中：{w_row['座號']}-{winner}")

        st.markdown("<br>", unsafe_allow_html=True)
        
        chunk_size = 3
        for i in range(0, len(present_students), chunk_size):
            cols = st.columns(chunk_size)
            for j, name in enumerate(present_students[i:i+chunk_size]):
                row = df_class[df_class['姓名'] == name].iloc[0]
                seat = row['座號']
                with cols[j]:
                    if st.button(f"{seat}-{name}", key=f"score_{name}"):
                        st.session_state[f'scores_{selected_class}'][name] += 1
                        st.rerun()
                        
        st.divider()
        st.markdown("#### 累積當日抽籤與加分次數")
        for name in present_students:
            row = df_class[df_class['姓名'] == name].iloc[0]
            seat = row['座號']
            draws = st.session_state[f'draws_{selected_class}'][name]
            scores = st.session_state[f'scores_{selected_class}'][name]
            st.markdown(f"{seat}-{name} - 中籤次數： **{draws}** 次、發言次數： **{scores}** 次")

    with tab3:
        st.subheader("隨機分組")
        group_n = st.selectbox("組數", [3, 4, 5, 6, 8])
        if st.button("開始分組"):
            shuffled = pd.Series(present_students).sample(frac=1).tolist()
            groups = [shuffled[i::group_n] for i in range(group_n)]
            for name in df_class["姓名"]: st.session_state[f'group_dict_{selected_class}'][name] = "無"
            for i, g in enumerate(groups):
                group_name = f"第 {i+1} 組"
                st.write(f"{group_name}: {', '.join([f'{str(df_class.loc[df_class['姓名']==name, '座號'].values[0])} {name}' for name in g])}")
                for name in g: st.session_state[f'group_dict_{selected_class}'][name] = group_name
        
        st.divider()
        st.subheader("📅 各週次分組紀錄")
        
        # 直接由總資料庫 history_df 中過濾出該班級真實的分組紀錄 (不再過濾掉「無」)
        if not history_df.empty and '班級' in history_df.columns and '分組' in history_df.columns:
            group_class = history_df[(history_df["班級"] == selected_class) & 
                                     (history_df["分組"].notna())].copy()
        else:
            group_class = pd.DataFrame(columns=['日期', '班級', '座號', '姓名', '分組'])
            
        today_str = datetime.date.today().strftime("%Y/%m/%d")
        has_active_grouping = any(v != "無" for v in st.session_state[f'group_dict_{selected_class}'].values())
        
        if has_active_grouping:
            today_data = []
            for name, g_val in st.session_state[f'group_dict_{selected_class}'].items():
                row_student = df_class[df_class['姓名'] == name].iloc[0]
                today_data.append({
                    "日期": today_str,
                    "班級": selected_class,
                    "座號": str(row_student['座號']),
                    "姓名": name,
                    "分組": g_val
                })
            if today_data:
                df_today = pd.DataFrame(today_data)
                # 即時顯示今日尚未存檔的分組或覆蓋同日的歷史紀錄
                if group_class.empty or today_str not in group_class["日期"].values:
                    group_class = pd.concat([df_today, group_class], ignore_index=True)
                else:
                    group_class = group_class[group_class["日期"] != today_str]
                    group_class = pd.concat([df_today, group_class], ignore_index=True)

        if not group_class.empty:
            dates = sorted(group_class["日期"].dropna().unique(), reverse=True)
            for d in dates:
                st.markdown(f"**{d}**")
                df_date = group_class[group_class["日期"] == d]
                groups = df_date["分組"].dropna().unique()
                
                # 將「有分組」與「無分組」分開處理，先處理正常組別
                regular_groups = [g for g in groups if str(g).strip() not in ["無", ""]]
                
                try:
                    regular_groups = sorted(regular_groups, key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else x)
                except:
                    regular_groups = sorted(regular_groups)
                    
                for g in regular_groups:
                    df_g = df_date[df_date["分組"] == g].copy()
                    
                    # 確保同組內人員照座號排好
                    df_g['numeric_seat'] = pd.to_numeric(df_g['座號'], errors='coerce').fillna(999)
                    df_g = df_g.sort_values(by="numeric_seat")
                    
                    members = []
                    for _, r in df_g.iterrows():
                        seat = str(r["座號"]) if pd.notna(r["座號"]) else ""
                        name = str(r["姓名"]) if pd.notna(r["姓名"]) else ""
                        members.append(f"{seat}{name}")
                    st.write(f"{g}: {' '.join(members)}")
                    
                # 在最後處理並顯示無分組(缺席)的同學名單
                df_unassigned = df_date[df_date["分組"].astype(str).str.strip().isin(["無", ""])].copy()
                if not df_unassigned.empty:
                    df_unassigned['numeric_seat'] = pd.to_numeric(df_unassigned['座號'], errors='coerce').fillna(999)
                    df_unassigned = df_unassigned.sort_values(by="numeric_seat")
                    
                    members_unassigned = []
                    for _, r in df_unassigned.iterrows():
                        seat = str(r["座號"]) if pd.notna(r["座號"]) else ""
                        name = str(r["姓名"]) if pd.notna(r["姓名"]) else ""
                        members_unassigned.append(f"{seat}{name}")
                    st.write(f"無分組: {' '.join(members_unassigned)}")
                    
                st.divider()
        else:
            st.write("目前無此班級的分組紀錄。")

    with tab4:
        st.subheader("繳費管理")
        for _, row in df_class.iterrows():
            name = row['姓名']
            st.session_state[f'payment_{selected_class}'][name] = st.checkbox(f"{row['班級']}-{row['座號']}-{name}", value=st.session_state[f'payment_{selected_class}'][name], key=f"pay_{name}")

    with tab5:
        st.subheader("📝 作業繳交管理")
        df_hw_all = st.session_state['hw_all_df']
        class_hw_df = df_hw_all[df_hw_all['班級'] == selected_class].copy()
        
        standard_cols = ['班級', '座號', '姓名']
        valid_cols = standard_cols.copy()
        for col in class_hw_df.columns:
            if col not in standard_cols:
                if not class_hw_df[col].astype(str).replace("nan", "").str.strip().eq("").all():
                    valid_cols.append(col)
        
        class_hw_df = class_hw_df[valid_cols]
        
        # 加入數值排序邏輯確保作業清單的座號順序正常
        class_hw_df['numeric_seat'] = pd.to_numeric(class_hw_df['座號'], errors='coerce').fillna(999)
        class_hw_df = class_hw_df.sort_values(by='numeric_seat').drop(columns=['numeric_seat'])
        
        class_hw_df['座號 - 姓名'] = class_hw_df['座號'].astype(str) + " - " + class_hw_df['姓名'].astype(str)
        class_hw_df.set_index('座號 - 姓名', inplace=True)
        
        cols_to_hide = ['班級', '座號', '姓名', '日期']
        display_hw_df = class_hw_df.drop(columns=[c for c in cols_to_hide if c in class_hw_df.columns])
        
        hw_col_config = {}
        for col in display_hw_df.columns:
            hw_col_config[col] = st.column_config.SelectboxColumn(col, options=["已繳", "未繳", ""])
        
        st.markdown("👇 **學生作業狀況總表 (點兩下儲存格可下拉修改狀態，選「已繳」儲存後會自動轉成當日日期)**")
        edited_display_df = st.data_editor(display_hw_df, use_container_width=True, column_config=hw_col_config)

        if st.button("📤 儲存表格修改至 Google Sheet", type="secondary"):
            with st.spinner("正在上傳紀錄..."):
                updates = []
                today_str = datetime.date.today().strftime("%Y/%m/%d")
                df_hw_all = st.session_state['hw_all_df']
                edited_reset = edited_display_df.reset_index()
                
                for idx, row in edited_reset.iterrows():
                    seat_val_str = str(row['座號 - 姓名']).split(" - ")[0]
                    mask = (df_hw_all['班級'] == selected_class) & (df_hw_all['座號'] == seat_val_str)
                    orig_row = df_hw_all[mask].iloc[0] if not df_hw_all[mask].empty else None

                    for col in edited_display_df.columns:
                        new_val = row[col]
                        if new_val == "已繳": new_val = today_str
                        if new_val == "未繳": new_val = ""

                        orig_val = orig_row[col] if orig_row is not None and col in orig_row else ""
                        if str(new_val) != str(orig_val):
                            updates.append({
                                "class_num": selected_class,
                                "seat": seat_val_str,
                                "hw_name": col,
                                "value": new_val
                            })
                            df_hw_all.loc[mask, col] = new_val

                st.session_state['hw_all_df'] = df_hw_all
                
                if updates:
                    update_payload = {"action": "manual_update_hw", "updates": updates}
                    try:
                        res = requests.post(WEB_APP_URL, json=update_payload, timeout=15)
                        if res.status_code == 200:
                            st.success("✅ 作業紀錄已成功更新，並已連動總資料庫！")
                            st.rerun()
                        else: st.error("儲存發生錯誤。")
                    except Exception as e: st.error(f"連線失敗: {e}")
                else:
                    st.info("沒有偵測到任何修改。")

        st.divider()
        st.markdown("#### 📥 批次匯入缺交名單")
        hw_input = st.text_area("貼上缺交名單", height=150, placeholder="可帶標籤：日期:2026/12/1、作業名稱:烹飪反思、班級:機縫實作、缺交同學座號:1、5\n或直接輸入：2026/12/1、烹飪反思、機縫實作、1、5")
        
        if st.button("一鍵匯入名單並同步至 Sheet", type="primary"):
            hw_input = hw_input.strip()
            hw_date = datetime.date.today().strftime("%Y/%m/%d")
            hw_name = ""
            hw_class = ""
            missing_seats = []
            
            if "作業" in hw_input or "班級" in hw_input:
                date_match = re.search(r'日期[：:]\s*([\d/]+)', hw_input)
                if date_match: hw_date = date_match.group(1).strip()

                name_match = re.search(r'作業名稱[：:]\s*(.*?)(?=(?:日期|班級|缺交同學座號)[：:]|$)', hw_input, re.DOTALL)
                if name_match: hw_name = name_match.group(1).strip().strip('、').strip(',')

                class_match = re.search(r'班級[：:]\s*(.*?)(?=(?:日期|作業名稱|缺交同學座號)[：:]|$)', hw_input, re.DOTALL)
                if class_match: hw_class = class_match.group(1).strip().strip('、').strip(',')

                missing_match = re.search(r'缺交同學座號[：:]\s*(.*)', hw_input, re.DOTALL)
                if missing_match:
                    parts = re.split(r'[、,，\s]+', missing_match.group(1).strip())
                    missing_seats = [str(int(p)) for p in parts if p.isdigit()]
            else:
                parts = [p.strip() for p in re.split(r'[、,，\s]+', hw_input) if p.strip()]
                if len(parts) >= 3:
                    if re.match(r'\d{4}/\d{1,2}/\d{1,2}', parts[0]):
                        hw_date = parts[0]
                        hw_name = parts[1]
                        hw_class = parts[2]
                        missing_seats = [str(int(p)) for p in parts[3:] if p.isdigit()]
                    else:
                        hw_name = parts[0]
                        hw_class = parts[1]
                        missing_seats = [str(int(p)) for p in parts[2:] if p.isdigit()]

            if not hw_name or not hw_class:
                st.error("❌ 格式解析錯誤。請確認格式包含作業名稱與班級")
            elif str(hw_class) != str(selected_class):
                st.error(f"⚠️ 貼上的班級 ({hw_class}) 與目前選擇的班級 ({selected_class}) 不符！")
            else:
                students_list = [{"座號": str(row['座號']), "姓名": row['姓名']} for _, row in df_class.iterrows()]
                
                payload = {
                    "action": "batch_import_hw",
                    "date": hw_date,
                    "hw_name": hw_name,
                    "class_num": str(hw_class),
                    "missing_seats": missing_seats,
                    "students": students_list
                }
                
                with st.spinner("正在同步至資料庫與作業分頁..."):
                    try:
                        res = requests.post(WEB_APP_URL, json=payload, timeout=15)
                        if res.status_code == 200:
                            st.success(f"✅ {hw_name} 紀錄匯入成功！已連動『總資料庫』與『作業繳交』雙表！")
                            df_hw_all = st.session_state['hw_all_df']
                            if hw_name not in df_hw_all.columns: df_hw_all[hw_name] = ""
                            mask_class = df_hw_all['班級'] == selected_class
                            for idx, row in df_hw_all[mask_class].iterrows():
                                seat = str(row['座號'])
                                df_hw_all.at[idx, hw_name] = "未繳" if seat in missing_seats else hw_date
                            st.session_state['hw_all_df'] = df_hw_all
                            st.rerun()
                        else: st.error("⚠️ 同步失敗。")
                    except Exception as e: st.error(f"❌ 請求失敗：{e}")

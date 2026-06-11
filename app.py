import streamlit as st
import pandas as pd

# --- 設定頁面 ---
st.set_page_config(layout="wide")
st.title("🍎 班級經營系統")

# --- 載入基礎資料 ---
@st.cache_data(ttl=600)
def load_data():
    csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8_2gDvKiTieAleMNeHdN1owBrEtkhhWBrg3Bpl3b8CzURHgOBouqPJ-_-LTbP8ZXJyPywXlnTKkKj/pub?gid=0&single=true&output=csv"
    try: return pd.read_csv(csv_url)
    except: return pd.DataFrame()

# --- 載入歷史紀錄 ---
@st.cache_data(ttl=600)
def load_history():
    # 請務必將此處改為您公開發布的 CSV 連結
    history_url = "您的歷史紀錄總表_發布至網路的CSV連結"
    try: return pd.read_csv(history_url)
    except: return pd.DataFrame()

all_df = load_data()
history_df = load_history()

if not all_df.empty:
    selected_class = st.sidebar.selectbox("請選擇班級", all_df["班級"].unique())
    df_class = all_df[all_df["班級"] == selected_class].copy()
    
    def get_display_name(row):
        return f"{int(row['班級'])}-{int(row['座號'])}-{row['姓名']}"

    # 初始化 Session State
    if f'attendance_{selected_class}' not in st.session_state:
        st.session_state[f'attendance_{selected_class}'] = {name: True for name in df_class["姓名"]}
    if f'scores_{selected_class}' not in st.session_state:
        st.session_state[f'scores_{selected_class}'] = {name: 0 for name in df_class["姓名"]}
    if f'payment_{selected_class}' not in st.session_state:
        st.session_state[f'payment_{selected_class}'] = {name: False for name in df_class["姓名"]}

    tab1, tab2, tab3, tab4 = st.tabs(["✅ 點名", "🎲 抽籤/發言", "👥 分組", "💰 繳費與20週紀錄"])

    with tab1:
        st.subheader("點名")
        for _, row in df_class.iterrows():
            name = row['姓名']
            st.session_state[f'attendance_{selected_class}'][name] = st.checkbox(get_display_name(row), value=st.session_state[f'attendance_{selected_class}'][name])

    present_students = [name for name, present in st.session_state[f'attendance_{selected_class}'].items() if present]

    with tab2:
        st.subheader("抽籤與發言")
        if st.button("🎲 隨機抽籤"):
            if present_students:
                winner = pd.Series(present_students).sample(1).iloc[0]
                st.session_state[f'scores_{selected_class}'][winner] += 1
                st.rerun()
        for name in present_students:
            row = df_class[df_class['姓名'] == name].iloc[0]
            col1, col2 = st.columns([3, 1])
            col1.write(f"{get_display_name(row)} (累積：{st.session_state[f'scores_{selected_class}'].get(name, 0)} 次)")
            if col2.button("加分", key=f"btn_{name}"):
                st.session_state[f'scores_{selected_class}'][name] += 1
                st.rerun()

    with tab3:
        st.subheader("隨機分組")
        for n in [3, 4, 5, 6, 8]:
            if st.button(f"{n} 組"):
                random_list = pd.Series(present_students).sample(frac=1).tolist()
                groups = [random_list[i::n] for i in range(n)]
                for i, group in enumerate(groups):
                    full_names = [get_display_name(df_class[df_class['姓名'] == name].iloc[0]) for name in group]
                    st.write(f"第 {i+1} 組: {', '.join(full_names)}")

    with tab4:
        st.subheader(f"{selected_class} 繳費管理")
        # 恢復繳費勾選功能
        for _, row in df_class.iterrows():
            name = row['姓名']
            st.session_state[f'payment_{selected_class}'][name] = st.checkbox(get_display_name(row), value=st.session_state[f'payment_{selected_class}'][name], key=f"pay_{name}")
        
        # 恢復匯出功能
        if st.button("💾 匯出本週紀錄 (CSV)"):
            export_data = []
            for name in df_class["姓名"]:
                row = df_class[df_class['姓名'] == name].iloc[0]
                export_data.append({
                    "班級": int(row['班級']), "座號": int(row['座號']), "姓名": row['姓名'],
                    "出席": st.session_state[f'attendance_{selected_class}'][name],
                    "發言": st.session_state[f'scores_{selected_class}'][name],
                    "繳費": "已繳" if st.session_state[f'payment_{selected_class}'][name] else "未繳"
                })
            df_export = pd.DataFrame(export_data)
            csv = df_export.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button("📥 點擊下載本週 CSV", csv, f"{selected_class}_紀錄.csv", "text/csv")
            
        st.divider()
        st.subheader("📊 20 週歷史紀錄")
        if not history_df.empty:
            st.dataframe(history_df, use_container_width=True)
        else:
            st.info("請確認歷史總表 CSV 連結已設定正確。")

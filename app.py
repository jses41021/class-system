import streamlit as st
import pandas as pd
import random

# 假設資料來源 (您之後可替換為讀取 CSV 的函數)
if 'students' not in st.session_state:
    st.session_state['students'] = pd.DataFrame({
        "座號": range(1, 21),
        "姓名": [f"學生{i}" for i in range(1, 21)],
        "被抽次數": 0,
        "出席": True,
        "繳費": False
    })

df = st.session_state['students']

st.title("🍎 班級經營系統")
tab1, tab2, tab3, tab4 = st.tabs(["✅ 點名", "🎲 抽籤/發言", "👥 隨機分組", "💰 繳費"])

# 1. 快速打勾點名
with tab1:
    st.subheader("點名 (預設出席，取消勾選為缺席)")
    edited_df = st.data_editor(df[["座號", "姓名", "出席"]], hide_index=True)
    if st.button("確認點名"):
        st.session_state['students']['出席'] = edited_df['出席']
        st.success("點名已儲存")

# 2. 抽籤與發言 (機率加權)
with tab2:
    st.subheader("機率加權抽籤")
    # 權重計算：次數越高，權重越低 (1 / (次數 + 1))
    weights = 1 / (df['被抽次數'] + 1)
    if st.button("抽一位同學"):
        winner = df.sample(1, weights=weights)
        st.success(f"抽中：{winner.iloc[0]['姓名']}")
        st.session_state['students'].loc[winner.index, '被抽次數'] += 1
    
    st.write("---")
    st.subheader("主動發言計次")
    target = st.selectbox("選擇學生", df['姓名'])
    if st.button("計入發言一次"):
        idx = df[df['姓名'] == target].index
        st.session_state['students'].loc[idx, '被抽次數'] += 1
        st.rerun()

# 3. 隨機分組
with tab3:
    st.subheader("隨機分組")
    num_groups = st.selectbox("選擇分組數量", [3, 4, 5, 6, 8])
    if st.button("開始分組"):
        shuffled = df['姓名'].sample(frac=1).tolist()
        groups = [shuffled[i::num_groups] for i in range(num_groups)]
        for i, group in enumerate(groups):
            st.write(f"第 {i+1} 組: {', '.join(group)}")

# 4. 繳費清單
with tab4:
    st.subheader("繳費管理 (預設未繳)")
    pay_df = st.data_editor(df[["座號", "姓名", "繳費"]], hide_index=True)
    if st.button("儲存繳費"):
        st.session_state['students']['繳費'] = pay_df['繳費']
        st.success("繳費狀態已更新")

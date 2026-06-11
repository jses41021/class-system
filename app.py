import streamlit as st
import pandas as pd

# ... (其餘讀取資料的程式碼保持不變) ...

# 核心顯示名稱轉換邏輯
def get_display_name(row):
    # 強制座號為整數，移除 .0
    seat_num = int(row['座號'])
    return f"{row['班級']}-{seat_num}-{row['姓名']}"

# 在讀取資料後，新增一欄顯示名稱
all_df['顯示名稱'] = all_df.apply(get_display_name, axis=1)

# --- 點名頁面修正 ---
with tab1:
    st.subheader(f"{selected_class} 點名 (打勾代表出席)")
    # 使用顯示名稱進行循環
    for _, row in df_class.iterrows():
        display_name = get_display_name(row)
        # 用原姓名當 key，但顯示名稱給使用者看
        st.session_state[f'attendance_{selected_class}'][row['姓名']] = st.checkbox(display_name, value=st.session_state[f'attendance_{selected_class}'].get(row['姓名'], True))

# --- 抽籤頁面修正 ---
with tab2:
    # ... (前略) ...
    # 加分按鈕顯示
    for _, row in df_class.iterrows():
        name = row['姓名']
        if name in present_students:
            col1, col2 = st.columns([3, 1])
            score = st.session_state[f'scores_{selected_class}'].get(name, 0)
            col1.write(f"{get_display_name(row)} (累積：{score} 次)") # 顯示格式：班級-座號-姓名
            if col2.button("加分", key=f"btn_{name}"):
                st.session_state[f'scores_{selected_class}'][name] += 1
                st.rerun()

# --- 分組頁面修正 ---
with tab3:
    # ... (前略) ...
    # 分組顯示
    full_names = []
    for name in group:
        # 從 df_class 中找到該姓名對應的行，以獲取班級座號
        student_row = df_class[df_class['姓名'] == name].iloc[0]
        full_names.append(get_display_name(student_row))
    st.write(f"第 {g_idx+1} 組: {', '.join(full_names)}")

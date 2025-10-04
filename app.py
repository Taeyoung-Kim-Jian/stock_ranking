import streamlit as st
import pandas as pd
from supabase import create_client

# -------------------------------
# Supabase 연결
# -------------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------------
# 데이터 불러오기
# -------------------------------
def load_stocks():
    res = supabase.table("stocks").select("*").execute()
    return pd.DataFrame(res.data)

# -------------------------------
# UI
# -------------------------------
st.set_page_config(page_title="Stocks Dashboard", layout="wide")
st.title("📊 종목 리스트")

df = load_stocks()
if df.empty:
    st.warning("⚠️ 데이터 없음")
    st.stop()

# ✅ 종목명 + 코드 합치기
df["종목"] = df["종목명"] + " (" + df["종목코드"] + ")"

# ✅ 테이블 형태로 반복 출력
st.subheader("📑 종목 목록")

for _, row in df.iterrows():
    code = row["종목코드"]
    name = row["종목"]

    col1, col2, col3, col4, col5 = st.columns([2, 3, 3, 3, 2])
    col1.write(code)
    col2.write(row["종목명"])
    col3.write(row.get("등록일", ""))
    col4.write(row.get("마지막업데이트일", ""))

    # ✅ 버튼 클릭 → 상세 페이지 이동
    if col5.button("상세보기", key=f"btn_{code}"):
        st.session_state.selected_code = code
        st.session_state.selected_name = row["종목명"]
        st.switch_page("pages/stock_detail.py")

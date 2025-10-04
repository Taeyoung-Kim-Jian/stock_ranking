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
# UI 시작
# -------------------------------
st.set_page_config(page_title="Stocks Dashboard", layout="wide")
st.title("📊 종목 리스트")

df = load_stocks()
if df.empty:
    st.warning("⚠️ Supabase의 stocks 테이블에 데이터가 없습니다.")
    st.stop()

# ✅ 표 + 상세보기 버튼
for _, row in df.iterrows():
    code = row["종목코드"]
    name = row["종목명"]

    col1, col2, col3, col4, col5 = st.columns([2, 3, 3, 3, 2])
    col1.write(code)
    col2.write(name)
    col3.write(row.get("등록일", ""))
    col4.write(row.get("마지막업데이트일", ""))

    # 상세보기 버튼 → stock_detail 페이지로 이동
    if col5.button("상세보기", key=f"btn_{code}"):
        st.switch_page(f"pages/stock_detail.py?code={code}")

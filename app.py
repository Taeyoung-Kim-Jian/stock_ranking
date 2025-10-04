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
    """stocks 테이블 전체"""
    res = supabase.table("stocks").select("*").execute()
    return pd.DataFrame(res.data)

def load_latest_price(code: str):
    """특정 종목의 최신 가격 데이터"""
    res = (
        supabase.table("prices")
        .select("날짜, 종가")
        .eq("종목코드", code)
        .order("날짜", desc=True)   # 최신 날짜순
        .limit(1)
        .execute()
    )
    if res.data:
        return res.data[0]["종가"], res.data[0]["날짜"]
    return None, None

# -------------------------------
# Streamlit UI
# -------------------------------
st.set_page_config(page_title="Stocks Dashboard", layout="wide")
st.title("📊 종목 리스트")

df = load_stocks()
if df.empty:
    st.warning("⚠️ Supabase의 stocks 테이블에 데이터가 없습니다.")
    st.stop()

# 테이블 헤더
header_cols = st.columns([2, 3, 3, 3, 2, 2, 2])
header_cols[0].write("종목코드")
header_cols[1].write("종목명")
header_cols[2].write("등록일")
header_cols[3].write("마지막업데이트일")
header_cols[4].write("최근 종가")
header_cols[5].write("최근 날짜")
header_cols[6].write("상세보기")

# 종목 리스트 반복 출력
for _, row in df.iterrows():
    code = row["종목코드"]
    name = row["종목명"]

    last_price, last_date = load_latest_price(code)

    col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 3, 3, 3, 2, 2, 2])
    col1.write(code)
    col2.write(name)
    col3.write(row.get("등록일", ""))
    col4.write(row.get("마지막업데이트일", ""))
    col5.write(last_price if last_price else "-")
    col6.write(last_date if last_date else "-")

    if col7.button("상세보기", key=f"btn_{code}"):
        st.session_state.selected_code = code
        st.switch_page("pages/stock_detail.py")

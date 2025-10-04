import streamlit as st
import pandas as pd
from supabase import create_client
import os

# ------------------------------
# 환경 변수 설정 (Streamlit Cloud에서는 Secrets에 저장)
# ------------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------------
# 데이터 불러오기
# ------------------------------
def load_stocks():
    res = supabase.table("stocks").select("*").execute()
    return pd.DataFrame(res.data)

# ------------------------------
# Streamlit UI
# ------------------------------
st.set_page_config(page_title="Stocks Dashboard", layout="wide")

st.title("📊 Stocks Dashboard (Supabase 연동)")

# 데이터 불러오기
df = load_stocks()

if df.empty:
    st.warning("⚠️ Supabase의 stocks 테이블에 데이터가 없습니다.")
else:
    # 테이블 표시
    st.dataframe(df, use_container_width=True)

    # 종목 선택
    stock_list = df["종목명"].tolist()
    stock = st.selectbox("종목 선택", stock_list)

    if stock:
        stock_code = df[df["종목명"] == stock]["종목코드"].iloc[0]
        st.subheader(f"📈 {stock} ({stock_code}) 상세 데이터")

        # prices 테이블에서 해당 종목 가격 데이터 불러오기
        res = supabase.table("prices").select("*").eq("종목코드", stock_code).order("날짜").execute()
        price_df = pd.DataFrame(res.data)

        if not price_df.empty:
            price_df["날짜"] = pd.to_datetime(price_df["날짜"])
            price_df = price_df.sort_values("날짜")

            st.line_chart(price_df.set_index("날짜")["종가"])
        else:
            st.info("가격 데이터가 없습니다.")

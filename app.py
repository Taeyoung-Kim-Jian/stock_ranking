import streamlit as st
import pandas as pd
from supabase import create_client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def load_stocks():
    res = supabase.table("stocks").select("*").execute()
    return pd.DataFrame(res.data)

st.title("📊 Stocks List")
df = load_stocks()

if not df.empty:
    st.dataframe(df)

    # 종목 선택 → 세션 저장
    stock = st.selectbox("종목 선택", df["종목명"].tolist())
    if st.button("➡ 상세 페이지로 이동"):
        stock_code = df[df["종목명"] == stock]["종목코드"].iloc[0]
        st.session_state["selected_stock"] = {"name": stock, "code": stock_code}
        st.switch_page("pages/stock_detail.py")  # Streamlit 1.25 이후 지원

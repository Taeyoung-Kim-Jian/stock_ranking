import streamlit as st
import pandas as pd
from supabase import create_client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("📈 Stock Detail")

# 세션에서 종목 읽기
if "selected_stock" not in st.session_state:
    st.error("⚠️ 메인 페이지에서 종목을 먼저 선택하세요.")
    st.stop()

stock = st.session_state["selected_stock"]
st.subheader(f"{stock['name']} ({stock['code']})")

# 가격 데이터 불러오기
res = supabase.table("prices").select("*").eq("종목코드", stock["code"]).order("날짜").execute()
df = pd.DataFrame(res.data)

if not df.empty:
    df["날짜"] = pd.to_datetime(df["날짜"])
    st.line_chart(df.set_index("날짜")["종가"])
else:
    st.info("데이터가 없습니다.")

import streamlit as st
import pandas as pd
from supabase import create_client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def load_stocks():
    res = supabase.table("stocks").select("*").execute()
    return pd.DataFrame(res.data)

st.set_page_config(page_title="Stocks Dashboard", layout="wide")
st.title("📊 종목 리스트")

df = load_stocks()
if df.empty:
    st.warning("⚠️ 데이터 없음")
    st.stop()

for _, row in df.iterrows():
    code = row["종목코드"]
    name = row["종목명"]

    col1, col2, col3, col4, col5 = st.columns([2, 3, 3, 3, 2])
    col1.write(code)
    col2.write(name)
    col3.write(row.get("등록일", ""))
    col4.write(row.get("마지막업데이트일", ""))

    if col5.button("상세보기", key=f"btn_{code}"):
        st.session_state.selected_code = code
        st.switch_page("pages/stock_detail.py")

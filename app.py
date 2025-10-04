import streamlit as st
import pandas as pd
from supabase import create_client
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# Supabase 연결
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

# AgGrid 설정
cols = ["종목코드", "종목명", "등록일", "마지막업데이트일"]
gb = GridOptionsBuilder.from_dataframe(df[cols])
gb.configure_selection("single", use_checkbox=True)  # ✅ 행 선택 가능
grid_options = gb.build()

grid_response = AgGrid(
    df[cols],
    gridOptions=grid_options,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    theme="streamlit",
    height=420,
    allow_unsafe_jscode=True,
)

selected = grid_response["selected_rows"]

# ✅ 선택된 종목이 있으면 상세 페이지 링크 표시
if selected:
    stock = selected[0]
    code = stock["종목코드"]
    name = stock["종목명"]
    st.markdown(f"👉 [{name} ({code}) 상세보기](stock_detail?code={code})")

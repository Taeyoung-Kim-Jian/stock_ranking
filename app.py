import streamlit as st
import pandas as pd
from supabase import create_client
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

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

# ✅ 테이블에서 보여줄 컬럼만 선택
cols = ["종목코드", "종목명", "등록일", "마지막업데이트일"]

# AgGrid 설정
gb = GridOptionsBuilder.from_dataframe(df[cols])
gb.configure_selection("single", use_checkbox=True)  # 단일 행 선택
grid_options = gb.build()

grid_response = AgGrid(
    df[cols],
    gridOptions=grid_options,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    theme="streamlit",
    height=420,
    allow_unsafe_jscode=True,
)

# -------------------------------
# 선택된 종목 처리
# -------------------------------
selected = grid_response["selected_rows"]

# ✅ 항상 리스트로 변환
if isinstance(selected, pd.DataFrame):
    selected = selected.to_dict(orient="records")

# ✅ 리스트 길이 체크 후 상세 페이지 링크 제공
if selected and len(selected) > 0:
    stock = selected[0]
    code = stock["종목코드"]
    name = stock["종목명"]
    st.markdown(f"👉 [{name} ({code}) 상세보기](stock_detail?code={code})")

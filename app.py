import streamlit as st
import pandas as pd
from supabase import create_client
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

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
    st.warning("⚠️ Supabase의 stocks 테이블에 데이터가 없습니다.")
    st.stop()

# ✅ 종목명 + 코드 합치기
df["종목"] = df["종목명"] + " (" + df["종목코드"] + ")"

# ✅ 상세보기 버튼을 위한 컬럼 추가
df["상세보기"] = ""

# ✅ 버튼 렌더러 정의 (JS)
cell_renderer = JsCode("""
function(params) {
    return '<button style="padding:5px 10px; background:#4CAF50; color:white; border:none; border-radius:4px; cursor:pointer;">상세보기</button>'
}
""")

# ✅ GridOptions 생성
gb = GridOptionsBuilder.from_dataframe(
    df[["종목코드","종목","등록일","마지막업데이트일","상세보기"]]
)
gb.configure_column("상세보기", cellRenderer=cell_renderer, width=120)
gb.configure_selection("single", use_checkbox=False)  # 행 클릭 감지

grid_options = gb.build()

# ✅ AgGrid 렌더링
grid_response = AgGrid(
    df,
    gridOptions=grid_options,
    update_mode="MODEL_CHANGED",
    fit_columns_on_grid_load=True,
    theme="streamlit",
    allow_unsafe_jscode=True,
    height=600,
)

# ✅ 선택된 행 가져오기
selected = grid_response["selected_rows"]

if selected:
    stock = selected[0]
    code = stock["종목코드"]
    name = stock["종목명"]

    # 세션 상태 저장 → 상세 페이지에서 사용
    st.session_state.selected_code = code
    st.session_state.selected_name = name

    st.success(f"👉 {name} ({code}) 상세 페이지로 이동합니다...")
    st.switch_page("pages/stock_detail.py")

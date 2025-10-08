# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from supabase import create_client
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# ------------------------------------------------
# 페이지 설정
# ------------------------------------------------
st.set_page_config(page_title="전체 종목 목록", layout="wide")

# ------------------------------------------------
# Supabase 연결
# ------------------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Supabase 환경변수(SUPABASE_URL, SUPABASE_KEY)가 설정되지 않았습니다.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------------------------------
# 헤더
# ------------------------------------------------
st.markdown("<h4 style='text-align:center;'>📋 전체 종목 리스트</h4>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray; font-size:13px;'>행을 클릭하면 상세 차트 페이지로 이동합니다.</p>", unsafe_allow_html=True)
st.markdown("---")

# ------------------------------------------------
# 데이터 로딩
# ------------------------------------------------
@st.cache_data(ttl=300)
def load_total_return():
    try:
        res = (
            supabase.table("total_return")
            .select("종목명, 시작가격, 현재가격, 수익률")  # 필요하면 '종목코드'도 포함하세요.
            .order("수익률", desc=True)
            .execute()
        )
        return pd.DataFrame(res.data or [])
    except Exception as e:
        st.error(f"❌ 데이터 불러오기 오류: {e}")
        return pd.DataFrame()

df = load_total_return()

if df.empty:
    st.warning("⚠️ Supabase total_return 테이블에서 데이터를 불러올 수 없습니다.")
    st.stop()

# ------------------------------------------------
# AgGrid 표시 설정
# ------------------------------------------------
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(resizable=True, sortable=True, filter=True)
gb.configure_selection(selection_mode="single", use_checkbox=False)
gb.configure_grid_options(domLayout="normal")
grid_options = gb.build()

st.markdown("### 🔍 종목 목록")
grid_response = AgGrid(
    df,
    gridOptions=grid_options,
    enable_enterprise_modules=False,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    theme="streamlit",
    fit_columns_on_grid_load=True,
    height=600,
    key="total_return_grid"  # 상태 안정화
)

# ------------------------------------------------
# selected_rows 안전 처리 (None / list / DataFrame 모두 대응)
# ------------------------------------------------
def get_selected_rows_safe(resp) -> pd.DataFrame:
    """AgGrid 응답에서 선택된 행들을 DataFrame으로 반환. 없으면 빈 DF."""
    if not isinstance(resp, dict):
        return pd.DataFrame()
    sel = resp.get("selected_rows", None)

    if sel is None:
        return pd.DataFrame()
    if isinstance(sel, list):
        # list[dict] -> DataFrame
        return pd.DataFrame(sel) if len(sel) > 0 else pd.DataFrame()
    if isinstance(sel, pd.DataFrame):
        return sel
    # 예외 타입 방어
    try:
        return pd.DataFrame(sel)
    except Exception:
        return pd.DataFrame()

selected_df = get_selected_rows_safe(grid_response)

# ------------------------------------------------
# 행 클릭 시 페이지 이동
# ------------------------------------------------
if not selected_df.empty:
    # DataFrame 접근은 iloc 사용 (사용자 코드 스타일 유지)
    selected_row = selected_df.iloc[0]

    # '종목명' 사용 (원 코드와 동일). 필요하면 '종목코드'도 함께 저장하세요.
    stock_name = str(selected_row.get("종목명", "")).strip()
    if stock_name:
        st.session_state["selected_stock"] = stock_name

        st.success(f"✅ {stock_name} 차트 페이지로 이동 중...")
        try:
            st.switch_page("pages/stock_detail.py")
        except Exception:
            # 경로 인식 문제 시 대체 시도
            st.switch_page("stock_detail.py")

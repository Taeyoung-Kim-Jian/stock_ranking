# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from supabase import create_client
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
# (예: pages/한국 돌파 종목.py 파일)

# ----------------------------------------------
# 💡 1. components 폴더의 header 파일에서 함수를 import
from header import show_app_header
# ----------------------------------------------

import streamlit as st
import pandas as pd
# ... (다른 import 구문)
# (예: pages/한국 돌파 종목.py 파일)

# ... (import 구문)

# ----------------------------------------------
# 💡 2. 헤더 함수 호출 (페이지 상단에 표시됨)
show_app_header()

# ------------------------------------------------
# Supabase 연결
# ------------------------------------------------

# 환경 변수 또는 st.secrets에서 값 로드
SUPABASE_URL = os.environ.get("SUPABASE_URL") or st.secrets["SUPABASE_URL"]
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or st.secrets["SUPABASE_KEY"]

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Supabase 환경변수(SUPABASE_URL, SUPABASE_KEY)가 설정되지 않았습니다.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------------------------------
# 페이지 설정
# ------------------------------------------------
st.set_page_config(page_title="전체 종목 목록", layout="wide")

st.markdown("<h4 style='text-align:center;'>📋스윙 투자 종목의 전체 리스트</h4>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray; font-size:13px;'> 해당 종목을 선택하시면 차트로 이동합니다.</p>", unsafe_allow_html=True)
st.markdown("---")

# ------------------------------------------------
# 데이터 로딩 (종목코드를 포함하도록 수정)
# ------------------------------------------------
@st.cache_data(ttl=300)
def load_total_return():
    try:
        # 종목코드가 '종목코드'라는 컬럼명이라고 가정하고 쿼리에 추가
        # 실제 테이블의 종목코드 컬럼명에 맞게 수정해주세요. (예: 'ticker' 등)
        res = (
            supabase.table("total_return")
            .select("종목코드", "종목명, 시작가격, 현재가격, 수익률")
            .order("수익률", desc=True)
            .execute()
        )
        return pd.DataFrame(res.data)
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
gb.configure_grid_options(domLayout='normal')
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
)

# ------------------------------------------------
# 행 클릭 시 페이지 이동 (종목코드를 세션에 저장하도록 수정)
# ------------------------------------------------
selected = grid_response.get("selected_rows")

# `selected`가 리스트 형태이고, 요소가 딕셔너리 또는 유사 딕셔너리 구조를 가질 때 처리합니다.
# `AgGrid`의 `get("selected_rows")`는 일반적으로 리스트 또는 데이터프레임으로 반환됩니다.
if selected is not None and len(selected) > 0:
    # `selected`가 리스트라면 첫 번째 요소를 사용합니다.
    if isinstance(selected, list):
        selected_row_data = selected[0]
    # `selected`가 데이터프레임이라면 첫 번째 행을 사용합니다.
    elif isinstance(selected, pd.DataFrame):
        selected_row_data = selected.iloc[0]
    else:
        st.error("선택된 행 데이터를 처리할 수 없습니다.")
        st.stop()

    try:
        # 종목코드와 종목명을 추출합니다.
        stock_code = selected_row_data.get("종목코드")
        stock_name = selected_row_data.get("종목명")
        
        if stock_code and stock_name:
            # 종목코드와 종목명을 세션에 저장합니다. (상세 페이지에서 이 코드를 사용해 데이터를 조회)
            st.session_state["selected_stock_code"] = stock_code
            st.session_state["selected_stock_name"] = stock_name

            st.success(f"✅ {stock_name} ({stock_code}) 차트 페이지로 이동 중...")
            st.switch_page("pages/stock_detail.py")
        else:
            st.warning("⚠️ 선택된 행에서 종목코드 또는 종목명을 찾을 수 없습니다. (컬럼명 확인 필요)")

    except KeyError:
        st.error("❌ 선택된 행 데이터에 '종목코드' 또는 '종목명' 키가 존재하지 않습니다. Supabase 쿼리와 컬럼명을 다시 확인해주세요.")
    except Exception as e:
        st.error(f"❌ 페이지 이동 중 오류 발생: {e}")

# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from supabase import create_client
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# ------------------------------------------------
# 페이지 설정 (항상 최상단에서)
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
        # ✅ 종목코드도 반드시 가져오기
        res = (
            supabase.table("total_return")
            .select("종목명, 종목코드, 시작가격, 현재가격, 수익률")
            .order("수익률", desc=True)
            .execute()
        )
        df = pd.DataFrame(res.data)
        # 컬럼 존재 보장
        expected_cols = ["종목명", "종목코드", "시작가격", "현재가격", "수익률"]
        for c in expected_cols:
            if c not in df.columns:
                df[c] = None
        # 문자열 컬럼 정리
        df["종목명"] = df["종목명"].astype(str).str.strip()
        df["종목코드"] = df["종목코드"].astype(str).str.strip()
        return df[expected_cols]
    except Exception as e:
        st.error(f"❌ 데이터 불러오기 오류: {e}")
        return pd.DataFrame(columns=["종목명", "종목코드", "시작가격", "현재가격", "수익률"])

df = load_total_return()

if df.empty:
    st.warning("⚠️ Supabase total_return 테이블에서 데이터를 불러올 수 없습니다.")
    st.stop()

# ------------------------------------------------
# AgGrid 표시 설정
# ------------------------------------------------
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(resizable=True, sortable=True, filter=True)

# 단일 선택
gb.configure_selection(selection_mode="single", use_checkbox=False)

# 컬럼 표시/숨김 (종목코드는 내부 전달용이라 숨기는 걸 권장)
gb.configure_column("종목코드", hide=True)
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
    key="total_return_grid"  # 상태안정용 key
)

# ------------------------------------------------
# 행 클릭 시 페이지 이동
# ------------------------------------------------
selected = grid_response.get("selected_rows", [])

# selected_rows는 list[dict] 형태입니다.
if selected and isinstance(selected, list):
    row = selected[0]  # 첫 번째 선택 행
    stock_name = str(row.get("종목명", "")).strip()
    stock_code = str(row.get("종목코드", "")).strip()

    if not stock_code:
        st.warning("선택된 행에 종목코드가 없습니다. 테이블 select에 '종목코드' 컬럼이 포함되어야 합니다.")
    else:
        # 상세 페이지에서 기대하는 키 이름으로 저장 (필요에 맞게 조정)
        st.session_state["selected_stock_name"] = stock_name
        st.session_state["selected_stock_code"] = stock_code

        st.success(f"✅ {stock_name} ({stock_code}) 차트 페이지로 이동 중...")

        # Streamlit 1.29+ 형식. pages 폴더 내 파일 경로가 정확한지 확인해 주세요.
        # 예: 프로젝트 루트에 pages/stock_detail.py 가 있어야 합니다.
        try:
            st.switch_page("pages/stock_detail.py")
        except Exception:
            # 만약 경로 인식 문제 시 파일명만으로도 시도
            st.switch_page("stock_detail.py")

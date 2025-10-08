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
st.markdown("<p style='text-align:center; color:gray; font-size:13px;'>행을 클릭한 뒤 오른쪽 상단의 '차트 열기' 버튼을 누르세요.</p>", unsafe_allow_html=True)
st.markdown("---")

# ------------------------------------------------
# 데이터 로딩
# ------------------------------------------------
@st.cache_data(ttl=300)
def load_total_return():
    try:
        res = (
            supabase.table("total_return")
            .select("종목명, 종목코드, 시작가격, 현재가격, 수익률")
            .order("수익률", desc=True)
            .execute()
        )
        df = pd.DataFrame(res.data or [])
        # 누락 컬럼 방어
        expected_cols = ["종목명", "종목코드", "시작가격", "현재가격", "수익률"]
        for c in expected_cols:
            if c not in df.columns:
                df[c] = None

        # 타입/공백 정리
        df["종목명"] = df["종목명"].astype(str).str.strip()
        df["종목코드"] = df["종목코드"].astype(str).str.strip()
        for c in ["시작가격", "현재가격", "수익률"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")

        # 보기 좋은 정렬/포맷은 그리드에서
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
gb.configure_selection(selection_mode="single", use_checkbox=False)

# 내부 전달용: 종목코드는 숨김
gb.configure_column("종목코드", hide=True)

# 숫자 포맷 살짝
gb.configure_column("시작가격", type=["numericColumn"], valueFormatter="x.toLocaleString()")
gb.configure_column("현재가격", type=["numericColumn"], valueFormatter="x.toLocaleString()")
gb.configure_column("수익률", type=["numericColumn"], valueFormatter="(x!=null? x.toFixed(2)+'%':'' )")

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
    key="total_return_grid"
)

# ------------------------------------------------
# 행 선택 상태 읽기
# ------------------------------------------------
selected_rows = grid_response.get("selected_rows") or []
row = selected_rows[0] if isinstance(selected_rows, list) and len(selected_rows) > 0 else None

# 현재 선택 정보
stock_name = (row.get("종목명") if row else "") or ""
stock_code = (row.get("종목코드") if row else "") or ""
stock_name = str(stock_name).strip()
stock_code = str(stock_code).strip()

# ------------------------------------------------
# 상단 우측: 차트 열기 버튼 & 디버그 토글
# ------------------------------------------------
top_cols = st.columns([1, 1])

with top_cols[0]:
    if stock_code:
        st.info(f"선택됨: **{stock_name} ({stock_code})**")
    else:
        st.info("행을 하나 선택하세요.")

with top_cols[1]:
    # 디버그 토글
    debug = st.toggle("🔧 디버그 보기", value=False, help="선택값/쿼리파라미터를 확인합니다.")
    # 명시적으로 이동
    open_chart = st.button("📈 차트 열기", type="primary", use_container_width=True, disabled=not bool(stock_code))

# ------------------------------------------------
# 차트 페이지로 이동
# - 세션 상태와 URL 쿼리파라미터를 모두 세팅해서 안정성 ↑
# ------------------------------------------------
if open_chart and stock_code:
    # 1) 세션 상태
    st.session_state["selected_stock_name"] = stock_name
    st.session_state["selected_stock_code"] = stock_code

    # 2) URL 쿼리파라미터
    #   Streamlit 최신 API: st.query_params (구 experimental_set_query_params 대체)
    try:
        st.query_params.update({"code": stock_code, "name": stock_name})
    except Exception:
        # 구버전 호환
        try:
            st.experimental_set_query_params(code=stock_code, name=stock_name)
        except Exception:
            pass

    st.success(f"✅ {stock_name} ({stock_code}) 차트 페이지로 이동합니다...")
    try:
        st.switch_page("pages/stock_detail.py")
    except Exception:
        st.switch_page("stock_detail.py")

# ------------------------------------------------
# 디버그 정보
# ------------------------------------------------
if debug:
    st.write("**선택된 rows(raw)**:", selected_rows)
    st.write("**세션 상태 현재값**:", {
        "selected_stock_name": st.session_state.get("selected_stock_name"),
        "selected_stock_code": st.session_state.get("selected_stock_code"),
    })
    # 쿼리파라미터 표기 (읽기만)
    try:
        qp = st.query_params  # dict-like
    except Exception:
        qp = {}
    st.write("**현재 쿼리파라미터**:", dict(qp))

# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from supabase import create_client
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

# ------------------------------------------------
# 페이지 설정 (항상 최상단)
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
st.markdown(
    "<p style='text-align:center; color:gray; font-size:13px;'>행을 클릭하면 즉시 차트 페이지로 이동합니다.</p>",
    unsafe_allow_html=True
)
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
        expected = ["종목명", "종목코드", "시작가격", "현재가격", "수익률"]
        for c in expected:
            if c not in df.columns:
                df[c] = None

        # 타입/공백 정리
        df["종목명"] = df["종목명"].astype(str).str.strip()
        df["종목코드"] = df["종목코드"].astype(str).str.strip()
        for c in ["시작가격", "현재가격", "수익률"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")

        return df[expected]
    except Exception as e:
        st.error(f"❌ 데이터 불러오기 오류: {e}")
        return pd.DataFrame(columns=["종목명", "종목코드", "시작가격", "현재가격", "수익률"])

df = load_total_return()
if df.empty:
    st.warning("⚠️ Supabase total_return 테이블에서 데이터를 불러올 수 없습니다.")
    st.stop()

# ------------------------------------------------
# AgGrid 설정 (행 클릭 → 선택 강제)
# ------------------------------------------------
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(resizable=True, sortable=True, filter=True)

# 단일 선택 + 체크박스 없이도 클릭으로 선택
gb.configure_selection(selection_mode="single", use_checkbox=False)
gb.configure_column("종목코드", hide=True)

# 숫자 포맷
gb.configure_column("시작가격", type=["numericColumn"], valueFormatter="x!=null ? x.toLocaleString() : ''")
gb.configure_column("현재가격", type=["numericColumn"], valueFormatter="x!=null ? x.toLocaleString() : ''")
gb.configure_column("수익률", type=["numericColumn"], valueFormatter="x!=null ? x.toFixed(2) + '%' : ''")

# 클릭 시 해당 행만 선택되게 강제
on_row_clicked = JsCode("""
function(e) {
  try {
    e.api.deselectAll();
    e.node.setSelected(true);
  } catch (err) {
    // no-op
  }
}
""")

gb.configure_grid_options(
    domLayout="normal",
    rowSelection="single",
    rowMultiSelectWithClick=True,
    suppressRowClickSelection=False,
    suppressCellSelection=True,
    onRowClicked=on_row_clicked
)

grid_options = gb.build()

st.markdown("### 🔍 종목 목록")
grid_response = AgGrid(
    df,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.SELECTION_CHANGED,   # 선택 변경 시 반영
    theme="streamlit",
    fit_columns_on_grid_load=True,
    height=600,
    allow_unsafe_jscode=True,                       # JsCode 사용 필수
    key="total_return_grid"
)

# ------------------------------------------------
# 행 클릭(=선택) 처리: selected는 항상 정의해서 NameError 방지
# ------------------------------------------------
selected = grid_response.get("selected_rows") or []

if isinstance(selected, list) and len(selected) > 0:
    row = selected[0]
    stock_name = str(row.get("종목명", "")).strip()
    stock_code = str(row.get("종목코드", "")).strip()

    if not stock_code:
        st.warning("선택된 행에 '종목코드'가 없습니다. total_return 쿼리에 '종목코드'를 포함하세요.")
    else:
        # 1) 세션 상태
        st.session_state["selected_stock_name"] = stock_name
        st.session_state["selected_stock_code"] = stock_code

        # 2) URL 쿼리파라미터 (버전별 호환)
        try:
            st.query_params.update({"code": stock_code, "name": stock_name})
        except Exception:
            try:
                st.experimental_set_query_params(code=stock_code, name=stock_name)
            except Exception:
                pass

        st.success(f"✅ {stock_name} ({stock_code}) 차트 페이지로 이동 중...")
        # 파일 경로는 프로젝트 루트 기준. 실제 파일 위치에 맞추세요.
        try:
            st.switch_page("pages/stock_detail.py")
        except Exception:
            st.switch_page("stock_detail.py")

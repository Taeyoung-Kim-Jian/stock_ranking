# pages/전체 종목.py
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from supabase import create_client
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

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
st.markdown("<p style='text-align:center; color:gray; font-size:13px;'>행을 클릭하면 즉시 차트 페이지로 이동합니다.</p>", unsafe_allow_html=True)
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
        expected = ["종목명", "종목코드", "시작가격", "현재가격", "수익률"]
        for c in expected:
            if c not in df.columns:
                df[c] = None
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
# AgGrid 설정 (클릭 → 선택 강제)
# ------------------------------------------------
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(resizable=True, sortable=True, filter=True)
gb.configure_selection(selection_mode="single", use_checkbox=False)
gb.configure_column("종목코드", hide=True)
gb.configure_column("시작가격", type=["numericColumn"], valueFormatter="x!=null? x.toLocaleString():''")
gb.configure_column("현재가격", type=["numericColumn"], valueFormatter="x!=null? x.toLocaleString():''")
gb.configure_column("수익률", type=["numericColumn"], valueFormatter="x!=null? x.toFixed(2)+'%':''")

on_row_clicked = JsCode("""
function(e) {
  try { e.api.deselectAll(); e.node.setSelected(true); } catch (err) {}
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
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    theme="streamlit",
    fit_columns_on_grid_load=True,
    height=600,
    allow_unsafe_jscode=True,
    key="total_return_grid"
)

# ------------------------------------------------
# selected_rows 안전 추출 (DataFrame/List/None 모두 처리)
# ------------------------------------------------
def get_selected_rows_safe(gr):
    if not isinstance(gr, dict):
        return []
    # get의 두 번째 인자를 쓰고, 진리값 평가 금지
    sel = gr.get("selected_rows", None)
    if sel is None:
        return []
    if isinstance(sel, list):
        return sel
    if isinstance(sel, pd.DataFrame):
        # st_aggrid 버전에 따라 DataFrame으로 오는 경우 방지
        return sel.to_dict(orient="records")
    # 예기치 타입 방어
    return []

selected = get_selected_rows_safe(grid_response)

# ------------------------------------------------
# 선택되면 이동
# ------------------------------------------------
   # ✅ 타입별 안전 처리
        if selected is not None:
            if isinstance(selected, pd.DataFrame):
                selected = selected.to_dict("records")

            if isinstance(selected, list) and len(selected) > 0:
                selected_row = selected[0]
                stock_name = selected_row.get("종목명")
                stock_code = selected_row.get("종목코드")

                if not stock_code:
                    st.warning("⚠️ 종목코드가 없습니다. 테이블 구조를 확인하세요.")
                    st.stop()

                # 세션 저장 후 바로 페이지 이동
                st.session_state["selected_stock_name"] = stock_name
                st.session_state["selected_stock_code"] = stock_code
                st.switch_page("pages/stock_detail.py")


st.markdown("---")
st.caption("💡 행을 클릭하면 해당 종목의 차트 페이지로 이동합니다.")

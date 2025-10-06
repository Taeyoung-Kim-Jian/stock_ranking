# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from supabase import create_client
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

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
# 페이지 설정
# ------------------------------------------------
st.set_page_config(page_title="📆 월별 성과", layout="wide")

st.markdown("<h4 style='text-align:center;'>📆 월별 성과</h4>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray; font-size:13px;'>행을 클릭하면 해당 종목의 차트 페이지로 이동합니다.</p>", unsafe_allow_html=True)
st.markdown("---")

# ------------------------------------------------
# 데이터 로딩
# ------------------------------------------------
@st.cache_data(ttl=300)
def load_monthly_tracking():
    try:
        res = (
            supabase.table("b_zone_monthly_tracking")
            .select("종목명, 종목코드, b가격, 측정일, 측정일종가, 현재가, 측정일대비수익률, 최고수익률, 최저수익률, 월구분")
            .order("월구분", desc=True)
            .execute()
        )
        return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"❌ 데이터 불러오기 오류: {e}")
        return pd.DataFrame()

df = load_monthly_tracking()

if df.empty:
    st.warning("⚠️ b_zone_monthly_tracking 테이블에 데이터가 없습니다.")
    st.stop()

# ------------------------------------------------
# 월 포맷 정리
# ------------------------------------------------
df["월포맷"] = pd.to_datetime(df["월구분"], errors="coerce").dt.strftime("%y.%m")
df = df[df["월포맷"].notna()]

# ------------------------------------------------
# 월별 탭 생성
# ------------------------------------------------
months = sorted(df["월포맷"].unique(), reverse=True)
tabs = st.tabs(months)

for i, month in enumerate(months):
    with tabs[i]:
        st.subheader(f"📅 {month}월 성과")
        df_month = df[df["월포맷"] == month].copy()
        df_month = df_month.sort_values("측정일대비수익률", ascending=False)

        display_cols = [
            "종목명", "종목코드", "b가격", "측정일", "측정일종가",
            "현재가", "측정일대비수익률", "최고수익률", "최저수익률"
        ]

        # ------------------------------------------------
        # AgGrid 설정
        # ------------------------------------------------
        gb = GridOptionsBuilder.from_dataframe(df_month[display_cols])
        gb.configure_default_column(resizable=True, sortable=True, filter=True)
        gb.configure_selection(selection_mode="single", use_checkbox=False)
        gb.configure_grid_options(domLayout='normal')
        grid_options = gb.build()

        grid_response = AgGrid(
            df_month[display_cols],
            gridOptions=grid_options,
            enable_enterprise_modules=False,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            theme="streamlit",
            fit_columns_on_grid_load=True,
            height=550,
        )

        selected = grid_response.get("selected_rows")

        # ------------------------------------------------
        # 클릭 시 차트 페이지로 이동
        # ------------------------------------------------
        iselected = grid_response.get("selected_rows")

if selected is not None and len(selected) > 0:
    # Streamlit Cloud 호환 (DataFrame/list 모두 지원)
    if isinstance(selected, pd.DataFrame):
        selected_row = selected.iloc[0].to_dict()
    elif isinstance(selected, list):
        selected_row = selected[0]
    else:
        st.warning("⚠️ 선택된 행 데이터를 인식할 수 없습니다.")
        st.stop()

    stock_name = selected_row.get("종목명")
    stock_code = selected_row.get("종목코드")

    if not stock_code:
        st.warning("⚠️ 종목코드가 없습니다. 테이블 구조를 확인하세요.")
        st.stop()

    # ✅ 세션 값 저장
    st.session_state["selected_stock_name"] = stock_name
    st.session_state["selected_stock_code"] = stock_code

    st.success(f"✅ {stock_name} ({stock_code}) 차트 페이지로 이동 중...")

    # ✅ rerun을 한 번 강제해서 세션이 완전히 반영되도록 함
    st.session_state["go_to_detail"] = True
    st.experimental_rerun()

# ✅ rerun 후 이 부분 실행 (세션 데이터가 안정적으로 존재)
if st.session_state.get("go_to_detail"):
    st.session_state.pop("go_to_detail")  # 플래그 제거
    st.switch_page("pages/stock_detail.py")

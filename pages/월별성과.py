# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from supabase import create_client
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# ------------------------------------------------
# 페이지 설정
# ------------------------------------------------
st.set_page_config(page_title="📆 월별 성과", layout="wide")

st.markdown("<h4 style='text-align:center;'>📈 월별 성과</h4>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray; font-size:13px;'>측정일 종가 대비 현재가의 수익률을 기준으로 한 월별 성과 데이터입니다.</p>", unsafe_allow_html=True)
st.markdown("---")

# ------------------------------------------------
# Supabase 연결
# ------------------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Supabase 환경변수가 설정되지 않았습니다.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------------------------------
# 데이터 로드
# ------------------------------------------------
@st.cache_data(ttl=600)
def load_monthly_data():
    try:
        res = supabase.table("b_zone_monthly_tracking").select("*").order("월구분", desc=True).execute()
        df = pd.DataFrame(res.data)

        if df.empty:
            return df

        # ✅ 월 구분
        df["월포맷"] = pd.to_datetime(df["월구분"], errors="coerce").dt.strftime("%y.%m")
        df = df[df["월포맷"].notna()]

        # ✅ NaN 처리 및 수익률 재계산
        df = df.fillna(0)
        df["측정일대비수익률"] = ((df["현재가"] - df["측정일종가"]) / df["측정일종가"] * 100).round(2)

        # ✅ 컬럼 정리
        display_cols = [
            "종목명", "종목코드", "b가격", "측정일", "측정일종가",
            "현재가", "측정일대비수익률", "최고수익률", "최저수익률", "월포맷"
        ]
        df = df[[col for col in display_cols if col in df.columns]]
        return df

    except Exception as e:
        st.error(f"❌ Supabase 데이터 로드 중 오류: {e}")
        return pd.DataFrame()

# ------------------------------------------------
# 데이터 불러오기
# ------------------------------------------------
with st.spinner("📊 월별 성과 데이터를 불러오는 중..."):
    df = load_monthly_data()

if df.empty:
    st.warning("📭 월별 성과 데이터가 없습니다.")
    st.stop()

st.success(f"✅ 총 {len(df)}건의 데이터 불러옴")

# ------------------------------------------------
# 월별 탭 표시
# ------------------------------------------------
months = sorted(df["월포맷"].unique(), reverse=True)
tabs = st.tabs(months)

for i, month in enumerate(months):
    with tabs[i]:
        st.subheader(f"📅 {month}월 성과")

        df_month = df[df["월포맷"] == month].copy()
        df_month = df_month.sort_values("측정일대비수익률", ascending=False)

        # ------------------------------------------------
        # AgGrid 설정
        # ------------------------------------------------
        display_cols = [
            "종목명", "종목코드", "b가격", "측정일", "측정일종가",
            "현재가", "측정일대비수익률", "최고수익률", "최저수익률"
        ]

        gb = GridOptionsBuilder.from_dataframe(df_month[display_cols])
        gb.configure_default_column(resizable=True, sortable=True, filter=True)
        gb.configure_selection(selection_mode="single", use_checkbox=False)
        grid_options = gb.build()

        grid_response = AgGrid(
            df_month[display_cols],
            gridOptions=grid_options,
            enable_enterprise_modules=False,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            theme="streamlit",
            fit_columns_on_grid_load=True,
            height=500,
        )

        selected = grid_response.get("selected_rows")

        # ------------------------------------------------
        # 클릭 시 차트 페이지로 이동
        # ------------------------------------------------
        if selected:
            selected_row = selected[0]
            stock_name = selected_row["종목명"]
            stock_code = selected_row["종목코드"]

            st.session_state["selected_stock_name"] = stock_name
            st.session_state["selected_stock_code"] = stock_code

            st.success(f"✅ {stock_name} ({stock_code}) 차트 페이지로 이동 중...")
            st.switch_page("pages/stock_detail.py")

st.markdown("---")
st.caption("💡 행을 클릭하면 해당 종목의 차트 페이지로 이동합니다.")

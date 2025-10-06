# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from supabase import create_client
from st_aggrid import AgGrid, GridOptionsBuilder

# ------------------------------------------------
# 페이지 설정
# ------------------------------------------------
st.set_page_config(page_title="📆 월별 성과", layout="wide")

st.markdown("<h4 style='text-align:center;'>📈 월별 성과</h4>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray; font-size:13px;'>b가격 ±5% 내에서 측정된 종목들의 월별 성과 데이터입니다.</p>", unsafe_allow_html=True)
st.markdown("---")

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
# 데이터 로드 함수
# ------------------------------------------------
@st.cache_data(ttl=600)
def load_monthly_data():
    try:
        res = supabase.table("b_zone_monthly_tracking").select("*").order("월구분", desc=True).execute()
        df = pd.DataFrame(res.data)
        if df.empty:
            return df
        df["월포맷"] = pd.to_datetime(df["월구분"]).dt.strftime("%y.%m")
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

        # NaN, Decimal, Timestamp 변환 처리
        df_month = df_month.fillna("")
        for col in df_month.columns:
            # 날짜형 → 문자열
            if "날짜" in col or col == "월구분":
                df_month[col] = df_month[col].astype(str)
            # 숫자형 변환
            elif "수익률" in col or col in ["b가격", "현재가", "측정일종가"]:
                df_month[col] = pd.to_numeric(df_month[col], errors="coerce").fillna(0).astype(float)

        # 표시 컬럼 선택
        display_cols = [
            "종목명", "b가격", "측정일", "측정일종가", "현재가",
            "현재가대비수익률", "최고수익률", "최저수익률"
        ]
        df_display = df_month[display_cols].copy()

        # AgGrid 설정
        gb = GridOptionsBuilder.from_dataframe(df_display)
        gb.configure_default_column(resizable=True, sortable=True, filter=True)
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_column("현재가대비수익률", cellStyle=lambda x: {
            "backgroundColor": "#c7f5d9" if x["value"] > 0 else "#f7c7c7"
        })
        grid_options = gb.build()

        # AgGrid 렌더링
        AgGrid(
            df_display,
            gridOptions=grid_options,
            height=550,
            theme="balham",
            fit_columns_on_grid_load=True,
        )

st.markdown("---")
st.caption("💡 본 데이터는 Supabase `b_zone_monthly_tracking` 테이블 기준으로 표시됩니다.")

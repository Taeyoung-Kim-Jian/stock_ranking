# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from supabase import create_client
from st_aggrid import AgGrid, GridOptionsBuilder

st.set_page_config(page_title="📆 월별 성과", layout="wide")

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
# 데이터 로드
# ------------------------------------------------
@st.cache_data(ttl=600)
def load_monthly_data():
    res = supabase.table("b_zone_monthly_tracking").select("*").order("월구분", desc=True).execute()
    df = pd.DataFrame(res.data)
    if df.empty:
        return df
    df["월포맷"] = pd.to_datetime(df["월구분"]).dt.strftime("%y.%m")
    return df

df = load_monthly_data()
if df.empty:
    st.warning("📭 월별 성과 데이터가 없습니다.")
    st.stop()

st.success(f"✅ 총 {len(df)}건의 월별 데이터 로드 완료")

# ------------------------------------------------
# 월별 탭
# ------------------------------------------------
months = sorted(df["월포맷"].unique(), reverse=True)
tabs = st.tabs(months)

for i, month in enumerate(months):
    with tabs[i]:
        st.subheader(f"📅 {month}월 성과")
        df_month = df[df["월포맷"] == month].copy()

        df_month = df_month[
            ["종목명", "b가격", "측정일", "측정일종가", "현재가",
             "현재가대비수익률", "최고수익률", "최저수익률"]
        ]

        gb = GridOptionsBuilder.from_dataframe(df_month)
        gb.configure_default_column(resizable=True, sortable=True)
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_column("현재가대비수익률", cellStyle=lambda x: {
            "backgroundColor": "#c7f5d9" if x["value"] > 0 else "#f7c7c7"
        })
        grid_options = gb.build()

        AgGrid(df_month, gridOptions=grid_options, height=550, theme="balham", fit_columns_on_grid_load=True)

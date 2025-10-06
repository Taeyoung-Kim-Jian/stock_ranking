# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="📆 월별 성과", layout="wide")

# =====================================================
# 1️⃣ Supabase 연결
# =====================================================
@st.cache_resource
def init_connection():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = init_connection()

# =====================================================
# 2️⃣ 데이터 불러오기
# =====================================================
@st.cache_data(ttl=600)
def load_monthly_performance():
    data = supabase.table("b_zone_monthly_tracking").select("*").execute()
    df = pd.DataFrame(data.data)
    if not df.empty:
        df["월포맷"] = pd.to_datetime(df["월구분"]).dt.strftime("%y.%m")
    return df

df = load_monthly_performance()

if df.empty:
    st.warning("📭 월별 성과 데이터가 없습니다.")
    st.stop()

# =====================================================
# 3️⃣ 월별 탭 인터페이스
# =====================================================
months = sorted(df["월포맷"].unique(), reverse=True)
tabs = st.tabs(months)

for i, month in enumerate(months):
    with tabs[i]:
        st.subheader(f"📅 {month}월 성과")
        df_month = df[df["월포맷"] == month].copy()

        # 수익률 컬럼 포맷
        df_month = df_month[
            [
                "종목명", "b가격", "측정일", "측정일종가",
                "현재가", "현재가대비수익률",
                "최고수익률", "최저수익률"
            ]
        ]
        df_month["현재가대비수익률"] = df_month["현재가대비수익률"].astype(float).round(2)
        df_month["최고수익률"] = df_month["최고수익률"].astype(float).round(2)
        df_month["최저수익률"] = df_month["최저수익률"].astype(float).round(2)

        st.dataframe(df_month, use_container_width=True)

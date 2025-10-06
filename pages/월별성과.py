# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from supabase import create_client

st.set_page_config(page_title="📆 월별 성과", layout="wide")

# =====================================================
# 1️⃣ Supabase 연결
# =====================================================
SUPABASE_URL = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Supabase 환경변수(SUPABASE_URL, SUPABASE_KEY)가 설정되지 않았습니다.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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

# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from supabase import create_client
import matplotlib.pyplot as plt

st.set_page_config(page_title="📆 월별 성과", layout="wide")

# ------------------------------------------------
# Supabase 연결
# ------------------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")

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

st.success(f"✅ 총 {len(df)}건의 데이터 불러옴")

# ------------------------------------------------
# 월별 평균 수익률 차트
# ------------------------------------------------
avg_df = df.groupby("월포맷")["현재가대비수익률"].mean().reset_index()
fig, ax = plt.subplots(figsize=(8, 3))
ax.bar(avg_df["월포맷"], avg_df["현재가대비수익률"], color="skyblue")
ax.set_title("📊 월별 평균 수익률")
ax.set_ylabel("평균 수익률 (%)")
for i, v in enumerate(avg_df["현재가대비수익률"]):
    ax.text(i, v + 0.2, f"{v:.1f}%", ha="center", fontsize=9)
st.pyplot(fig)

# ------------------------------------------------
# ✅ 월별 탭 (완벽히 동작)
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
        # 수익률 정렬
        df_month = df_month.sort_values("현재가대비수익률", ascending=False)

        # 기본 테이블 렌더링 (Cloud 완전 호환)
        st.dataframe(
            df_month.style.format({
                "b가격": "{:,.0f}",
                "측정일종가": "{:,.0f}",
                "현재가": "{:,.0f}",
                "현재가대비수익률": "{:.2f}%",
                "최고수익률": "{:.2f}%",
                "최저수익률": "{:.2f}%"
            })
        )

st.markdown("---")
st.caption("💡 AgGrid 대신 기본 Streamlit 테이블을 사용하여 Cloud 환경에서도 안정적으로 동작합니다.")

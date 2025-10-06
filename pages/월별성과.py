# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from supabase import create_client
import matplotlib.pyplot as plt

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
    st.error("❌ Supabase 환경변수(SUPABASE_URL, SUPABASE_KEY)가 설정되지 않았습니다.")
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

        # 월 포맷 추가
        df["월포맷"] = pd.to_datetime(df["월구분"]).dt.strftime("%y.%m")

        # NaN 제거
        df = df.fillna(0)

        # ✅ 측정일대비수익률 재계산 (측정일 종가 대비 현재가)
        df["측정일대비수익률"] = ((df["현재가"] - df["측정일종가"]) / df["측정일종가"] * 100).round(2)
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
# 월별 평균 수익률 시각화
# ------------------------------------------------
try:
    avg_df = (
        df.groupby("월포맷")["측정일대비수익률"]
        .mean()
        .reset_index()
        .sort_values("월포맷", ascending=True)
    )

    fig, ax = plt.subplots(figsize=(8, 3))
    ax.bar(avg_df["월포맷"], avg_df["측정일대비수익률"], color="skyblue")
    ax.set_title("📊 월별 평균 수익률", fontsize=13)
    ax.set_ylabel("평균 수익률 (%)")
    ax.set_xlabel("월")
    for i, v in enumerate(avg_df["측정일대비수익률"]):
        ax.text(i, v + 0.2, f"{v:.1f}%", ha="center", fontsize=9)
    st.pyplot(fig)
except Exception as e:
    st.warning(f"⚠️ 월별 평균 수익률 그래프 생성 중 오류: {e}")

# ------------------------------------------------
# 월별 탭
# ------------------------------------------------
months = sorted(df["월포맷"].unique(), reverse=True)
tabs = st.tabs(months)

for i, month in enumerate(months):
    with tabs[i]:
        st.subheader(f"📅 {month}월 성과")
        df_month = df[df["월포맷"] == month].copy()

        # 정렬: 수익률 높은 순
        df_month = df_month.sort_values("측정일대비수익률", ascending=False)

        display_cols = [
            "종목명", "b가격", "측정일", "측정일종가", "현재가",
            "측정일대비수익률", "최고수익률", "최저수익률"
        ]

        # 숫자 포맷 적용
        st.dataframe(
            df_month[display_cols].style.format({
                "b가격": "{:,.0f}",
                "측정일종가": "{:,.0f}",
                "현재가": "{:,.0f}",
                "측정일대비수익률": "{:.2f}%",
                "최고수익률": "{:.2f}%",
                "최저수익률": "{:.2f}%"
            })
        )

st.markdown("---")
st.caption("💡 수익률은 측정일 종가 대비 현재가 기준으로 계산됩니다.")

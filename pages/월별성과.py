# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from supabase import create_client

st.set_page_config(page_title="📆 월별 성과", layout="wide")

# ======================================
# 1️⃣ Supabase 연결
# ======================================
SUPABASE_URL = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Supabase 환경변수(SUPABASE_URL, SUPABASE_KEY)가 설정되지 않았습니다.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ======================================
# 2️⃣ 데이터 불러오기
# ======================================
@st.cache_data(ttl=600)
def load_data():
    prices_data = supabase.table("prices").select("*").execute().data
    bt_data = supabase.table("bt_points").select("*").execute().data

    if not prices_data or not bt_data:
        return None, None

    prices = pd.DataFrame(prices_data)
    bt_points = pd.DataFrame(bt_data)
    prices["날짜"] = pd.to_datetime(prices["날짜"])
    bt_points["b날짜"] = pd.to_datetime(bt_points["b날짜"])
    return prices, bt_points

prices, bt_points = load_data()

if prices is None or bt_points is None:
    st.warning("❌ Supabase에 prices 또는 bt_points 데이터가 없습니다.")
    st.stop()

# ======================================
# 3️⃣ 계산 함수
# ======================================
def calculate_b_zone(prices, bt_points):
    results = []
    today = prices["날짜"].max()

    for _, b in bt_points.iterrows():
        code = b["종목코드"]
        b_price = float(b["b가격"])
        b_date = b["b날짜"]
        name = b.get("종목명", "")

        df_p = prices[prices["종목코드"] == code].copy()
        df_p = df_p[df_p["날짜"] >= pd.Timestamp("2025-01-28")]
        if df_p.empty:
            continue

        # 현재가: 오늘 데이터 없으면 가장 가까운 날짜 사용
        df_p["일차"] = abs((df_p["날짜"] - today).dt.days)
        current_row = df_p.loc[df_p["일차"].idxmin()]
        current_price = current_row["종가"]
        current_date = current_row["날짜"]

        # ±5% 범위 구간
        mask = (df_p["종가"] >= b_price * 0.95) & (df_p["종가"] <= b_price * 1.05)
        df_range = df_p[mask]
        if df_range.empty:
            continue

        for _, row in df_range.iterrows():
            measure_date = row["날짜"]
            measure_price = row["종가"]

            # 이후 구간
            future = df_p[df_p["날짜"] >= measure_date]
            max_price = future["종가"].max()
            min_price = future["종가"].min()

            results.append({
                "종목코드": code,
                "종목명": name,
                "b가격": b_price,
                "b날짜": b_date.date(),
                "측정일": measure_date.date(),
                "측정일종가": measure_price,
                "현재가일자": current_date.date(),
                "현재가": current_price,
                "현재가대비수익률": round((current_price - b_price) / b_price * 100, 2),
                "이후최고가": max_price,
                "이후최저가": min_price,
                "최고수익률": round((max_price - b_price) / b_price * 100, 2),
                "최저수익률": round((min_price - b_price) / b_price * 100, 2),
                "월구분": pd.to_datetime(measure_date).to_period("M").to_timestamp(),
            })

    df = pd.DataFrame(results)
    if not df.empty:
        df["월포맷"] = df["월구분"].dt.strftime("%y.%m")
    return df

# ======================================
# 4️⃣ 계산 실행
# ======================================
with st.spinner("데이터 계산 중..."):
    df = calculate_b_zone(prices, bt_points)

if df.empty:
    st.warning("📭 월별 성과 데이터가 없습니다.")
    st.stop()

# ======================================
# 5️⃣ 탭으로 월별 성과 표시
# ======================================
months = sorted(df["월포맷"].unique(), reverse=True)
tabs = st.tabs(months)

for i, month in enumerate(months):
    with tabs[i]:
        st.subheader(f"📅 {month}월 성과")
        df_month = df[df["월포맷"] == month].copy()

        df_month = df_month[
            [
                "종목명", "b가격", "측정일", "측정일종가",
                "현재가", "현재가대비수익률",
                "최고수익률", "최저수익률"
            ]
        ]

        # 수익률 포맷 및 색상
        def highlight(val):
            if pd.isna(val):
                return ""
            color = "lightgreen" if val > 0 else "#ffb3b3"
            return f"background-color:{color}"

        styled = (
            df_month.style
            .format({"현재가대비수익률": "{:.2f}%", "최고수익률": "{:.2f}%", "최저수익률": "{:.2f}%"})
            .applymap(highlight, subset=["현재가대비수익률"])
        )
        st.dataframe(styled, use_container_width=True)

# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from supabase import create_client
import altair as alt
from datetime import timedelta

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
# 페이지 설정
# ------------------------------------------------
st.set_page_config(page_title="종목 상세 차트", layout="wide")

# ------------------------------------------------
# 선택된 종목 확인
# ------------------------------------------------
if "selected_stock_code" not in st.session_state or "selected_stock_name" not in st.session_state:
    st.warning("⚠️ 종목이 선택되지 않았습니다. 메인 페이지로 이동합니다...")
    st.switch_page("스윙 종목.py")

stock_name = st.session_state["selected_stock_name"]
stock_code = st.session_state["selected_stock_code"]

st.markdown(f"<h4 style='text-align:center;'>📈 {stock_name} ({stock_code}) 주가 차트</h4>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray; font-size:13px;'>b가격 표시 모드 / 기간 선택 / 댓글 시스템</p>", unsafe_allow_html=True)
st.markdown("---")

# ------------------------------------------------
# 데이터 로드
# ------------------------------------------------
@st.cache_data(ttl=300)
def load_price_data(code):
    try:
        all_data, start, step = [], 0, 1000
        while True:
            res = (
                supabase.table("prices")
                .select("날짜, 종가")
                .eq("종목코드", code)
                .order("날짜", desc=False)
                .range(start, start + step - 1)
                .execute()
            )
            chunk = res.data
            if not chunk:
                break
            all_data.extend(chunk)
            if len(chunk) < step:
                break
            start += step

        df = pd.DataFrame(all_data)
        if not df.empty:
            df["날짜"] = pd.to_datetime(df["날짜"])
            df = df.sort_values("날짜")
        return df
    except Exception as e:
        st.error(f"❌ 가격 데이터 로딩 오류: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_b_prices(code):
    try:
        res = supabase.table("bt_points").select("b가격").eq("종목코드", code).execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            df["b가격"] = df["b가격"].astype(float)
            df = df.sort_values("b가격")
        return df
    except Exception as e:
        st.error(f"❌ b가격 데이터 로딩 오류: {e}")
        return pd.DataFrame()


df_price = load_price_data(stock_code)
df_b = load_b_prices(stock_code)

# ------------------------------------------------
# 기간 선택
# ------------------------------------------------
st.subheader("⏳ 차트 기간 선택")
period = st.radio("보기 기간 선택", ("1년", "2년", "3년", "전체"), horizontal=True)

if not df_price.empty:
    latest_date = df_price["날짜"].max()
    if period != "전체":
        years = int(period.replace("년", ""))
        start_date = latest_date - timedelta(days=365 * years)
        df_price = df_price[df_price["날짜"] >= start_date]

# ------------------------------------------------
# b가격 표시 옵션
# ------------------------------------------------
col1, col2 = st.columns([1, 3])
with col1:
    show_b = st.toggle("📊 b가격 표시", value=True)
with col2:
    mode = st.radio(
        "b가격 표시 모드 선택",
        ("가까운 1개", "가까운 3개", "전체"),
        horizontal=True,
        disabled=not show_b
    )

# ------------------------------------------------
# 차트 표시
# ------------------------------------------------
if df_price.empty:
    st.warning("⚠️ 가격 데이터 없음")
else:
    current_price = df_price["종가"].iloc[-1]
    y_min, y_max = df_price["종가"].min(), df_price["종가"].max()

    base_chart = (
        alt.Chart(df_price)
        .mark_line(color="#f9a825")
        .encode(
            x=alt.X("날짜:T", title="날짜"),
            y=alt.Y("종가:Q", title="종가 (₩)"),
            tooltip=["날짜", "종가"]
        )
    )

    if show_b and not df_b.empty:
        # ✅ 현재 표시된 구간(y_min~y_max) 내의 b가격만 필터링
        visible_b_all = df_b[(df_b["b가격"] >= y_min) & (df_b["b가격"] <= y_max)].copy()

        if not visible_b_all.empty:
            # 현재가 기준으로 가까운 순 정렬
            visible_b_all["diff"] = (visible_b_all["b가격"] - current_price).abs()
            visible_b_all = visible_b_all.sort_values("diff").reset_index(drop=True)

            if mode == "가까운 1개":
                visible_b = visible_b_all.head(1)

            elif mode == "가까운 3개":
                # ✅ 현재 기간 내에서 가까운 3개
                nearest_idx = visible_b_all["diff"].idxmin()
                start_idx = max(0, nearest_idx - 1)
                end_idx = min(len(visible_b_all), nearest_idx + 3)
                visible_b = visible_b_all.iloc[start_idx:end_idx]

            else:  # 전체
                visible_b = visible_b_all.copy()
        else:
            visible_b = pd.DataFrame()

        # ------------------------------------------------
        # 시각화
        # ------------------------------------------------
        if not visible_b.empty:
            rules = alt.Chart(visible_b).mark_rule(color="gray").encode(y="b가격:Q")

            texts = (
                alt.Chart(visible_b)
                .mark_text(
                    align="left",
                    baseline="middle",
                    dx=-250,
                    color="gray",
                    fontSize=11,
                    fontWeight="bold"
                )
                .encode(
                    y="b가격:Q",
                    text=alt.Text("b가격:Q", format=".0f")
                )
            )

            chart = (base_chart + rules + texts).properties(width="container", height=400)
        else:
            chart = base_chart.properties(width="container", height=400)
    else:
        chart = base_chart.properties(width="container", height=400)

    st.altair_chart(chart, use_container_width=True)

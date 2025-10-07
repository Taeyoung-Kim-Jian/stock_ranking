# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from supabase import create_client
import altair as alt

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
st.set_page_config(page_title="종목 상세 차트", layout="wide")

# ------------------------------------------------
# 선택된 종목 확인
# ------------------------------------------------
if "selected_stock" not in st.session_state:
    st.warning("⚠️ 종목이 선택되지 않았습니다. '전체 종목' 페이지에서 선택하세요.")
    st.stop()

stock_name = st.session_state["selected_stock"]

st.markdown(f"<h4 style='text-align:center;'>📈 {stock_name} 주가 차트</h4>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray; font-size:13px;'>Supabase에서 불러온 가격 데이터 기반</p>", unsafe_allow_html=True)
st.markdown("---")

# ------------------------------------------------
# 데이터 로드
# ------------------------------------------------
@st.cache_data(ttl=300)
def load_price_data(name):
    """
    Supabase의 prices 테이블에서 특정 종목의 일자별 가격 데이터 조회
    (날짜, 종가, 거래량 등 컬럼이 있다고 가정)
    """
    try:
        res = (
            supabase.table("prices")
            .select("날짜, 종가")
            .eq("종목명", name)
            .order("날짜", desc=False)
            .limit(5000)  # ✅ 최대 5000일 데이터 불러오기
            .execute()
        )
        df = pd.DataFrame(res.data)
        if not df.empty:
            df["날짜"] = pd.to_datetime(df["날짜"])
            df = df.sort_values("날짜")
        return df
    except Exception as e:
        st.error(f"❌ 가격 데이터 로딩 오류: {e}")
        return pd.DataFrame()

df_price = load_price_data(stock_name)

# ------------------------------------------------
# 차트 표시
# ------------------------------------------------
if df_price.empty:
    st.warning("⚠️ 해당 종목의 가격 데이터를 찾을 수 없습니다.")
else:
    line_chart = (
        alt.Chart(df_price)
        .mark_line(color="#f9a825", interpolate="monotone")
        .encode(
            x=alt.X("날짜:T", title="날짜"),
            y=alt.Y("종가:Q", title="종가 (₩)"),
            tooltip=["날짜", "종가"]
        )
        .properties(width="container", height=400)
    )

    st.altair_chart(line_chart, use_container_width=True)

# ------------------------------------------------
# 뒤로가기 버튼
# ------------------------------------------------
if st.button("⬅️ 전체 종목으로 돌아가기"):
    st.switch_page("pages/전체 종목.py")

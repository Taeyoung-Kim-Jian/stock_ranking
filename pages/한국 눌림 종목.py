# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from supabase import create_client

# ------------------------------------------------
# Supabase 연결 (Render + Streamlit Cloud 겸용)
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
st.set_page_config(page_title="b_return 수익률 테이블", layout="wide")

st.markdown("<h4 style='text-align:center;'>📊 b_return 테이블 (수익률 순)</h4>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-size:13px; color:gray;'>Supabase에서 불러온 데이터를 수익률 순으로 정렬하고 시각화합니다.</p>", unsafe_allow_html=True)
st.markdown("---")

# ------------------------------------------------
# 데이터 로딩
# ------------------------------------------------
@st.cache_data(ttl=300)
def load_b_return():
    query = (
        supabase.table("b_return")
        .select("종목명, 종목코드, 수익률, 발생일, 구분")
        .order("수익률", desc=True)
        .limit(1000)
    )
    res = query.execute()
    return pd.DataFrame(res.data)

df = load_b_return()

if df.empty:
    st.warning("⚠️ b_return 테이블에 데이터가 없습니다.")
    st.stop()

# ------------------------------------------------
# 데이터 전처리
# ------------------------------------------------
df["수익률"] = df["수익률"].astype(float)
df_sorted = df.sort_values("수익률", ascending=False).reset_index(drop=True)

# ------------------------------------------------
# 수익률 시각화 (막대 컬러 스타일)
# ------------------------------------------------
def style_table(df):
    styled = (
        df.style
        .bar(subset=["수익률"], color=["#ffb74d", "#81c784"], align="mid")
        .format({"수익률": "{:.2f}%"})
        .set_table_styles(
            [
                {"selector": "th", "props": "text-align: center; background-color: #f8f9fa;"},
                {"selector": "td", "props": "text-align: center;"},
            ]
        )
    )
    return styled

# ------------------------------------------------
# 표 표시
# ------------------------------------------------
st.dataframe(
    df_sorted,
    use_container_width=True,
    hide_index=True
)

st.markdown("### 🎨 수익률 시각화 보기")
st.dataframe(
    style_table(df_sorted),
    use_container_width=True,
    hide_index=True
)

# ------------------------------------------------
# 하단 안내
# ------------------------------------------------
st.markdown("---")
st.caption("💡 상단 표는 원시 데이터, 하단 표는 수익률 컬러 막대 시각화입니다. (5분 캐시)")

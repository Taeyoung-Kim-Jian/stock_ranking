# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from supabase import create_client

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
st.set_page_config(page_title="전체 종목 목록", layout="wide")

st.markdown("<h4 style='text-align:center;'>📋 전체 종목 리스트</h4>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray; font-size:13px;'>행을 클릭하면 상세 차트 페이지로 이동합니다.</p>", unsafe_allow_html=True)
st.markdown("---")

# ------------------------------------------------
# 데이터 로딩
# ------------------------------------------------
@st.cache_data(ttl=300)
def load_total_return():
    try:
        res = (
            supabase.table("total_return")
            .select("*")
            .order("수익률", desc=True)
            .execute()
        )
        return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"❌ 데이터 불러오기 오류: {e}")
        return pd.DataFrame()

df = load_total_return()

if df.empty:
    st.warning("⚠️ Supabase total_return 테이블에서 데이터를 불러올 수 없습니다.")
    st.stop()

# ------------------------------------------------
# 테이블 표시
# ------------------------------------------------
st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)

# ------------------------------------------------
# 클릭 기능 구현
# ------------------------------------------------
# Streamlit은 기본적으로 dataframe 클릭 이벤트를 지원하지 않기 때문에,
# selectbox로 대체 (또는 streamlit-aggrid 사용 가능)
selected = st.selectbox("🔍 차트를 보고 싶은 종목을 선택하세요:", df["종목명"].unique())

if st.button("📈 선택한 종목의 차트로 이동"):
    st.switch_page("pages/stock_detail.py")

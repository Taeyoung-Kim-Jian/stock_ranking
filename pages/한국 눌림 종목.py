# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from supabase import create_client

# ------------------------------------------------
# 환경 변수 및 Supabase 연결 (Render + Streamlit Cloud 겸용)
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
st.set_page_config(page_title="한국 눌림 종목 순위", layout="wide")

st.markdown("<h4 style='text-align:center;'>📊 b_return 테이블 (수익률 순)</h4>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-size:13px; color:gray;'>Supabase에서 불러온 데이터를 수익률 순으로 정렬하여 표시합니다.</p>", unsafe_allow_html=True)
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
# 수익률 정렬 및 표시
# ------------------------------------------------
df["수익률"] = df["수익률"].astype(float)
df_sorted = df.sort_values("수익률", ascending=False).reset_index(drop=True)

# 포맷 조정
df_sorted["수익률"] = df_sorted["수익률"].map("{:.2f}%".format)

st.dataframe(
    df_sorted,
    use_container_width=True,
    hide_index=True
)

# ------------------------------------------------
# 하단 안내
# ------------------------------------------------
st.markdown("---")
st.caption("💡 이 페이지는 Supabase의 b_return 데이터를 실시간으로 불러옵니다. (5분 캐시)")

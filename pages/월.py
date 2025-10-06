# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from supabase import create_client

# ------------------------------------------------
# 페이지 설정
# ------------------------------------------------
st.set_page_config(page_title="Supabase 연결 점검", layout="wide")
st.markdown("### 🧭 Supabase 연결 테스트")

# ------------------------------------------------
# Supabase 연결
# ------------------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Supabase 환경변수가 설정되지 않았습니다.")
    st.stop()

# ✅ 클라이언트 생성
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
st.success("✅ Supabase 클라이언트 생성 완료")

# ------------------------------------------------
# 테이블 데이터 확인
# ------------------------------------------------
try:
    res = supabase.table("b_zone_monthly_tracking").select("*").limit(5).execute()
    st.write("📦 Raw Result:", res)
    st.write("📊 Data:", res.data)

    if not res.data:
        st.warning("⚠️ Supabase에서 데이터를 가져오지 못했습니다. (빈 응답)")
    else:
        df = pd.DataFrame(res.data)
        st.success(f"✅ {len(df)}개의 데이터 수신됨")
        st.dataframe(df)
except Exception as e:
    st.error(f"❌ Supabase 요청 중 오류 발생: {e}")

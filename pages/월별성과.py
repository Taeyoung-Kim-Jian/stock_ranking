# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="📆 월별 성과", layout="wide")

# ======================================
# 1️⃣ Supabase 연결
# ======================================
@st.cache_resource
def init_connection():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = init_connection()

# ======================================
# 2️⃣ SQL 실행 함수
# ======================================
@st.cache_data(ttl=600)
def load_monthly_results():
    query = """
    WITH daily_measure AS (
        SELECT 
            b.종목코드,
            COALESCE(p.종목명, '') AS 종목명,
            b.b가격,
            b.b날짜,
            p.날짜 AS 측정일,
            p.종가 AS 측정일종가,

            (
                SELECT p_today.종가
                FROM prices p_today
                WHERE p_today.종목코드 = b.종목코드
                ORDER BY ABS(p_today.날짜 - CURRENT_DATE)
                LIMIT 1
            ) AS 현재가,

            ROUND(((p.종가 - b.b가격) / b.b가격 * 100)::numeric, 2) AS 측정일대비수익률,

            (
                SELECT MAX(p2.종가)
                FROM prices p2
                WHERE p2.종목코드 = b.종목코드
                  AND p2.날짜 >= p.날짜
            ) AS 이후최고가,
            (
                SELECT MIN(p3.종가)
                FROM prices p3
                WHERE p3.종목코드 = b.종목코드
                  AND p3.날짜 >= p.날짜
            ) AS 이후최저가,

            DATE_TRUNC('month', p.날짜)::date AS 월구분
        FROM bt_points b
        JOIN prices p 
            ON b.종목코드 = p.종목코드
            AND p.날짜 BETWEEN '2025-01-28' AND CURRENT_DATE
            AND p.종가 BETWEEN b.b가격 * 0.95 AND b.b가격 * 1.05
    )
    SELECT DISTINCT ON (종목코드, 월구분)
        종목코드,
        종목명,
        b가격,
        b날짜,
        측정일,
        측정일종가,
        현재가,
        ROUND(((현재가 - b가격) / b가격 * 100)::numeric, 2) AS 현재가대비수익률,
        이후최고가,
        이후최저가,
        ROUND(((이후최고가 - b가격) / b가격 * 100)::numeric, 2) AS 최고수익률,
        ROUND(((이후최저가 - b가격) / b가격 * 100)::numeric, 2) AS 최저수익률,
        월구분
    FROM daily_measure
    ORDER BY 종목코드, 월구분, 측정일;
    """

    # ✅ Supabase RPC(sql) 함수 이용 (미리 만들어둬야 함)
    result = supabase.rpc("sql", {"query": query}).execute()
    df = pd.DataFrame(result.data)
    if not df.empty:
        df["월포맷"] = pd.to_datetime(df["월구분"]).dt.strftime("%y.%m")
    return df

# ======================================
# 3️⃣ 데이터 로드 및 표시
# ======================================
with st.spinner("📊 월별 성과 계산 중..."):
    df = load_monthly_results()

if df.empty:
    st.warning("📭 월별 성과 데이터가 없습니다.")
    st.stop()

st.success(f"✅ 총 {len(df)}건의 데이터 불러옴")

# ======================================
# 4️⃣ 월별 탭 표시
# ======================================
months = sorted(df["월포맷"].unique(), reverse=True)
tabs = st.tabs(months)

for i, month in enumerate(months):
    with tabs[i]:
        st.subheader(f"📅 {month}월 성과")
        df_month = df[df["월포맷"] == month].copy()

        df_month = df_month[
            ["종목명", "b가격", "측정]()

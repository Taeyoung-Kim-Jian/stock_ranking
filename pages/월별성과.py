# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from supabase import create_client
from st_aggrid import AgGrid, GridOptionsBuilder

st.set_page_config(page_title="📆 월별 성과", layout="wide")

# ------------------------------------------------
# 1️⃣ Supabase 연결
# ------------------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Supabase 환경변수(SUPABASE_URL, SUPABASE_KEY)가 설정되지 않았습니다.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------------------------------
# 2️⃣ SQL 실행 (b_zone_monthly_tracking 없이 보기 전용)
# ------------------------------------------------
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

            -- ✅ 현재가: 오늘 데이터가 없으면 가장 가까운 날짜의 종가 사용
            (
                SELECT p_today.종가
                FROM prices p_today
                WHERE p_today.종목코드 = b.종목코드
                ORDER BY ABS(p_today.날짜 - CURRENT_DATE)
                LIMIT 1
            ) AS 현재가,

            ROUND(((p.종가 - b.b가격) / b.b가격 * 100)::numeric, 2) AS 측정일대비수익률,

            -- ✅ 측정일 이후 최고가 / 최저가
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
    # ✅ Supabase SQL 실행
    result = supabase.rpc("sql", {"query": query}).execute()
    df = pd.DataFrame(result.data)
    if not df.empty:
        df["월포맷"] = pd.to_datetime(df["월구분"]).dt.strftime("%y.%m")
    return df

# ------------------------------------------------
# 3️⃣ 데이터 로드
# ------------------------------------------------
with st.spinner("📊 월별 성과 계산 중..."):
    df = load_monthly_results()

if df.empty:
    st.warning("📭 월별 성과 데이터가 없습니다.")
    st.stop()

st.success(f"✅ 총 {len(df)}건 데이터 불러옴")

# ------------------------------------------------
# 4️⃣ 월별 탭 표시
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

        gb = GridOptionsBuilder.from_dataframe(df_month)
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_default_column(resizable=True, sortable=True)
        gb.configure_column("현재가대비수익률", cellStyle=lambda x: {
            "backgroundColor": "#c7f5d9" if x["value"] > 0 else "#f7c7c7"
        })
        grid_options = gb.build()

        AgGrid(df_month, gridOptions=grid_options, height=550, theme="balham", update_mode="NO_UPDATE")

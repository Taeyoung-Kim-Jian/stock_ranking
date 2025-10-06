# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import psycopg2

st.set_page_config(page_title="📆 월별 성과", layout="wide")

# ======================================
# 1️⃣ DB 연결 (Supabase or PostgreSQL)
# ======================================
@st.cache_data(ttl=600)
def load_monthly_performance():
    conn = psycopg2.connect(
        host="YOUR_HOST",
        dbname="YOUR_DB",
        user="YOUR_USER",
        password="YOUR_PASSWORD",
        port="5432"
    )
    query = """
        SELECT 
            종목코드,
            종목명,
            b가격,
            b날짜,
            측정일,
            측정일종가,
            현재가일자,
            현재가,
            현재가대비수익률,
            이후최고가,
            이후최저가,
            최고수익률,
            최저수익률,
            TO_CHAR(월구분, 'YY.MM') AS 월포맷
        FROM b_zone_monthly_tracking
        ORDER BY 월구분 DESC, 현재가대비수익률 DESC;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

df = load_monthly_performance()

if df.empty:
    st.warning("📭 데이터가 없습니다.")
    st.stop()

# ======================================
# 2️⃣ 월 탭 자동 생성
# ======================================
months = sorted(df["월포맷"].unique(), reverse=True)
tabs = st.tabs(months)

# ======================================
# 3️⃣ 각 월별 탭 테이블 표시
# ======================================
for i, month in enumerate(months):
    with tabs[i]:
        st.subheader(f"📅 {month}월 성과")
        df_month = df[df["월포맷"] == month].copy()

        # 수익률 색상 강조
        def highlight_profit(val):
            if pd.isna(val):
                return ""
            color = "lightgreen" if val > 0 else "#ffb3b3"
            return f"background-color: {color}"

        styled = (
            df_month[
                [
                    "종목명", "b가격", "측정일", "측정일종가", "현재가", 
                    "현재가대비수익률", "최고수익률", "최저수익률"
                ]
            ]
            .style.format({"현재가대비수익률": "{:.2f}%", "최고수익률": "{:.2f}%", "최저수익률": "{:.2f}%"})
            .applymap(highlight_profit, subset=["현재가대비수익률"])
        )

        st.dataframe(styled, use_container_width=True)

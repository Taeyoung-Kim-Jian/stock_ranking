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
st.set_page_config(page_title="투자 적정 종목", layout="wide")

st.markdown("<h4 style='text-align:center;'>💰 투자 적정 구간 종목 리스트</h4>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray; font-size:13px;'>현재가격이 b가격 ±5% 이내인 종목입니다.</p>", unsafe_allow_html=True)
st.markdown("---")

# ------------------------------------------------
# 데이터 로딩
# ------------------------------------------------
@st.cache_data(ttl=300)
def load_fair_price_stocks():
    """
    Supabase에서 b가격 ±5% 범위의 종목을 SQL 쿼리로 직접 가져옴
    """
    query = """
        SELECT
            t.종목명,
            b.종목코드,
            b.b가격,
            t.현재가격,
            ROUND(((t.현재가격 - b.b가격) / b.b가격 * 100)::numeric, 2) AS 변동률
        FROM
            bt_points AS b
        JOIN
            total_return AS t
        ON
            b.종목코드 = t.종목코드
        WHERE
            t.현재가격 BETWEEN b.b가격 * 0.95 AND b.b가격 * 1.05
        ORDER BY
            변동률 ASC;
    """
    try:
        result = supabase.rpc("exec_sql", {"sql": query}).execute()
        # ↑ 주의: Supabase 기본 client는 직접 SQL 실행을 지원하지 않음
        # Supabase에서 view 생성 또는 python 내 join으로 대체 가능
        return pd.DataFrame(result.data)
    except Exception as e:
        st.error(f"❌ SQL 실행 중 오류 발생: {e}")
        return pd.DataFrame()

# ------------------------------------------------
# Supabase가 SQL 실행을 직접 지원하지 않으므로
# Python에서 JOIN으로 대체 (권장)
# ------------------------------------------------
@st.cache_data(ttl=300)
def load_via_join():
    try:
        bt = supabase.table("bt_points").select("종목코드, b가격").execute()
        tt = supabase.table("total_return").select("종목명, 종목코드, 현재가격").execute()

        df_b = pd.DataFrame(bt.data)
        df_t = pd.DataFrame(tt.data)
        if df_b.empty or df_t.empty:
            return pd.DataFrame()

        df = pd.merge(df_b, df_t, on="종목코드", how="inner")
        df["변동률"] = ((df["현재가격"] - df["b가격"]) / df["b가격"] * 100).round(2)
        df = df[(df["현재가격"] >= df["b가격"] * 0.95) & (df["현재가격"] <= df["b가격"] * 1.05)]
        df = df.sort_values("변동률", ascending=True)
        return df[["종목명", "종목코드", "b가격", "현재가격", "변동률"]]
    except Exception as e:
        st.error(f"❌ 데이터 병합 중 오류: {e}")
        return pd.DataFrame()

# ------------------------------------------------
# 데이터 표시
# ------------------------------------------------
df = load_via_join()

if df.empty:
    st.warning("⚠️ 현재 b가격 ±5% 이내의 종목이 없습니다.")
    st.stop()

st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("💡 b가격 ±5% 구간에 위치한 종목은 매수/매도 균형 구간으로 해석할 수 있습니다.")

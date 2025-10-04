import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.graph_objects as go

# -------------------------------
# Supabase 연결
# -------------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------------
# 데이터 불러오기
# -------------------------------
def load_prices(code: str):
    """특정 종목코드의 가격 데이터를 불러오기"""
    res = (
        supabase.table("prices")
        .select("*")
        .eq("종목코드", code)
        .gte("날짜", "2025-01-01")  # ✅ 2025년 데이터만
        .lte("날짜", "2025-12-31")
        .order("날짜")
        .execute()
    )
    return pd.DataFrame(res.data)

# -------------------------------
# Streamlit UI
# -------------------------------
st.set_page_config(page_title="삼양식품 주가", layout="wide")
st.title("📈 삼양식품 (003230) 2025년 주가 데이터")

df = load_prices("003230")

if df.empty:
    st.warning("⚠️ Supabase에 2025년 삼양식품 데이터가 없습니다.")
else:
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df = df.sort_values("날짜")

    # Plotly 캔들차트
    fig = go.Figure(data=[
        go.Candlestick(
            x=df["날짜"],
            open=df["시가"],
            high=df["고가"],
            low=df["저가"],
            close=df["종가"],
            name="삼양식품"
        )
    ])

    fig.update_layout(
        title="삼양식품 (003230) 2025년 일별 주가",
        xaxis_title="날짜",
        yaxis_title="가격 (원)",
        xaxis_rangeslider_visible=False,
        height=800,
        template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)

    # 데이터 테이블
    st.subheader("📊 원본 데이터")
    st.dataframe(df)

# pages/stock_detail.py
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client

# ------------------------------------------------
# Supabase 연결
# ------------------------------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------------------------------
# 페이지 설정
# ------------------------------------------------
st.set_page_config(page_title="📈 종목 상세", layout="wide")

# ------------------------------------------------
# 세션 상태 확인
# ------------------------------------------------
if "selected_code" not in st.session_state:
    st.warning("⚠️ 선택된 종목이 없습니다. 메인 페이지에서 종목을 선택하세요.")
    st.stop()

code = st.session_state.selected_code
name = st.session_state.selected_name

st.title(f"📈 {name} ({code}) 상세 차트")

# ------------------------------------------------
# 데이터 로딩 함수
# ------------------------------------------------
@st.cache_data(ttl=300)
def load_prices(code):
    """prices 테이블에서 최대 5000개 데이터 로드"""
    code = str(code).zfill(6)  # ✅ 항상 6자리 문자열로 변환
    all_data = []
    chunk_size = 1000

    for i in range(0, 5000, chunk_size):
        res = (
            supabase.table("prices")
            .select("날짜, 종가")
            .eq("종목코드", code)
            .order("날짜", desc=False)
            .range(i, i + chunk_size - 1)
            .execute()
        )
        if not res.data:
            break
        all_data.extend(res.data)

    df = pd.DataFrame(all_data)
    if not df.empty:
        # ✅ 날짜가 20250128 같은 형식이면 변환
        df["날짜"] = pd.to_datetime(df["날짜"], format="%Y%m%d", errors="coerce")
        df = df.dropna(subset=["날짜"])
        df["종가"] = df["종가"].astype(float)
    return df


@st.cache_data(ttl=300)
def load_b_points(code):
    """low_after_b 테이블에서 B 포인트 로드"""
    code = str(code).zfill(6)
    res = (
        supabase.table("low_after_b")
        .select("구분, b가격, 발생일")
        .eq("종목코드", code)
        .order("발생일", desc=True)
        .range(0, 999)
        .execute()
    )
    df = pd.DataFrame(res.data)
    if not df.empty:
        df["발생일"] = pd.to_datetime(df["발생일"], errors="coerce")
        df["b가격"] = df["b가격"].astype(float)
    return df

# ------------------------------------------------
# 데이터 불러오기
# ------------------------------------------------
df_price = load_prices(code)
df_bpoints = load_b_points(code)

if df_price.empty:
    st.warning("⚠️ 가격 데이터가 없습니다. (Supabase 'prices' 테이블을 확인하세요.)")
    st.stop()

# ------------------------------------------------
# 차트 생성
# ------------------------------------------------
fig = go.Figure()

# ✅ 종가 라인
fig.add_trace(
    go.Scatter(
        x=df_price["날짜"],
        y=df_price["종가"],
        mode="lines",
        name="종가",
        line=dict(color="royalblue", width=2),
    )
)

# ✅ B 포인트 수평선
if not df_bpoints.empty:
    for _, row in df_bpoints.iterrows():
        if pd.notna(row["b가격"]):
            fig.add_hline(
                y=row["b가격"],
                line=dict(color="red", width=1.8, dash="dot"),
                annotation_text=f"B({row['구분']})",
                annotation_position="right",
                annotation_font=dict(color="red", size=12),
            )

# ------------------------------------------------
# 차트 레이아웃
# ------------------------------------------------
fig.update_layout(
    title=f"{name} ({code}) 주가 차트",
    height=700,
    xaxis_title="날짜",
    yaxis_title="가격 (₩)",
    template="plotly_white",
    margin=dict(l=30, r=30, t=50, b=30),
    showlegend=False,
)

# ✅ X축 전체 표시 (2025년 포함)
if not df_price.empty:
    fig.update_xaxes(range=[df_price["날짜"].min(), df_price["날짜"].max()])

# ------------------------------------------------
# 출력
# ------------------------------------------------
st.plotly_chart(fig, use_container_width=True)
st.markdown("---")
st.caption("📊 수평선은 각 B가격을 의미하며, 발생일 기준으로 표시됩니다.")

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
# 세션 상태에서 선택 종목 불러오기
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
    res = (
        supabase.table("prices")
        .select("날짜, 종가")
        .eq("종목코드", code)
        .order("날짜", desc=False)
        .execute()
    )
    df = pd.DataFrame(res.data)
    if not df.empty:
        df["날짜"] = pd.to_datetime(df["날짜"])
        df["종가"] = df["종가"].astype(float)
    return df

@st.cache_data(ttl=300)
def load_b_points(code):
    res = (
        supabase.table("low_after_b")
        .select("구분, b가격, 발생일")
        .eq("종목코드", code)
        .order("발생일", desc=True)
        .execute()
    )
    df = pd.DataFrame(res.data)
    if not df.empty:
        df["발생일"] = pd.to_datetime(df["발생일"])
        df["b가격"] = df["b가격"].astype(float)
    return df

# ------------------------------------------------
# 데이터 불러오기
# ------------------------------------------------
df_price = load_prices(code)
df_bpoints = load_b_points(code)

if df_price.empty:
    st.warning("가격 데이터가 없습니다.")
    st.stop()

# ------------------------------------------------
# 차트 생성
# ------------------------------------------------
fig = go.Figure()

# 종가 라인
fig.add_trace(
    go.Scatter(
        x=df_price["날짜"],
        y=df_price["종가"],
        mode="lines",
        name="종가",
        line=dict(color="lightblue", width=2),
    )
)

# B 포인트 표시
if not df_bpoints.empty:
    for _, row in df_bpoints.iterrows():
        fig.add_trace(
            go.Scatter(
                x=[row["발생일"]],
                y=[row["b가격"]],
                mode="markers+text",
                name=f"B({row['구분']})",
                text=row["구분"],
                textposition="top center",
                marker=dict(color="red", size=9, symbol="diamond"),
            )
        )

fig.update_layout(
    height=700,
    xaxis_title="날짜",
    yaxis_title="가격",
    template="plotly_white",
    margin=dict(l=20, r=20, t=40, b=20),
    showlegend=False,
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("📊 차트에는 최근 종가 흐름과 B 포인트가 함께 표시됩니다.")

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
def load_prices(code):
    res = (
        supabase.table("prices")
        .select("*")
        .eq("종목코드", code)
        .range(0, 5000)
        .execute()
    )
    df = pd.DataFrame(res.data)
    if not df.empty:
        df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
        df = df.dropna(subset=["날짜"]).sort_values("날짜")
    return df

def load_detected_stock(code):
    res = supabase.table("detected_stocks").select("*").eq("종목코드", code).execute()
    if res.data:
        return res.data[0]
    return None

# -------------------------------
# UI 기본 설정
# -------------------------------
st.set_page_config(page_title="Stock Detail", layout="centered")

# ✅ 세션 상태에서 종목코드/이름 불러오기
code = st.session_state.get("selected_code", None)
name = st.session_state.get("selected_name", None)

if not code:
    st.warning("❌ 종목 코드가 없습니다. 메인 페이지에서 선택하세요.")
    st.stop()

title_text = f"📈 {name} ({code}) 상세보기" if name else f"📈 {code} 상세보기"

# 📌 제목 스타일 (모바일에서 크기 줄이기)
st.markdown(f"""
    <style>
    h1 {{
        font-size: 2rem; /* 기본 제목 크기 */
    }}
    @media (max-width: 768px) {{
        h1 {{
            font-size: 1.3rem;  /* 모바일에서는 더 작게 */
        }}
    }}
    </style>
    <h1>{title_text}</h1>
""", unsafe_allow_html=True)

# -------------------------------
# 가격 데이터 불러오기
# -------------------------------
price_df = load_prices(code)
if not price_df.empty:
    detected = load_detected_stock(code)

    # 📊 선차트 생성
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=price_df["날짜"],
        y=price_df["종가"],
        mode="lines",
        name="종가",
        line=dict(color="blue")
    ))

    # 기준가 라인 추가
    if detected:
        for i in [1, 2, 3]:
            key = f"{i}차_기준가"
            if key in detected and detected[key] is not None:
                try:
                    기준가 = float(detected[key])
                    fig.add_hline(
                        y=기준가,
                        line_dash="dot",
                        line_color="red" if i == 1 else ("blue" if i == 2 else "green"),
                        annotation_text=f"{i}차 기준가 {기준가}",
                        annotation_position="top left"
                    )
                except ValueError:
                    pass

    # 📊 레이아웃 (반응형)
    fig.update_layout(
        autosize=True,
        margin=dict(l=10, r=10, t=40, b=40),
        template="plotly_white",
        yaxis_title="가격 (원)",
        xaxis_title="날짜"
    )

    # 📌 CSS 반응형 높이
    st.markdown("""
        <style>
        .plotly-graph-div {
            height: 60vh !important;   /* PC: 화면 높이의 60% */
        }
        @media (max-width: 768px) {
            .plotly-graph-div {
                height: 40vh !important;  /* 모바일: 화면 높이의 40% */
            }
        }
        </style>
    """, unsafe_allow_html=True)

    # 📊 차트 출력
    st.plotly_chart(fig, use_container_width=True, config={"responsive": True})

    # 📑 데이터 테이블
    st.subheader("📊 원본 데이터")
    st.dataframe(price_df, use_container_width=True)

else:
    st.info("⚠️ 가격 데이터가 없습니다.")

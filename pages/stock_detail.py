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
        .order("날짜")
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
# Streamlit UI
# -------------------------------
st.set_page_config(page_title="Stock Detail", layout="wide")

code = st.session_state.get("selected_code", None)
name = st.session_state.get("selected_name", None)

if not code:
    st.warning("❌ 종목 코드가 없습니다. 메인 페이지에서 선택하세요.")
    st.stop()

st.title(f"📈 {name} ({code}) 상세보기" if name else f"📈 {code} 상세보기")

# -------------------------------
# 가격 데이터 로드 및 차트
# -------------------------------
price_df = load_prices(code)

if not price_df.empty:
    detected = load_detected_stock(code)

    # ✅ 캔들차트
    fig = go.Figure(data=[
        go.Candlestick(
            x=price_df["날짜"],
            open=price_df["시가"],
            high=price_df["고가"],
            low=price_df["저가"],
            close=price_df["종가"],
            name="가격"
        )
    ])

    # ✅ 기준가 라인 추가
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

    fig.update_layout(
        autosize=True,
        xaxis_rangeslider_visible=False,
        height=700,
        margin=dict(l=10, r=10, t=40, b=40),
        template="plotly_white",
        dragmode=False  # ❌ 드래그 이동 방지
    )

    # ✅ PC: 마우스 휠 줌 / 모바일: 핀치 줌 허용
    config = {
        "scrollZoom": True,       # 마우스 휠 / 모바일 핀치 줌 허용
        "displayModeBar": False,  # 툴바 숨김
        "doubleClick": "reset"    # 더블클릭 시 리셋
    }

    st.plotly_chart(fig, use_container_width=True, config=config)

    # 원본 데이터 테이블
    st.subheader("📊 원본 데이터")
    st.dataframe(price_df, use_container_width=True)

else:
    st.info("⚠️ 가격 데이터가 없습니다.")

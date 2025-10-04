import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.graph_objects as go
from streamlit_js_eval import streamlit_js_eval   # ✅ 모바일/PC 구분용

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
    """Supabase에서 특정 종목의 2000일치 데이터를 페이지네이션으로 불러오기"""
    page_size = 1000
    all_rows = []
    start = 0
    while True:
        res = (
            supabase.table("prices")
            .select("*")
            .eq("종목코드", code)
            .order("날짜")
            .range(start, start + page_size - 1)
            .execute()
        )
        rows = res.data
        if not rows:
            break
        all_rows.extend(rows)
        if len(rows) < page_size:
            break
        start += page_size

    df = pd.DataFrame(all_rows)
    if not df.empty:
        df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
        df = df.dropna(subset=["날짜"]).sort_values("날짜")
    return df

def load_detected_stock(code):
    """기준가 테이블에서 특정 종목 불러오기"""
    res = supabase.table("detected_stocks").select("*").eq("종목코드", code).execute()
    if res.data:
        return res.data[0]
    return None

# -------------------------------
# Streamlit UI
# -------------------------------
st.set_page_config(page_title="Stock Detail", layout="wide")

# ✅ 세션 상태에서 종목코드/종목명 불러오기
code = st.session_state.get("selected_code", None)
name = st.session_state.get("selected_name", None)

if not code:
    st.warning("❌ 종목 코드가 없습니다. 메인 페이지에서 선택하세요.")
    st.stop()

st.subheader(f"📈 {name} ({code})")

# -------------------------------
# 모바일/PC 구분
# -------------------------------
screen_width = streamlit_js_eval(js_expressions="window.innerWidth", key="SCR")
is_mobile = screen_width is not None and screen_width < 768

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

    # ✅ 기준가 라인 표시
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

    # ✅ 차트 높이: PC는 500, 모바일은 350
    fig.update_layout(
        autosize=True,
        xaxis_rangeslider_visible=False,
        height=350 if is_mobile else 500,
        margin=dict(l=10, r=10, t=40, b=40),
        template="plotly_white"
    )

    # ✅ PC → 인터랙티브, 모바일 → 고정
    if is_mobile:
        st.plotly_chart(fig, use_container_width=True, config={"staticPlot": True})
    else:
        st.plotly_chart(fig, use_container_width=True, config={"responsive": True})

    # 데이터 테이블
    st.subheader("📊 원본 데이터 (2000일치)")
    st.dataframe(price_df, use_container_width=True)

else:
    st.info("⚠️ 가격 데이터가 없습니다.")

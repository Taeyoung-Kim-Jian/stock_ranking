import streamlit as st
import pandas as pd
import sqlite3
import numpy as np
import plotly.graph_objects as go

DB_PATH = "stock_data.db"

# -----------------------------
# DB에서 종목/데이터 불러오기
# -----------------------------
def load_data():
    conn = sqlite3.connect(DB_PATH)
    # ⚠️ 실제 DB 테이블/컬럼명에 맞게 수정 필요
    query = """
        SELECT 종목, 상태, 현재가, 예상상승률, 예상목표가, 예상기간
        FROM stocks
    """
    df = pd.read_sql(query, conn)
    conn.close()

    # 오늘 날짜 기준 예상도달일 계산
    base_date = pd.Timestamp.today().normalize()
    df["예상도달일"] = base_date + pd.to_timedelta(df["예상기간"], unit="D")
    return df

# -----------------------------
# 미니차트 생성 함수
# -----------------------------
def make_sparkline(prices, 종목명):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=prices,
        mode="lines",
        line=dict(color="blue"),
        showlegend=False
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=20, b=0),
        height=120,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        title=dict(text=f"{종목명} 최근 흐름", x=0.5, font=dict(size=12))
    )
    return fig

# -----------------------------
# 카드 뷰 생성
# -----------------------------
def render_cards(df):
    for _, row in df.iterrows():
        col1, col2 = st.columns([2, 3])
        with col1:
            st.markdown(f"""
            <div style="padding:15px; border-radius:10px; background:#f9f9f9;
                        margin-bottom:15px; box-shadow:2px 2px 5px rgba(0,0,0,0.1);">
                <h4>{row['종목']} <span style="font-size:0.8em;">{row['상태']}</span></h4>
                <p>💰 현재가: <b>{row['현재가']:,}원</b></p>
                <p>📈 예상 수익률: <b style="color:green;">{row['예상상승률']:.1f}%</b></p>
                <p>🎯 목표가: <b>{row['예상목표가']:,}원</b></p>
                <p>⏳ 예상 기간: {row['예상기간']}일</p>
                <p>📅 예상 도달일: {row['예상도달일'].date()}</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            # ⚠️ DB에 실제 가격 이력 테이블 있으면 불러오기
            sample_prices = np.cumsum(np.random.randn(50)) + row['현재가']
            fig = make_sparkline(sample_prices, row['종목'])
            st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Streamlit UI
# -----------------------------
def main():
    st.title("📊 TOP10 종목 리포트 (예상 수익률 & 기간)")

    df = load_data()

    # 수익률 기준 TOP10
    df_top10_rise = df.sort_values("예상상승률", ascending=False).head(10)

    # 기간 기준 TOP10
    df_top10_period = df.sort_values("예상기간").head(10)

    # -----------------
    # 탭 구조
    # -----------------
    tab1, tab2 = st.tabs(["📈 수익률 TOP10", "⏳ 기간 TOP10"])

    with tab1:
        st.subheader("📈 예상 수익률 기준 TOP10")
        styled_rise = df_top10_rise.style.background_gradient(
            subset=["예상상승률"], cmap="Greens"
        )
        st.dataframe(styled_rise, use_container_width=True)
        st.markdown("### 카드 뷰")
        render_cards(df_top10_rise)

    with tab2:
        st.subheader("⏳ 예상 기간 기준 TOP10")
        styled_period = df_top10_period.style.background_gradient(
            subset=["예상기간"], cmap="Blues"
        )
        st.dataframe(styled_period, use_container_width=True)
        st.markdown("### 카드 뷰")
        render_cards(df_top10_period)

if __name__ == "__main__":
    main()

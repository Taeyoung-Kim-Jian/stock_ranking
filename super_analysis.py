import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go

DB_PATH = "stock_data.db"

# -----------------------------
# DB에서 종목 불러오기
# -----------------------------
def load_symbols():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT 종목코드, 종목명 FROM stocks", conn)
    conn.close()
    return df

# -----------------------------
# 가격 데이터 로드 + 보정
# -----------------------------
def load_prices(code):
    conn = sqlite3.connect(DB_PATH)
    query = f"""
        SELECT 날짜, 종가, 시가, 고가, 저가, 거래량, 종목명
        FROM prices
        WHERE 종목코드='{code}'
        ORDER BY 날짜
    """
    df = pd.read_sql(query, conn, parse_dates=["날짜"])
    conn.close()
    return preprocess_prices(df)

def preprocess_prices(df, threshold=0.3):
    df = df.copy()
    df["종가보정"] = df["종가"]

    for i in range(1, len(df)):
        prev = df.loc[i-1, "종가보정"]
        curr = df.loc[i, "종가보정"]

        if curr > prev * (1 + threshold) or curr < prev * (1 - threshold):
            ratio = curr / prev
            st.warning(f"⚠️ 가격 보정 발생: {df.loc[i,'날짜'].date()} "
                       f"(전일 {prev:.2f} → 당일 {curr:.2f}, 배율={ratio:.3f})")
            df.loc[:i-1, ["종가보정", "시가", "고가", "저가"]] *= ratio

    return df

# -----------------------------
# B/T 탐색
# -----------------------------
def find_bt(df, rise_threshold=0.3):
    closes = df["종가보정"].values
    dates = df["날짜"].values

    b_points, t_points = [], []
    prev_high = closes[0]

    for i in range(1, len(closes)):
        price = closes[i]

        if price > prev_high:
            b_date, b_price = dates[i], price
            b_points.append((b_date, b_price))

            for j in range(i+1, len(closes)):
                if closes[j] >= b_price * (1 + rise_threshold):
                    peak_idx = j
                    while peak_idx+1 < len(closes) and closes[peak_idx+1] >= closes[peak_idx]:
                        peak_idx += 1
                    t_date, t_price = dates[peak_idx], closes[peak_idx]
                    t_points.append((t_date, t_price))
                    prev_high = t_price
                    i = peak_idx
                    break

        prev_high = max(prev_high, price)

    return b_points, t_points

# -----------------------------
# 분석 로직
# -----------------------------
def analyze_retests(df, b_points, t_points):
    result = []
    closes = df.set_index("날짜")["종가보정"]

    # date 변환
    b_points = [(pd.to_datetime(d).date(), p) for d, p in b_points]
    t_points = [(pd.to_datetime(d).date(), p) for d, p in t_points]

    for t_idx, (t_date, _) in enumerate(t_points):
        for b_idx in range(t_idx+1):
            b_date, b_price = b_points[b_idx]

            closes_after_t = closes.loc[str(t_date):]
            if closes_after_t.min() <= b_price:
                retest_date = closes_after_t.idxmin().date()

                later_t = [d for d, _ in t_points if d > retest_date]
                if later_t:
                    next_t_date = later_t[0]
                    next_t_price = closes.loc[str(next_t_date)]
                    period = (next_t_date - b_date).days
                    max_return = (closes.loc[str(b_date):str(next_t_date)].max() / b_price - 1) * 100
                    min_return = (closes.loc[str(b_date):str(next_t_date)].min() / b_price - 1) * 100

                    result.append({
                        "현재T": f"T{t_idx}",
                        "B번호": f"B{b_idx}",
                        "B가격": b_price,
                        "회귀일": b_date,
                        "목표": "다음T",
                        "목표가격": next_t_price,
                        "목표일": next_t_date,
                        "기간(일)": period,
                        "최고수익률(%)": round(max_return, 2),
                        "최저수익률(%)": round(min_return, 2)
                    })
                else:
                    closes_after_retest = closes.loc[str(retest_date):]
                    future_high = closes_after_retest.max()
                    future_date = closes_after_retest.idxmax().date()

                    period = (future_date - b_date).days
                    max_return = (future_high / b_price - 1) * 100
                    min_return = (closes.loc[str(b_date):].min() / b_price - 1) * 100

                    result.append({
                        "현재T": f"T{t_idx}",
                        "B번호": f"B{b_idx}",
                        "B가격": b_price,
                        "회귀일": b_date,
                        "목표": "최고가",
                        "목표가격": future_high,
                        "목표일": future_date,
                        "기간(일)": period,
                        "최고수익률(%)": round(max_return, 2),
                        "최저수익률(%)": round(min_return, 2)
                    })

    return pd.DataFrame(result)

# -----------------------------
# 차트
# -----------------------------
def plot_chart(df, b_points, t_points, title):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["날짜"], y=df["종가보정"],
        mode="lines", name="종가(보정)", line=dict(color="blue")
    ))

    if b_points:
        fig.add_trace(go.Scatter(
            x=[pd.to_datetime(d) for d, _ in b_points],
            y=[p for _, p in b_points],
            mode="markers+text",
            name="B (돌파)",
            text=["B"]*len(b_points),
            textposition="top center",
            marker=dict(color="blue", size=8, symbol="circle")
        ))

    if t_points:
        fig.add_trace(go.Scatter(
            x=[pd.to_datetime(d) for d, _ in t_points],
            y=[p for _, p in t_points],
            mode="markers+text",
            name="T (파동끝)",
            text=["T"]*len(t_points),
            textposition="bottom center",
            marker=dict(color="red", size=10, symbol="triangle-down")
        ))

    fig.update_layout(
        title=title,
        xaxis_title="날짜",
        yaxis_title="가격",
        template="plotly_white",
        height=600
    )
    return fig

# -----------------------------
# Streamlit UI
# -----------------------------
def main():
    st.title("📈 B/T 기반 안전구간 분석")

    symbols = load_symbols()
    if symbols.empty:
        st.error("DB에 종목 데이터가 없습니다.")
        return

    choice = st.selectbox("종목 선택", symbols["종목명"] + " (" + symbols["종목코드"] + ")")
    code = choice.split("(")[-1].strip(")")

    df = load_prices(code)
    b_points, t_points = find_bt(df)

    st.write(f"✅ {choice} 데이터 ({len(df)}일치)")

    result = analyze_retests(df, b_points, t_points)
    if not result.empty:
        st.subheader("📊 분석 결과 테이블")
        st.dataframe(result)

    st.subheader("📈 차트")
    fig = plot_chart(df, b_points, t_points, choice)
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()

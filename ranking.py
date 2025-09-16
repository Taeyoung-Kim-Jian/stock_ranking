import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from super_analysis import load_prices, find_bt, analyze_retests  # 기존 B/T 함수 import

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
# 목표가/예상기간 계산
# -----------------------------
def analyze_target(df):
    b_points, t_points = find_bt(df)
    results = analyze_retests(df, b_points, t_points)

    if results.empty:
        return None

    # 마지막 분석 결과 기준
    last = results.iloc[-1]
    target_price = last["목표가격"]
    period = last["기간(일)"]

    # 도달일 = 오늘 + 기간
    today = pd.Timestamp.today().normalize()
    target_date = today + pd.to_timedelta(period, unit="D")

    current_price = df["종가보정"].iloc[-1]
    expected_return = round((target_price - current_price) / current_price * 100, 1)

    return target_price, expected_return, period, target_date.date()

# -----------------------------
# 카드 뷰 생성
# -----------------------------
def render_cards(df):
    for _, row in df.iterrows():
        st.markdown(f"""
        <div style="padding:15px; border-radius:10px; background:#f9f9f9;
                    margin-bottom:15px; box-shadow:2px 2px 5px rgba(0,0,0,0.1);">
            <h4>{row['종목명']}</h4>
            <p>💰 현재가: <b>{row['현재가']:,}원</b></p>
            <p>📈 예상 수익률: <b style="color:green;">{row['예상상승률(%)']:.1f}%</b></p>
            <p>🎯 목표가: <b>{row['예상목표가']:,}원</b></p>
            <p>⏳ 예상 기간: {row['예상기간(일)']}일</p>
            <p>📅 예상 도달일: {row['예상도달일']}</p>
        </div>
        """, unsafe_allow_html=True)

# -----------------------------
# Streamlit UI
# -----------------------------
def main():
    st.title("📊 TOP10 종목 리포트")

    symbols = load_symbols()
    results = []

    for _, row in symbols.iterrows():
        code, name = row["종목코드"], row["종목명"]
        df = load_prices(code)
        if df.empty:
            continue

        res = analyze_target(df)
        if not res:
            continue

        target_price, exp_return, period, target_date = res

        results.append({
            "종목명": name,
            "현재가": df["종가보정"].iloc[-1],
            "예상목표가": target_price,
            "예상상승률(%)": exp_return,
            "예상기간(일)": period,
            "예상도달일": target_date
        })

    df_result = pd.DataFrame(results)

    if df_result.empty:
        st.warning("분석 가능한 종목이 없습니다.")
        return

    # TOP10 (수익률 / 도달일)
    df_top10_return = df_result.sort_values("예상상승률(%)", ascending=False).head(10)
    df_top10_date = df_result.sort_values("예상도달일").head(10)

    # -----------------
    # 탭 구조
    # -----------------
    tab1, tab2 = st.tabs(["📈 수익률 TOP10", "⏳ 도달일 TOP10"])

    with tab1:
        st.subheader("📈 예상 수익률 TOP10")
        st.dataframe(df_top10_return, use_container_width=True)
        render_cards(df_top10_return)

    with tab2:
        st.subheader("⏳ 예상 도달일 TOP10")
        st.dataframe(df_top10_date, use_container_width=True)
        render_cards(df_top10_date)

if __name__ == "__main__":
    main()

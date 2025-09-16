import streamlit as st
import pandas as pd
from super_analysis import load_symbols, load_prices, analyze_target

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

def main():
    st.title("📊 TOP10 종목 리포트 (B/T 기반)")

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

    # TOP10 (수익률/도달일)
    df_top10_return = df_result.sort_values("예상상승률(%)", ascending=False).head(10)
    df_top10_date = df_result.sort_values("예상도달일").head(10)

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

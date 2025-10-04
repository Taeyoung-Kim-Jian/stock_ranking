# 모달 풀스크린 + 내부 콘텐츠 확장 CSS
st.markdown("""
    <style>
    [data-testid="stDialog"] {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        z-index: 9999 !important;
        background-color: white !important;
    }
    [data-testid="stDialog"] > div {
        display: flex !important;
        flex-direction: column !important;
        height: 100% !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    /* 차트를 모달 안에서 꽉 채우기 */
    .fullscreen-chart {
        flex: 1 !important;
        width: 100% !important;
    }
    </style>
""", unsafe_allow_html=True)


@st.dialog(f"📈 {stock['종목명']} ({stock['종목코드']}) 상세보기")
def show_detail():
    # 상단 차트 (화면 대부분 차지)
    st.subheader("📊 캔들차트 (기준가 포함)")

    price_df = load_prices(stock["종목코드"])
    if not price_df.empty:
        price_df["날짜"] = pd.to_datetime(price_df["날짜"], errors="coerce")
        price_df = price_df.dropna(subset=["날짜"]).sort_values("날짜")

        detected = load_detected_stock(stock["종목코드"])

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

        # 기준가 라인
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
            xaxis_rangeslider_visible=False,
            height=800,  # 차트 세로 크게
            margin=dict(l=10, r=10, t=40, b=40),
            template="plotly_white"
        )

        # CSS 클래스 적용
        st.plotly_chart(fig, use_container_width=True, key="main_chart", 
                        config={"displayModeBar": True})
    else:
        st.info("가격 데이터가 없습니다.")

    # 하단 종목 정보 (작게)
    st.markdown("---")
    st.subheader("ℹ️ 종목 정보")
    st.write(f"**종목코드**: {stock['종목코드']}")
    st.write(f"**종목명**: {stock['종목명']}")
    st.write(f"**등록일**: {stock.get('등록일')}")
    st.write(f"**마지막 업데이트**: {stock.get('마지막업데이트일')}")

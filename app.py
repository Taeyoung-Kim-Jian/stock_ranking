import streamlit as st
import pandas as pd
from supabase import create_client
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
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
def load_stocks():
    res = supabase.table("stocks").select("*").execute()
    return pd.DataFrame(res.data)

def load_prices(code):
    res = supabase.table("prices").select("*").eq("종목코드", code).order("날짜").execute()
    return pd.DataFrame(res.data)

def load_detected_stock(code: str):
    res = supabase.table("detected_stocks").select("*").eq("종목코드", code).execute()
    if res.data:
        return res.data[0]
    return None

# -------------------------------
# UI 시작
# -------------------------------
st.set_page_config(page_title="Stocks Dashboard", layout="wide", initial_sidebar_state="collapsed")
st.title("📊 종목 리스트")

# ✅ 풀스크린 모달 + 차트 중앙정렬 CSS
st.markdown("""
    <style>
    [data-testid="stDialog"] {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        width: 100% !important;
        height: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        z-index: 9999 !important;
        background-color: white !important;
        border-radius: 0 !important;
    }
    [data-testid="stDialog"] > div {
        height: 100% !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        display: flex !important;
        flex-direction: column !important;
    }
    .chart-container {
        flex: 9;   /* 화면 90% */
        width: 100%;
        display: flex;
        justify-content: center;  /* 중앙정렬 */
        align-items: center;
    }
    .info-container {
        flex: 1;   /* 화면 10% */
        width: 100%;
        padding: 1rem;
        background: #fafafa;
        border-top: 1px solid #ddd;
    }
    .stPlotlyChart {
        width: 100% !important;
        margin: auto !important;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------------------
# 종목 리스트 표시
# -------------------------------
df = load_stocks()
if df.empty:
    st.warning("⚠️ Supabase의 stocks 테이블에 데이터가 없습니다.")
    st.stop()

cols = ["종목코드", "종목명", "등록일", "마지막업데이트일"]
gb = GridOptionsBuilder.from_dataframe(df[cols])
gb.configure_selection("single", use_checkbox=False)
grid_options = gb.build()

grid_response = AgGrid(
    df[cols],
    gridOptions=grid_options,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    theme="streamlit",
    height=420,
    allow_unsafe_jscode=True,
)

selected = grid_response["selected_rows"]
if isinstance(selected, pd.DataFrame):
    selected = selected.to_dict(orient="records")

# -------------------------------
# 모달창 (종목 상세보기)
# -------------------------------
sel_code = selected[0]["종목코드"] if selected else None
if "open_code" not in st.session_state:
    st.session_state.open_code = None

if sel_code and st.session_state.open_code != sel_code:
    st.session_state.open_code = sel_code
    stock = selected[0]

    @st.dialog(f"📈 {stock['종목명']} ({stock['종목코드']}) 상세보기")
    def show_detail():
        # -------------------------------
        # 상단 차트 (90%)
        # -------------------------------
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)

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
                height=750,
                margin=dict(l=20, r=20, t=40, b=40),
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("가격 데이터가 없습니다.")

        st.markdown('</div>', unsafe_allow_html=True)

        # -------------------------------
        # 하단 종목 정보 (10%)
        # -------------------------------
        st.markdown('<div class="info-container">', unsafe_allow_html=True)
        st.subheader("ℹ️ 종목 정보")
        st.write(f"**종목코드**: {stock['종목코드']}")
        st.write(f"**종목명**: {stock['종목명']}")
        st.write(f"**등록일**: {stock.get('등록일')}")
        st.write(f"**마지막 업데이트**: {stock.get('마지막업데이트일')}")
        st.markdown('</div>', unsafe_allow_html=True)

    show_detail()

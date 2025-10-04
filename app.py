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
    """stocks 테이블 전체 불러오기"""
    res = supabase.table("stocks").select("*").execute()
    return pd.DataFrame(res.data)

def load_prices(code):
    """prices 테이블에서 특정 종목의 일별 가격 불러오기"""
    res = supabase.table("prices").select("*").eq("종목코드", code).order("날짜").execute()
    return pd.DataFrame(res.data)

def load_detected_stock(code: str):
    """detected_stocks 테이블에서 기준가 불러오기"""
    res = supabase.table("detected_stocks").select("*").eq("종목코드", code).execute()
    if res.data:
        return res.data[0]
    return None

# -------------------------------
# UI 기본 설정
# -------------------------------
st.set_page_config(
    page_title="Stocks Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.title("📊 종목 리스트")

# -------------------------------
# 종목 리스트 표시
# -------------------------------
df = load_stocks()
if df.empty:
    st.warning("⚠️ Supabase의 stocks 테이블에 데이터가 없습니다.")
    st.stop()

# AgGrid 설정
cols = ["종목코드", "종목명", "등록일", "마지막업데이트일"]
gb = GridOptionsBuilder.from_dataframe(df[cols])
gb.configure_selection("single", use_checkbox=False)  # 단일행 선택
grid_options = gb.build()

grid_response = AgGrid(
    df[cols],
    gridOptions=grid_options,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    theme="streamlit",
    height=420,
    allow_unsafe_jscode=True,
)

# 항상 리스트로 변환
selected = grid_response["selected_rows"]
if isinstance(selected, pd.DataFrame):
    selected = selected.to_dict(orient="records")

# -------------------------------
# 모달창 (종목 상세보기)
# -------------------------------

# 모달 크기 확장 CSS
st.markdown("""
    <style>
    [data-testid="stDialog"] {
        width: 90% !important;
        max-width: 90% !important;
    }
    </style>
""", unsafe_allow_html=True)

sel_code = selected[0]["종목코드"] if selected else None
if "open_code" not in st.session_state:
    st.session_state.open_code = None

if sel_code and st.session_state.open_code != sel_code:
    st.session_state.open_code = sel_code
    stock = selected[0]

    @st.dialog(f"📈 {stock['종목명']} ({stock['종목코드']}) 상세보기")
    def show_detail():
        col1, col2 = st.columns([2, 1])

        # 왼쪽: 캔들차트
        with col1:
            st.subheader("📊 캔들차트 (기준가 포함)")
            price_df = load_prices(stock["종목코드"])
            if not price_df.empty:
                price_df["날짜"] = pd.to_datetime(price_df["날짜"])
                price_df = price_df.sort_values("날짜")

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

                # 기준가 라인 표시
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
                                pass  # 변환 불가능하면 무시

                fig.update_layout(
                    xaxis_rangeslider_visible=False,
                    height=600,
                    template="plotly_white"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("가격 데이터가 없습니다.")

        # 오른쪽: 종목 정보
        with col2:
            st.subheader("ℹ️ 종목 정보")
            st.write(f"**종목코드**: {stock['종목코드']}")
            st.write(f"**종목명**: {stock['종목명']}")
            st.write(f"**등록일**: {stock.get('등록일')}")
            st.write(f"**마지막 업데이트**: {stock.get('마지막업데이트일')}")

    show_detail()

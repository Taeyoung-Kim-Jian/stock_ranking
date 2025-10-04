import streamlit as st
import pandas as pd
from supabase import create_client
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# ----- Supabase -----
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def load_stocks():
    res = supabase.table("stocks").select("*").execute()
    return pd.DataFrame(res.data)

def load_prices(code):
    res = supabase.table("prices").select("*").eq("종목코드", code).order("날짜").execute()
    return pd.DataFrame(res.data)

# ----- UI -----
st.set_page_config(page_title="Stocks Dashboard", layout="wide")
st.title("📊 종목 리스트")

df = load_stocks()
if df.empty:
    st.warning("⚠️ Supabase의 stocks 테이블에 데이터가 없습니다.")
    st.stop()

# AgGrid
cols = ["종목코드","종목명","등록일","마지막업데이트일"]
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

# 항상 리스트로 변환
selected = grid_response["selected_rows"]
if isinstance(selected, pd.DataFrame):
    selected = selected.to_dict(orient="records")

# 모달/익스페리멘탈/폴백 결정 함수
def open_detail_dialog(stock: dict):
    title = f"📈 {stock['종목명']} ({stock['종목코드']}) 상세보기"

    def render_body():
        st.write(f"종목코드: {stock['종목코드']}")
        st.write(f"등록일: {stock.get('등록일')}")
        st.write(f"마지막 업데이트: {stock.get('마지막업데이트일')}")
        price_df = load_prices(stock["종목코드"])
        if not price_df.empty:
            price_df["날짜"] = pd.to_datetime(price_df["날짜"])
            price_df = price_df.sort_values("날짜")
            st.line_chart(price_df.set_index("날짜")["종가"])
        else:
            st.info("가격 데이터가 없습니다.")

    # 1) 정식 API (1.37+)
    if hasattr(st, "dialog"):
        @st.dialog(title)
        def _dlg():
            render_body()
        _dlg()
        return

    # 2) 실험적 API (1.34~1.36)
    if hasattr(st, "experimental_dialog"):
        @st.experimental_dialog(title)
        def _dlg():
            render_body()
        _dlg()
        return

    # 3) 폴백: expander
    with st.expander(title, expanded=True):
        render_body()

# 선택 변화가 있을 때만 열리게 (재실행 시 반복 오픈 방지)
sel_code = selected[0]["종목코드"] if selected else None
if "open_code" not in st.session_state:
    st.session_state.open_code = None

if sel_code and st.session_state.open_code != sel_code:
    st.session_state.open_code = sel_code
    stock = selected[0]
    open_detail_dialog(stock)

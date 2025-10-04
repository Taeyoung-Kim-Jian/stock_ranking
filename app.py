import streamlit as st
import pandas as pd
from supabase import create_client
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

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

# -------------------------------
# UI
# -------------------------------
st.set_page_config(page_title="Stocks Dashboard", layout="wide")
st.title("📊 종목 리스트")

# 종목 불러오기
df = load_stocks()

if df.empty:
    st.warning("⚠️ Supabase에 종목 데이터(stocks 테이블)가 없습니다.")
else:
    # AgGrid 옵션
    gb = GridOptionsBuilder.from_dataframe(df[["종목코드","종목명","등록일","마지막업데이트일"]])
    gb.configure_selection("single", use_checkbox=False)  # 행 단일 선택
    grid_options = gb.build()

    grid_response = AgGrid(
        df[["종목코드","종목명","등록일","마지막업데이트일"]],
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        theme="streamlit",
        height=400,
        allow_unsafe_jscode=True,
    )

    selected = grid_response["selected_rows"]

    # 행 클릭 시 팝업 띄우기
    if selected:
        stock = selected[0]
        with st.modal(f"📈 {stock['종목명']} ({stock['종목코드']}) 상세보기"):
            st.write(f"종목코드: {stock['종목코드']}")
            st.write(f"등록일: {stock['등록일']}")
            st.write(f"마지막 업데이트: {stock['마지막업데이트일']}")

            # 가격 데이터 로드
            price_df = load_prices(stock["종목코드"])
            if not price_df.empty:
                price_df["날짜"] = pd.to_datetime(price_df["날짜"])
                price_df = price_df.sort_values("날짜")
                st.line_chart(price_df.set_index("날짜")["종가"])
            else:
                st.info("가격 데이터가 없습니다.")

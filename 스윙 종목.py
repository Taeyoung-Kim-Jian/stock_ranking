import streamlit as st
import pandas as pd
from supabase import create_client
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# ------------------------------------------------
# Supabase 연결
# ------------------------------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------------------------------
# 데이터 로딩 함수
# ------------------------------------------------
@st.cache_data(ttl=300)
def load_returns(limit=None):
    query = supabase.table("b_return").select(
        "종목명, 종목코드, 수익률, 발생일, 발생일종가, 현재가격, 기간"
    ).order("수익률", desc=True)
    if limit:
        query = query.limit(limit)
    res = query.execute()
    return pd.DataFrame(res.data)

# ------------------------------------------------
# 페이지 설정
# ------------------------------------------------
st.set_page_config(page_title="스윙 종목", layout="wide")
st.title("💹 스윙 종목 대시보드")

# ------------------------------------------------
# 데이터 로드
# ------------------------------------------------
show_all = st.toggle("🔍 전체 수익률 보기", value=False)
df = load_returns() if show_all else load_returns(limit=5)

if df.empty:
    st.warning("⚠️ Supabase의 b_return 테이블에 데이터가 없습니다.")
    st.stop()

df["수익률"] = df["수익률"].astype(float)
df["수익률(%)"] = df["수익률"].map("{:.2f}%".format)

# ------------------------------------------------
# 1️⃣ 상위 5개 순위 리스트
# ------------------------------------------------
if not show_all:
    st.subheader("🏆 수익률 상위 5개 종목")

    for i, row in df.iterrows():
        if st.button(f"{i+1}위. {row['종목명']} ({row['종목코드']}) — {row['수익률(%)']}", key=row["종목코드"]):
            st.session_state.selected_code = row["종목코드"]
            st.session_state.selected_name = row["종목명"]
            st.switch_page("pages/stock_detail.py")

# ------------------------------------------------
# 2️⃣ 전체 보기 (AgGrid 클릭 → 이동)
# ------------------------------------------------
else:
    st.subheader("📊 전체 수익률 목록")

    gb = GridOptionsBuilder.from_dataframe(
        df[["종목명", "종목코드", "수익률(%)", "기간", "발생일", "발생일종가", "현재가격"]]
    )
    gb.configure_default_column(resizable=True, sortable=True, filter=True)
    gb.configure_selection("single", use_checkbox=False)  # ✅ 행 클릭 방식
    grid_options = gb.build()

    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True,
        theme="streamlit",
        height=700,
    )

    selected = grid_response["selected_rows"]

    if selected and len(selected) > 0:
        stock = selected[0]
        st.session_state.selected_code = stock["종목코드"]
        st.session_state.selected_name = stock["종목명"]
        st.success(f"👉 {stock['종목명']} ({stock['종목코드']}) 상세 페이지로 이동합니다...")
        st.switch_page("pages/stock_detail.py")

st.markdown("---")
st.caption("💡 행을 클릭하면 해당 종목의 상세 차트 페이지로 이동합니다.")

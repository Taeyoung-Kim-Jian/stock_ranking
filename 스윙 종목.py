# -*- coding: utf-8 -*-
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
# 페이지 설정
# ------------------------------------------------
st.set_page_config(page_title="스윙 종목", layout="wide")
st.title("💹 스윙 종목 대시보드")

# ------------------------------------------------
# 데이터 로딩 함수
# ------------------------------------------------
@st.cache_data(ttl=300)
def load_returns(limit=None):
    query = (
        supabase.table("b_return")
        .select("종목명, 종목코드, 수익률, 발생일, 발생일종가, 현재가격, 기간")
        .order("수익률", desc=True)
    )
    if limit:
        query = query.limit(limit)
    res = query.execute()
    return pd.DataFrame(res.data)

# ------------------------------------------------
# CSS 스타일
# ------------------------------------------------
st.markdown("""
<style>
.rank-item {
    background: linear-gradient(90deg, #ffed91, #ffc300);
    color: #000000;
    padding: 12px 18px;
    border-radius: 10px;
    font-weight: 800;
    font-size: 18px;
    margin-bottom: 10px;
    box-shadow: 1px 1px 4px rgba(0,0,0,0.15);
    cursor: pointer;
}
.rank-item:hover {
    background: linear-gradient(90deg, #fff6b0, #ffd84a);
}
.rank-item span {
    float: right;
    font-weight: 700;
    color: #cc0000;
}
body, p, div {
    font-family: "Segoe UI", "Noto Sans KR", sans-serif;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# 데이터 불러오기
# ------------------------------------------------
show_all = st.toggle("🔍 전체 수익률 보기", value=False)
df = load_returns() if show_all else load_returns(limit=5)

if df.empty:
    st.warning("⚠️ Supabase의 b_return 테이블에 데이터가 없습니다.")
    st.stop()

df["수익률"] = df["수익률"].astype(float)
df["수익률(%)"] = df["수익률"].map("{:.2f}%".format)

# ------------------------------------------------
# 1️⃣ 상위 5개 보기 (메인화면)
# ------------------------------------------------
if not show_all:
    st.subheader("🏆 수익률 상위 5개 종목")

    df_sorted = df.sort_values("수익률", ascending=False).reset_index(drop=True)

    # 종목 클릭 시 이동 기능
    for i, row in df_sorted.iterrows():
        # HTML을 사용해 각 종목에 Streamlit 버튼 생성
        if st.button(f"🔥 {i+1}위: {row['종목명']} ({row['종목코드']}) — {row['수익률(%)']}", key=row['종목코드']):
            st.session_state.selected_code = row["종목코드"]
            st.session_state.selected_name = row["종목명"]
            st.switch_page("pages/stock_detail.py")

# ------------------------------------------------
# 2️⃣ 전체 보기 (행 클릭 시 이동)
# ------------------------------------------------
else:
    st.subheader("📊 전체 수익률 목록 (클릭 시 차트 보기)")

    gb = GridOptionsBuilder.from_dataframe(
        df[["종목명", "종목코드", "수익률(%)", "기간", "발생일", "발생일종가", "현재가격"]]
    )
    gb.configure_default_column(resizable=True, sortable=True, filter=True)
    gb.configure_selection("single", use_checkbox=False)
    grid_options = gb.build()

    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True,
        theme="streamlit",
        height=850,
    )

    selected = grid_response["selected_rows"]
    if isinstance(selected, pd.DataFrame):
        selected = selected.to_dict(orient="records")

    if selected and len(selected) > 0:
        stock = selected[0]
        st.session_state.selected_code = stock["종목코드"]
        st.session_state.selected_name = stock["종목명"]
        st.success(f"👉 {stock['종목명']} ({stock['종목코드']}) 차트로 이동합니다...")
        st.switch_page("pages/stock_detail.py")

# ------------------------------------------------
# 푸터
# ------------------------------------------------
st.markdown("---")
st.caption("💡 상위 5개는 버튼 클릭으로 차트 이동, 전체 보기에서는 행 클릭으로 이동합니다.")

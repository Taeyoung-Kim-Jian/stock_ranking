import streamlit as st
import pandas as pd
from supabase import create_client
from st_aggrid import AgGrid, GridOptionsBuilder

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
    )
    query = query.order("수익률", desc=True)
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
# CSS 스타일 적용
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
# 데이터 로드
# ------------------------------------------------
show_all = st.toggle("🔍 전체 수익률 보기", value=False)

if show_all:
    df = load_returns()
else:
    df = load_returns(limit=5)

if df.empty:
    st.warning("⚠️ Supabase의 b_return 테이블에 데이터가 없습니다.")
    st.stop()

# ------------------------------------------------
# 데이터 전처리
# ------------------------------------------------
df["수익률"] = df["수익률"].astype(float)
df["수익률(%)"] = df["수익률"].map("{:.2f}%".format)

# ------------------------------------------------
# 1️⃣ 상위 5개 순위 리스트
# ------------------------------------------------
if not show_all:
    st.subheader("🏆 수익률 상위 5개 종목")

    df_sorted = df.sort_values("수익률", ascending=False).reset_index(drop=True)

    for i, row in df_sorted.iterrows():
        st.markdown(
            f"""
            <div class="rank-item">
                {i+1}위. <b>{row['종목명']} ({row['종목코드']})</b>
                <span>{row['수익률(%)']}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

# ------------------------------------------------
# 2️⃣ 전체 보기 모드 (스크롤 가능)
# ------------------------------------------------
else:
    st.subheader("📊 전체 수익률 목록")

    gb = GridOptionsBuilder.from_dataframe(
        df[["종목명", "종목코드", "수익률(%)", "기간", "발생일", "발생일종가", "현재가격"]]
    )
    gb.configure_default_column(resizable=True, sortable=True, filter=True)
    gb.configure_grid_options(domLayout="normal")  # ✅ 스크롤 가능하게
    grid_options = gb.build()

    AgGrid(
        df,
        gridOptions=grid_options,
        fit_columns_on_grid_load=True,
        theme="streamlit",
        height=850,  # ✅ 스크롤 가능 높이
    )

st.markdown("---")
st.caption("💡 상위 5개는 수익률 순 정렬 기준이며, 전체 보기에서 모든 종목을 확인할 수 있습니다.")

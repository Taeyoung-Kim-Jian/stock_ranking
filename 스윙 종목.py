# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client

# ------------------------------------------------
# Supabase 연결
# ------------------------------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------------------------------
# 페이지 설정
# ------------------------------------------------
st.set_page_config(page_title="스윙 종목 대시보드", layout="wide")
st.title("💹 스윙 종목 대시보드")

# ------------------------------------------------
# 데이터 로딩 함수
# ------------------------------------------------
@st.cache_data(ttl=300)
def load_returns(category=None, limit=5):
    """Supabase에서 b_return 데이터 로드"""
    query = (
        supabase.table("b_return")
        .select("종목명, 종목코드, 수익률, 발생일, 발생일종가, 현재가격, 기간, 구분")
        .order("수익률", desc=True)
    )

    # 구분값으로 분리 (B0~B2는 눌림 / B3~T는 추격 예시)
    if category == "눌림":
        query = query.like("구분", "B%")
    elif category == "추격":
        query = query.like("구분", "T%")

    query = query.limit(limit)
    res = query.execute()
    return pd.DataFrame(res.data)

# ------------------------------------------------
# CSS 스타일
# ------------------------------------------------
st.markdown("""
<style>
.section-title {
    font-size: 22px;
    font-weight: 800;
    margin-bottom: 10px;
    color: #222;
}
.rank-box {
    background: linear-gradient(90deg, #ffed91, #ffc300);
    color: #000000;
    padding: 12px 18px;
    border-radius: 10px;
    font-weight: 700;
    font-size: 17px;
    margin-bottom: 10px;
    box-shadow: 1px 1px 4px rgba(0,0,0,0.15);
    cursor: pointer;
}
.rank-box:hover {
    background: linear-gradient(90deg, #fff6b0, #ffd84a);
}
.rank-box span {
    float: right;
    font-weight: 700;
    color: #cc0000;
}
body, p, div {
    font-family: "Segoe UI", "Noto Sans KR", sans-serif;
}
.button-row {
    display: flex;
    justify-content: center;
    gap: 15px;
    margin-top: 30px;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# 데이터 불러오기
# ------------------------------------------------
df_pullback = load_returns(category="눌림", limit=5)
df_chase = load_returns(category="추격", limit=5)

if df_pullback.empty and df_chase.empty:
    st.warning("⚠️ Supabase의 b_return 테이블에 데이터가 없습니다.")
    st.stop()

# ------------------------------------------------
# 두 컬럼 레이아웃
# ------------------------------------------------
col1, col2 = st.columns(2)

# ✅ 왼쪽: 눌림 수익률 TOP 5
with col1:
    st.markdown('<div class="section-title">📉 눌림 수익률 TOP 5</div>', unsafe_allow_html=True)
    if not df_pullback.empty:
        df_pullback = df_pullback.sort_values("수익률", ascending=False).reset_index(drop=True)
        for i, row in df_pullback.iterrows():
            if st.button(f"{i+1}위. {row['종목명']} ({row['종목코드']}) — {row['수익률']:.2f}%", key=f"pull_{row['종목코드']}"):
                st.session_state.selected_code = row["종목코드"]
                st.session_state.selected_name = row["종목명"]
                st.switch_page("pages/stock_detail.py")
    else:
        st.info("데이터가 없습니다.")

# ✅ 오른쪽: 추격 수익률 TOP 5
with col2:
    st.markdown('<div class="section-title">🚀 추격 수익률 TOP 5</div>', unsafe_allow_html=True)
    if not df_chase.empty:
        df_chase = df_chase.sort_values("수익률", ascending=False).reset_index(drop=True)
        for i, row in df_chase.iterrows():
            if st.button(f"{i+1}위. {row['종목명']} ({row['종목코드']}) — {row['수익률']:.2f}%", key=f"chase_{row['종목코드']}"):
                st.session_state.selected_code = row["종목코드"]
                st.session_state.selected_name = row["종목명"]
                st.switch_page("pages/stock_detail.py")
    else:
        st.info("데이터가 없습니다.")

# ------------------------------------------------
# 하단 버튼 영역
# ------------------------------------------------
st.markdown('<div class="button-row">', unsafe_allow_html=True)

col_a, col_b, col_c = st.columns(3)
with col_a:
    if st.button("🔍 전체 수익률 보기"):
        st.switch_page("pages/total_returns.py")
with col_b:
    if st.button("📊 눌림 수익률 전체 보기"):
        st.switch_page("pages/pullback_returns.py")
with col_c:
    if st.button("⚡ 추격 수익률 전체 보기"):
        st.switch_page("pages/chase_returns.py")

st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------
# 푸터
# ------------------------------------------------
st.markdown("---")
st.caption("💡 위의 Top5 리스트에서 클릭 시 차트 페이지로 이동합니다. 아래 버튼으로 전체 보기 전환 가능합니다.")

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
st.markdown("<h3 style='text-align:center; margin-bottom:10px;'>💹 스윙 종목 대시보드</h3>", unsafe_allow_html=True)

# ------------------------------------------------
# 데이터 로딩 함수
# ------------------------------------------------
@st.cache_data(ttl=300)
def load_returns():
    query = (
        supabase.table("b_return")
        .select("종목명, 종목코드, 수익률, 발생일, 발생일종가, 현재가격, 기간, 구분")
        .order("수익률", desc=True)
        .limit(5000)
    )
    res = query.execute()
    return pd.DataFrame(res.data)

# ------------------------------------------------
# CSS (모바일에서도 2단, 미니화)
# ------------------------------------------------
st.markdown("""
<style>
:root {
    --card-bg: linear-gradient(90deg, #fff7b3, #ffd84a);
}
.section-container {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    gap: 8px;
}
.section {
    flex: 1 1 48%;
    min-width: 230px;
}
.section-title {
    font-size: 16px;
    font-weight: 800;
    margin-bottom: 6px;
    color: #333;
    text-align: center;
}
.rank-box {
    background: var(--card-bg);
    color: #000;
    padding: 6px 10px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 13px;
    margin-bottom: 6px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    cursor: pointer;
    transition: all 0.25s ease;
}
.rank-box:hover {
    transform: scale(1.02);
    background: linear-gradient(90deg, #fff9c9, #ffde66);
}
.rank-box span {
    float: right;
    color: #d11;
    font-weight: 700;
    font-size: 12px;
}
.button-row {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 8px;
    margin-top: 15px;
}
.stButton>button {
    font-size: 13px !important;
    padding: 4px 10px !important;
}
.stButton>button[disabled] {
    opacity: 0.5 !important;
    pointer-events: none !important;
}
body, p, div {
    font-family: "Noto Sans KR", sans-serif;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# 데이터 불러오기
# ------------------------------------------------
df_all = load_returns()

if df_all.empty:
    st.warning("⚠️ Supabase의 b_return 테이블에 데이터가 없습니다.")
    st.stop()

df_all["수익률"] = df_all["수익률"].astype(float)
df_top5 = df_all.sort_values("수익률", ascending=False).head(5).reset_index(drop=True)
df_bottom5 = df_all.sort_values("수익률", ascending=True).head(5).reset_index(drop=True)

# ------------------------------------------------
# 반응형 2단 카드 레이아웃
# ------------------------------------------------
st.markdown('<div class="section-container">', unsafe_allow_html=True)

# 상위 5개
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📈 수익률 상위 5개 (눌림형)</div>', unsafe_allow_html=True)
for i, row in df_top5.iterrows():
    if st.button(f"{i+1}위. {row['종목명']} ({row['종목코드']})", key=f"top_{row['종목코드']}"):
        st.session_state.selected_code = row["종목코드"]
        st.session_state.selected_name = row["종목명"]
        st.switch_page("pages/stock_detail.py")
    st.markdown(f"<div class='rank-box'>{row['종목명']} <span>{row['수익률']:.2f}%</span></div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# 하위 5개
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📉 수익률 하위 5개 (추격형)</div>', unsafe_allow_html=True)
for i, row in df_bottom5.iterrows():
    if st.button(f"{i+1}위. {row['종목명']} ({row['종목코드']})", key=f"bottom_{row['종목코드']}"):
        st.session_state.selected_code = row["종목코드"]
        st.session_state.selected_name = row["종목명"]
        st.switch_page("pages/stock_detail.py")
    st.markdown(f"<div class='rank-box'>{row['종목명']} <span>{row['수익률']:.2f}%</span></div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------
# 하단 버튼 (비활성화)
# ------------------------------------------------
st.markdown('<div class="button-row">', unsafe_allow_html=True)
cols = st.columns(3)
with cols[0]:
    st.button("🔍 전체 수익률 보기", disabled=True)
with cols[1]:
    st.button("📊 눌림 수익률 전체 보기", disabled=True)
with cols[2]:
    st.button("⚡ 추격 수익률 전체 보기", disabled=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.caption("📱 모바일에서도 좌우 2단으로 표시되며, 글씨와 카드 크기를 줄여 가독성을 높였습니다.")

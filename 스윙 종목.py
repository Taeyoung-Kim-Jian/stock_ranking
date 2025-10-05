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
st.set_page_config(page_title="스윙 종목", layout="wide")
st.markdown("<h3 style='text-align:center; margin-bottom:10px;'>💹 스윙 종목</h3>", unsafe_allow_html=True)

# ------------------------------------------------
# 데이터 로딩
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

df_all = load_returns()
if df_all.empty:
    st.warning("⚠️ Supabase의 b_return 테이블에 데이터가 없습니다.")
    st.stop()

df_all["수익률"] = df_all["수익률"].astype(float)
df_top5 = df_all.sort_values("수익률", ascending=False).head(5).reset_index(drop=True)
df_bottom5 = df_all.sort_values("수익률", ascending=True).head(5).reset_index(drop=True)

# ------------------------------------------------
# CSS — PC/Mobile 둘 다 2단 유지 (Grid 기반)
# ------------------------------------------------
st.markdown("""
<style>
body, div, p {
    font-family: 'Noto Sans KR', sans-serif;
}
.grid-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    width: 100%;
    align-items: start;
}
@media (max-width: 768px) {
    .grid-container {
        grid-template-columns: 1fr 1fr;  /* ✅ 모바일에서도 좌우 유지 */
        gap: 6px;
        transform: scale(0.9); /* 화면 좁을 때 자동 축소 */
    }
}
.section {
    background-color: white;
    border-radius: 10px;
    padding: 6px;
    box-sizing: border-box;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.section-title {
    font-size: 15px;
    font-weight: 800;
    text-align: center;
    color: #333;
    margin-bottom: 8px;
}
.rank-box {
    background: linear-gradient(90deg, #fff9c9, #ffd84a);
    color: #000;
    padding: 6px 10px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 12px;
    margin-bottom: 6px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    cursor: pointer;
    transition: transform 0.2s ease;
}
.rank-box:hover {
    transform: scale(1.04);
    background: linear-gradient(90deg, #fffedb, #ffeb6d);
}
.rank-box span {
    float: right;
    color: #c00;
    font-weight: 700;
}
.button-row {
    display: flex;
    justify-content: center;
    gap: 10px;
    margin-top: 15px;
}
.stButton>button {
    font-size: 13px !important;
    padding: 5px 12px !important;
}
.stButton>button[disabled] {
    opacity: 0.5 !important;
    pointer-events: none !important;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# 2단 고정 Grid Layout
# ------------------------------------------------
st.markdown('<div class="grid-container">', unsafe_allow_html=True)

# 상위 5개
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📈 수익률 상위 5개 (눌림형)</div>', unsafe_allow_html=True)
for i, row in df_top5.iterrows():
    if st.button(f"{i+1}위. {row['종목명']} ({row['종목코드']})", key=f"top_{row['종목코드']}"):
        st.session_state.selected_code = row["종목코드"]
        st.session_state.selected_name = row["종목명"]
        st.switch_page("pages/stock_detail.py")
    st.markdown(
        f"<div class='rank-box'>{row['종목명']} <span>{row['수익률']:.2f}%</span></div>",
        unsafe_allow_html=True,
    )
st.markdown('</div>', unsafe_allow_html=True)

# 하위 5개
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📉 수익률 하위 5개 (추격형)</div>', unsafe_allow_html=True)
for i, row in df_bottom5.iterrows():
    if st.button(f"{i+1}위. {row['종목명']} ({row['종목코드']})", key=f"bottom_{row['종목코드']}"):
        st.session_state.selected_code = row["종목코드"]
        st.session_state.selected_name = row["종목명"]
        st.switch_page("pages/stock_detail.py")
    st.markdown(
        f"<div class='rank-box'>{row['종목명']} <span>{row['수익률']:.2f}%</span></div>",
        unsafe_allow_html=True,
    )
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------
# 하단 버튼 (비활성화)
# ------------------------------------------------
st.markdown("<hr>", unsafe_allow_html=True)
cols = st.columns(3)
with cols[0]:
    st.button("🔍 전체 수익률 보기", disabled=True)
with cols[1]:
    st.button("📊 눌림 수익률 전체 보기", disabled=True)
with cols[2]:
    st.button("⚡ 추격 수익률 전체 보기", disabled=True)

st.markdown("<hr>", unsafe_allow_html=True)
st.caption("📱 PC와 모바일 모두 좌우 2단 구조로 고정되어 표시됩니다.")



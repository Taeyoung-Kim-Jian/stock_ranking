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
st.markdown("<h4 style='text-align:center;'>💹 스윙 종목 대시보드</h4>", unsafe_allow_html=True)

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
# CSS (반응형 flex 2단 구조 + 모바일 유지)
# ------------------------------------------------
st.markdown("""
<style>
body, div, p {
    font-family: 'Noto Sans KR', sans-serif;
}
.flex-container {
    display: flex;
    justify-content: space-between;
    gap: 8px;
    width: 100%;
    flex-wrap: nowrap;
}
.flex-column {
    flex: 1;
    min-width: 0;
    background: #fff;
}
@media (max-width: 768px) {
    .flex-container {
        display: flex;
        flex-direction: row; /* 📱 모바일에서도 좌우 유지 */
        overflow-x: auto; /* 좌우 스크롤 허용 */
    }
    .flex-column {
        flex: 0 0 48%; /* 모바일에서 반씩 */
        min-width: 48%;
    }
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
    padding: 6px 8px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 12px;
    margin-bottom: 6px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    transition: transform 0.2s ease;
    cursor: pointer;
    white-space: nowrap;
}
.rank-box:hover {
    transform: scale(1.03);
    background: linear-gradient(90deg, #fffedb, #ffeb6d);
}
.rank-box span {
    float: right;
    color: #d11;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# HTML 구조 (모바일/PC 모두 2단)
# ------------------------------------------------
st.markdown("<div class='flex-container'>", unsafe_allow_html=True)

# ✅ 왼쪽 컬럼
st.markdown("<div class='flex-column'>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>📈 수익률 상위 5개 (눌림형)</div>", unsafe_allow_html=True)
for i, row in df_top5.iterrows():
    if st.button(f"{i+1}위. {row['종목명']} ({row['수익률']:.2f}%)", key=f"top_{row['종목코드']}"):
        st.session_state.selected_code = row["종목코드"]
        st.session_state.selected_name = row["종목명"]
        st.switch_page("pages/stock_detail.py")
st.markdown("</div>", unsafe_allow_html=True)

# ✅ 오른쪽 컬럼
st.markdown("<div class='flex-column'>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>📉 수익률 하위 5개 (추격형)</div>", unsafe_allow_html=True)
for i, row in df_bottom5.iterrows():
    if st.button(f"{i+1}위. {row['종목명']} ({row['수익률']:.2f}%)", key=f"bottom_{row['종목코드']}"):
        st.session_state.selected_code = row["종목코드"]
        st.session_state.selected_name = row["종목명"]
        st.switch_page("pages/stock_detail.py")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------------
# 하단 버튼
# ------------------------------------------------
st.markdown("---")
cols = st.columns(3)
with cols[0]:
    st.button("🔍 전체 수익률 보기", disabled=True)
with cols[1]:
    st.button("📊 눌림 수익률 전체 보기", disabled=True)
with cols[2]:
    st.button("⚡ 추격 수익률 전체 보기", disabled=True)
st.markdown("---")
st.caption("💡 PC와 모바일 모두 좌우 2단(가로 스크롤 포함)으로 표시됩니다.")

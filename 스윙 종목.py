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
def load_returns(limit=5):
    """Supabase에서 b_return 데이터 로드"""
    query = (
        supabase.table("b_return")
        .select("종목명, 종목코드, 수익률, 발생일, 발생일종가, 현재가격, 기간, 구분")
        .order("수익률", desc=True)
        .limit(5000)
    )
    res = query.execute()
    return pd.DataFrame(res.data)

# ------------------------------------------------
# CSS 스타일 (반응형 포함)
# ------------------------------------------------
st.markdown("""
<style>
:root {
    --card-bg: linear-gradient(90deg, #ffed91, #ffc300);
    --card-hover: linear-gradient(90deg, #fff6b0, #ffd84a);
}
.section-container {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    gap: 10px;
}
.section {
    flex: 1 1 48%;
    min-width: 320px;
    background-color: #fff;
}
.section-title {
    font-size: 20px;
    font-weight: 800;
    margin-bottom: 10px;
    color: #222;
}
.rank-box {
    background: var(--card-bg);
    color: #000000;
    padding: 12px 18px;
    border-radius: 10px;
    font-weight: 700;
    font-size: 16px;
    margin-bottom: 10px;
    box-shadow: 1px 1px 4px rgba(0,0,0,0.15);
    cursor: pointer;
    transition: background 0.3s ease;
}
.rank-box:hover {
    background: var(--card-hover);
}
.rank-box span {
    float: right;
    font-weight: 700;
    color: #cc0000;
}
.button-row {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 10px;
    margin-top: 25px;
}
button[disabled], .stButton>button[disabled] {
    opacity: 0.5 !important;
    pointer-events: none !important;
}
@media (max-width: 768px) {
    .section {
        flex: 1 1 100%;
    }
    .section-title {
        text-align: center;
    }
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
# 반응형 2단 레이아웃 (HTML Flexbox)
# ------------------------------------------------
st.markdown('<div class="section-container">', unsafe_allow_html=True)

# 왼쪽 - 상위 5개
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📈 수익률 상위 5개 (눌림형)</div>', unsafe_allow_html=True)
for i, row in df_top5.iterrows():
    if st.button(f"{i+1}. {row['종목명']} — {row['수익률']:.2f}%", key=f"top_{row['종목코드']}"):
        st.session_state.selected_code = row["종목코드"]
        st.session_state.selected_name = row["종목명"]
        st.switch_page("pages/stock_detail.py")
st.markdown('</div>', unsafe_allow_html=True)

# 오른쪽 - 하위 5개
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📉 수익률 하위 5개 (추격형)</div>', unsafe_allow_html=True)
for i, row in df_bottom5.iterrows():
    if st.button(f"{i+1}. {row['종목명']} — {row['수익률']:.2f}%", key=f"bottom_{row['종목코드']}"):
        st.session_state.selected_code = row["종목코드"]
        st.session_state.selected_name = row["종목명"]
        st.switch_page("pages/stock_detail.py")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)  # section-container 닫기

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
st.caption("📱 모바일에서도 좌우로 자동 정렬되며, 클릭 시 차트로 이동합니다.")



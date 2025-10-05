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
# CSS: 글씨/카드 작게 + 모바일 반응형
# ------------------------------------------------
st.markdown("""
<style>
body, div, p {
    font-family: 'Noto Sans KR', sans-serif;
}
.section-title {
    font-size: 15px;
    font-weight: 800;
    text-align: center;
    color: #333;
    margin-bottom: 6px;
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
.stButton>button {
    font-size: 12px !important;
    padding: 5px 10px !important;
}
@media (max-width: 768px) {
    .section-title {
        font-size: 14px;
    }
    .rank-box {
        font-size: 11px;
        padding: 5px 6px;
    }
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# 2단 컬럼 — Streamlit 기본 레이아웃
# ------------------------------------------------
col1, col2 = st.columns(2)

# ✅ 왼쪽: 수익률 상위 5개
with col1:
    st.markdown('<div class="section-title">📈 수익률 상위 5개 (눌림형)</div>', unsafe_allow_html=True)
    for i, row in df_top5.iterrows():
        st.markdown(
            f"<div class='rank-box' onclick=\"window.parent.postMessage({{type: 'streamlit:setComponentValue', value: '{row['종목코드']}' }}, '*');\">"
            f"{i+1}위. {row['종목명']} <span>{row['수익률']:.2f}%</span></div>",
            unsafe_allow_html=True,
        )
        if st.button(f"{row['종목명']} ({row['종목코드']})", key=f"top_{row['종목코드']}"):
            st.session_state.selected_code = row["종목코드"]
            st.session_state.selected_name = row["종목명"]
            st.switch_page("pages/stock_detail.py")

# ✅ 오른쪽: 수익률 하위 5개
with col2:
    st.markdown('<div class="section-title">📉 수익률 하위 5개 (추격형)</div>', unsafe_allow_html=True)
    for i, row in df_bottom5.iterrows():
        st.markdown(
            f"<div class='rank-box' onclick=\"window.parent.postMessage({{type: 'streamlit:setComponentValue', value: '{row['종목코드']}' }}, '*');\">"
            f"{i+1}위. {row['종목명']} <span>{row['수익률']:.2f}%</span></div>",
            unsafe_allow_html=True,
        )
        if st.button(f"{row['종목명']} ({row['종목코드']})", key=f"bottom_{row['종목코드']}"):
            st.session_state.selected_code = row["종목코드"]
            st.session_state.selected_name = row["종목명"]
            st.switch_page("pages/stock_detail.py")

# ------------------------------------------------
# 하단 버튼 (비활성화)
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
st.caption("💡 PC와 모바일 모두 좌우 2단 구조로 자동 맞춤 표시됩니다.")

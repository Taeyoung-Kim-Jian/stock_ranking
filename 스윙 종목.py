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
st.markdown("<h4 style='text-align:center;'>💹 스윙 종목 TOP5 대시보드</h4>", unsafe_allow_html=True)

# ------------------------------------------------
# 데이터 로딩
# ------------------------------------------------
@st.cache_data(ttl=300)
def load_returns():
    query = (
        supabase.table("b_return")
        .select("종목명, 종목코드, 수익률, 발생일, 구분")
        .order("수익률", desc=True)
        .limit(5000)
    )
    res = query.execute()
    return pd.DataFrame(res.data)

df_all = load_returns()
if df_all.empty:
    st.warning("⚠️ Supabase의 b_return 테이블에 데이터가 없습니다.")
    st.stop()

# ------------------------------------------------
# 데이터 샘플 구성 (가상 데이터 포함)
# ------------------------------------------------
df_all["수익률"] = df_all["수익률"].astype(float)
domestic_top5 = df_all.sort_values("수익률", ascending=False).head(5).reset_index(drop=True)
domestic_bottom5 = df_all.sort_values("수익률", ascending=True).head(5).reset_index(drop=True)

# 가상 데이터 (예시용)
foreign_top5 = pd.DataFrame({
    "종목명": ["Apple", "Nvidia", "Microsoft", "Tesla", "Amazon"],
    "수익률": [15.4, 13.2, 11.8, 10.6, 9.9]
})
foreign_bottom5 = pd.DataFrame({
    "종목명": ["Intel", "Cisco", "AT&T", "Pfizer", "IBM"],
    "수익률": [-3.5, -4.1, -5.0, -6.8, -8.2]
})

# ------------------------------------------------
# CSS 스타일 정의
# ------------------------------------------------
st.markdown("""
<style>
body, div, p {
    font-family: 'Noto Sans KR', sans-serif;
}
.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
    gap: 16px;
    width: 100%;
}
.card {
    background: linear-gradient(135deg, #fff8cc, #ffd966);
    border-radius: 12px;
    padding: 14px 16px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    transition: transform 0.15s ease, box-shadow 0.25s ease;
}
.card:hover {
    transform: scale(1.02);
    box-shadow: 0 4px 10px rgba(0,0,0,0.25);
}
.card-title {
    font-size: 15px;
    font-weight: 800;
    color: #b35a00;
    margin-bottom: 8px;
    text-align: center;
}
.card-item {
    font-size: 13px;
    color: #333;
    padding: 3px 0;
    border-bottom: 1px dashed rgba(0,0,0,0.1);
}
.card-item b {
    color: #c75000;
}
.card-item span {
    float: right;
    color: #333;
    font-weight: 600;
}
@media (max-width: 768px) {
    .dashboard-grid {
        grid-template-columns: repeat(2, 1fr); /* ✅ 모바일에서도 2단 유지 */
    }
    .card {
        padding: 10px;
    }
    .card-item {
        font-size: 12px;
    }
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# 카드 생성 함수
# ------------------------------------------------
def make_card(title, df):
    html = f"<div class='card'><div class='card-title'>{title}</div>"
    for i, row in df.iterrows():
        html += f"<div class='card-item'><b>{i+1}위. {row['종목명']}</b><span>{row['수익률']:.2f}%</span></div>"
    html += "</div>"
    return html

# ------------------------------------------------
# 4개 카드 표시
# ------------------------------------------------
cards_html = """
<div class='dashboard-grid'>
    {0}
    {1}
    {2}
    {3}
</div>
""".format(
    make_card("🇰🇷 국내 눌림 상위 TOP5", domestic_top5),
    make_card("🇰🇷 국내 눌림 하위 TOP5", domestic_bottom5),
    make_card("🌎 해외 성장 상위 TOP5", foreign_top5),
    make_card("🌎 해외 성장 하위 TOP5", foreign_bottom5)
)

st.markdown(cards_html, unsafe_allow_html=True)

# ------------------------------------------------
# 하단 안내
# ------------------------------------------------
st.markdown("---")
st.caption("💡 각 카드에는 상위/하위 5개 종목이 표시됩니다. 모바일에서도 2단 레이아웃으로 자동 조정됩니다.")

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

# ------------------------------------------------
# 상단 스크롤형 한글 네비게이션 바
# ------------------------------------------------
st.markdown("""
<style>
.scroll-nav {
    display: flex;
    overflow-x: auto;
    white-space: nowrap;
    gap: 12px;
    padding: 6px 8px;
    margin-top: -5px;
    margin-bottom: 14px;
    scrollbar-width: thin;
    scrollbar-color: #ccc transparent;
}
.scroll-nav::-webkit-scrollbar {
    height: 6px;
}
.scroll-nav::-webkit-scrollbar-thumb {
    background-color: #bbb;
    border-radius: 4px;
}
.scroll-nav::-webkit-scrollbar-track {
    background: transparent;
}
.icon-btn {
    display: inline-block;
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 6px 14px;
    font-size: 13px;
    font-weight: 600;
    text-decoration: none;
    color: #333;
    flex-shrink: 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    transition: all 0.2s ease;
}
.icon-btn:hover {
    transform: scale(1.05);
    background: #ffe9c4;
    border-color: #f0b400;
    color: #b35a00;
}
@media (max-width: 768px) {
    .icon-btn {
        font-size: 12px;
        padding: 6px 12px;
    }
}
</style>

<div class="scroll-nav">
    <a href="?page=국내눌림" class="icon-btn">메인</a>
    <a href="?page=국내눌림" class="icon-btn">🟠 국내 눌림</a>
    <a href="?page=국내추격" class="icon-btn">🔵 국내 추격</a>
    <a href="?page=해외눌림" class="icon-btn">🟢 해외 눌림</a>
    <a href="?page=해외추격" class="icon-btn">🔴 해외 추격</a>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------
# 페이지 타이틀
# ------------------------------------------------
st.markdown("<h4 style='text-align:center; margin-bottom:0;'>💹 스윙 종목 TOP5 대시보드</h4>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-size:13px; color:gray; margin-top:2px;'>카테고리를 선택하여 세부 페이지로 이동하세요.</p>", unsafe_allow_html=True)

st.markdown("---")

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
# 데이터 구성
# ------------------------------------------------
df_all["수익률"] = df_all["수익률"].astype(float)
domestic_top5 = df_all.sort_values("수익률", ascending=False).head(5).reset_index(drop=True)
domestic_bottom5 = df_all.sort_values("수익률", ascending=True).head(5).reset_index(drop=True)

foreign_top5 = pd.DataFrame({
    "종목명": ["Apple", "Nvidia", "Microsoft", "Tesla", "Amazon"],
    "수익률": [15.4, 13.2, 11.8, 10.6, 9.9]
})
foreign_bottom5 = pd.DataFrame({
    "종목명": ["Intel", "Cisco", "AT&T", "Pfizer", "IBM"],
    "수익률": [-3.5, -4.1, -5.0, -6.8, -8.2]
})

# ------------------------------------------------
# 카드 CSS
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
        grid-template-columns: repeat(2, 1fr);
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
# 카드 4개 표시
# ------------------------------------------------
cards_html = f"""
<div class='dashboard-grid'>
    {make_card("🟠 국내 눌림 상위 TOP5", domestic_top5)}
    {make_card("🟠 국내 눌림 하위 TOP5", domestic_bottom5)}
    {make_card("🟢 해외 성장 상위 TOP5", foreign_top5)}
    {make_card("🟢 해외 성장 하위 TOP5", foreign_bottom5)}
</div>
"""
st.markdown(cards_html, unsafe_allow_html=True)

# ------------------------------------------------
# 하단 안내
# ------------------------------------------------
st.markdown("---")
st.caption("💡 상단 스크롤 네비게이션으로 페이지를 선택하세요. (모바일: 손가락으로 좌우 스크롤 가능)")

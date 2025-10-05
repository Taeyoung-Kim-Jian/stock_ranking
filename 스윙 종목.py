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
# 스크롤 가능한 네비게이션 바 (Streamlit 버튼 + 내부 이동)
# ------------------------------------------------
st.markdown("""
<style>
.scroll-container {
    display: flex;
    overflow-x: auto;
    white-space: nowrap;
    padding: 6px 4px;
    gap: 10px;
    margin-top: -8px;
    margin-bottom: 10px;
    scrollbar-width: thin;
    scrollbar-color: #bbb transparent;
}
.scroll-container::-webkit-scrollbar {
    height: 6px;
}
.scroll-container::-webkit-scrollbar-thumb {
    background-color: #bbb;
    border-radius: 3px;
}
.scroll-item {
    flex: 0 0 auto;
}
.stButton>button {
    border-radius: 10px;
    border: 1px solid #ddd;
    background-color: white;
    color: #333;
    font-size: 13px;
    font-weight: 600;
    padding: 6px 14px;
    transition: all 0.2s ease;
}
.stButton>button:hover {
    background-color: #ffe9c4;
    border-color: #f0b400;
    color: #b35a00;
    transform: scale(1.05);
}
@media (max-width: 768px) {
    .stButton>button {
        font-size: 12px;
        padding: 6px 10px;
    }
}
</style>
""", unsafe_allow_html=True)

# 버튼 구성
nav_items = [
    ("🟠 국내 눌림", "pages/국내눌림.py"),
    ("🔵 국내 추격", "pages/국내추격.py"),
    ("🟢 해외 눌림", "pages/해외눌림.py"),
    ("🔴 해외 추격", "pages/해외추격.py"),
]

# 버튼을 스크롤 가능한 div 안에 배치
st.markdown('<div class="scroll-container">', unsafe_allow_html=True)
cols = st.columns(len(nav_items))
for i, (label, path) in enumerate(nav_items):
    with cols[i]:
        if st.button(label, key=f"nav_{i}", use_container_width=True):
            st.switch_page(path)
st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------
# 타이틀
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
# 카드 스타일
# ------------------------------------------------
st.markdown("""
<style>
.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
    gap: 16px;
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
    text-align: center;
    margin-bottom: 8px;
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
# 카드 표시
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
st.caption("💡 상단 스크롤 네비게이션 바를 이용해 페이지를 이동할 수 있습니다. (모바일은 손가락으로 좌우 스크롤 가능)")

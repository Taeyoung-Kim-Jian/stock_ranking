# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from supabase import create_client

# ------------------------------------------------
# 환경 변수 및 Supabase 연결
# ------------------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Supabase 환경변수(SUPABASE_URL, SUPABASE_KEY)가 설정되지 않았습니다.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------------------------------
# 페이지 설정
# ------------------------------------------------
st.set_page_config(page_title="스윙 종목 대시보드", layout="wide")

# ------------------------------------------------
# ✅ 상단 네비게이션
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
.scroll-nav::-webkit-scrollbar {height: 6px;}
.scroll-nav::-webkit-scrollbar-thumb {background-color: #bbb; border-radius: 4px;}
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
    .icon-btn {font-size: 12px; padding: 6px 12px;}
}
</style>
""", unsafe_allow_html=True)

col_nav = st.columns(5)
with col_nav[0]:
    if st.button("🏠 메인", use_container_width=True):
        st.switch_page("app.py")
with col_nav[1]:
    if st.button("🟠 국내 눌림", use_container_width=True):
        st.switch_page("pages/한국 눌림 종목.py")
with col_nav[2]:
    if st.button("🔵 국내 추격", use_container_width=True):
        st.switch_page("pages/한국 돌파 종목.py")
with col_nav[3]:
    if st.button("🟢 해외 눌림", use_container_width=True):
        st.switch_page("pages/해외 눌림 종목.py")
with col_nav[4]:
    if st.button("🔴 해외 추격", use_container_width=True):
        st.switch_page("pages/해외 돌파 종목.py")

st.markdown("---")

# ------------------------------------------------
# 타이틀
# ------------------------------------------------
st.markdown("<h4 style='text-align:center; margin-bottom:0;'>💹 스윙 종목 TOP5 대시보드</h4>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-size:13px; color:gray; margin-top:2px;'>카테고리를 선택하여 세부 페이지로 이동하세요.</p>", unsafe_allow_html=True)
st.markdown("---")

# ------------------------------------------------
# 데이터 로딩 (종목명, 수익률만 불러오기)
# ------------------------------------------------
@st.cache_data(ttl=300)
def load_returns():
    try:
        query = (
            supabase.table("total_return")
            .select("종목명, 수익률")
            .order("수익률", desc=True)
            .limit(5000)
        )
        res = query.execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"❌ Supabase 쿼리 오류 발생: {e}")
        return pd.DataFrame()

df_all = load_returns()
if df_all.empty:
    st.warning("⚠️ Supabase의 total_return 테이블에 데이터가 없습니다.")
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
# 카드 디자인
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
.card:hover {transform: scale(1.02); box-shadow: 0 4px 10px rgba(0,0,0,0.25);}
.card-title {font-size: 15px; font-weight: 800; color: #b35a00; text-align: center;}
.card-item {font-size: 13px; color: #333; padding: 3px 0; border-bottom: 1px dashed rgba(0,0,0,0.1);}
.card-item b {color: #c75000;}
.card-item span {float: right; font-weight: 600;}
@media (max-width: 768px) {.dashboard-grid {grid-template-columns: repeat(2, 1fr);}}
</style>
""", unsafe_allow_html=True)

def make_card(title, df):
    html = f"<div class='card'><div class='card-title'>{title}</div>"
    for i, row in df.iterrows():
        html += f"<div class='card-item'><b>{i+1}위. {row['종목명']}</b><span>{row['수익률']:.2f}%</span></div>"
    html += "</div>"
    return html

cards_html = f"""
<div class='dashboard-grid'>
    {make_card("🟠 국내 스윙 상위 TOP5", domestic_top5)}
    {make_card("🟠 국내 스윙 하위 TOP5", domestic_bottom5)}
    {make_card("🟢 해외 성장 상위 TOP5", foreign_top5)}
    {make_card("🟢 해외 성장 하위 TOP5", foreign_bottom5)}
</div>
"""
st.markdown(cards_html, unsafe_allow_html=True)

st.markdown("---")
st.caption("💡 상단 스크롤 네비게이션으로 페이지를 선택하세요. (모바일에서도 좌우 스크롤 가능)")

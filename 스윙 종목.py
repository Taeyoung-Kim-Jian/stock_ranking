import streamlit as st

st.set_page_config(layout="wide")

st.markdown("""
<style>
body, div {
  font-family: 'Noto Sans KR', sans-serif;
}
.card-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}
.card {
  background: linear-gradient(135deg, #fff4cc, #ffd966);
  padding: 10px;
  border-radius: 10px;
  font-size: 12px;
  text-align: center;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}
.card b {
  color: #c75000;
  display: block;
  font-size: 13px;
  margin-bottom: 2px;
}
.card span {
  color: #444;
  font-size: 11px;
}
@media (max-width: 600px) {
  .card-container {
    grid-template-columns: repeat(2, 1fr); /* ✅ 모바일에서도 2단 유지 */
  }
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h5 style='text-align:center;'>📈 수익률 상위 5개</h5>", unsafe_allow_html=True)

cards_html = """
<div class='card-container'>
  <div class='card'><b>1위. 삼성전자</b><span>+12.4%</span></div>
  <div class='card'><b>2위. LG화학</b><span>+9.7%</span></div>
  <div class='card'><b>3위. 카카오</b><span>+8.2%</span></div>
  <div class='card'><b>4위. NAVER</b><span>+6.9%</span></div>
  <div class='card'><b>5위. 현대차</b><span>+6.5%</span></div>
</div>
"""
st.markdown(cards_html, unsafe_allow_html=True)

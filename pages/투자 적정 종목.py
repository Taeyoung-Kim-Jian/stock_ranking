# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from supabase import create_client

# ------------------------------------------------
# Supabase 연결
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
st.set_page_config(page_title="투자 적정 종목", layout="wide")

st.markdown("<h4 style='text-align:center;'>💰 투자 적정 구간 종목 리스트</h4>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray; font-size:13px;'>현재가격이 b가격 ±5% 이내인 종목입니다. 클릭하면 차트 페이지로 이동합니다.</p>", unsafe_allow_html=True)
st.markdown("---")

# ------------------------------------------------
# 데이터 로딩
# ------------------------------------------------
@st.cache_data(ttl=300)
def load_via_join():
    try:
        bt = supabase.table("bt_points").select("종목코드, b가격").execute()
        tt = supabase.table("total_return").select("종목명, 종목코드, 현재가격").execute()

        df_b = pd.DataFrame(bt.data)
        df_t = pd.DataFrame(tt.data)
        if df_b.empty or df_t.empty:
            return pd.DataFrame()

        df = pd.merge(df_b, df_t, on="종목코드", how="inner")
        df["변동률"] = ((df["현재가격"] - df["b가격"]) / df["b가격"] * 100).round(2)
        df = df[(df["현재가격"] >= df["b가격"] * 0.95) & (df["현재가격"] <= df["b가격"] * 1.05)]
        df = df.sort_values("변동률", ascending=True)
        return df[["종목명", "종목코드", "b가격", "현재가격", "변동률"]]
    except Exception as e:
        st.error(f"❌ 데이터 병합 중 오류: {e}")
        return pd.DataFrame()

df = load_via_join()
if df.empty:
    st.warning("⚠️ 현재 b가격 ±5% 이내의 종목이 없습니다.")
    st.stop()

# ------------------------------------------------
# CSS 스타일 (테이블을 예쁘게)
# ------------------------------------------------
st.markdown("""
<style>
.table-container {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 16px;
    margin-top: 10px;
}
.stock-card {
    background: linear-gradient(145deg, #ffffff, #f8f8f8);
    border: 1px solid #e6e6e6;
    border-radius: 12px;
    padding: 14px 16px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    cursor: pointer;
}
.stock-card:hover {
    transform: scale(1.03);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.stock-name {
    font-size: 15px;
    font-weight: 700;
    color: #333;
    margin-bottom: 6px;
}
.stock-info {
    font-size: 13px;
    line-height: 1.6;
    color: #444;
}
.stock-info span {
    float: right;
    font-weight: 600;
}
.positive { color: #d32f2f; }
.negative { color: #1976d2; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# 카드형 테이블 렌더링
# ------------------------------------------------
st.markdown("<div class='table-container'>", unsafe_allow_html=True)

for _, row in df.iterrows():
    color_class = "positive" if row["변동률"] > 0 else "negative"
    html = f"""
    <div class='stock-card' onclick="window.location.href='/stock_detail'">
        <div class='stock-name'>{row['종목명']}</div>
        <div class='stock-info'>b가격 <span>{row['b가격']:,}원</span></div>
        <div class='stock-info'>현재가격 <span>{row['현재가격']:,}원</span></div>
        <div class='stock-info'>변동률 <span class='{color_class}'>{row['변동률']:.2f}%</span></div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.caption("💡 b가격 ±5% 구간에 위치한 종목은 매수/매도 균형 구간으로 해석할 수 있습니다.")

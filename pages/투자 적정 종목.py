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
    st.error("❌ Supabase 환경변수가 없습니다.")
    st.stop()
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------------------------------
# 페이지 설정
# ------------------------------------------------
st.set_page_config(page_title="투자 적정 종목", layout="wide")
st.markdown("<h4 style='text-align:center;'>💰 투자 적정 구간 종목 리스트</h4>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray;'>현재가격이 b가격 ±5% 이내인 종목입니다. 클릭하면 차트로 이동합니다.</p>", unsafe_allow_html=True)
st.markdown("---")

# ------------------------------------------------
# 데이터 로드
# ------------------------------------------------
@st.cache_data(ttl=300)
def load_via_join():
    try:
        bt = supabase.table("bt_points").select("종목코드, b가격").execute()
        tt = supabase.table("total_return").select("종목명, 종목코드, 현재가격").execute()
        df_b, df_t = pd.DataFrame(bt.data), pd.DataFrame(tt.data)
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
# 카드 스타일
# ------------------------------------------------
st.markdown("""
<style>
.table-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
    gap: 14px;
    margin-top: 10px;
}
.card {
    background: linear-gradient(145deg, #fff, #f8f8f8);
    border: 1px solid #e5e5e5;
    border-radius: 12px;
    padding: 14px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    transition: transform 0.2s, box-shadow 0.2s;
}
.card:hover {
    transform: scale(1.03);
    box-shadow: 0 4px 10px rgba(0,0,0,0.15);
}
.card-title {
    font-size: 15px; font-weight: 700; color: #333;
}
.card-info {
    font-size: 13px; color: #555; line-height: 1.5;
}
.positive { color: #d32f2f; }
.negative { color: #1976d2; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# 카드형 UI + 클릭 이동
# ------------------------------------------------
st.markdown("<div class='table-grid'>", unsafe_allow_html=True)

for _, row in df.iterrows():
    # 카드 내부 HTML 렌더링
    color = "positive" if row["변동률"] > 0 else "negative"
    with st.container():
        col = st.columns([1])
        with col[0]:
            if st.button(f"📈 {row['종목명']}", key=row["종목코드"]):
                st.session_state["selected_stock"] = row["종목명"]
                st.switch_page("pages/stock_detail.py")
            st.markdown(
                f"""
                <div class='card'>
                    <div class='card-title'>{row['종목명']}</div>
                    <div class='card-info'>b가격 <span>{row['b가격']:,}원</span></div>
                    <div class='card-info'>현재가격 <span>{row['현재가격']:,}원</span></div>
                    <div class='card-info'>변동률 <span class='{color}'>{row['변동률']:.2f}%</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("---")
st.caption("💡 b가격 ±5% 구간은 매수·매도 균형 영역으로 해석할 수 있습니다.")

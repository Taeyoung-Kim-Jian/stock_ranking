# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from supabase import create_client
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

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
# AgGrid 스타일 및 설정
# ------------------------------------------------
# 1️⃣ 수익률 색상 강조 (JS 코드)
cell_style_jscode = JsCode("""
function(params) {
    if (params.value > 0) {
        return {color: 'red', fontWeight: 'bold'};
    } else if (params.value < 0) {
        return {color: 'blue', fontWeight: 'bold'};
    } else {
        return {color: 'black'};
    }
}
""")

# 2️⃣ Grid 옵션 구성
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(resizable=True, sortable=True, filter=True, cellStyle={'fontSize': '13px', 'fontFamily': 'Pretendard, sans-serif'})
gb.configure_column("변동률", cellStyle=cell_style_jscode)  # 색상 강조
gb.configure_selection(selection_mode="single", use_checkbox=False)
gb.configure_grid_options(domLayout='normal', rowHeight=35)

grid_options = gb.build()

# ------------------------------------------------
# AgGrid 렌더링
# ------------------------------------------------
grid_response = AgGrid(
    df,
    gridOptions=grid_options,
    enable_enterprise_modules=False,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    theme="streamlit",  # light/dark 자동 적용
    fit_columns_on_grid_load=True,
    height=600,
)

selected = grid_response.get("selected_rows")

# ------------------------------------------------
# 행 클릭 시 차트 페이지로 이동
# ------------------------------------------------
if selected is not None and len(selected) > 0:
    selected_row = selected.iloc[0]
    stock_name = selected_row["종목명"]
    st.session_state["selected_stock"] = stock_name

    st.success(f"✅ {stock_name} 차트 페이지로 이동 중...")
    st.switch_page("pages/stock_detail.py")

st.markdown("---")
st.caption("💡 b가격 ±5% 구간에 위치한 종목은 매수/매도 균형 구간으로 해석할 수 있습니다.")

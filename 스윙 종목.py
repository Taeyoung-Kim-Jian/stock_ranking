import streamlit as st
import pandas as pd
from supabase import create_client
from st_aggrid import AgGrid, GridOptionsBuilder
import plotly.express as px

# ------------------------------------------------
# Supabase 연결
# ------------------------------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------------------------------
# 데이터 로딩 함수
# ------------------------------------------------
@st.cache_data(ttl=300)
def load_returns(limit=None):
    query = supabase.table("b_return").select(
        "종목명, 종목코드, 수익률, 발생일, 발생일종가, 현재가격, 기간"
    )
    query = query.order("수익률", desc=True)
    if limit:
        query = query.limit(limit)
    res = query.execute()
    return pd.DataFrame(res.data)

# ------------------------------------------------
# 페이지 설정
# ------------------------------------------------
st.set_page_config(page_title="스윙 종목", layout="wide")
st.title("💹 스윙 종목 대시보드")

# ------------------------------------------------
# 데이터 로드
# ------------------------------------------------
show_all = st.toggle("🔍 전체 수익률 보기", value=False)

if show_all:
    df = load_returns()
else:
    df = load_returns(limit=5)

if df.empty:
    st.warning("⚠️ Supabase의 b_return 테이블에 데이터가 없습니다.")
    st.stop()

# ------------------------------------------------
# 데이터 정리
# ------------------------------------------------
df["수익률"] = df["수익률"].astype(float)
df["현재가격"] = df["현재가격"].astype(float)
df["발생일종가"] = df["발생일종가"].astype(float)
df["수익률(%)"] = df["수익률"].map("{:.2f}%".format)
df["현재가격(원)"] = df["현재가격"].map("{:,.0f}".format)
df["발생일종가(원)"] = df["발생일종가"].map("{:,.0f}".format)

# ------------------------------------------------
# 1️⃣ 상위 5개 카드 + 그래프 보기
# ------------------------------------------------
if not show_all:
    st.subheader("🏆 수익률 상위 5개 종목")

    # 막대그래프 (Plotly)
    fig = px.bar(
        df.sort_values("수익률", ascending=True),
        x="수익률",
        y="종목명",
        orientation="h",
        text=df["수익률"].map("{:.2f}%".format),
        color="수익률",
        color_continuous_scale="Agsunset",
        title="📈 상위 5개 종목 수익률 비교",
    )
    fig.update_layout(
        xaxis_title="수익률 (%)",
        yaxis_title="종목명",
        coloraxis_showscale=False,
        height=400,
        margin=dict(l=40, r=40, t=60, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)

    # 카드형 정보 출력
    st.markdown("---")
    for i, row in df.iterrows():
        st.markdown(
            f"""
            ### 🥇 {i+1}. **{row['종목명']} ({row['종목코드']})**
            - 수익률: **{row['수익률(%)']}**
            - 발생일: {row['발생일']}  (기간: {row['기간']}일)
            - 발생일 종가: {row['발생일종가(원)']}원  
              현재가격: {row['현재가격(원)']}원
            """
        )
        st.divider()

# ------------------------------------------------
# 2️⃣ 전체 보기 모드
# ------------------------------------------------
else:
    st.subheader("📊 전체 수익률 목록")

    gb = GridOptionsBuilder.from_dataframe(
        df[["종목명", "종목코드", "수익률(%)", "기간", "발생일", "발생일종가(원)", "현재가격(원)"]]
    )
    gb.configure_default_column(resizable=True, sortable=True, filter=True)
    gb.configure_grid_options(domLayout="autoHeight")
    grid_options = gb.build()

    AgGrid(
        df,
        gridOptions=grid_options,
        fit_columns_on_grid_load=True,
        theme="streamlit",
        height=600,
    )

st.markdown("---")
st.caption("💡 상위 5개는 수익률 순 정렬 기준이며, 전체 보기에서 모든 종목을 확인할 수 있습니다.")

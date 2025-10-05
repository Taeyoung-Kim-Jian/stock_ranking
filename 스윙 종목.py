import streamlit as st
import pandas as pd
from supabase import create_client
from st_aggrid import AgGrid, GridOptionsBuilder
import plotly.express as px
import re  # 색상값 파싱용

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
# CSS 스타일 적용
# ------------------------------------------------
st.markdown("""
<style>
/* 🔹 그래프 내부 텍스트 효과 (그림자 + 강조) */
.plotly text {
    font-weight: 700 !important;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.7);
}

/* 🔸 카드 텍스트 강조 스타일 */
.highlight-text {
    background: linear-gradient(90deg, #ff7e00, #ffb700);
    color: #ffffff;
    padding: 10px 16px;
    border-radius: 8px;
    font-weight: 800;
    font-size: 17px;
    text-shadow: 2px 2px 6px #000;
    letter-spacing: 0.5px;
}

/* 📋 기본 폰트 설정 */
body, p, div {
    font-family: "Segoe UI", "Noto Sans KR", sans-serif;
}
</style>
""", unsafe_allow_html=True)

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
# 데이터 전처리
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

    # ✅ 수익률 높은 순 정렬
    df_sorted = df.sort_values("수익률", ascending=False)

    # ✅ Plotly 막대그래프 생성
    fig = px.bar(
        df_sorted,
        x="수익률",
        y=df_sorted.index,
        orientation="h",
        color="수익률",
        color_continuous_scale="Agsunset",
    )

    # ✅ 색상별 평균 밝기 계산 (matplotlib 없이)
    colors = px.colors.sample_colorscale("Agsunset", [i/(len(df_sorted)-1) for i in range(len(df_sorted))])
    avg_brightness = sum(
        (float(x) for c in colors for x in re.findall(r"[\d.]+", c)[:3])
    ) / (len(colors) * 3)
    text_color = "black" if avg_brightness > 180 else "white"

    # ✅ 텍스트 스타일: 왼쪽 정렬, 전체 색 자동 적용
    fig.update_traces(
        text=df_sorted.apply(lambda r: f"{r['종목명']}  {r['수익률']:.2f}%", axis=1),
        textposition="inside",
        insidetextanchor="start",
        textfont=dict(size=17, family="Arial Black", color=text_color),
        hovertemplate="<b>%{text}</b><extra></extra>",
    )

    # ✅ 그래프 레이아웃
    fig.update_layout(
        xaxis_title=None,
        yaxis_title=None,
        yaxis=dict(showticklabels=False, showgrid=False, categoryorder="total descending"),
        xaxis=dict(showgrid=False),
        coloraxis_showscale=False,
        height=320,
        margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(fig, use_container_width=True)

    # ✅ 카드 텍스트 섹션
    st.markdown("---")
    for i, row in df_sorted.iterrows():
        st.markdown(
            f"""
            <div class="highlight-text">
            🥇 {i+1}. <b>{row['종목명']} ({row['종목코드']})</b> — {row['수익률(%)']}
            </div>
            <p>📅 {row['발생일']} (기간: {row['기간']}일)<br>
            💰 {row['발생일종가(원)']} → {row['현재가격(원)']}</p>
            <hr>
            """,
            unsafe_allow_html=True
        )

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

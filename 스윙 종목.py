import streamlit as st
import pandas as pd
from supabase import create_client
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import plotly.graph_objects as go

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

@st.cache_data(ttl=300)
def load_prices(code):
    res = (
        supabase.table("prices")
        .select("날짜, 종가")
        .eq("종목코드", code)
        .order("날짜", desc=False)
        .execute()
    )
    df = pd.DataFrame(res.data)
    if not df.empty:
        df["날짜"] = pd.to_datetime(df["날짜"])
        df["종가"] = df["종가"].astype(float)
    return df

@st.cache_data(ttl=300)
def load_b_points(code):
    res = (
        supabase.table("low_after_b")
        .select("구분, b가격, 발생일")
        .eq("종목코드", code)
        .order("발생일", desc=True)
        .execute()
    )
    df = pd.DataFrame(res.data)
    if not df.empty:
        df["발생일"] = pd.to_datetime(df["발생일"])
        df["b가격"] = df["b가격"].astype(float)
    return df

# ------------------------------------------------
# 페이지 설정
# ------------------------------------------------
st.set_page_config(page_title="스윙 종목", layout="wide")
st.title("💹 스윙 종목 대시보드")

# ------------------------------------------------
# CSS 스타일
# ------------------------------------------------
st.markdown("""
<style>
.rank-item {
    background: linear-gradient(90deg, #ffed91, #ffc300);
    color: #000000;
    padding: 12px 18px;
    border-radius: 10px;
    font-weight: 800;
    font-size: 18px;
    margin-bottom: 10px;
    box-shadow: 1px 1px 4px rgba(0,0,0,0.15);
}
.rank-item span {
    float: right;
    font-weight: 700;
    color: #cc0000;
}
body, p, div {
    font-family: "Segoe UI", "Noto Sans KR", sans-serif;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# 데이터 로드
# ------------------------------------------------
show_all = st.toggle("🔍 전체 수익률 보기", value=False)
df = load_returns() if show_all else load_returns(limit=5)

if df.empty:
    st.warning("⚠️ Supabase의 b_return 테이블에 데이터가 없습니다.")
    st.stop()

df["수익률"] = df["수익률"].astype(float)
df["수익률(%)"] = df["수익률"].map("{:.2f}%".format)

# ------------------------------------------------
# 1️⃣ 상위 5개 순위 리스트
# ------------------------------------------------
if not show_all:
    st.subheader("🏆 수익률 상위 5개 종목")

    df_sorted = df.sort_values("수익률", ascending=False).reset_index(drop=True)
    for i, row in df_sorted.iterrows():
        st.markdown(
            f"""
            <div class="rank-item">
                {i+1}위. <b>{row['종목명']} ({row['종목코드']})</b>
                <span>{row['수익률(%)']}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

# ------------------------------------------------
# 2️⃣ 전체 보기 (클릭 → 차트 표시)
# ------------------------------------------------
else:
    st.subheader("📊 전체 수익률 목록")

    gb = GridOptionsBuilder.from_dataframe(
        df[["종목명", "종목코드", "수익률(%)", "기간", "발생일", "발생일종가", "현재가격"]]
    )
    gb.configure_default_column(resizable=True, sortable=True, filter=True)
    gb.configure_selection("single", use_checkbox=True)
    gb.configure_grid_options(domLayout="normal")
    grid_options = gb.build()

    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True,
        theme="streamlit",
        height=700,
    )

    selected = grid_response["selected_rows"]

    if selected:
        sel = selected[0]
        code = sel["종목코드"]
        name = sel["종목명"]

        st.markdown("---")
        st.subheader(f"📈 {name} ({code}) 차트")

        df_price = load_prices(code)
        df_bpoints = load_b_points(code)

        if df_price.empty:
            st.warning("가격 데이터가 없습니다.")
            st.stop()

        # 최근 200일 데이터만 표시
        df_price = df_price.tail(200)

        # 차트
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df_price["날짜"],
                y=df_price["종가"],
                mode="lines",
                name="종가",
                line=dict(color="lightblue", width=2),
            )
        )

        # B 포인트 표시
        if not df_bpoints.empty:
            b_in_range = df_bpoints[df_bpoints["발생일"].between(df_price["날짜"].min(), df_price["날짜"].max())]
            for _, row in b_in_range.iterrows():
                fig.add_trace(
                    go.Scatter(
                        x=[row["발생일"]],
                        y=[row["b가격"]],
                        mode="markers+text",
                        name=f"B({row['구분']})",
                        text=row["구분"],
                        textposition="top center",
                        marker=dict(color="red", size=9, symbol="diamond"),
                    )
                )

        fig.update_layout(
            height=600,
            xaxis_title="날짜",
            yaxis_title="가격",
            template="plotly_white",
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=False,
        )

        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("💡 행을 클릭하면 해당 종목의 차트를 확인할 수 있습니다.")

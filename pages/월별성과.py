# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os, json
from supabase import create_client
from st_aggrid import AgGrid, GridOptionsBuilder
import matplotlib.pyplot as plt

# ------------------------------------------------
# 페이지 설정
# ------------------------------------------------
st.set_page_config(page_title="📆 월별 성과", layout="wide")

st.markdown("<h4 style='text-align:center;'>📈 월별 성과</h4>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray; font-size:13px;'>b가격 ±5% 내에서 측정된 종목들의 월별 성과 데이터입니다.</p>", unsafe_allow_html=True)
st.markdown("---")

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
# 안전 변환 함수 (모든 타입을 JSON 직렬화 가능하게)
# ------------------------------------------------
def safe_convert(df):
    df = df.replace({pd.NA: None}).fillna("")
    for c in df.columns:
        # 날짜형 → 문자열
        if "날짜" in c or c == "월구분":
            df[c] = df[c].astype(str)
        else:
            # 숫자형 변환 (NaN, Inf 방지)
            df[c] = pd.to_numeric(df[c], errors="coerce")
            df[c] = df[c].replace([float("inf"), float("-inf")], 0).fillna(0).astype(float)
    # numpy.float64 → Python float
    df = df.applymap(lambda x: x.item() if hasattr(x, "item") else x)
    # object형 (리스트, None 등) → 문자열로 변환
    df = df.applymap(lambda x: x if isinstance(x, (str, int, float)) else str(x))
    # JSON 직렬화 테스트
    try:
        json.dumps(df.to_dict(orient="records"))
    except Exception as e:
        st.warning(f"⚠️ JSON 직렬화 중 변환된 데이터 예외 발생: {e}")
    return df

# ------------------------------------------------
# 데이터 로드 함수
# ------------------------------------------------
@st.cache_data(ttl=600)
def load_monthly_data():
    try:
        res = supabase.table("b_zone_monthly_tracking").select("*").order("월구분", desc=True).execute()
        df = pd.DataFrame(res.data)
        if df.empty:
            return df
        df["월포맷"] = pd.to_datetime(df["월구분"]).dt.strftime("%y.%m")
        return df
    except Exception as e:
        st.error(f"❌ Supabase 데이터 로드 중 오류: {e}")
        return pd.DataFrame()

# ------------------------------------------------
# 데이터 불러오기
# ------------------------------------------------
with st.spinner("📊 월별 성과 데이터를 불러오는 중..."):
    df = load_monthly_data()

if df.empty:
    st.warning("📭 월별 성과 데이터가 없습니다.")
    st.stop()

st.success(f"✅ 총 {len(df)}건의 데이터 불러옴")

# ------------------------------------------------
# 월별 평균 수익률 시각화
# ------------------------------------------------
try:
    avg_df = (
        df.groupby("월포맷")["현재가대비수익률"]
        .mean()
        .reset_index()
        .sort_values("월포맷", ascending=True)
    )

    fig, ax = plt.subplots(figsize=(8, 3))
    ax.bar(avg_df["월포맷"], avg_df["현재가대비수익률"], color="skyblue")
    ax.set_title("📊 월별 평균 수익률", fontsize=13)
    ax.set_ylabel("평균 수익률 (%)")
    ax.set_xlabel("월")
    for i, v in enumerate(avg_df["현재가대비수익률"]):
        ax.text(i, v + 0.2, f"{v:.1f}%", ha="center", fontsize=9)
    st.pyplot(fig)
except Exception as e:
    st.warning(f"⚠️ 월별 평균 수익률 그래프 생성 중 오류: {e}")

# ------------------------------------------------
# 월별 탭 표시
# ------------------------------------------------
months = sorted(df["월포맷"].unique(), reverse=True)
tabs = st.tabs(months)

for i, month in enumerate(months):
    with tabs[i]:
        st.subheader(f"📅 {month}월 성과")
        df_month = df[df["월포맷"] == month].copy()

        display_cols = [
            "종목명", "b가격", "측정일", "측정일종가", "현재가",
            "현재가대비수익률", "최고수익률", "최저수익률"
        ]

        # 안전 변환 적용
        df_display = safe_convert(df_month[display_cols].copy())

        # AgGrid 설정
        gb = GridOptionsBuilder.from_dataframe(df_display)
        gb.configure_default_column(resizable=True, sortable=True, filter=True)
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_column("현재가대비수익률", cellStyle=lambda x: {
            "backgroundColor": "#c7f5d9" if x["value"] > 0 else "#f7c7c7"
        })
        grid_options = gb.build()

        AgGrid(
            df_display,
            gridOptions=grid_options,
            height=550,
            theme="balham",
            fit_columns_on_grid_load=True,
        )

st.markdown("---")
st.caption("💡 본 데이터는 Supabase `b_zone_monthly_tracking` 테이블 기준으로 표시됩니다.")

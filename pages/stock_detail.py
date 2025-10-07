# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from supabase import create_client
import altair as alt

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
st.set_page_config(page_title="종목 상세 차트", layout="wide")

# ------------------------------------------------
# 선택된 종목 확인
# ------------------------------------------------
if "selected_stock" not in st.session_state:
    st.warning("⚠️ 종목이 선택되지 않았습니다. '전체 종목' 페이지에서 선택하세요.")
    st.stop()

stock_name = st.session_state["selected_stock"]

st.markdown(f"<h4 style='text-align:center;'>📈 {stock_name} 주가 차트</h4>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray; font-size:13px;'>Supabase에서 불러온 가격 데이터 기반</p>", unsafe_allow_html=True)
st.markdown("---")

# ------------------------------------------------
# 종목코드 조회
# ------------------------------------------------
@st.cache_data(ttl=300)
def get_stock_code(name):
    """stocks 테이블에서 종목코드를 조회"""
    try:
        res = (
            supabase.table("stocks")
            .select("종목코드")
            .eq("종목명", name)
            .limit(1)
            .execute()
        )
        data = res.data
        if data and len(data) > 0:
            return data[0]["종목코드"]
        else:
            return None
    except Exception as e:
        st.error(f"❌ 종목코드 조회 오류: {e}")
        return None

stock_code = get_stock_code(stock_name)
if not stock_code:
    st.error("❌ 해당 종목의 종목코드를 찾을 수 없습니다.")
    st.stop()

# ------------------------------------------------
# 가격 데이터 로드
# ------------------------------------------------
@st.cache_data(ttl=300)
def load_price_data(name):
    """prices 테이블에서 특정 종목의 전체 일자별 가격 데이터 조회"""
    try:
        all_data = []
        start = 0
        step = 1000
        while True:
            res = (
                supabase.table("prices")
                .select("날짜, 종가")
                .eq("종목명", name)
                .order("날짜", desc=False)
                .range(start, start + step - 1)
                .execute()
            )
            data_chunk = res.data
            if not data_chunk:
                break
            all_data.extend(data_chunk)
            if len(data_chunk) < step:
                break
            start += step

        df = pd.DataFrame(all_data)
        if not df.empty:
            df["날짜"] = pd.to_datetime(df["날짜"])
            df = df.sort_values("날짜")
        return df

    except Exception as e:
        st.error(f"❌ 가격 데이터 로딩 오류: {e}")
        return pd.DataFrame()

# ------------------------------------------------
# b가격 데이터 로드 (bt_points 테이블)
# ------------------------------------------------
@st.cache_data(ttl=300)
def load_b_prices(code):
    """bt_points 테이블에서 해당 종목코드의 모든 b가격 조회"""
    try:
        res = (
            supabase.table("bt_points")
            .select("b가격")
            .eq("종목코드", code)
            .execute()
        )
        df = pd.DataFrame(res.data)
        if not df.empty:
            df["b가격"] = df["b가격"].astype(float)
        return df
    except Exception as e:
        st.error(f"❌ b가격 데이터 로딩 오류: {e}")
        return pd.DataFrame()

# ------------------------------------------------
# 데이터 로드 실행
# ------------------------------------------------
df_price = load_price_data(stock_name)
df_b = load_b_prices(stock_code)

# ------------------------------------------------
# b가격 표시 토글 추가
# ------------------------------------------------
show_b_lines = st.toggle("📊 b가격 표시", value=True)

# ------------------------------------------------
# 차트 표시
# ------------------------------------------------
if df_price.empty:
    st.warning("⚠️ 해당 종목의 가격 데이터를 찾을 수 없습니다.")
else:
    base_chart = (
        alt.Chart(df_price)
        .mark_line(color="#f9a825", interpolate="monotone")
        .encode(
            x=alt.X("날짜:T", title="날짜"),
            y=alt.Y("종가:Q", title="종가 (₩)"),
            tooltip=["날짜", "종가"]
        )
    )

    chart = base_chart

    # ✅ 토글이 ON일 때만 b가격 수평선 + 텍스트 표시
    if show_b_lines and not df_b.empty:
        # 회색 수평선 (직선)
        rules = alt.Chart(df_b).mark_rule(color="gray").encode(
            y="b가격:Q"
        )

        # 왼쪽 시작점에 빨간 텍스트 표시
        texts = (
            alt.Chart(df_b)
            .mark_text(
                align="left",
                baseline="bottom",
                dx=3,
                dy=-6,
                color="gray",
                fontSize=11,
                fontWeight="bold"
            )
            .encode(
                x=alt.value(5),  # 왼쪽 시작 위치 고정
                y="b가격:Q",
                text=alt.Text("b가격:Q", format=".0f")
            )
        )

        chart = chart + rules + texts

    st.altair_chart(chart.properties(width="container", height=400), use_container_width=True)

# ------------------------------------------------
# 뒤로가기 버튼
# ------------------------------------------------
if st.button("⬅️ 전체 종목으로 돌아가기"):
    st.switch_page("pages/전체 종목.py")

# ------------------------------------------------
# 💬 댓글 게시판
# ------------------------------------------------
st.markdown("---")
st.subheader("💬 종목 댓글 게시판")

# 댓글 입력 박스
user_name = st.text_input("작성자 이름", key="comment_user")
comment_text = st.text_area("댓글 내용", key="comment_text")

if st.button("댓글 작성 ✍️"):
    if not user_name or not comment_text:
        st.warning("이름과 내용을 모두 입력해주세요.")
    else:
        try:
            # Supabase에 댓글 저장
            supabase.table("comments").insert({
                "종목코드": stock_code,
                "종목명": stock_name,
                "작성자": user_name,
                "내용": comment_text
            }).execute()
            st.success("✅ 댓글이 등록되었습니다!")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"❌ 댓글 저장 오류: {e}")

# ------------------------------------------------
# 댓글 목록 불러오기
# ------------------------------------------------
try:
    res = (
        supabase.table("comments")
        .select("작성자, 내용, 작성일")
        .eq("종목코드", stock_code)
        .order("작성일", desc=True)
        .execute()
    )
    comments = pd.DataFrame(res.data)

    if not comments.empty:
        for _, row in comments.iterrows():
            st.markdown(
                f"""
                <div style='background-color:#f7f7f7; padding:10px; border-radius:8px; margin-bottom:8px;'>
                <b>{row['작성자']}</b> <span style='color:gray; font-size:12px;'>({pd.to_datetime(row['작성일']).strftime('%Y-%m-%d %H:%M')})</span><br>
                {row['내용']}
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("아직 댓글이 없습니다. 첫 댓글을 남겨보세요 💬")

except Exception as e:
    st.error(f"❌ 댓글 불러오기 오류: {e}")



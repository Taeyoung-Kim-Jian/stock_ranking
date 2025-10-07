# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from supabase import create_client
import altair as alt
from datetime import timedelta

# ------------------------------------------------
# Supabase 연결
# ------------------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Supabase 환경변수가 설정되지 않았습니다.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ✅ 세션 복원
try:
    token = st.session_state.get("access_token")
    if not token:
        sess = supabase.auth.get_session()
        token = (
            getattr(sess, "access_token", None)
            or (isinstance(sess, dict) and (sess.get("access_token") or (sess.get("session") or {}).get("access_token")))
        )
        if token:
            st.session_state["access_token"] = token
            user_info = supabase.auth.get_user()
            if user_info and getattr(user_info, "user", None):
                st.session_state["user"] = user_info.user
    if token:
        supabase.postgrest.auth(token)
except Exception:
    pass

# ------------------------------------------------
# 페이지 설정
# ------------------------------------------------
st.set_page_config(page_title="종목 상세 차트", layout="wide")

# ------------------------------------------------
# 선택된 종목 확인
# ------------------------------------------------
if "selected_stock_code" not in st.session_state or "selected_stock_name" not in st.session_state:
    st.warning("⚠️ 종목이 선택되지 않았습니다. 메인 페이지로 이동합니다...")
    st.switch_page("스윙 종목.py")

stock_name = st.session_state["selected_stock_name"]
stock_code = st.session_state["selected_stock_code"]

st.markdown(f"<h4 style='text-align:center;'>📈 {stock_name} ({stock_code}) 주가 차트</h4>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray; font-size:13px;'>b가격 모드 / 기간 선택 / 댓글 시스템</p>", unsafe_allow_html=True)
st.markdown("---")

# ------------------------------------------------
# 데이터 로드
# ------------------------------------------------
@st.cache_data(ttl=300)
def load_price_data(code):
    try:
        all_data, start, step = [], 0, 1000
        while True:
            res = (
                supabase.table("prices")
                .select("날짜, 종가")
                .eq("종목코드", code)
                .order("날짜", desc=False)
                .range(start, start + step - 1)
                .execute()
            )
            chunk = res.data
            if not chunk:
                break
            all_data.extend(chunk)
            if len(chunk) < step:
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


@st.cache_data(ttl=300)
def load_b_prices(code):
    try:
        res = supabase.table("bt_points").select("b가격").eq("종목코드", code).execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            df["b가격"] = df["b가격"].astype(float)
            df = df.sort_values("b가격")
        return df
    except Exception as e:
        st.error(f"❌ b가격 데이터 로딩 오류: {e}")
        return pd.DataFrame()


df_price = load_price_data(stock_code)
df_b = load_b_prices(stock_code)

# ------------------------------------------------
# 기간 선택 (라디오)
# ------------------------------------------------
st.subheader("⏳ 차트 기간 선택")
period = st.radio(
    "보기 기간 선택",
    ("1년", "2년", "3년", "전체"),
    horizontal=True
)

if not df_price.empty:
    latest_date = df_price["날짜"].max()
    if period != "전체":
        years = int(period.replace("년", ""))
        start_date = latest_date - timedelta(days=365 * years)
        df_price = df_price[df_price["날짜"] >= start_date]

# ------------------------------------------------
# b가격 표시 + 모드 선택
# ------------------------------------------------
col1, col2 = st.columns([1, 3])
with col1:
    show_b = st.toggle("📊 b가격 표시", value=True)
with col2:
    mode = st.radio(
        "b가격 표시 모드 선택",
        ("가까운 1개", "가까운 3개", "전체"),
        horizontal=True,
        disabled=not show_b
    )

# ------------------------------------------------
# 차트 표시
# ------------------------------------------------
if df_price.empty:
    st.warning("⚠️ 가격 데이터 없음")
else:
    current_price = df_price["종가"].iloc[-1]

    base_chart = (
        alt.Chart(df_price)
        .mark_line(color="#f9a825")
        .encode(
            x=alt.X("날짜:T", title="날짜"),
            y=alt.Y("종가:Q", title="종가 (₩)"),
            tooltip=["날짜", "종가"]
        )
    )

    if show_b and not df_b.empty:
        # 현재 종가 기준으로 가장 가까운 b가격 찾기
        df_b["diff"] = (df_b["b가격"] - current_price).abs()
        df_b_sorted = df_b.sort_values("diff")

        if mode == "가까운 1개":
            visible_b = df_b_sorted.head(1)
        elif mode == "가까운 3개":
            idx = df_b_sorted.index[0]
            idx_pos = df_b_sorted.index.get_loc(idx)
            visible_b = df_b_sorted.iloc[max(0, idx_pos-1): idx_pos+2]
        else:  # 전체
            visible_b = df_b.copy()

        # 현재 차트 구간 내 종가 범위에 있는 b가격만 표시
        y_min, y_max = df_price["종가"].min(), df_price["종가"].max()
        visible_b = visible_b[(visible_b["b가격"] >= y_min) & (visible_b["b가격"] <= y_max)]

        if not visible_b.empty:
            rules = alt.Chart(visible_b).mark_rule(color="gray").encode(y="b가격:Q")

            texts = (
                alt.Chart(visible_b)
                .mark_text(
                    align="left",
                    baseline="middle",
                    dx=-250,
                    color="orange",
                    fontSize=11,
                    fontWeight="bold"
                )
                .encode(
                    y="b가격:Q",
                    text=alt.Text("b가격:Q", format=".0f")
                )
            )

            chart = (base_chart + rules + texts).properties(width="container", height=400)
        else:
            chart = base_chart.properties(width="container", height=400)
    else:
        chart = base_chart.properties(width="container", height=400)

    st.altair_chart(chart, use_container_width=True)

# ------------------------------------------------
# 💬 댓글 시스템
# ------------------------------------------------
st.markdown("---")
st.subheader("💬 종목 댓글 게시판")

if st.session_state.user:
    comment_text = st.text_area("댓글을 입력하세요", key="comment_text")

    if st.button("댓글 작성 ✍️", key="submit_comment"):
        if not comment_text.strip():
            st.warning("내용을 입력해주세요.")
        else:
            try:
                user = st.session_state.user
                user_id = user.id
                user_email = user.email or "익명"

                data = {
                    "종목코드": stock_code,
                    "종목명": stock_name,
                    "작성자": user_email,
                    "내용": comment_text,
                    "user_id": user_id,
                }

                supabase.table("comments").insert(data).execute()
                st.success("✅ 댓글이 등록되었습니다!")
                st.rerun()

            except Exception as e:
                st.error(f"❌ 댓글 저장 오류: {e}")
else:
    st.info("🔒 로그인 후 댓글을 작성할 수 있습니다.")

# ------------------------------------------------
# 댓글 목록 표시 + 수정/삭제
# ------------------------------------------------
try:
    res = (
        supabase.table("comments")
        .select("id, 작성자, 내용, 작성일, user_id")
        .eq("종목코드", stock_code)
        .order("작성일", desc=True)
        .execute()
    )
    comments = pd.DataFrame(res.data)

    if not comments.empty:
        for _, row in comments.iterrows():
            is_owner = (
                st.session_state.user
                and st.session_state.user.id == row["user_id"]
            )

            with st.container():
                st.markdown(
                    f"""
                    <div style='background-color:#f7f7f7;padding:10px;border-radius:8px;margin-bottom:6px;'>
                    <b>{row["작성자"]}</b> 
                    <span style='color:gray;font-size:12px;'>({pd.to_datetime(row["작성일"]).strftime('%Y-%m-%d %H:%M')})</span><br>
                    {row["내용"]}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if is_owner:
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("✏️ 수정", key=f"edit_btn_{row['id']}"):
                            new_text = st.text_area(
                                "수정 내용",
                                row["내용"],
                                key=f"edit_text_{row['id']}",
                            )
                            if st.button("💾 저장", key=f"save_btn_{row['id']}"):
                                supabase.table("comments").update({"내용": new_text}).eq("id", row["id"]).execute()
                                st.rerun()
                    with col2:
                        if st.button("🗑️ 삭제", key=f"delete_btn_{row['id']}"):
                            supabase.table("comments").delete().eq("id", row["id"]).execute()
                            st.rerun()
    else:
        st.info("아직 댓글이 없습니다 💬")

except Exception as e:
    st.error(f"❌ 댓글 불러오기 오류: {e}")

# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from supabase import create_client
import altair as alt
from datetime import datetime

# ------------------------------------------------
# Supabase 연결
# ------------------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
REDIRECT_URL = os.environ.get("REDIRECT_URL") or st.secrets.get("REDIRECT_URL")

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
# ------------------------------------------------
# 선택된 종목 확인
# ------------------------------------------------
if "selected_stock_code" not in st.session_state or "selected_stock_name" not in st.session_state:
    st.warning("⚠️ 종목이 선택되지 않았습니다. '월별 성과' 페이지에서 선택하세요.")
    st.stop()

stock_name = st.session_state["selected_stock_name"]
stock_code = st.session_state["selected_stock_code"]

st.markdown(f"<h4 style='text-align:center;'>📈 {stock_name} 주가 차트</h4>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray; font-size:13px;'>Supabase 기반 로그인 + 댓글 시스템</p>", unsafe_allow_html=True)
st.markdown("---")

# ------------------------------------------------
# 종목코드 조회
# ------------------------------------------------
@st.cache_data(ttl=300)
def get_stock_code(name):
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
    try:
        all_data, start, step = [], 0, 1000
        while True:
            res = (
                supabase.table("prices")
                .select("날짜, 종가")
                .eq("종목명", name)
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

df_price = load_price_data(stock_name)

# ------------------------------------------------
# 로그인 / 회원가입 / Google 로그인
# ------------------------------------------------
if "user" not in st.session_state:
    st.session_state.user = None

st.sidebar.title("🔐 로그인 / 회원가입")

# ------------------------------------------------
# 이메일 로그인
# ------------------------------------------------
if not st.session_state.user:
    email = st.sidebar.text_input("이메일")
    password = st.sidebar.text_input("비밀번호", type="password")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("로그인"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.success(f"👋 {email}님 로그인 완료!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ 로그인 실패: {e}")
    with col2:
        if st.button("회원가입"):
            try:
                res = supabase.auth.sign_up({"email": email, "password": password})
                if res.user:
                    st.success("✅ 회원가입 완료! 로그인 해주세요.")
                    st.experimental_rerun()
            except Exception as e:
                st.error(f"❌ 회원가입 실패: {e}")

    # ------------------------------------------------
    # Google 로그인 (자동 리디렉션)
    # ------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.markdown("🌐 또는 Google 계정으로 로그인")

    if st.sidebar.button("🔐 Google로 로그인"):
        try:
            res = supabase.auth.sign_in_with_oauth(
                {
                    "provider": "google",
                    "options": {
                        "redirect_to": REDIRECT_URL,
                    },
                }
            )
            # ✅ 브라우저 자동 이동
            st.markdown(
                f"<meta http-equiv='refresh' content='0; url={res.url}'>",
                unsafe_allow_html=True,
            )
        except Exception as e:
            st.sidebar.error(f"❌ Google 로그인 오류: {e}")

else:
    # 로그인된 사용자 표시
    user_email = st.session_state.user.email or "Google 사용자"
    st.sidebar.success(f"👤 {user_email} 님 로그인 중")
    if st.sidebar.button("로그아웃"):
        st.session_state.user = None
        supabase.auth.sign_out()
        st.experimental_rerun()

# ------------------------------------------------
# 로그인 세션 복원 (Google 로그인 복귀 시)
# ------------------------------------------------
try:
    session = supabase.auth.get_session()
    if session and session.access_token:
        user_info = supabase.auth.get_user()
        if user_info and user_info.user:
            st.session_state.user = user_info.user
except Exception:
    pass

# ------------------------------------------------
# 차트 표시
# ------------------------------------------------
if df_price.empty:
    st.warning("⚠️ 가격 데이터 없음")
else:
    line_chart = (
        alt.Chart(df_price)
        .mark_line(color="#f9a825")
        .encode(
            x=alt.X("날짜:T", title="날짜"),
            y=alt.Y("종가:Q", title="종가 (₩)"),
            tooltip=["날짜", "종가"],
        )
        .properties(width="container", height=400)
    )
    st.altair_chart(line_chart, use_container_width=True)

# ------------------------------------------------
# 💬 댓글 게시판
# ------------------------------------------------
st.markdown("---")
st.subheader("💬 종목 댓글 게시판")

if st.session_state.user:
    comment_text = st.text_area("댓글을 입력하세요", key="comment_text")
    if st.button("댓글 작성 ✍️"):
        if not comment_text.strip():
            st.warning("내용을 입력해주세요.")
        else:
            supabase.table("comments").insert({
                "종목코드": stock_code,
                "종목명": stock_name,
                "내용": comment_text,
                "user_id": st.session_state.user.id,
            }).execute()
            st.success("✅ 댓글이 등록되었습니다!")
            st.experimental_rerun()
else:
    st.info("🔒 로그인 후 댓글을 작성할 수 있습니다.")

# ------------------------------------------------
# 댓글 목록 표시 + 수정/삭제
# ------------------------------------------------
try:
    res = (
        supabase.table("comments")
        .select("id, 내용, 작성일, user_id")
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
                    <span style='color:gray;font-size:12px;'>{pd.to_datetime(row["작성일"]).strftime('%Y-%m-%d %H:%M')}</span><br>
                    {row["내용"]}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if is_owner:
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button(f"✏️ 수정_{row['id']}"):
                            new_text = st.text_area("수정 내용", row["내용"], key=f"edit_{row['id']}")
                            if st.button(f"저장_{row['id']}"):
                                supabase.table("comments").update({"내용": new_text}).eq("id", row["id"]).execute()
                                st.experimental_rerun()
                    with col2:
                        if st.button(f"🗑️ 삭제_{row['id']}"):
                            supabase.table("comments").delete().eq("id", row["id"]).execute()
                            st.experimental_rerun()
    else:
        st.info("아직 댓글이 없습니다 💬")

except Exception as e:
    st.error(f"❌ 댓글 불러오기 오류: {e}")

# ------------------------------------------------
# 뒤로가기 버튼
# ------------------------------------------------
if st.button("⬅️ 전체 종목으로 돌아가기"):
    st.switch_page("pages/전체 종목.py")

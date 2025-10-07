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
    st.error("❌ Supabase 환경변수가 설정되지 않았습니다.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ✅ 세션 복원 & access_token 자동 주입
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
    st.warning("⚠️ 종목이 선택되지 않았습니다. '월별 성과' 페이지에서 선택하세요.")
    st.stop()

stock_name = st.session_state["selected_stock_name"]
stock_code = st.session_state["selected_stock_code"]

st.markdown(f"<h4 style='text-align:center;'>📈 {stock_name} ({stock_code}) 주가 차트</h4>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray; font-size:13px;'>Supabase 기반 로그인 + 댓글 시스템</p>", unsafe_allow_html=True)
st.markdown("---")

# ------------------------------------------------
# 가격 데이터 로드
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

df_price = load_price_data(stock_code)

# ------------------------------------------------
# 로그인 / 회원가입 UI
# ------------------------------------------------
if "user" not in st.session_state:
    st.session_state.user = None

st.sidebar.title("🔐 로그인 / 회원가입")

if not st.session_state.user:
    email = st.sidebar.text_input("이메일")
    password = st.sidebar.text_input("비밀번호", type="password")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("로그인"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.session_state.access_token = res.session.access_token
                supabase.postgrest.auth(res.session.access_token)
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
                    st.rerun()
            except Exception as e:
                st.error(f"❌ 회원가입 실패: {e}")

else:
    user_email = st.session_state.user.email or "Google 사용자"
    st.sidebar.success(f"👤 {user_email} 님 로그인 중")
    if st.sidebar.button("로그아웃"):
        st.session_state.user = None
        supabase.auth.sign_out()
        st.rerun()

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


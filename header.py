# -*- coding: utf-8 -*-
import streamlit as st
import os
from supabase import create_client

# ------------------------------------------------
# Supabase 연결
# ------------------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ------------------------------------------------
# 헤더 UI 함수
# ------------------------------------------------
def show_header():
    """
    모든 페이지 상단에 공통 헤더 표시
    - Streamlit 시스템 메뉴(⋮, footer 등) 제거
    - 로그인 / 로그아웃 버튼 표시
    """

    # ✅ 시스템 메뉴 및 footer 숨기기 (CSS + JS)
    st.markdown("""
        <style>
            /* 상단 점 세개 메뉴, 상태바 숨기기 */
            [data-testid="stToolbar"] {visibility: hidden !important;}
            [data-testid="stDecoration"] {visibility: hidden !important;}
            [data-testid="stStatusWidget"] {visibility: hidden !important;}
            #MainMenu {visibility: hidden !important;}

            /* 하단 footer 제거 */
            footer {visibility: hidden !important;}
            div.block-container:has(footer) {padding-bottom: 0px !important;}
        </style>

        <script>
            window.addEventListener('load', function() {
                const footers = parent.document.querySelectorAll('footer');
                footers.forEach(el => el.style.display = 'none');
            });
        </script>
    """, unsafe_allow_html=True)

    # ✅ 로그인 세션 복원
    if "user" not in st.session_state:
        st.session_state.user = None

    # ✅ 헤더 UI 구성
    st.markdown("""
        <div style='display:flex; justify-content:space-between; align-items:center;'>
            <h3 style='margin:0;'>📊 Swing Investor</h3>
    """, unsafe_allow_html=True)

    # 로그인 상태에 따라 다른 버튼 표시
    col1, col2, col3 = st.columns([6, 3, 2])

    with col3:
        if st.session_state.user:
            user_email = st.session_state.user.email or "User"
            if st.button(f"👋 {user_email}\n(로그아웃)", key="logout_btn"):
                supabase.auth.sign_out()
                st.session_state.user = None
                st.rerun()
        else:
            if st.button("🔐 로그인", key="login_btn"):
                # 로그인 페이지로 이동
                st.switch_page("pages/login.py")

    st.markdown("<hr style='margin-top:8px; margin-bottom:8px;'>", unsafe_allow_html=True)

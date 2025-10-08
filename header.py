# -*- coding: utf-8 -*-
import streamlit as st
import os

# ------------------------------------------------
# 통합된 공통 헤더 및 네비게이션 함수
# ------------------------------------------------
# Supabase 연결 코드는 헤더 기능에 직접 필요하지 않으므로 제거하거나 주석 처리했습니다.
# 필요하다면 이 파일 대신, 각 페이지 파일에서 개별적으로 연결하세요.

def show_app_header():
    """
    앱의 공통 헤더와 내비게이션 버튼을 표시하는 함수.
    """

    # ✅ 시스템 메뉴 및 footer 숨기기 (CSS)
    st.markdown("""
        <style>
            /* 상단 점 세개 메뉴, 상태바 숨기기 */
            #MainMenu {visibility: hidden !important;}
            [data-testid="stToolbar"] {visibility: hidden !important;}
            [data-testid="stStatusWidget"] {visibility: hidden !important;}
            /* 하단 footer 제거 */
            footer {visibility: hidden !important;}
        </style>
    """, unsafe_allow_html=True)
    
    # ✅ 앱 제목
    st.markdown("<h3 style='margin:0 0 10px 0;'>📊 Swing Investor</h3>", unsafe_allow_html=True)

    # ------------------------------------------------
    # ✅ 상단 네비게이션 버튼
    # ------------------------------------------------

    col_nav = st.columns(5)
    
    # 버튼 로직
    with col_nav[0]:
        if st.button("🏠 메인", use_container_width=True):
            st.switch_page("app.py")
    with col_nav[1]:
        if st.button("🟠 국내 눌림", use_container_width=True):
            st.switch_page("pages/한국 눌림 종목.py")
    with col_nav[2]:
        if st.button("🔵 국내 추격", use_container_width=True):
            st.switch_page("pages/한국 돌파 종목.py")
    with col_nav[3]:
        if st.button("🟢 해외 눌림", use_container_width=True):
            st.switch_page("pages/해외 눌림 종목.py")
    with col_nav[4]:
        if st.button("🔴 해외 추격", use_container_width=True):
            st.switch_page("pages/해외 돌파 종목.py")

    st.markdown("---")

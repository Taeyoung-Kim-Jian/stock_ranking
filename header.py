# -*- coding: utf-8 -*-
import streamlit as st
import os
from supabase import create_client

# ------------------------------------------------
# Supabase 연결 및 초기화 (필요하다면 유지)
# ------------------------------------------------
# 이 코드는 header 함수 밖, 앱의 최상위 스크립트에 있어야 합니다.
# (모든 페이지에서 SUPABASE_URL, SUPABASE_KEY가 필요할 경우)

# SUPABASE_URL = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
# SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
# 
# if SUPABASE_URL and SUPABASE_KEY:
#     try:
#         supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
#     except Exception as e:
#         st.error(f"❌ Supabase 연결 오류: {e}")
#         # supabase 객체가 필요한 경우 여기서 중단하거나, 함수 내에서 처리합니다.
# else:
#     # st.error("❌ Supabase 환경변수가 설정되지 않았습니다.")
#     # supabase가 헤더 기능에 직접 사용되지 않으므로 경고만 표시하고 진행
#     pass


# ------------------------------------------------
# 통합된 공통 헤더 및 네비게이션 함수
# ------------------------------------------------
def show_app_header():
    """
    앱의 공통 헤더와 내비게이션 버튼을 표시하는 함수.
    - 시스템 메뉴 및 footer 숨김
    - 앱 제목 표시
    - 페이지 이동 버튼 표시
    """

    # ✅ 시스템 메뉴 및 footer 숨기기 (CSS)
    # Streamlit 기본 메뉴/푸터/상태 위젯을 숨깁니다.
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

    # 네비게이션 버튼을 위한 컬럼 분할
    col_nav = st.columns(5)
    
    # 💡 st.button 대신 st.page_link를 사용하면 더 간결하고 페이지 전환이 명확해집니다.
    # 하지만 st.button을 요청하셨으므로 그대로 사용합니다.
    
    with col_nav[0]:
        if st.button("🏠 메인", use_container_width=True):
            st.switch_page("app.py") # 메인 페이지 파일명 확인 (보통 app.py)
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


# ------------------------------------------------
# ✅ 사용 예시 (이 함수를 각 페이지 상단에서 호출)
# ------------------------------------------------
# 예시: main app.py 또는 pages/*.py 파일 상단에서 호출
# if __name__ == '__main__':
#     st.set_page_config(page_title="스윙 종목 대시보드", layout="wide")
#     show_app_header()
#     st.write("페이지 본문 내용...")

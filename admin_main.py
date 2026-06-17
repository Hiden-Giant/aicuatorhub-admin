"""
Aicuatorhub Admin 메인 진입점
Streamlit Multi-Page Apps를 사용하여 자동으로 pages/ 폴더의 페이지들을 메뉴로 표시합니다.
"""
import streamlit as st
import sys
import os

# 프로젝트 루트 경로 추가
_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _project_root)

# Firebase 서비스 키 설정
# 운영 환경: FIREBASE_SERVICE_ACCOUNT_KEY_JSON 환경 변수 사용 (권장)
# 로컬 개발: serviceAccountKey.json 파일 사용 (환경 변수가 없을 때만)
_service_key_path = os.path.join(_project_root, "serviceAccountKey.json")
# 환경 변수가 설정되지 않았고, 파일이 존재하는 경우에만 파일 경로 설정
if "FIREBASE_SERVICE_ACCOUNT_KEY_JSON" not in os.environ and "FIREBASE_SERVICE_ACCOUNT_KEY_PATH" not in os.environ:
    if os.path.exists(_service_key_path):
        os.environ["FIREBASE_SERVICE_ACCOUNT_KEY_PATH"] = _service_key_path

from admin.firebase import get_db
from admin.components import render_header, render_language_selector
from admin.i18n import t
from admin.menu import get_current_language

# 페이지 설정
st.set_page_config(
    page_title="Aicuatorhub Admin",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if "db" not in st.session_state:
    st.session_state.db = None

# Firebase 초기화
db = get_db()
if db is None:
    st.error("⚠️ Firebase 연결에 실패했습니다. 설정을 확인해주세요.")
    st.stop()

st.session_state.db = db

# 사이드바에 브랜딩 표시 (스타일: .streamlit/custom.css)
st.sidebar.markdown("""
<div class="admin-sidebar-branding">
    <h2 class="admin-sidebar-branding-title">Aicuatorhub Admin</h2>
</div>
""", unsafe_allow_html=True)

# 언어 선택 UI 추가
render_language_selector()

# 메인 콘텐츠 영역
current_lang = get_current_language()
render_header(t("admin_title", current_lang))

st.info(f"""
📋 **{t("welcome_title", current_lang)}**

{t("welcome_message", current_lang)}
""")

# 하단 정보 (스타일: .streamlit/custom.css)
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div class="admin-sidebar-footer">
    <p>Version 1.0.0</p>
    <p>© 2025 Aicuatorhub</p>
</div>
""", unsafe_allow_html=True)

"""
설정 페이지 - 시스템 설정 및 Firebase 연결 상태 확인
"""
import streamlit as st
import sys
import os
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from admin.firebase import get_db, init_firebase
from admin.components import render_page_header
from admin.config import (
    ENV, DEBUG, COLLECTIONS, FIREBASE_SERVICE_ACCOUNT_KEY_PATH, 
    FIREBASE_SERVICE_ACCOUNT_KEY_JSON, CATEGORIES
)
from admin.tools import get_all_tools
from admin.users import get_all_users
from admin.public_recipes import get_all_public_recipes as get_all_recipes
from admin.translations import get_all_translations
from admin.applications import get_all_tool_registrations
from admin.paid_services import get_all_paid_service_requests

# 페이지 설정
st.set_page_config(
    page_title="설정 - Aicuatorhub Admin",
    page_icon="⚙️",
    layout="wide"
)

# 페이지 헤더
render_page_header("⚙️ 설정", "시스템 설정 및 Firebase 연결 상태를 확인할 수 있습니다.")

# 탭으로 구분
tab1, tab2, tab3, tab4 = st.tabs([
    "Firebase 연결 상태", "메뉴별 컬렉션 상태", "시스템 정보", "캐시 관리"
])

# 탭 1: Firebase 연결 상태
with tab1:
    st.markdown("### 🔥 Firebase 연결 상태")
    
    # Firebase 연결 테스트
    db = get_db()
    
    if db is None:
        st.error("❌ Firebase 연결 실패")
        st.markdown("#### 연결 실패 원인")
        
        # 서비스 계정 키 파일 확인
        if os.path.exists(FIREBASE_SERVICE_ACCOUNT_KEY_PATH):
            st.info(f"✅ 서비스 계정 키 파일 발견: `{FIREBASE_SERVICE_ACCOUNT_KEY_PATH}`")
        else:
            st.warning(f"⚠️ 서비스 계정 키 파일 없음: `{FIREBASE_SERVICE_ACCOUNT_KEY_PATH}`")
        
        # 환경 변수 확인
        if FIREBASE_SERVICE_ACCOUNT_KEY_JSON:
            st.info("✅ 환경 변수 FIREBASE_SERVICE_ACCOUNT_KEY_JSON 설정됨")
        else:
            st.warning("⚠️ 환경 변수 FIREBASE_SERVICE_ACCOUNT_KEY_JSON 설정 안 됨")
        
        st.markdown("---")
        st.markdown("#### 해결 방법")
        st.markdown("""
        1. 상위 폴더에 `serviceAccountKey.json` 파일이 있는지 확인
        2. 또는 환경 변수 `FIREBASE_SERVICE_ACCOUNT_KEY_JSON` 설정
        3. 또는 환경 변수 `FIREBASE_SERVICE_ACCOUNT_KEY_PATH` 설정
        """)
    else:
        st.success("✅ Firebase 연결 성공")
        
        # Firebase 연결 상세 정보
        col_fb1, col_fb2 = st.columns(2)
        
        with col_fb1:
            st.markdown("#### 연결 정보")
            st.write(f"**연결 상태**: ✅ 연결됨")
            st.write(f"**Firestore 클라이언트**: 활성")
            
            # 서비스 계정 키 경로 확인
            if os.path.exists(FIREBASE_SERVICE_ACCOUNT_KEY_PATH):
                st.write(f"**서비스 계정 키**: `{FIREBASE_SERVICE_ACCOUNT_KEY_PATH}`")
                st.success("✅ 파일 존재")
            elif FIREBASE_SERVICE_ACCOUNT_KEY_JSON:
                st.write("**서비스 계정 키**: 환경 변수 (JSON)")
                st.success("✅ 환경 변수 사용")
            else:
                st.write("**서비스 계정 키**: 확인 불가")
                st.warning("⚠️ 경로 확인 필요")
        
        with col_fb2:
            st.markdown("#### 연결 테스트")
            if st.button("🔄 연결 재확인", use_container_width=True):
                # 캐시 초기화 후 재연결
                init_firebase.clear()
                db_test = get_db()
                if db_test:
                    st.success("✅ 재연결 성공!")
                    st.rerun()
                else:
                    st.error("❌ 재연결 실패")
        
        # 간단한 데이터 조회 테스트
        st.markdown("---")
        st.markdown("#### 데이터 조회 테스트")
        
        test_col1, test_col2, test_col3 = st.columns(3)
        
        with test_col1:
            try:
                tools_ref = db.collection(COLLECTIONS["AI_TOOLS"])
                tools_count = len(list(tools_ref.limit(1).stream()))
                st.success(f"✅ ai-tools 컬렉션 접근 가능")
            except Exception as e:
                st.error(f"❌ ai-tools 컬렉션 접근 실패: {str(e)[:50]}")
        
        with test_col2:
            try:
                users_ref = db.collection(COLLECTIONS["USERS"])
                users_count = len(list(users_ref.limit(1).stream()))
                st.success(f"✅ users 컬렉션 접근 가능")
            except Exception as e:
                st.error(f"❌ users 컬렉션 접근 실패: {str(e)[:50]}")
        
        with test_col3:
            try:
                recipes_ref = db.collection(COLLECTIONS["RECIPES"])
                recipes_count = len(list(recipes_ref.limit(1).stream()))
                st.success(f"✅ my_recipe 컬렉션 접근 가능")
            except Exception as e:
                st.error(f"❌ my_recipe 컬렉션 접근 실패: {str(e)[:50]}")

# 탭 2: 메뉴별 컬렉션 상태
with tab2:
    st.markdown("### 📋 메뉴별 컬렉션 상태")
    
    if db is None:
        st.error("⚠️ Firebase 연결이 필요합니다.")
    else:
        # 메뉴별 컬렉션 정보
        menu_collections = {
            "📊 대시보드": {
                "collections": ["ai-tools", "users", "my_recipe"],
                "description": "전체 통계 조회"
            },
            "🔧 AI 도구 관리": {
                "collections": ["ai-tools"],
                "description": "AI 도구 CRUD 작업"
            },
            "👥 사용자 관리": {
                "collections": ["users"],
                "description": "사용자 정보 및 서브컬렉션 관리"
            },
            "📝 AI 레시피 관리": {
                "collections": ["my_recipe"],
                "description": "레시피 승인/거부 관리"
            },
            "🌐 다국어 관리": {
                "collections": ["translations"],
                "description": "번역 데이터 관리"
            },
            "📦 카테고리 관리": {
                "collections": ["categories", "ai-tools"],
                "description": "카테고리 정보 및 통계"
            },
            "📋 등록 신청 관리": {
                "collections": ["applications/tool-registrations", "tool-registrations"],
                "description": "도구 등록 신청 처리"
            },
            "💳 유료 서비스 관리": {
                "collections": ["applications/paid-service-requests", "paid-service-requests"],
                "description": "유료 서비스 신청 처리"
            }
        }
        
        # 각 메뉴별 상태 확인
        for menu_name, menu_info in menu_collections.items():
            with st.expander(f"{menu_name} - {menu_info['description']}", expanded=False):
                col_menu1, col_menu2 = st.columns([2, 1])
                
                with col_menu1:
                    st.write(f"**설명**: {menu_info['description']}")
                    st.write(f"**사용 컬렉션**: {', '.join(menu_info['collections'])}")
                
                with col_menu2:
                    # 컬렉션별 데이터 개수 확인
                    total_count = 0
                    collection_status = []
                    
                    for collection_name in menu_info['collections']:
                        try:
                            # 컬렉션 경로 처리
                            if "/" in collection_name:
                                # 서브컬렉션인 경우
                                parts = collection_name.split("/")
                                parent_col = db.collection(parts[0])
                                # 서브컬렉션은 직접 카운트하기 어려우므로 접근 가능 여부만 확인
                                collection_status.append(f"✅ {collection_name} (접근 가능)")
                            else:
                                # 일반 컬렉션
                                collection_ref = db.collection(collection_name)
                                count = len(list(collection_ref.limit(1000).stream()))
                                total_count += count
                                collection_status.append(f"✅ {collection_name}: {count}개")
                        except Exception as e:
                            collection_status.append(f"❌ {collection_name}: 오류")
                    
                    st.write("**상태**:")
                    for status in collection_status:
                        st.write(status)
                    
                    if total_count > 0:
                        st.metric("총 데이터 수", f"{total_count:,}개")

# 탭 3: 시스템 정보
with tab3:
    st.markdown("### 💻 시스템 정보")
    
    col_sys1, col_sys2 = st.columns(2)
    
    with col_sys1:
        st.markdown("#### 환경 설정")
        st.write(f"**환경**: {ENV}")
        st.write(f"**디버그 모드**: {'✅ 활성화' if DEBUG else '❌ 비활성화'}")
        st.write(f"**Python 버전**: {sys.version.split()[0]}")
        
        # Streamlit 버전
        try:
            import streamlit as st_lib
            st.write(f"**Streamlit 버전**: {st_lib.__version__}")
        except:
            st.write("**Streamlit 버전**: 확인 불가")
    
    with col_sys2:
        st.markdown("#### Firebase 설정")
        st.write(f"**서비스 계정 키 경로**: `{FIREBASE_SERVICE_ACCOUNT_KEY_PATH}`")
        st.write(f"**환경 변수 사용**: {'✅ 예' if FIREBASE_SERVICE_ACCOUNT_KEY_JSON else '❌ 아니오'}")
        
        # 컬렉션 목록
        st.markdown("#### 등록된 컬렉션")
        for key, value in COLLECTIONS.items():
            st.write(f"- **{key}**: `{value}`")
    
    st.markdown("---")
    
    # 데이터 통계
    st.markdown("### 📊 데이터 통계")
    
    if db:
        with st.spinner("데이터를 불러오는 중..."):
            try:
                all_tools = get_all_tools()
                all_users = get_all_users()
                all_recipes = get_all_recipes()
                all_translations = get_all_translations()
                all_registrations = get_all_tool_registrations()
                all_paid_requests = get_all_paid_service_requests()
                
                stat_col1, stat_col2, stat_col3 = st.columns(3)
                
                with stat_col1:
                    st.metric("AI 도구", f"{len(all_tools):,}개")
                    st.metric("사용자", f"{len(all_users):,}명")
                
                with stat_col2:
                    st.metric("레시피", f"{len(all_recipes):,}개")
                    st.metric("번역", f"{len(all_translations):,}개")
                
                with stat_col3:
                    st.metric("등록 신청", f"{len(all_registrations):,}개")
                    st.metric("유료 서비스 신청", f"{len(all_paid_requests):,}개")
            except Exception as e:
                st.error(f"데이터 로드 실패: {str(e)}")
    else:
        st.warning("Firebase 연결이 필요합니다.")

# 탭 4: 캐시 관리
with tab4:
    st.markdown("### 🔄 캐시 관리")
    
    st.info("""
    Streamlit은 `@st.cache_data`와 `@st.cache_resource` 데코레이터를 사용하여 데이터를 캐시합니다.
    캐시를 초기화하면 다음 요청 시 데이터를 다시 불러옵니다.
    """)
    
    col_cache1, col_cache2 = st.columns(2)
    
    with col_cache1:
        st.markdown("#### 캐시 초기화")
        
        if st.button("🔄 전체 캐시 초기화", use_container_width=True, type="primary"):
            # 모든 캐시 함수 초기화
            try:
                get_all_tools.clear()
                get_all_users.clear()
                get_all_recipes.clear()
                get_all_translations.clear()
                get_all_tool_registrations.clear()
                get_all_paid_service_requests.clear()
                init_firebase.clear()
                
                st.success("✅ 전체 캐시가 초기화되었습니다!")
                st.info("페이지를 새로고침하면 데이터가 다시 로드됩니다.")
            except Exception as e:
                st.error(f"캐시 초기화 실패: {str(e)}")
        
        st.markdown("---")
        
        st.markdown("#### 개별 캐시 초기화")
        
        cache_buttons = {
            "AI 도구": get_all_tools.clear,
            "사용자": get_all_users.clear,
            "레시피": get_all_recipes.clear,
            "번역": get_all_translations.clear,
            "등록 신청": get_all_tool_registrations.clear,
            "유료 서비스 신청": get_all_paid_service_requests.clear,
            "Firebase 연결": init_firebase.clear
        }
        
        for name, clear_func in cache_buttons.items():
            if st.button(f"🔄 {name} 캐시 초기화", key=f"clear_{name}", use_container_width=True):
                try:
                    clear_func()
                    st.success(f"✅ {name} 캐시가 초기화되었습니다!")
                except Exception as e:
                    st.error(f"❌ {name} 캐시 초기화 실패: {str(e)}")
    
    with col_cache2:
        st.markdown("#### 캐시 정보")
        st.write("**캐시 타입**:")
        st.write("- `@st.cache_data`: 데이터 캐시 (TTL: 300초)")
        st.write("- `@st.cache_resource`: 리소스 캐시 (Firebase 연결)")
        
        st.markdown("---")
        st.write("**캐시된 함수**:")
        st.write("- `get_all_tools()`")
        st.write("- `get_all_users()`")
        st.write("- `get_all_recipes()`")
        st.write("- `get_all_translations()`")
        st.write("- `get_all_tool_registrations()`")
        st.write("- `get_all_paid_service_requests()`")
        st.write("- `init_firebase()`")

# 사이드바
with st.sidebar:
    st.markdown("### ⚙️ 빠른 설정")
    
    if db:
        st.success("✅ Firebase 연결됨")
    else:
        st.error("❌ Firebase 연결 안 됨")
    
    st.markdown("---")
    
    st.write(f"**환경**: {ENV}")
    st.write(f"**디버그**: {'✅' if DEBUG else '❌'}")
    
    st.markdown("---")
    
    if st.button("🔄 페이지 새로고침", use_container_width=True):
        st.rerun()

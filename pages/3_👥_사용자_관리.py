"""
사용자 관리 페이지
"""
import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime, date
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from admin.firebase import get_db
from admin.components import render_page_header
from admin.config import COLLECTIONS, SUPPORTED_LANGUAGES
from admin.users import (
    get_all_users, get_user_by_id, update_user, delete_user,
    get_user_favorites, get_user_reviews, get_user_ai_sets
)
from admin.user_recipes import get_user_recipes
from admin.utils import convert_firestore_data, format_datetime, format_value

# 페이지 설정
st.set_page_config(
    page_title="사용자 관리 - Aicuatorhub Admin",
    page_icon="👥",
    layout="wide"
)

# Firebase 연결
db = get_db()
if db is None:
    st.error("⚠️ Firebase 연결에 실패했습니다.")
    st.stop()

# 세션 상태 초기화
if 'selected_user_id' not in st.session_state:
    st.session_state.selected_user_id = None
if 'selected_user_data' not in st.session_state:
    st.session_state.selected_user_data = None
if 'is_edit_mode' not in st.session_state:
    st.session_state.is_edit_mode = False

# 페이지 헤더
render_page_header("👥 사용자 관리", "사용자 정보를 조회하고 관리할 수 있습니다.")

# 검색 및 필터
st.markdown("### 🔍 검색 필터")
filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

with filter_col1:
    search_query = st.text_input(
        "검색어 (이메일/UID)",
        key="user_search_query",
        placeholder="이메일 또는 UID 입력..."
    )

with filter_col2:
    member_type_filter = st.selectbox(
        "회원 타입",
        ["전체", "basic", "premium", "admin"],
        key="member_type_filter"
    )

with filter_col3:
    country_filter = st.selectbox(
        "국가",
        ["전체", "KR", "US", "JP", "CN", "기타"],
        key="country_filter"
    )

with filter_col4:
    language_filter = st.selectbox(
        "언어",
        ["전체"] + [info["native"] for info in SUPPORTED_LANGUAGES.values()],
        key="language_filter"
    )

st.markdown("---")

# 사용자 목록 로드 및 필터링
all_users = get_all_users()

# 필터링 적용
filtered_users = all_users

if search_query:
    search_lower = search_query.lower()
    filtered_users = [
        u for u in filtered_users
        if search_lower in str(u.get("email", "")).lower()
        or search_lower in str(u.get("uid", "")).lower()
    ]

if member_type_filter != "전체":
    filtered_users = [
        u for u in filtered_users
        if u.get("memberType", "") == member_type_filter
    ]

if country_filter != "전체":
    filtered_users = [
        u for u in filtered_users
        if u.get("country", "") == country_filter
    ]

if language_filter != "전체":
    lang_code = [k for k, v in SUPPORTED_LANGUAGES.items() if v["native"] == language_filter]
    if lang_code:
        filtered_users = [
            u for u in filtered_users
            if u.get("language", "") == lang_code[0]
        ]

# 결과 정보
st.info(f"📊 검색 결과: {len(filtered_users)}개 (전체 {len(all_users)}개)")

# 사용자 목록 표시
if filtered_users:
    # 테이블 데이터 준비
    table_data = []
    for idx, user in enumerate(filtered_users, 1):
        row = {
            "No.": idx,
            "UID": user.get("uid", "-"),
            "이메일": user.get("email", "-"),
            "고객번호": user.get("custNo", "-"),
            "회원타입": user.get("memberType", "-"),
            "언어": SUPPORTED_LANGUAGES.get(user.get("language", ""), {}).get("native", user.get("language", "-")),
            "국가": user.get("country", "-"),
            "가입일": format_datetime(user.get("registeredDate"), "%Y-%m-%d") if user.get("registeredDate") else "-",
            "마케팅동의": "✅" if user.get("marketingConsent", False) else "❌",
            "_id": user.get("uid", "")
        }
        table_data.append(row)
    
    df = pd.DataFrame(table_data)
    
    # AgGrid 설정
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_selection('single')
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
    gb.configure_default_column(
        resizable=True,
        sortable=True,
        filterable=True,
        editable=False,
        minWidth=100
    )
    
    # 컬럼 폭 설정
    gb.configure_column("No.", width=60, pinned='left')
    gb.configure_column("UID", width=200)
    gb.configure_column("이메일", width=250)
    gb.configure_column("고객번호", width=120)
    gb.configure_column("회원타입", width=100)
    gb.configure_column("언어", width=100)
    gb.configure_column("국가", width=80)
    gb.configure_column("가입일", width=120)
    gb.configure_column("마케팅동의", width=100)
    gb.configure_column("_id", hide=True)
    
    grid_options = gb.build()
    
    st.markdown("### 📋 사용자 목록")
    st.caption("💡 행을 클릭하여 선택하면 상세 정보가 표시됩니다.")
    
    # AgGrid 출력
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        height=400,
        width='100%',
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True,
        key="user_grid",
        theme='streamlit'
    )
    
    # 선택 이벤트 처리
    selected_rows = grid_response.get('selected_rows', [])
    
    if isinstance(selected_rows, pd.DataFrame):
        selected_rows = selected_rows.to_dict('records')
    elif selected_rows is None:
        selected_rows = []
    
    if len(selected_rows) > 0:
        try:
            selected_row = selected_rows[0]
            clicked_user_id = str(selected_row.get('_id', '')).strip()
            
            if clicked_user_id and st.session_state.selected_user_id != clicked_user_id:
                st.session_state.selected_user_id = clicked_user_id
                user_data = get_user_by_id(clicked_user_id)
                if user_data:
                    st.session_state.selected_user_data = user_data
                else:
                    st.warning(f"사용자를 찾을 수 없습니다: {clicked_user_id}")
                    st.session_state.selected_user_data = None
                st.rerun()
        except Exception as e:
            if st.session_state.get('debug_mode', False):
                st.error(f"데이터 매칭 오류: {e}")
else:
    st.warning("검색 결과가 없습니다.")

# 상세 정보 영역
st.markdown("---")
st.markdown("### 📝 사용자 상세 정보")

if st.session_state.selected_user_data:
    user = st.session_state.selected_user_data
    
    # 탭으로 구분
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "기본 정보", "즐겨찾기", "리뷰", "AI 세트", "나의 리시피", "전체 데이터"
    ])
    
    with tab1:
        st.markdown("#### 기본 정보")
        
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            if st.session_state.is_edit_mode:
                user_email = st.text_input("이메일", value=user.get("email", ""), key="edit_email")
                user_cust_no = st.number_input("고객번호", value=int(user.get("custNo", 0)), key="edit_cust_no")
                user_member_type = st.selectbox(
                    "회원 타입",
                    ["basic", "premium", "admin"],
                    index=["basic", "premium", "admin"].index(user.get("memberType", "basic")) if user.get("memberType") in ["basic", "premium", "admin"] else 0,
                    key="edit_member_type"
                )
            else:
                st.text_input("UID", value=user.get("uid", ""), disabled=True, key="view_uid")
                st.text_input("이메일", value=user.get("email", ""), disabled=True, key="view_email")
                st.number_input("고객번호", value=int(user.get("custNo", 0)), disabled=True, key="view_cust_no")
                st.text_input("회원 타입", value=user.get("memberType", "-"), disabled=True, key="view_member_type")
        
        with col_info2:
            if st.session_state.is_edit_mode:
                user_language = st.selectbox(
                    "언어",
                    list(SUPPORTED_LANGUAGES.keys()),
                    index=list(SUPPORTED_LANGUAGES.keys()).index(user.get("language", "ko")) if user.get("language") in SUPPORTED_LANGUAGES else 0,
                    format_func=lambda x: SUPPORTED_LANGUAGES[x]["native"],
                    key="edit_language"
                )
                user_country = st.text_input("국가", value=user.get("country", ""), key="edit_country")
                user_marketing = st.checkbox("마케팅 동의", value=user.get("marketingConsent", False), key="edit_marketing")
            else:
                lang_code = user.get("language", "")
                lang_name = SUPPORTED_LANGUAGES.get(lang_code, {}).get("native", lang_code)
                st.text_input("언어", value=lang_name, disabled=True, key="view_language")
                st.text_input("국가", value=user.get("country", "-"), disabled=True, key="view_country")
                st.checkbox("마케팅 동의", value=user.get("marketingConsent", False), disabled=True, key="view_marketing")
                st.text_input("가입일", value=format_datetime(user.get("registeredDate")), disabled=True, key="view_registered_date")
        
        # 편집 모드일 때 저장 버튼
        if st.session_state.is_edit_mode:
            col_save1, col_save2 = st.columns([1, 1])
            with col_save1:
                if st.button("💾 저장", use_container_width=True, type="primary"):
                    update_data = {
                        "email": user_email,
                        "custNo": user_cust_no,
                        "memberType": user_member_type,
                        "language": user_language,
                        "country": user_country,
                        "marketingConsent": user_marketing
                    }
                    
                    if update_user(st.session_state.selected_user_id, update_data):
                        st.success("✅ 사용자 정보가 업데이트되었습니다!")
                        st.session_state.is_edit_mode = False
                        get_all_users.clear()
                        get_user_by_id.clear()
                        st.rerun()
            
            with col_save2:
                if st.button("❌ 취소", use_container_width=True):
                    st.session_state.is_edit_mode = False
                    st.rerun()
    
    with tab2:
        st.markdown("#### 즐겨찾기")
        
        favorites = get_user_favorites(st.session_state.selected_user_id)
        
        if favorites:
            fav_data = []
            for fav in favorites:
                fav_data.append({
                    "도구 ID": fav.get("toolId", "-"),
                    "추가일": format_datetime(fav.get("favoritedAt")),
                })
            
            fav_df = pd.DataFrame(fav_data)
            st.dataframe(fav_df, use_container_width=True)
            st.info(f"총 {len(favorites)}개의 즐겨찾기가 있습니다.")
        else:
            st.info("즐겨찾기가 없습니다.")
    
    with tab3:
        st.markdown("#### 리뷰")
        
        reviews = get_user_reviews(st.session_state.selected_user_id)
        
        if reviews:
            review_data = []
            for review in reviews:
                review_data.append({
                    "리뷰 ID": review.get("id", "-"),
                    "도구 ID": review.get("toolId", "-"),
                    "평점": review.get("rating", 0),
                    "내용": review.get("content", "-")[:100] + "..." if len(str(review.get("content", ""))) > 100 else review.get("content", "-"),
                    "작성일": format_datetime(review.get("createdAt")),
                })
            
            review_df = pd.DataFrame(review_data)
            st.dataframe(review_df, use_container_width=True)
            st.info(f"총 {len(reviews)}개의 리뷰가 있습니다.")
        else:
            st.info("리뷰가 없습니다.")
    
    with tab4:
        st.markdown("#### AI 세트")
        
        ai_sets = get_user_ai_sets(st.session_state.selected_user_id)
        
        if ai_sets:
            for ai_set in ai_sets:
                with st.expander(f"{ai_set.get('title', 'N/A')} ({ai_set.get('id', 'N/A')})"):
                    st.write(f"**세트 ID**: {ai_set.get('setId', '-')}")
                    st.write(f"**제목**: {ai_set.get('title', '-')}")
                    st.write(f"**도구 ID 목록**: {format_value(ai_set.get('toolIds', []))}")
                    st.write(f"**생성일**: {format_datetime(ai_set.get('createdAt'))}")
            
            st.info(f"총 {len(ai_sets)}개의 AI 세트가 있습니다.")
        else:
            st.info("AI 세트가 없습니다.")
    
    with tab5:
        st.markdown("#### 나의 리시피")
        
        user_recipes = get_user_recipes(st.session_state.selected_user_id)
        
        if user_recipes:
            # 레시피 목록 테이블
            recipe_data = []
            for recipe in user_recipes:
                status = recipe.get("status", "pending")
                status_badge = {
                    "pending": "⏳ 대기",
                    "approved": "✅ 승인",
                    "rejected": "❌ 거부",
                    "draft": "📝 초안"
                }.get(status, status)
                
                recipe_data.append({
                    "레시피 ID": recipe.get("id", "-"),
                    "제목": recipe.get("title", "-"),
                    "카테고리": recipe.get("my_recipe_category", recipe.get("category", "-")),
                    "상태": status_badge,
                    "조회수": recipe.get("views", 0),
                    "좋아요": recipe.get("likes", 0),
                    "생성일": format_datetime(recipe.get("createdAt"), "%Y-%m-%d") if recipe.get("createdAt") else "-",
                })
            
            if recipe_data:
                recipe_df = pd.DataFrame(recipe_data)
                st.dataframe(recipe_df, use_container_width=True)
            
            st.info(f"총 {len(user_recipes)}개의 레시피가 있습니다.")
            
            # 레시피 상세 보기
            if user_recipes:
                st.markdown("---")
                st.markdown("#### 레시피 상세 정보")
                
                selected_recipe_id = st.selectbox(
                    "레시피 선택",
                    [r.get("id", "") for r in user_recipes],
                    format_func=lambda x: next((r.get("title", r.get("id", "-")) for r in user_recipes if r.get("id") == x), x),
                    key="user_recipe_select"
                )
                
                if selected_recipe_id:
                    selected_recipe = next((r for r in user_recipes if r.get("id") == selected_recipe_id), None)
                    if selected_recipe:
                        with st.expander("레시피 상세 정보", expanded=True):
                            col_recipe1, col_recipe2 = st.columns(2)
                            
                            with col_recipe1:
                                st.write(f"**레시피 ID**: {selected_recipe.get('id', '-')}")
                                st.write(f"**제목**: {selected_recipe.get('title', '-')}")
                                st.write(f"**카테고리**: {selected_recipe.get('my_recipe_category', selected_recipe.get('category', '-'))}")
                                st.write(f"**상태**: {status_badge}")
                            
                            with col_recipe2:
                                st.write(f"**조회수**: {selected_recipe.get('views', 0)}")
                                st.write(f"**좋아요**: {selected_recipe.get('likes', 0)}")
                                st.write(f"**생성일**: {format_datetime(selected_recipe.get('createdAt'))}")
                            
                            if selected_recipe.get("description"):
                                st.write(f"**설명**: {selected_recipe.get('description')}")
                            
                            if selected_recipe.get("content"):
                                st.markdown("**내용**:")
                                st.markdown(selected_recipe.get("content"))
                            
                            # 포함된 도구 목록
                            tool_ids = selected_recipe.get("toolIds", selected_recipe.get("tools", []))
                            if tool_ids:
                                st.write(f"**포함된 도구**: {format_value(tool_ids)}")
        else:
            st.info("레시피가 없습니다.")
    
    with tab6:
        st.markdown("#### 전체 데이터 (JSON)")
        user_json = convert_firestore_data(user)
        st.json(user_json)
    
    # 액션 버튼
    st.markdown("---")
    col_action1, col_action2, col_action3 = st.columns([1, 1, 2])
    
    with col_action1:
        if st.button("✏️ 수정하기", use_container_width=True, type="primary"):
            st.session_state.is_edit_mode = True
            st.rerun()
    
    with col_action2:
        if st.session_state.get('confirm_delete_user', False):
            if st.button("✅ 확인 (삭제)", use_container_width=True, type="primary"):
                if delete_user(st.session_state.selected_user_id):
                    st.success("삭제 완료!")
                    st.session_state.selected_user_data = None
                    st.session_state.selected_user_id = None
                    st.session_state.confirm_delete_user = False
                    get_all_users.clear()
                    get_user_by_id.clear()
                    st.rerun()
            if st.button("❌ 취소", use_container_width=True):
                st.session_state.confirm_delete_user = False
                st.rerun()
        else:
            if st.button("🗑️ 삭제하기", use_container_width=True):
                st.session_state.confirm_delete_user = True
                st.warning("⚠️ 정말 삭제하시겠습니까? 확인 버튼을 클릭하면 삭제됩니다.")
                st.rerun()
else:
    st.info("👆 위의 테이블에서 행을 선택하여 사용자 상세 정보를 조회하세요.")

# 사이드바 통계
with st.sidebar:
    st.markdown("### 📊 통계")
    
    # 전체 사용자 수
    st.metric("전체 사용자 수", f"{len(all_users):,}명")
    
    # 회원 타입별 통계
    if all_users:
        st.markdown("#### 회원 타입별 분포")
        member_types = {}
        for user in all_users:
            member_type = user.get("memberType", "unknown")
            member_types[member_type] = member_types.get(member_type, 0) + 1
        
        for mtype, count in member_types.items():
            st.write(f"**{mtype}**: {count}명")
    
    # 국가별 통계
    if all_users:
        st.markdown("#### 국가별 분포 (상위 5개)")
        countries = {}
        for user in all_users:
            country = user.get("country", "unknown")
            countries[country] = countries.get(country, 0) + 1
        
        sorted_countries = sorted(countries.items(), key=lambda x: x[1], reverse=True)[:5]
        for country, count in sorted_countries:
            st.write(f"**{country}**: {count}명")
    
    # 캐시 초기화
    if st.button("🔄 캐시 초기화", use_container_width=True):
        get_all_users.clear()
        get_user_by_id.clear()
        st.success("캐시가 초기화되었습니다!")
        st.rerun()

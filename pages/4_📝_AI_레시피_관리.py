"""
AI 레시피 관리 페이지
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
from admin.config import COLLECTIONS, CATEGORIES
from admin.public_recipes import (
    get_all_public_recipes as get_all_recipes, 
    get_public_recipe_by_id as get_recipe_by_id, 
    update_public_recipe as update_recipe, 
    create_public_recipe as create_recipe, 
    delete_public_recipe as delete_recipe,
    approve_public_recipe as approve_recipe, 
    reject_public_recipe as reject_recipe
)
from admin.utils import convert_firestore_data, format_datetime, format_value

# 페이지 설정
st.set_page_config(
    page_title="AI 레시피 관리 - Aicuatorhub Admin",
    page_icon="📝",
    layout="wide"
)

# Firebase 연결
db = get_db()
if db is None:
    st.error("⚠️ Firebase 연결에 실패했습니다.")
    st.stop()

# 세션 상태 초기화
if 'selected_recipe_id' not in st.session_state:
    st.session_state.selected_recipe_id = None
if 'selected_recipe_data' not in st.session_state:
    st.session_state.selected_recipe_data = None
if 'is_edit_mode' not in st.session_state:
    st.session_state.is_edit_mode = False

# 페이지 헤더
render_page_header("📝 AI 레시피 관리", "AI 레시피를 조회하고 관리할 수 있습니다.")

# 검색 및 필터
st.markdown("### 🔍 검색 필터")
filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

with filter_col1:
    search_query = st.text_input(
        "검색어 (제목/내용)",
        key="recipe_search_query",
        placeholder="검색어 입력..."
    )

with filter_col2:
    category_filter = st.selectbox(
        "레시피 카테고리",
        ["전체"] + [cat for cat in CATEGORIES.keys() if cat != "전체"],
        key="recipe_category_filter"
    )

with filter_col3:
    status_filter = st.selectbox(
        "상태",
        ["전체", "pending", "approved", "rejected", "draft"],
        key="recipe_status_filter"
    )

with filter_col4:
    date_from = st.date_input(
        "등록일 (시작)",
        value=None,
        key="recipe_date_from"
    )

st.markdown("---")

# 레시피 목록 로드 및 필터링
all_recipes = get_all_recipes()

# 필터링 적용
filtered_recipes = all_recipes

if search_query:
    search_lower = search_query.lower()
    filtered_recipes = [
        r for r in filtered_recipes
        if search_lower in str(r.get("title", "")).lower()
        or search_lower in str(r.get("description", "")).lower()
        or search_lower in str(r.get("content", "")).lower()
    ]

if category_filter != "전체":
    filtered_recipes = [
        r for r in filtered_recipes
        if category_filter in str(r.get("my_recipe_category", ""))
        or category_filter in str(r.get("category", ""))
    ]

if status_filter != "전체":
    filtered_recipes = [
        r for r in filtered_recipes
        if r.get("status", "pending") == status_filter
    ]

if date_from:
    filtered_recipes = [
        r for r in filtered_recipes
        if r.get("createdAt") and datetime.fromisoformat(r.get("createdAt").replace("Z", "+00:00")).date() >= date_from
    ]

# 결과 정보
st.info(f"📊 검색 결과: {len(filtered_recipes)}개 (전체 {len(all_recipes)}개)")

# 레시피 목록 표시
if filtered_recipes:
    # 테이블 데이터 준비
    table_data = []
    for idx, recipe in enumerate(filtered_recipes, 1):
        # 상태에 따른 배지
        status = recipe.get("status", "pending")
        status_badge = {
            "pending": "⏳ 대기",
            "approved": "✅ 승인",
            "rejected": "❌ 거부",
            "draft": "📝 초안"
        }.get(status, status)
        
        row = {
            "No.": idx,
            "레시피 ID": recipe.get("id", "-"),
            "제목": recipe.get("title", "-"),
            "카테고리": recipe.get("my_recipe_category", recipe.get("category", "-")),
            "작성자": recipe.get("author", recipe.get("userId", "-")),
            "상태": status_badge,
            "조회수": recipe.get("views", 0),
            "좋아요": recipe.get("likes", 0),
            "등록일": format_datetime(recipe.get("createdAt"), "%Y-%m-%d") if recipe.get("createdAt") else "-",
            "_id": recipe.get("id", "")
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
    gb.configure_column("레시피 ID", width=200)
    gb.configure_column("제목", width=300)
    gb.configure_column("카테고리", width=150)
    gb.configure_column("작성자", width=150)
    gb.configure_column("상태", width=100)
    gb.configure_column("조회수", width=80)
    gb.configure_column("좋아요", width=80)
    gb.configure_column("등록일", width=120)
    gb.configure_column("_id", hide=True)
    
    grid_options = gb.build()
    
    st.markdown("### 📋 레시피 목록")
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
        key="recipe_grid",
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
            clicked_recipe_id = str(selected_row.get('_id', '')).strip()
            
            if clicked_recipe_id and st.session_state.selected_recipe_id != clicked_recipe_id:
                st.session_state.selected_recipe_id = clicked_recipe_id
                recipe_data = get_recipe_by_id(clicked_recipe_id)
                if recipe_data:
                    st.session_state.selected_recipe_data = recipe_data
                else:
                    st.warning(f"레시피를 찾을 수 없습니다: {clicked_recipe_id}")
                    st.session_state.selected_recipe_data = None
                st.rerun()
        except Exception as e:
            if st.session_state.get('debug_mode', False):
                st.error(f"데이터 매칭 오류: {e}")
else:
    st.warning("검색 결과가 없습니다.")

# 상세 정보 영역
st.markdown("---")
st.markdown("### 📝 레시피 상세 정보")

if st.session_state.selected_recipe_data:
    recipe = st.session_state.selected_recipe_data
    
    # 탭으로 구분
    tab1, tab2, tab3 = st.tabs([
        "기본 정보", "레시피 내용", "전체 데이터"
    ])
    
    with tab1:
        st.markdown("#### 기본 정보")
        
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            st.text_input("레시피 ID", value=recipe.get("id", ""), disabled=True, key="view_recipe_id")
            st.text_input("제목", value=recipe.get("title", "-"), disabled=True, key="view_title")
            st.text_input("카테고리", value=recipe.get("my_recipe_category", recipe.get("category", "-")), disabled=True, key="view_category")
            st.text_input("작성자", value=recipe.get("author", recipe.get("userId", "-")), disabled=True, key="view_author")
        
        with col_info2:
            status = recipe.get("status", "pending")
            status_options = {
                "pending": "⏳ 대기",
                "approved": "✅ 승인",
                "rejected": "❌ 거부",
                "draft": "📝 초안"
            }
            st.text_input("상태", value=status_options.get(status, status), disabled=True, key="view_status")
            st.number_input("조회수", value=int(recipe.get("views", 0)), disabled=True, key="view_views")
            st.number_input("좋아요", value=int(recipe.get("likes", 0)), disabled=True, key="view_likes")
            st.text_input("등록일", value=format_datetime(recipe.get("createdAt")), disabled=True, key="view_created_at")
            if recipe.get("updatedAt"):
                st.text_input("수정일", value=format_datetime(recipe.get("updatedAt")), disabled=True, key="view_updated_at")
        
        # 레시피 설명
        st.text_area("설명", value=recipe.get("description", ""), disabled=True, height=100, key="view_description")
        
        # 포함된 도구 목록
        tool_ids = recipe.get("toolIds", recipe.get("tools", []))
        if tool_ids:
            st.markdown("#### 포함된 도구")
            st.write(format_value(tool_ids))
    
    with tab2:
        st.markdown("#### 레시피 내용")
        
        # 레시피 내용 표시 (마크다운 또는 텍스트)
        content = recipe.get("content", recipe.get("steps", ""))
        if content:
            st.markdown(content)
        else:
            st.info("레시피 내용이 없습니다.")
        
        # 레시피 단계 (steps가 배열인 경우)
        steps = recipe.get("steps", [])
        if isinstance(steps, list) and len(steps) > 0:
            st.markdown("#### 레시피 단계")
            for idx, step in enumerate(steps, 1):
                st.markdown(f"**{idx}. {step}**")
    
    with tab3:
        st.markdown("#### 전체 데이터 (JSON)")
        recipe_json = convert_firestore_data(recipe)
        st.json(recipe_json)
    
    # 액션 버튼
    st.markdown("---")
    col_action1, col_action2, col_action3, col_action4 = st.columns(4)
    
    current_status = recipe.get("status", "pending")
    
    with col_action1:
        if current_status == "pending":
            if st.button("✅ 승인", use_container_width=True, type="primary"):
                if approve_recipe(st.session_state.selected_recipe_id):
                    st.success("레시피가 승인되었습니다!")
                    get_all_recipes.clear()
                    get_recipe_by_id.clear()
                    st.rerun()
    
    with col_action2:
        if current_status == "pending":
            if st.session_state.get('show_rejection_form', False):
                rejection_reason = st.text_input("거부 사유", key="rejection_reason")
                col_reject1, col_reject2 = st.columns(2)
                with col_reject1:
                    if st.button("✅ 거부 확인", use_container_width=True, type="primary"):
                        if reject_recipe(st.session_state.selected_recipe_id, rejection_reason):
                            st.success("레시피가 거부되었습니다!")
                            st.session_state.show_rejection_form = False
                            get_all_recipes.clear()
                            get_recipe_by_id.clear()
                            st.rerun()
                with col_reject2:
                    if st.button("❌ 취소", use_container_width=True):
                        st.session_state.show_rejection_form = False
                        st.rerun()
            else:
                if st.button("❌ 거부", use_container_width=True):
                    st.session_state.show_rejection_form = True
                    st.rerun()
    
    with col_action3:
        if st.button("✏️ 수정하기", use_container_width=True):
            st.session_state.is_edit_mode = True
            st.rerun()
    
    with col_action4:
        if st.session_state.get('confirm_delete_recipe', False):
            if st.button("✅ 확인 (삭제)", use_container_width=True, type="primary"):
                if delete_recipe(st.session_state.selected_recipe_id):
                    st.success("삭제 완료!")
                    st.session_state.selected_recipe_data = None
                    st.session_state.selected_recipe_id = None
                    st.session_state.confirm_delete_recipe = False
                    get_all_recipes.clear()
                    get_recipe_by_id.clear()
                    st.rerun()
            if st.button("❌ 취소", use_container_width=True):
                st.session_state.confirm_delete_recipe = False
                st.rerun()
        else:
            if st.button("🗑️ 삭제하기", use_container_width=True):
                st.session_state.confirm_delete_recipe = True
                st.warning("⚠️ 정말 삭제하시겠습니까? 확인 버튼을 클릭하면 삭제됩니다.")
                st.rerun()
else:
    st.info("👆 위의 테이블에서 행을 선택하여 레시피 상세 정보를 조회하세요.")

# 사이드바 통계
with st.sidebar:
    st.markdown("### 📊 통계")
    
    # 전체 레시피 수
    st.metric("전체 레시피 수", f"{len(all_recipes):,}개")
    
    # 상태별 통계
    if all_recipes:
        st.markdown("#### 상태별 분포")
        status_counts = {}
        for recipe in all_recipes:
            status = recipe.get("status", "pending")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in status_counts.items():
            status_name = {
                "pending": "⏳ 대기",
                "approved": "✅ 승인",
                "rejected": "❌ 거부",
                "draft": "📝 초안"
            }.get(status, status)
            st.write(f"**{status_name}**: {count}개")
    
    # 카테고리별 통계
    if all_recipes:
        st.markdown("#### 카테고리별 분포 (상위 5개)")
        category_counts = {}
        for recipe in all_recipes:
            category = recipe.get("my_recipe_category", recipe.get("category", "기타"))
            category_counts[category] = category_counts.get(category, 0) + 1
        
        sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        for category, count in sorted_categories:
            st.write(f"**{category}**: {count}개")
    
    # 캐시 초기화
    if st.button("🔄 캐시 초기화", use_container_width=True):
        get_all_recipes.clear()
        get_recipe_by_id.clear()
        st.success("캐시가 초기화되었습니다!")
        st.rerun()

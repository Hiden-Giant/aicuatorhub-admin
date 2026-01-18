"""
AI 도구 관리 페이지
기존 단일 AI 도구 관리 패널 기능을 통합
"""
import streamlit as st
import sys
import os
import json
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from admin.firebase import get_db
from admin.components import render_page_header, render_language_selector
from admin.config import COLLECTIONS
from admin.tools import (
    get_all_tools, get_tool_by_id, update_tool, create_tool, delete_tool, normalize_tool_id
)
from admin.utils import convert_firestore_data, format_value

# 페이지 설정
st.set_page_config(
    page_title="AI 도구 관리 - Aicuatorhub Admin",
    page_icon="🔧",
    layout="wide"
)

# Firebase 연결
db = get_db()
if db is None:
    st.error("⚠️ Firebase 연결에 실패했습니다.")
    st.stop()

# 언어 선택 UI (사이드바에 표시)
render_language_selector()

# 세션 상태 초기화
if 'selected_tool_id' not in st.session_state:
    st.session_state.selected_tool_id = None
if 'selected_tool_data' not in st.session_state:
    st.session_state.selected_tool_data = None
if 'manual_input_tool_id' not in st.session_state:
    st.session_state.manual_input_tool_id = ""
if 'current_submenu' not in st.session_state:
    st.session_state.current_submenu = "도구 조회"

# 페이지 헤더
render_page_header("🔧 AI 도구 관리", "AI 도구를 조회, 등록, 수정, 삭제할 수 있습니다.")

# 서브 메뉴
submenu = st.radio(
    "메뉴",
    ["도구 조회", "도구 등록", "도구 수정"],
    key="ai_tools_submenu",
    horizontal=True
)

st.session_state.current_submenu = submenu
st.markdown("---")

# 사이드바 통계
with st.sidebar:
    st.markdown("### 📊 통계")
    all_tools_for_stats = get_all_tools()
    all_tools_count = len(all_tools_for_stats)
    st.metric("전체 도구 수", f"{all_tools_count:,}개")
    
    # 캐시 초기화 버튼
    if st.button("🔄 캐시 초기화", use_container_width=True):
        get_all_tools.clear()
        get_tool_by_id.clear()
        st.success("캐시가 초기화되었습니다!")
        st.rerun()

# 도구 조회
if submenu == "도구 조회":
    # 상단 헤더
    col_header1, col_header2, col_header3 = st.columns([2, 1, 1])
    with col_header1:
        st.markdown("### 📋 AI 도구 조회")
    with col_header2:
        if st.button("🔄 새로고침", use_container_width=True):
            get_all_tools.clear()
            get_tool_by_id.clear()
            st.rerun()
    with col_header3:
        if st.button("📥 Excel 다운로드", use_container_width=True):
            st.info("Excel 다운로드 기능은 준비 중입니다.")
    
    st.markdown("---")
    
    # 검색 필터 영역
    st.markdown("### 🔍 검색 필터")
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
    
    with filter_col1:
        search_query = st.text_input(
            "검색어 (이름/설명/URL)", 
            key="search_query", 
            placeholder="검색어 입력...",
            help="도구 이름, 설명, URL로 검색할 수 있습니다"
        )
        primary_category_filter = st.selectbox(
            "주 카테고리",
            ["전체"] + ["비즈니스 & 생산성", "텍스트 & 오디오", "이미지 & 비디오", "개발자 도구", "기타"],
            key="primary_category_filter"
        )
    
    with filter_col2:
        sub_category_filter = st.selectbox(
            "하위 카테고리",
            ["전체", "마케팅·세일즈 AI 도구", "생산성/비즈니스", "Chatbot/CS", "기타"],
            key="sub_category_filter"
        )
        status_filter = st.selectbox(
            "상태",
            ["전체", "active", "inactive"],
            key="status_filter"
        )
    
    with filter_col3:
        verified_filter = st.selectbox(
            "검증 여부",
            ["전체", "검증됨", "미검증"],
            key="verified_filter"
        )
        featured_filter = st.selectbox(
            "추천 도구",
            ["전체", "추천", "일반"],
            key="featured_filter"
        )
    
    with filter_col4:
        rating_min = st.number_input("최소 평점", min_value=0.0, max_value=5.0, value=0.0, step=0.1, key="rating_min")
        review_count_min = st.number_input("최소 리뷰 수", min_value=0, value=0, key="review_count_min")
    
    st.markdown("---")
    
    # 도구 목록 로드 및 필터링
    all_tools = get_all_tools()
    
    # 필터링 적용
    filtered_tools = all_tools
    
    if search_query:
        search_lower = search_query.lower()
        filtered_tools = [
            t for t in filtered_tools
            if search_lower in t.get("name", "").lower()
            or search_lower in t.get("description", "").lower()
            or search_lower in t.get("websiteUrl", "").lower()
        ]
    
    if primary_category_filter != "전체":
        filtered_tools = [
            t for t in filtered_tools
            if primary_category_filter in str(t.get("primaryCategory", ""))
        ]
    
    if sub_category_filter != "전체":
        filtered_tools = [
            t for t in filtered_tools
            if sub_category_filter in str(t.get("subCategoryKr", ""))
        ]
    
    if status_filter != "전체":
        filtered_tools = [
            t for t in filtered_tools
            if t.get("status", "") == status_filter
        ]
    
    if verified_filter == "검증됨":
        filtered_tools = [t for t in filtered_tools if t.get("verified", False)]
    elif verified_filter == "미검증":
        filtered_tools = [t for t in filtered_tools if not t.get("verified", False)]
    
    if featured_filter == "추천":
        filtered_tools = [t for t in filtered_tools if t.get("featured", False)]
    elif featured_filter == "일반":
        filtered_tools = [t for t in filtered_tools if not t.get("featured", False)]
    
    if rating_min > 0:
        filtered_tools = [
            t for t in filtered_tools
            if float(t.get("rating", 0)) >= rating_min
        ]
    
    if review_count_min > 0:
        filtered_tools = [
            t for t in filtered_tools
            if int(t.get("reviewCount", 0)) >= review_count_min
        ]
    
    # 결과 정보
    st.info(f"📊 검색 결과: {len(filtered_tools)}개 (전체 {len(all_tools)}개)")
    
    # 도구 목록 표시
    if filtered_tools:
        # DataFrame 변환
        columns = [
            "id", "name", "categories", "categoryDisplayNames", "company", "cons",
            "description", "featured", "features", "featuresEn", "featuresKr",
            "imageUrl", "logoFileName", "logoUrl", "popularityScore", "pricing",
            "primaryCategory", "primaryCategoryEn", "primaryCategoryKr", "pros",
            "rating", "reviewCount", "source", "sourceUrl", "status",
            "subCategoryEn", "subCategoryKr", "tagsEn", "tagsKr", "verified", "websiteUrl"
        ]
        
        rows = []
        for tool in filtered_tools:
            row = {}
            for col in columns:
                value = tool.get(col, "")
                row[col] = format_value(value)
            rows.append(row)
        
        df = pd.DataFrame(rows)
        
        # 페이지당 표시 개수 선택
        page_size = st.selectbox("페이지당 표시 개수", [10, 25, 50, 100], index=1, key="page_size")
        
        st.markdown("### 📊 도구 목록")
        st.caption("💡 행을 클릭하여 선택하면 상세 정보가 표시됩니다.")
        
        # AgGrid 설정
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_selection('single')
        gb.configure_pagination(
            paginationAutoPageSize=False, 
            paginationPageSize=page_size
        )
        gb.configure_default_column(
            resizable=True,
            sortable=True,
            filterable=True,
            editable=False,
            groupable=False,
            minWidth=150,
            width=200,
            wrapText=True,
            autoHeight=False
        )
        
        # 주요 컬럼별 폭 설정
        if 'id' in df.columns:
            gb.configure_column('id', pinned='left', width=180, minWidth=150)
        if 'name' in df.columns:
            gb.configure_column('name', width=250, minWidth=200)
        if 'description' in df.columns:
            gb.configure_column('description', width=400, minWidth=300, wrapText=True)
        if 'company' in df.columns:
            gb.configure_column('company', width=200, minWidth=150)
        if 'websiteUrl' in df.columns:
            gb.configure_column('websiteUrl', width=300, minWidth=250)
        if 'status' in df.columns:
            gb.configure_column('status', width=120, minWidth=100)
        if 'rating' in df.columns:
            gb.configure_column('rating', width=100, minWidth=80)
        if 'reviewCount' in df.columns:
            gb.configure_column('reviewCount', width=120, minWidth=100)
        if 'primaryCategory' in df.columns:
            gb.configure_column('primaryCategory', width=200, minWidth=150)
        if 'primaryCategoryKr' in df.columns:
            gb.configure_column('primaryCategoryKr', width=200, minWidth=150)
        if 'subCategoryKr' in df.columns:
            gb.configure_column('subCategoryKr', width=200, minWidth=150)
        
        grid_options = gb.build()
        
        # AgGrid 출력
        grid_response = AgGrid(
            df,
            gridOptions=grid_options,
            height=400,
            width='100%',
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            allow_unsafe_jscode=True,
            key="tool_grid",
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
                clicked_tool_id = str(selected_row.get('id', '')).strip()
                
                # 선택된 도구 ID가 변경되었거나, 데이터가 없는 경우 항상 업데이트
                if clicked_tool_id:
                    # 선택이 변경되었거나, 현재 데이터가 없거나, 다른 도구를 선택한 경우
                    needs_update = (
                        st.session_state.selected_tool_id != clicked_tool_id or
                        st.session_state.selected_tool_data is None or
                        (st.session_state.selected_tool_data and 
                         st.session_state.selected_tool_data.get('id') != clicked_tool_id)
                    )
                    
                    if needs_update:
                        st.session_state.selected_tool_id = clicked_tool_id
                        st.session_state.manual_input_tool_id = clicked_tool_id
                        
                        # 항상 최신 데이터를 가져오기 위해 캐시 무효화 후 조회
                        tool_data = get_tool_by_id(clicked_tool_id)
                        if tool_data:
                            st.session_state.selected_tool_data = tool_data
                        else:
                            st.warning(f"도구를 찾을 수 없습니다: {clicked_tool_id}")
                            st.session_state.selected_tool_data = None
                        
                        st.rerun()
            except (KeyError, IndexError, AttributeError) as e:
                if st.session_state.get('debug_mode', False):
                    st.error(f"데이터 매칭 오류: {e}")
        else:
            # 선택이 해제된 경우
            if st.session_state.selected_tool_id is not None:
                st.session_state.selected_tool_data = None
                st.session_state.selected_tool_id = None
                st.session_state.manual_input_tool_id = ""
        
        # 수동 입력란
        st.markdown("---")
        col_manual1, col_manual2 = st.columns([3, 1])
        with col_manual1:
            manual_tool_id = st.text_input(
                "도구 ID 직접 입력/확인", 
                value=st.session_state.manual_input_tool_id, 
                key="manual_tool_id_input",
                placeholder="도구 ID 입력...",
                help="도구 ID를 입력하고 조회 버튼을 클릭하거나, 그리드에서 행을 선택하면 자동으로 조회됩니다"
            )
        with col_manual2:
            if st.button("ID로 직접 조회", use_container_width=True):
                if manual_tool_id:
                    manual_tool_id = str(manual_tool_id).strip()
                    st.session_state.selected_tool_data = None
                    st.session_state.selected_tool_id = manual_tool_id
                    st.session_state.manual_input_tool_id = manual_tool_id
                    with st.spinner("상세 정보를 불러오는 중..."):
                        tool_data = get_tool_by_id(manual_tool_id)
                        if tool_data:
                            st.session_state.selected_tool_data = tool_data
                        else:
                            st.warning(f"도구를 찾을 수 없습니다: {manual_tool_id}")
                            st.session_state.selected_tool_data = None
                    st.rerun()
                else:
                    st.warning("도구 ID를 입력해주세요.")
        
        # 상세 정보 영역
        st.markdown("---")
        st.markdown("### 📝 상세 정보")
        
        if st.session_state.selected_tool_data:
            tool = st.session_state.selected_tool_data
            
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "기본 정보", "카테고리 정보", "태그/기능", "평가 정보", "전체 데이터"
            ])
            
            with tab1:
                col_info1, col_info2 = st.columns([2, 1])
                with col_info1:
                    st.text_input("도구 ID", value=tool.get('id', ''), disabled=True, key="detail_id")
                    st.text_input("도구 이름", value=tool.get('name', ''), disabled=True, key="detail_name")
                    st.text_input("회사명", value=tool.get('company', ''), disabled=True, key="detail_company")
                    st.text_area("설명", value=tool.get('description', ''), disabled=True, height=100, key="detail_description")
                    st.text_input("웹사이트 URL", value=tool.get('websiteUrl', ''), disabled=True, key="detail_url")
                with col_info2:
                    logo_url = tool.get('logoUrl')
                    image_url = tool.get('imageUrl')
                    valid_logo_url = logo_url if logo_url and isinstance(logo_url, str) and logo_url.strip() else None
                    valid_image_url = image_url if image_url and isinstance(image_url, str) and image_url.strip() else None
                    
                    display_url = valid_logo_url or valid_image_url
                    if display_url:
                        try:
                            st.image(display_url, width=200)
                        except Exception as e:
                            st.warning(f"이미지를 불러올 수 없습니다: {str(e)}")
                    else:
                        st.info("이미지 없음")
                    
                    st.text_input("로고 파일명", value=tool.get('logoFileName', ''), disabled=True, key="detail_logo_file")
                    st.text_input("이미지 URL", value=tool.get('imageUrl', '') if tool.get('imageUrl') else '', disabled=True, key="detail_image_url")
                    st.text_input("로고 URL", value=tool.get('logoUrl', '') if tool.get('logoUrl') else '', disabled=True, key="detail_logo_url")
            
            with tab2:
                col_cat1, col_cat2 = st.columns(2)
                with col_cat1:
                    st.text_input("주 카테고리", value=tool.get('primaryCategory', ''), disabled=True, key="detail_primary_cat")
                    st.text_input("주 카테고리 (한글)", value=tool.get('primaryCategoryKr', ''), disabled=True, key="detail_primary_cat_kr")
                    st.text_input("주 카테고리 (영문)", value=tool.get('primaryCategoryEn', ''), disabled=True, key="detail_primary_cat_en")
                with col_cat2:
                    st.text_input("하위 카테고리 (한글)", value=tool.get('subCategoryKr', ''), disabled=True, key="detail_sub_cat_kr")
                    st.text_input("하위 카테고리 (영문)", value=tool.get('subCategoryEn', ''), disabled=True, key="detail_sub_cat_en")
                    st.text_area("카테고리 배열", value=format_value(tool.get('categories', [])), disabled=True, height=80, key="detail_categories")
                    st.text_area("카테고리 표시명", value=format_value(tool.get('categoryDisplayNames', {})), disabled=True, height=80, key="detail_cat_display")
            
            with tab3:
                col_tag1, col_tag2 = st.columns(2)
                with col_tag1:
                    st.text_area("태그 (한글)", value=format_value(tool.get('tagsKr', [])), disabled=True, height=100, key="detail_tags_kr")
                    st.text_area("태그 (영문)", value=format_value(tool.get('tagsEn', [])), disabled=True, height=100, key="detail_tags_en")
                with col_tag2:
                    st.text_area("기능 (한글)", value=format_value(tool.get('featuresKr', [])), disabled=True, height=100, key="detail_features_kr")
                    st.text_area("기능 (영문)", value=format_value(tool.get('featuresEn', [])), disabled=True, height=100, key="detail_features_en")
                    st.text_area("기능 (일반)", value=format_value(tool.get('features', [])), disabled=True, height=100, key="detail_features")
            
            with tab4:
                col_rating1, col_rating2 = st.columns(2)
                with col_rating1:
                    st.number_input("평점", value=float(tool.get('rating', 0)), disabled=True, key="detail_rating")
                    st.number_input("리뷰 개수", value=int(tool.get('reviewCount', 0)), disabled=True, key="detail_review_count")
                    st.number_input("인기 점수", value=int(tool.get('popularityScore', 0)), disabled=True, key="detail_popularity")
                with col_rating2:
                    st.text_input("상태", value=tool.get('status', ''), disabled=True, key="detail_status")
                    st.checkbox("검증됨", value=tool.get('verified', False), disabled=True, key="detail_verified")
                    st.checkbox("추천 도구", value=tool.get('featured', False), disabled=True, key="detail_featured")
                    st.text_input("출처", value=tool.get('source', ''), disabled=True, key="detail_source")
                    st.text_input("출처 URL", value=tool.get('sourceUrl', ''), disabled=True, key="detail_source_url")
            
            with tab5:
                tool_json = convert_firestore_data(tool)
                st.text_area("전체 데이터 (JSON)", value=json.dumps(tool_json, ensure_ascii=False, indent=2, default=str), height=500, disabled=True, key="detail_json")
            
            # 액션 버튼
            st.markdown("---")
            col_action1, col_action2, col_action3 = st.columns([1, 1, 2])
            with col_action1:
                if st.button("✏️ 수정하기", use_container_width=True, type="primary"):
                    st.session_state.current_submenu = "도구 수정"
                    st.rerun()
            with col_action2:
                if st.button("🗑️ 삭제하기", use_container_width=True):
                    if delete_tool(tool.get('id')):
                        st.success("삭제 완료!")
                        st.session_state.selected_tool_data = None
                        st.session_state.selected_tool_id = None
                        get_all_tools.clear()
                        get_tool_by_id.clear()
                        st.rerun()
        else:
            st.info("👆 위의 그리드에서 행을 선택하거나 도구 ID를 입력하여 상세 정보를 조회하세요.")
    else:
        st.warning("검색 결과가 없습니다.")

# 도구 등록
elif submenu == "도구 등록":
    st.markdown("### ➕ 새 AI 도구 등록")
    
    with st.form("new_tool_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            tool_name = st.text_input("도구 이름 *", key="new_name")
            company = st.text_input("회사명", key="new_company")
            website_url = st.text_input("웹사이트 URL", key="new_url")
            description = st.text_area("설명 *", key="new_description", height=100)
            primary_category = st.text_input("주 카테고리", key="new_primary_category")
            primary_category_kr = st.text_input("주 카테고리 (한글)", key="new_primary_category_kr")
            primary_category_en = st.text_input("주 카테고리 (영문)", key="new_primary_category_en")
        
        with col2:
            sub_category_kr = st.text_input("하위 카테고리 (한글)", key="new_sub_category_kr")
            sub_category_en = st.text_input("하위 카테고리 (영문)", key="new_sub_category_en")
            rating = st.number_input("평점", min_value=0.0, max_value=5.0, value=0.0, step=0.1, key="new_rating")
            review_count = st.number_input("리뷰 개수", min_value=0, value=0, key="new_review_count")
            verified = st.checkbox("검증됨", key="new_verified")
            featured = st.checkbox("추천 도구", key="new_featured")
            status = st.selectbox("상태", ["active", "inactive"], key="new_status")
        
        tags_kr = st.text_input("태그 (한글) - 쉼표로 구분", key="new_tags_kr")
        tags_en = st.text_input("태그 (영문) - 쉼표로 구분", key="new_tags_en")
        features_kr = st.text_area("기능 (한글) - 줄바꿈으로 구분", key="new_features_kr", height=80)
        features_en = st.text_area("기능 (영문) - 줄바꿈으로 구분", key="new_features_en", height=80)
        
        submitted = st.form_submit_button("등록", use_container_width=True, type="primary")
        
        if submitted:
            if not tool_name or not description:
                st.error("도구 이름과 설명은 필수입니다.")
            else:
                tool_id = normalize_tool_id(tool_name)
                existing_tool = get_tool_by_id(tool_id)
                if existing_tool:
                    st.error(f"이미 존재하는 도구 ID입니다: {tool_id}")
                else:
                    tool_data = {
                        "name": tool_name,
                        "company": company if company else None,
                        "websiteUrl": website_url if website_url else None,
                        "description": description,
                        "primaryCategory": primary_category if primary_category else None,
                        "primaryCategoryKr": primary_category_kr if primary_category_kr else None,
                        "primaryCategoryEn": primary_category_en if primary_category_en else None,
                        "subCategoryKr": sub_category_kr if sub_category_kr else None,
                        "subCategoryEn": sub_category_en if sub_category_en else None,
                        "rating": rating,
                        "reviewCount": review_count,
                        "verified": verified,
                        "featured": featured,
                        "status": status,
                        "tags": [],
                        "tagsKr": [tag.strip() for tag in tags_kr.split(",") if tag.strip()] if tags_kr else [],
                        "tagsEn": [tag.strip() for tag in tags_en.split(",") if tag.strip()] if tags_en else [],
                        "featuresKr": [f.strip() for f in features_kr.split("\n") if f.strip()] if features_kr else [],
                        "featuresEn": [f.strip() for f in features_en.split("\n") if f.strip()] if features_en else [],
                        "categories": [],
                    }
                    
                    if create_tool(tool_id, tool_data):
                        st.success(f"✅ 도구가 성공적으로 등록되었습니다! (ID: {tool_id})")
                        st.balloons()
                        # 폼 초기화를 위해 리런
                        st.rerun()

# 도구 수정
elif submenu == "도구 수정":
    st.markdown("### ✏️ AI 도구 수정")
    
    tool_id_input = st.text_input("도구 ID 입력", value=st.session_state.selected_tool_id or "", key="edit_tool_id")
    
    if tool_id_input:
        tool = get_tool_by_id(tool_id_input)
        
        if tool:
            st.success(f"✅ 도구를 찾았습니다: {tool.get('name', 'N/A')}")
            
            with st.form("edit_tool_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    tool_name = st.text_input("도구 이름 *", value=tool.get("name", ""), key="edit_name")
                    company = st.text_input("회사명", value=tool.get("company", ""), key="edit_company")
                    website_url = st.text_input("웹사이트 URL", value=tool.get("websiteUrl", ""), key="edit_url")
                    description = st.text_area("설명 *", value=tool.get("description", ""), key="edit_description", height=100)
                    primary_category = st.text_input("주 카테고리", value=tool.get("primaryCategory", ""), key="edit_primary_category")
                    primary_category_kr = st.text_input("주 카테고리 (한글)", value=tool.get("primaryCategoryKr", ""), key="edit_primary_category_kr")
                    primary_category_en = st.text_input("주 카테고리 (영문)", value=tool.get("primaryCategoryEn", ""), key="edit_primary_category_en")
                
                with col2:
                    sub_category_kr = st.text_input("하위 카테고리 (한글)", value=tool.get("subCategoryKr", ""), key="edit_sub_category_kr")
                    sub_category_en = st.text_input("하위 카테고리 (영문)", value=tool.get("subCategoryEn", ""), key="edit_sub_category_en")
                    rating = st.number_input("평점", min_value=0.0, max_value=5.0, value=float(tool.get("rating", 0)), step=0.1, key="edit_rating")
                    review_count = st.number_input("리뷰 개수", min_value=0, value=int(tool.get("reviewCount", 0)), key="edit_review_count")
                    verified = st.checkbox("검증됨", value=tool.get("verified", False), key="edit_verified")
                    featured = st.checkbox("추천 도구", value=tool.get("featured", False), key="edit_featured")
                    status = st.selectbox("상태", ["active", "inactive"], index=0 if tool.get("status") == "active" else 1, key="edit_status")
                
                tags_kr = st.text_input("태그 (한글) - 쉼표로 구분", value=", ".join(tool.get("tagsKr", [])), key="edit_tags_kr")
                tags_en = st.text_input("태그 (영문) - 쉼표로 구분", value=", ".join(tool.get("tagsEn", [])), key="edit_tags_en")
                features_kr = st.text_area("기능 (한글) - 줄바꿈으로 구분", value="\n".join(tool.get("featuresKr", [])), key="edit_features_kr", height=80)
                features_en = st.text_area("기능 (영문) - 줄바꿈으로 구분", value="\n".join(tool.get("featuresEn", [])), key="edit_features_en", height=80)
                
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("💾 저장", use_container_width=True, type="primary")
                with col2:
                    cancel = st.form_submit_button("❌ 취소", use_container_width=True)
                
                if submitted:
                    if not tool_name or not description:
                        st.error("도구 이름과 설명은 필수입니다.")
                    else:
                        update_data = {
                            "name": tool_name,
                            "company": company if company else None,
                            "websiteUrl": website_url if website_url else None,
                            "description": description,
                            "primaryCategory": primary_category if primary_category else None,
                            "primaryCategoryKr": primary_category_kr if primary_category_kr else None,
                            "primaryCategoryEn": primary_category_en if primary_category_en else None,
                            "subCategoryKr": sub_category_kr if sub_category_kr else None,
                            "subCategoryEn": sub_category_en if sub_category_en else None,
                            "rating": rating,
                            "reviewCount": review_count,
                            "verified": verified,
                            "featured": featured,
                            "status": status,
                            "tagsKr": [tag.strip() for tag in tags_kr.split(",") if tag.strip()] if tags_kr else [],
                            "tagsEn": [tag.strip() for tag in tags_en.split(",") if tag.strip()] if tags_en else [],
                            "featuresKr": [f.strip() for f in features_kr.split("\n") if f.strip()] if features_kr else [],
                            "featuresEn": [f.strip() for f in features_en.split("\n") if f.strip()] if features_en else [],
                        }
                        
                        if update_tool(tool_id_input, update_data):
                            st.success("✅ 도구 정보가 업데이트되었습니다!")
                            get_all_tools.clear()
                            get_tool_by_id.clear()
                            st.rerun()
        else:
            st.error(f"❌ 도구를 찾을 수 없습니다: {tool_id_input}")

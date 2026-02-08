"""
다국어 관리 페이지
HTML mockup을 기반으로 구현
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
from admin.components import render_page_header, render_language_selector
from admin.config import (
    COLLECTIONS, SUPPORTED_LANGUAGES, TRANSLATION_TYPES, 
    ORIGIN_LANGUAGES, REQUIRED_LANGUAGES
)
from admin.translations import (
    get_all_translations, get_translation_by_id, update_translation,
    create_translation, delete_translation, format_translation_for_display,
    get_all_tool_translations, get_tool_translation_by_id, get_tool_translations_by_tool_id,
    get_tool_translations_by_language, format_tool_translation_for_display,
    update_tool_translation, create_tool_translation
)
from admin.utils import convert_firestore_data, format_datetime

# 페이지 설정
st.set_page_config(
    page_title="다국어 관리 - Aicuatorhub Admin",
    page_icon="🌐",
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
if 'selected_translation_id' not in st.session_state:
    st.session_state.selected_translation_id = None
if 'selected_translation_data' not in st.session_state:
    st.session_state.selected_translation_data = None
if 'is_edit_mode' not in st.session_state:
    st.session_state.is_edit_mode = False
if 'search_applied' not in st.session_state:
    st.session_state.search_applied = False
if 'selected_tool_translation_data' not in st.session_state:
    st.session_state.selected_tool_translation_data = None
if 'selected_tool_id' not in st.session_state:
    st.session_state.selected_tool_id = None
if 'selected_tool_lang' not in st.session_state:
    st.session_state.selected_tool_lang = None

# 페이지 헤더
render_page_header("🌐 다국어 관리", "다국어 번역을 조회하고 관리할 수 있습니다.")

# 번역 목록 (탭·사이드바 공용)
all_translations = get_all_translations()

# 탭 선택 (UI 텍스트 번역 vs AI 도구 콘텐츠 번역)
tab1, tab2 = st.tabs(["📝 UI 텍스트 번역", "🔧 AI 도구 콘텐츠 번역"])

with tab1:
    # 기존 UI 텍스트 번역 관리 코드
    st.markdown("### 📝 UI 텍스트 번역 관리")
    st.caption("사이트 전체 UI 요소의 번역을 관리합니다. (public/lang/*.json 기반)")

    # 검색 패널 (탭 내부에 배치)
    st.markdown("### 🔍 검색 필터")
    search_col1, search_col2, search_col3, search_col4 = st.columns([2, 2, 2, 1])

    with search_col1:
        translation_type_filter = st.selectbox(
            "언어 타입",
            ["전체"] + list(TRANSLATION_TYPES.values()),
            key="translation_type_filter"
        )

    with search_col2:
        search_keyword = st.text_input(
            "검색 키워드 (한국어/영어/메뉴 이름 등)",
            key="search_keyword",
            placeholder="한국어·영어·메뉴 이름으로 검색..."
        )

    with search_col3:
        date_from = st.date_input(
            "등록 날짜 (시작)",
            value=None,
            key="date_from"
        )
        date_to = st.date_input(
            "등록 날짜 (종료)",
            value=None,
            key="date_to"
        )

    with search_col4:
        st.write("")  # 공간
        search_clicked = st.button("🔍 검색", use_container_width=True, type="primary", key="i18n_search_btn")
        if search_clicked:
            st.session_state.search_applied = True
            st.rerun()

    st.markdown("---")

    # 액션 바
    col_action1, col_action2, col_action3, col_action4 = st.columns([2, 1, 1, 1])
    with col_action1:
        st.write("")  # 공간
    with col_action2:
        if st.button("🌍 필수 지원 언어 일괄 번역", use_container_width=True, key="i18n_batch_btn"):
            st.info("일괄 번역 기능은 준비 중입니다.")
    with col_action3:
        if st.button("💾 저장", use_container_width=True, type="primary", key="i18n_save_btn"):
            if st.session_state.selected_translation_data and st.session_state.is_edit_mode:
                st.session_state.is_edit_mode = False
                st.rerun()
    with col_action4:
        if st.button("✏️ 수정", use_container_width=True, key="i18n_edit_btn"):
            if st.session_state.selected_translation_data:
                st.session_state.is_edit_mode = True
                st.rerun()

    st.markdown("---")

    # 필터링 적용 (all_translations는 상단에서 로드)
    filtered_translations = list(all_translations)

    if translation_type_filter != "전체":
        type_key = [k for k, v in TRANSLATION_TYPES.items() if v == translation_type_filter][0]
        filtered_translations = [
            t for t in filtered_translations
            if t.get("type") == type_key
        ]

    # 키워드 검색: 한국어(ko), 영어(en), 메뉴 ID(id) 등 모든 언어 필드 검색
    if search_keyword and search_keyword.strip():
        search_lower = search_keyword.strip().lower()
        searchable_fields = ["id", "ko", "en", "ja", "zh", "ru", "es", "pt", "ar", "vi", "fr", "hi", "ms"]
        filtered_translations = [
            t for t in filtered_translations
            if any(
                search_lower in str(t.get(field, "") or "").lower()
                for field in searchable_fields
            )
        ]

    if date_from:
        filtered_translations = [
            t for t in filtered_translations
            if t.get("createdAt") and datetime.fromisoformat(t.get("createdAt").replace("Z", "+00:00")).date() >= date_from
        ]

    if date_to:
        filtered_translations = [
            t for t in filtered_translations
            if t.get("createdAt") and datetime.fromisoformat(t.get("createdAt").replace("Z", "+00:00")).date() <= date_to
        ]

    # 결과 정보
    st.info(f"📊 검색 결과: {len(filtered_translations)}개 (전체 {len(all_translations)}개)")

    # 번역 목록 테이블
    if filtered_translations:
        # 테이블 데이터 준비
        table_data = []
        for idx, trans in enumerate(filtered_translations, 1):
            formatted = format_translation_for_display(trans, max_length=30)
            row = {
                "No.": idx,
                "언어타입": TRANSLATION_TYPES.get(trans.get("type", ""), trans.get("type", "-")),
                "한국어": formatted.get("ko", "-"),
                "영어": formatted.get("en", "-"),
                "일본어 (JP)": formatted.get("ja", "-"),
                "중국어 (간체)": formatted.get("zh", "-"),
                "스페인어": formatted.get("es", "-"),
                "러시아어": formatted.get("ru", "-"),
                "포르투갈어": formatted.get("pt", "-"),
                "아랍어": formatted.get("ar", "-"),
                "말레이어": formatted.get("ms", "-"),
                "인도네시아어": formatted.get("id", "-"),
                "수정 날짜": format_datetime(trans.get("updatedAt"), "%Y-%m-%d") if trans.get("updatedAt") else "-",
                "수정 ID": trans.get("updatedBy", "-"),
                "_id": trans.get("id", "")  # 내부 사용
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
            minWidth=100,
            wrapText=True
        )

        # 컬럼 폭 설정
        gb.configure_column("No.", width=60, pinned='left')
        gb.configure_column("언어타입", width=100)
        gb.configure_column("한국어", width=200)
        gb.configure_column("영어", width=200)
        gb.configure_column("일본어 (JP)", width=150)
        gb.configure_column("중국어 (간체)", width=150)
        gb.configure_column("스페인어", width=150)
        gb.configure_column("러시아어", width=150)
        gb.configure_column("포르투갈어", width=150)
        gb.configure_column("아랍어", width=150)
        gb.configure_column("말레이어", width=150)
        gb.configure_column("인도네시아어", width=150)
        gb.configure_column("수정 날짜", width=120)
        gb.configure_column("수정 ID", width=100)
        gb.configure_column("_id", hide=True)  # 숨김

        grid_options = gb.build()

        st.markdown("### 📋 번역 목록")
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
            key="translation_grid",
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
                clicked_trans_id = str(selected_row.get('_id', '')).strip()

                if clicked_trans_id and st.session_state.selected_translation_id != clicked_trans_id:
                    st.session_state.selected_translation_id = clicked_trans_id
                    trans_data = get_translation_by_id(clicked_trans_id)
                    if trans_data:
                        st.session_state.selected_translation_data = trans_data
                    else:
                        st.warning(f"번역을 찾을 수 없습니다: {clicked_trans_id}")
                        st.session_state.selected_translation_data = None
                    st.rerun()
            except Exception as e:
                if st.session_state.get('debug_mode', False):
                    st.error(f"데이터 매칭 오류: {e}")
    else:
        st.warning("검색 결과가 없습니다.")

    # 상세 편집 영역 (탭1 내부)
    st.markdown("---")
    st.markdown("### 📝 상세 편집")

    if st.session_state.selected_translation_data:
        trans = st.session_state.selected_translation_data

        # 오리진 언어 섹션
        st.markdown("""
    <div style="
        font-size: 14px;
        font-weight: bold;
        margin-bottom: 10px;
        color: #2c3e50;
        border-left: 3px solid #3498db;
        padding-left: 6px;
    ">오리진 언어</div>
        """, unsafe_allow_html=True)

        origin_col1, origin_col2 = st.columns(2)

        with origin_col1:
            ko_value = trans.get("ko", "")
            if st.session_state.is_edit_mode:
                ko_text = st.text_area(
                    "한국어",
                    value=ko_value,
                    height=80,
                    key="edit_ko",
                    help="오리진 언어 (한국어)"
                )
            else:
                st.text_area(
                    "한국어",
                    value=ko_value,
                    height=80,
                    key="view_ko",
                    disabled=True
                )
                ko_text = ko_value

        with origin_col2:
            en_value = trans.get("en", "")
            if st.session_state.is_edit_mode:
                en_text = st.text_area(
                    "영어",
                    value=en_value,
                    height=80,
                    key="edit_en",
                    help="오리진 언어 (영어)"
                )
            else:
                st.text_area(
                    "영어",
                    value=en_value,
                    height=80,
                    key="view_en",
                    disabled=True
                )
                en_text = en_value

        # 오리진 언어 스타일 적용
        st.markdown("""
        <style>
        div[data-testid="stTextArea"] textarea {
            background-color: #fff9e6 !important;
            border-color: #fae588 !important;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # 필수 지원 언어 섹션
        st.markdown("""
        <div style="
            font-size: 14px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #2c3e50;
            border-left: 3px solid #3498db;
            padding-left: 6px;
        ">필수 지원 언어</div>
        """, unsafe_allow_html=True)

        # 필수 지원 언어를 2열 그리드로 표시
        required_lang_cols = st.columns(2)

        required_lang_data = {}
        lang_index = 0

        # 필수 지원 언어 목록 (HTML mockup 기준)
        required_languages_display = [
            ("ja", "일본어 (JP)"),
            ("zh", "중국어 (간체, CN)"),
            ("es", "스페인어"),
            ("ru", "러시아어"),
            ("pt", "포르투갈어"),
            ("ar", "아랍어"),
            ("ms", "말레이어 (Malay)"),
            ("id", "인도네시아어 (Indonesian)")
        ]

        for lang_code, lang_label in required_languages_display:
            col_idx = lang_index % 2
            with required_lang_cols[col_idx]:
                lang_value = trans.get(lang_code, "")
                if st.session_state.is_edit_mode:
                    lang_text = st.text_area(
                        lang_label,
                        value=lang_value,
                        height=80,
                        key=f"edit_{lang_code}_{lang_index}",
                        help=f"필수 지원 언어 ({lang_label})"
                    )
                    required_lang_data[lang_code] = lang_text
                else:
                    st.text_area(
                        lang_label,
                        value=lang_value,
                        height=80,
                        key=f"view_{lang_code}_{lang_index}",
                        disabled=True
                    )
                    required_lang_data[lang_code] = lang_value
            lang_index += 1

        # 저장 버튼 (편집 모드일 때만)
        if st.session_state.is_edit_mode:
            st.markdown("---")
            col_save1, col_save2 = st.columns([1, 1])
            with col_save1:
                if st.button("💾 저장", use_container_width=True, type="primary", key="i18n_detail_save_btn"):
                    update_data = {
                        "ko": ko_text,
                        "en": en_text,
                        **required_lang_data
                    }

                    if update_translation(st.session_state.selected_translation_id, update_data):
                        st.success("✅ 번역이 업데이트되었습니다!")
                        st.session_state.is_edit_mode = False
                        get_all_translations.clear()
                        get_translation_by_id.clear()
                        st.rerun()

            with col_save2:
                if st.button("❌ 취소", use_container_width=True, key="i18n_detail_cancel_btn"):
                    st.session_state.is_edit_mode = False
                    st.rerun()
    else:
        st.info("👆 위의 테이블에서 행을 선택하여 번역을 편집하세요.")

with tab2:
    # AI 도구 콘텐츠 번역 관리
    st.markdown("### 🔧 AI 도구 콘텐츠 번역 관리")
    st.caption("각 AI 도구의 설명, 장단점 등 콘텐츠 번역을 관리합니다. (tool_translations 컬렉션)")
    
    # AI 도구 번역 검색 필터
    st.markdown("#### 🔍 검색 필터")
    tool_search_col1, tool_search_col2, tool_search_col3, tool_search_col4 = st.columns([2, 2, 2, 1])
    
    with tool_search_col1:
        tool_id_filter = st.text_input(
            "도구 ID",
            key="tool_id_filter",
            placeholder="도구 ID를 입력하세요 (예: tldv)"
        )
    
    with tool_search_col2:
        tool_lang_filter = st.selectbox(
            "언어",
            ["전체"] + list(SUPPORTED_LANGUAGES.keys()),
            key="tool_lang_filter"
        )
    
    with tool_search_col3:
        tool_status_filter = st.selectbox(
            "번역 상태",
            ["전체", "ai_generated", "edited", "reviewed", "stale", "error"],
            key="tool_status_filter"
        )
    
    with tool_search_col4:
        st.write("")  # 공간
        tool_search_clicked = st.button("🔍 검색", use_container_width=True, type="primary", key="tool_search_btn")
        if tool_search_clicked:
            st.session_state.tool_search_applied = True
            st.rerun()
    
    st.markdown("---")
    
    # AI 도구 번역 목록 로드
    all_tool_translations = get_all_tool_translations()
    
    # 필터링 적용
    filtered_tool_translations = all_tool_translations
    
    if tool_id_filter and tool_id_filter.strip():
        tool_id_lower = tool_id_filter.strip().lower()
        filtered_tool_translations = [
            t for t in filtered_tool_translations
            if tool_id_lower in t.get("toolId", "").lower()
        ]
    
    if tool_lang_filter != "전체":
        filtered_tool_translations = [
            t for t in filtered_tool_translations
            if t.get("lang") == tool_lang_filter
        ]
    
    if tool_status_filter != "전체":
        # fields 내부의 status 검색
        filtered_tool_translations = [
            t for t in filtered_tool_translations
            if any(
                field_data.get("status") == tool_status_filter
                for field_data in t.get("fields", {}).values()
                if isinstance(field_data, dict)
            ) or t.get("docStatus") == tool_status_filter
        ]
    
    # 결과 정보
    st.info(f"📊 검색 결과: {len(filtered_tool_translations)}개 (전체 {len(all_tool_translations)}개)")
    
    # AI 도구 번역 목록 테이블
    if filtered_tool_translations:
        table_data = []
        for idx, trans in enumerate(filtered_tool_translations, 1):
            formatted = format_tool_translation_for_display(trans, max_length=30)
            row = {
                "No.": idx,
                "도구 ID": formatted.get("toolId", "-"),
                "언어": formatted.get("lang", "-"),
                "상태": formatted.get("docStatus", "-"),
                "shortDescription": formatted.get("fields", {}).get("shortDescription", {}).get("text", "-") if isinstance(formatted.get("fields"), dict) else "-",
                "description": formatted.get("fields", {}).get("description", {}).get("text", "-") if isinstance(formatted.get("fields"), dict) else "-",
                "pros": formatted.get("fields", {}).get("pros", {}).get("text", "-") if isinstance(formatted.get("fields"), dict) else "-",
                "cons": formatted.get("fields", {}).get("cons", {}).get("text", "-") if isinstance(formatted.get("fields"), dict) else "-",
                "수정 날짜": format_datetime(trans.get("updatedAt"), "%Y-%m-%d") if trans.get("updatedAt") else "-",
                "_id": trans.get("id", ""),
                "_toolId": trans.get("toolId", ""),
                "_lang": trans.get("lang", "")
            }
            table_data.append(row)
        
        df_tool = pd.DataFrame(table_data)
        
        # AgGrid 설정
        gb_tool = GridOptionsBuilder.from_dataframe(df_tool)
        gb_tool.configure_selection('single')
        gb_tool.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
        gb_tool.configure_default_column(
            resizable=True,
            sortable=True,
            filterable=True,
            editable=False,
            minWidth=100,
            wrapText=True
        )
        
        # 컬럼 폭 설정
        gb_tool.configure_column("No.", width=60, pinned='left')
        gb_tool.configure_column("도구 ID", width=120)
        gb_tool.configure_column("언어", width=80)
        gb_tool.configure_column("상태", width=100)
        gb_tool.configure_column("shortDescription", width=200)
        gb_tool.configure_column("description", width=200)
        gb_tool.configure_column("pros", width=150)
        gb_tool.configure_column("cons", width=150)
        gb_tool.configure_column("수정 날짜", width=120)
        gb_tool.configure_column("_id", hide=True)
        gb_tool.configure_column("_toolId", hide=True)
        gb_tool.configure_column("_lang", hide=True)
        
        grid_options_tool = gb_tool.build()
        
        st.markdown("### 📋 AI 도구 번역 목록")
        st.caption("💡 행을 클릭하여 선택하면 상세 정보가 표시됩니다.")
        
        # AgGrid 출력
        grid_response_tool = AgGrid(
            df_tool,
            gridOptions=grid_options_tool,
            height=400,
            width='100%',
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            allow_unsafe_jscode=True,
            key="tool_translation_grid",
            theme='streamlit'
        )
        
        # 선택 이벤트 처리
        selected_rows_tool = grid_response_tool.get('selected_rows', [])
        
        if isinstance(selected_rows_tool, pd.DataFrame):
            selected_rows_tool = selected_rows_tool.to_dict('records')
        elif selected_rows_tool is None:
            selected_rows_tool = []
        
        if len(selected_rows_tool) > 0:
            try:
                selected_row_tool = selected_rows_tool[0]
                clicked_tool_id = selected_row_tool.get('_toolId', '').strip()
                clicked_lang = selected_row_tool.get('_lang', '').strip()
                
                if clicked_tool_id and clicked_lang:
                    tool_trans_data = get_tool_translation_by_id(clicked_tool_id, clicked_lang)
                    if tool_trans_data:
                        st.session_state.selected_tool_translation_data = tool_trans_data
                        st.session_state.selected_tool_id = clicked_tool_id
                        st.session_state.selected_tool_lang = clicked_lang
                    else:
                        st.warning(f"번역을 찾을 수 없습니다: {clicked_tool_id}_{clicked_lang}")
                        st.session_state.selected_tool_translation_data = None
            except Exception as e:
                if st.session_state.get('debug_mode', False):
                    st.error(f"데이터 매칭 오류: {e}")
    else:
        st.warning("검색 결과가 없습니다.")
        if len(all_tool_translations) == 0:
            st.info("💡 AI 도구 콘텐츠 번역 데이터가 없습니다. 번역 작업을 먼저 수행해주세요.")
    
    # AI 도구 번역 상세 편집 영역
    st.markdown("---")
    st.markdown("### 📝 AI 도구 번역 상세 편집")
    
    if st.session_state.get('selected_tool_translation_data'):
        tool_trans = st.session_state.selected_tool_translation_data
        tool_id = st.session_state.get('selected_tool_id', '')
        tool_lang = st.session_state.get('selected_tool_lang', '')
        
        st.info(f"도구 ID: **{tool_id}** | 언어: **{tool_lang}**")
        
        # fields 편집
        fields = tool_trans.get("fields", {})
        edited_fields = {}
        
        for field_name, field_data in fields.items():
            if isinstance(field_data, dict):
                field_text = field_data.get("text", "")
                field_status = field_data.get("status", "ai_generated")
                
                st.markdown(f"#### {field_name}")
                col_field1, col_field2 = st.columns([3, 1])
                
                with col_field1:
                    if isinstance(field_text, list):
                        edited_text = st.text_area(
                            "내용",
                            value="\n".join(str(item) for item in field_text),
                            height=100,
                            key=f"tool_edit_{field_name}_text"
                        )
                        edited_fields[field_name] = {
                            "text": edited_text.split("\n") if edited_text else [],
                            "status": field_status
                        }
                    else:
                        edited_text = st.text_area(
                            "내용",
                            value=str(field_text),
                            height=100,
                            key=f"tool_edit_{field_name}_text"
                        )
                        edited_fields[field_name] = {
                            "text": edited_text,
                            "status": field_status
                        }
                
                with col_field2:
                    edited_status = st.selectbox(
                        "상태",
                        ["ai_generated", "edited", "reviewed", "stale", "error"],
                        index=["ai_generated", "edited", "reviewed", "stale", "error"].index(field_status) if field_status in ["ai_generated", "edited", "reviewed", "stale", "error"] else 0,
                        key=f"tool_edit_{field_name}_status"
                    )
                    edited_fields[field_name]["status"] = edited_status
        
        # 저장 버튼
        col_save_tool1, col_save_tool2 = st.columns([1, 1])
        with col_save_tool1:
            if st.button("💾 저장", use_container_width=True, type="primary", key="tool_save_btn"):
                update_data = {
                    "fields": edited_fields,
                    "docStatus": tool_trans.get("docStatus", "ai_generated")
                }
                
                if update_tool_translation(tool_id, tool_lang, update_data):
                    st.success("✅ AI 도구 번역이 업데이트되었습니다!")
                    get_all_tool_translations.clear()
                    get_tool_translation_by_id.clear()
                    st.session_state.selected_tool_translation_data = None
                    st.rerun()
        
        with col_save_tool2:
            if st.button("❌ 취소", use_container_width=True, key="tool_cancel_btn"):
                st.session_state.selected_tool_translation_data = None
                st.rerun()
    else:
        st.info("👆 위의 테이블에서 행을 선택하여 AI 도구 번역을 편집하세요.")

# 사이드바 통계
with st.sidebar:
    st.markdown("### 📊 통계")
    st.metric("UI 텍스트 번역 수", f"{len(all_translations):,}개")
    st.metric("AI 도구 번역 수", f"{len(get_all_tool_translations()):,}개")
    
    # 언어별 번역 완료율
    if all_translations:
        st.markdown("#### 언어별 완료율")
        for lang_code in REQUIRED_LANGUAGES:
            lang_info = SUPPORTED_LANGUAGES.get(lang_code, {})
            lang_name = lang_info.get("native", lang_code)
            completed = sum(1 for t in all_translations if t.get(lang_code))
            total = len(all_translations)
            percentage = (completed / total * 100) if total > 0 else 0
            st.progress(percentage / 100, text=f"{lang_name}: {completed}/{total} ({percentage:.1f}%)")
    
    # 캐시 초기화
    if st.button("🔄 캐시 초기화", use_container_width=True):
        get_all_translations.clear()
        get_translation_by_id.clear()
        get_all_tool_translations.clear()
        get_tool_translation_by_id.clear()
        get_tool_translations_by_tool_id.clear()
        get_tool_translations_by_language.clear()
        st.success("캐시가 초기화되었습니다!")
        st.rerun()

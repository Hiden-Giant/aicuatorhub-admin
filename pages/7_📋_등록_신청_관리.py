"""
등록 신청 관리 페이지
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
from admin.config import COLLECTIONS
from admin.applications import (
    get_all_tool_registrations, get_registration_by_id, update_registration,
    approve_registration, reject_registration, delete_registration
)
from admin.utils import convert_firestore_data, format_datetime, format_value

# 페이지 설정
st.set_page_config(
    page_title="등록 신청 관리 - Aicuatorhub Admin",
    page_icon="📋",
    layout="wide"
)

# Firebase 연결
db = get_db()
if db is None:
    st.error("⚠️ Firebase 연결에 실패했습니다.")
    st.stop()

# 세션 상태 초기화
if 'selected_registration_id' not in st.session_state:
    st.session_state.selected_registration_id = None
if 'selected_registration_data' not in st.session_state:
    st.session_state.selected_registration_data = None

# 페이지 헤더
render_page_header("📋 등록 신청 관리", "AI 도구 등록 신청을 조회하고 처리할 수 있습니다.")

# 검색 및 필터
st.markdown("### 🔍 검색 필터")
filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

with filter_col1:
    search_query = st.text_input(
        "검색어 (도구명/신청자)",
        key="registration_search_query",
        placeholder="검색어 입력..."
    )

with filter_col2:
    status_filter = st.selectbox(
        "상태",
        ["전체", "pending", "approved", "rejected", "reviewing"],
        key="registration_status_filter"
    )

with filter_col3:
    date_from = st.date_input(
        "신청일 (시작)",
        value=None,
        key="registration_date_from"
    )

with filter_col4:
    date_to = st.date_input(
        "신청일 (종료)",
        value=None,
        key="registration_date_to"
    )

st.markdown("---")

# 등록 신청 목록 로드 및 필터링
all_registrations = get_all_tool_registrations()

# 필터링 적용
filtered_registrations = all_registrations

if search_query:
    search_lower = search_query.lower()
    filtered_registrations = [
        r for r in filtered_registrations
        if search_lower in str(r.get("toolName", "")).lower()
        or search_lower in str(r.get("applicantName", "")).lower()
        or search_lower in str(r.get("applicantEmail", "")).lower()
        or search_lower in str(r.get("company", "")).lower()
    ]

if status_filter != "전체":
    filtered_registrations = [
        r for r in filtered_registrations
        if r.get("status", "pending") == status_filter
    ]

if date_from:
    filtered_registrations = [
        r for r in filtered_registrations
        if r.get("createdAt") and datetime.fromisoformat(r.get("createdAt").replace("Z", "+00:00")).date() >= date_from
    ]

if date_to:
    filtered_registrations = [
        r for r in filtered_registrations
        if r.get("createdAt") and datetime.fromisoformat(r.get("createdAt").replace("Z", "+00:00")).date() <= date_to
    ]

# 결과 정보
st.info(f"📊 검색 결과: {len(filtered_registrations)}개 (전체 {len(all_registrations)}개)")

# 등록 신청 목록 표시
if filtered_registrations:
    # 테이블 데이터 준비
    table_data = []
    for idx, registration in enumerate(filtered_registrations, 1):
        # 상태에 따른 배지
        status = registration.get("status", "pending")
        status_badge = {
            "pending": "⏳ 대기",
            "approved": "✅ 승인",
            "rejected": "❌ 거부",
            "reviewing": "🔍 검토중"
        }.get(status, status)
        
        row = {
            "No.": idx,
            "신청 ID": registration.get("id", "-"),
            "도구명": registration.get("toolName", registration.get("name", "-")),
            "신청자": registration.get("applicantName", registration.get("applicant", "-")),
            "이메일": registration.get("applicantEmail", registration.get("email", "-")),
            "회사": registration.get("company", "-"),
            "상태": status_badge,
            "신청일": format_datetime(registration.get("createdAt"), "%Y-%m-%d") if registration.get("createdAt") else "-",
            "_id": registration.get("id", "")
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
    gb.configure_column("신청 ID", width=200)
    gb.configure_column("도구명", width=250)
    gb.configure_column("신청자", width=150)
    gb.configure_column("이메일", width=200)
    gb.configure_column("회사", width=150)
    gb.configure_column("상태", width=100)
    gb.configure_column("신청일", width=120)
    gb.configure_column("_id", hide=True)
    
    grid_options = gb.build()
    
    st.markdown("### 📋 등록 신청 목록")
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
        key="registration_grid",
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
            clicked_registration_id = str(selected_row.get('_id', '')).strip()
            
            if clicked_registration_id and st.session_state.selected_registration_id != clicked_registration_id:
                st.session_state.selected_registration_id = clicked_registration_id
                registration_data = get_registration_by_id(clicked_registration_id)
                if registration_data:
                    st.session_state.selected_registration_data = registration_data
                else:
                    st.warning(f"등록 신청을 찾을 수 없습니다: {clicked_registration_id}")
                    st.session_state.selected_registration_data = None
                st.rerun()
        except Exception as e:
            if st.session_state.get('debug_mode', False):
                st.error(f"데이터 매칭 오류: {e}")
else:
    st.warning("검색 결과가 없습니다.")

# 상세 정보 영역
st.markdown("---")
st.markdown("### 📝 등록 신청 상세 정보")

if st.session_state.selected_registration_data:
    registration = st.session_state.selected_registration_data
    
    # 탭으로 구분
    tab1, tab2 = st.tabs([
        "기본 정보", "전체 데이터"
    ])
    
    with tab1:
        st.markdown("#### 기본 정보")
        
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            st.text_input("신청 ID", value=registration.get("id", ""), disabled=True, key="view_reg_id")
            st.text_input("도구명", value=registration.get("toolName", registration.get("name", "-")), disabled=True, key="view_tool_name")
            st.text_input("회사명", value=registration.get("company", "-"), disabled=True, key="view_company")
            st.text_area("설명", value=registration.get("description", ""), disabled=True, height=100, key="view_description")
            st.text_input("웹사이트 URL", value=registration.get("websiteUrl", "-"), disabled=True, key="view_website")
        
        with col_info2:
            st.text_input("신청자명", value=registration.get("applicantName", registration.get("applicant", "-")), disabled=True, key="view_applicant")
            st.text_input("이메일", value=registration.get("applicantEmail", registration.get("email", "-")), disabled=True, key="view_email")
            st.text_input("전화번호", value=registration.get("phone", registration.get("phoneNumber", "-")), disabled=True, key="view_phone")
            status = registration.get("status", "pending")
            status_options = {
                "pending": "⏳ 대기",
                "approved": "✅ 승인",
                "rejected": "❌ 거부",
                "reviewing": "🔍 검토중"
            }
            st.text_input("상태", value=status_options.get(status, status), disabled=True, key="view_status")
            st.text_input("신청일", value=format_datetime(registration.get("createdAt")), disabled=True, key="view_created_at")
            if registration.get("updatedAt"):
                st.text_input("수정일", value=format_datetime(registration.get("updatedAt")), disabled=True, key="view_updated_at")
            if registration.get("rejectionReason"):
                st.text_area("거부 사유", value=registration.get("rejectionReason", ""), disabled=True, height=80, key="view_rejection_reason")
    
    with tab2:
        st.markdown("#### 전체 데이터 (JSON)")
        registration_json = convert_firestore_data(registration)
        st.json(registration_json)
    
    # 액션 버튼
    st.markdown("---")
    col_action1, col_action2, col_action3, col_action4 = st.columns(4)
    
    current_status = registration.get("status", "pending")
    
    with col_action1:
        if current_status == "pending" or current_status == "reviewing":
            if st.button("✅ 승인", use_container_width=True, type="primary"):
                if approve_registration(st.session_state.selected_registration_id):
                    st.success("등록 신청이 승인되었습니다!")
                    get_all_tool_registrations.clear()
                    get_registration_by_id.clear()
                    st.rerun()
    
    with col_action2:
        if current_status == "pending" or current_status == "reviewing":
            if st.session_state.get('show_rejection_form_reg', False):
                rejection_reason = st.text_input("거부 사유", key="rejection_reason_reg")
                col_reject1, col_reject2 = st.columns(2)
                with col_reject1:
                    if st.button("✅ 거부 확인", use_container_width=True, type="primary"):
                        if reject_registration(st.session_state.selected_registration_id, rejection_reason):
                            st.success("등록 신청이 거부되었습니다!")
                            st.session_state.show_rejection_form_reg = False
                            get_all_tool_registrations.clear()
                            get_registration_by_id.clear()
                            st.rerun()
                with col_reject2:
                    if st.button("❌ 취소", use_container_width=True):
                        st.session_state.show_rejection_form_reg = False
                        st.rerun()
            else:
                if st.button("❌ 거부", use_container_width=True):
                    st.session_state.show_rejection_form_reg = True
                    st.rerun()
    
    with col_action3:
        if current_status == "pending":
            if st.button("🔍 검토중으로 변경", use_container_width=True):
                if update_registration(st.session_state.selected_registration_id, {"status": "reviewing"}):
                    st.success("상태가 '검토중'으로 변경되었습니다!")
                    get_all_tool_registrations.clear()
                    get_registration_by_id.clear()
                    st.rerun()
    
    with col_action4:
        if st.session_state.get('confirm_delete_reg', False):
            if st.button("✅ 확인 (삭제)", use_container_width=True, type="primary"):
                if delete_registration(st.session_state.selected_registration_id):
                    st.success("삭제 완료!")
                    st.session_state.selected_registration_data = None
                    st.session_state.selected_registration_id = None
                    st.session_state.confirm_delete_reg = False
                    get_all_tool_registrations.clear()
                    get_registration_by_id.clear()
                    st.rerun()
            if st.button("❌ 취소", use_container_width=True):
                st.session_state.confirm_delete_reg = False
                st.rerun()
        else:
            if st.button("🗑️ 삭제하기", use_container_width=True):
                st.session_state.confirm_delete_reg = True
                st.warning("⚠️ 정말 삭제하시겠습니까? 확인 버튼을 클릭하면 삭제됩니다.")
                st.rerun()
else:
    st.info("👆 위의 테이블에서 행을 선택하여 등록 신청 상세 정보를 조회하세요.")

# 사이드바 통계
with st.sidebar:
    st.markdown("### 📊 통계")
    
    # 전체 등록 신청 수
    st.metric("전체 신청 수", f"{len(all_registrations):,}개")
    
    # 상태별 통계
    if all_registrations:
        st.markdown("#### 상태별 분포")
        status_counts = {}
        for registration in all_registrations:
            status = registration.get("status", "pending")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in status_counts.items():
            status_name = {
                "pending": "⏳ 대기",
                "approved": "✅ 승인",
                "rejected": "❌ 거부",
                "reviewing": "🔍 검토중"
            }.get(status, status)
            st.write(f"**{status_name}**: {count}개")
    
    # 캐시 초기화
    if st.button("🔄 캐시 초기화", use_container_width=True):
        get_all_tool_registrations.clear()
        get_registration_by_id.clear()
        st.success("캐시가 초기화되었습니다!")
        st.rerun()

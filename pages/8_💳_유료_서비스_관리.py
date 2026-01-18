"""
유료 서비스 관리 페이지
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
from admin.paid_services import (
    get_all_paid_service_requests, get_paid_service_request_by_id, update_paid_service_request,
    approve_paid_service_request, reject_paid_service_request, delete_paid_service_request
)
from admin.utils import convert_firestore_data, format_datetime, format_value

# 페이지 설정
st.set_page_config(
    page_title="유료 서비스 관리 - Aicuatorhub Admin",
    page_icon="💳",
    layout="wide"
)

# Firebase 연결
db = get_db()
if db is None:
    st.error("⚠️ Firebase 연결에 실패했습니다.")
    st.stop()

# 세션 상태 초기화
if 'selected_request_id' not in st.session_state:
    st.session_state.selected_request_id = None
if 'selected_request_data' not in st.session_state:
    st.session_state.selected_request_data = None

# 페이지 헤더
render_page_header("💳 유료 서비스 관리", "유료 서비스 신청을 조회하고 처리할 수 있습니다.")

# 검색 및 필터
st.markdown("### 🔍 검색 필터")
filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

with filter_col1:
    search_query = st.text_input(
        "검색어 (서비스명/신청자)",
        key="paid_service_search_query",
        placeholder="검색어 입력..."
    )

with filter_col2:
    status_filter = st.selectbox(
        "상태",
        ["전체", "pending", "approved", "rejected", "processing", "completed"],
        key="paid_service_status_filter"
    )

with filter_col3:
    service_type_filter = st.selectbox(
        "서비스 타입",
        ["전체", "premium", "enterprise", "custom"],
        key="paid_service_type_filter"
    )

with filter_col4:
    date_from = st.date_input(
        "신청일 (시작)",
        value=None,
        key="paid_service_date_from"
    )

st.markdown("---")

# 유료 서비스 신청 목록 로드 및 필터링
all_requests = get_all_paid_service_requests()

# 필터링 적용
filtered_requests = all_requests

if search_query:
    search_lower = search_query.lower()
    filtered_requests = [
        r for r in filtered_requests
        if search_lower in str(r.get("serviceName", "")).lower()
        or search_lower in str(r.get("applicantName", "")).lower()
        or search_lower in str(r.get("applicantEmail", "")).lower()
        or search_lower in str(r.get("company", "")).lower()
    ]

if status_filter != "전체":
    filtered_requests = [
        r for r in filtered_requests
        if r.get("status", "pending") == status_filter
    ]

if service_type_filter != "전체":
    filtered_requests = [
        r for r in filtered_requests
        if r.get("serviceType", "") == service_type_filter
    ]

if date_from:
    filtered_requests = [
        r for r in filtered_requests
        if r.get("createdAt") and datetime.fromisoformat(r.get("createdAt").replace("Z", "+00:00")).date() >= date_from
    ]

# 결과 정보
st.info(f"📊 검색 결과: {len(filtered_requests)}개 (전체 {len(all_requests)}개)")

# 유료 서비스 신청 목록 표시
if filtered_requests:
    # 테이블 데이터 준비
    table_data = []
    for idx, request in enumerate(filtered_requests, 1):
        # 상태에 따른 배지
        status = request.get("status", "pending")
        status_badge = {
            "pending": "⏳ 대기",
            "approved": "✅ 승인",
            "rejected": "❌ 거부",
            "processing": "⚙️ 처리중",
            "completed": "✅ 완료"
        }.get(status, status)
        
        # 금액 정보
        amount = request.get("amount", request.get("price", 0))
        amount_str = f"${amount:,.0f}" if amount else "-"
        
        row = {
            "No.": idx,
            "신청 ID": request.get("id", "-"),
            "서비스명": request.get("serviceName", request.get("name", "-")),
            "서비스 타입": request.get("serviceType", "-"),
            "신청자": request.get("applicantName", request.get("applicant", "-")),
            "이메일": request.get("applicantEmail", request.get("email", "-")),
            "금액": amount_str,
            "상태": status_badge,
            "신청일": format_datetime(request.get("createdAt"), "%Y-%m-%d") if request.get("createdAt") else "-",
            "_id": request.get("id", "")
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
    gb.configure_column("서비스명", width=250)
    gb.configure_column("서비스 타입", width=120)
    gb.configure_column("신청자", width=150)
    gb.configure_column("이메일", width=200)
    gb.configure_column("금액", width=120)
    gb.configure_column("상태", width=100)
    gb.configure_column("신청일", width=120)
    gb.configure_column("_id", hide=True)
    
    grid_options = gb.build()
    
    st.markdown("### 📋 유료 서비스 신청 목록")
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
        key="paid_service_grid",
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
            clicked_request_id = str(selected_row.get('_id', '')).strip()
            
            if clicked_request_id and st.session_state.selected_request_id != clicked_request_id:
                st.session_state.selected_request_id = clicked_request_id
                request_data = get_paid_service_request_by_id(clicked_request_id)
                if request_data:
                    st.session_state.selected_request_data = request_data
                else:
                    st.warning(f"유료 서비스 신청을 찾을 수 없습니다: {clicked_request_id}")
                    st.session_state.selected_request_data = None
                st.rerun()
        except Exception as e:
            if st.session_state.get('debug_mode', False):
                st.error(f"데이터 매칭 오류: {e}")
else:
    st.warning("검색 결과가 없습니다.")

# 상세 정보 영역
st.markdown("---")
st.markdown("### 📝 유료 서비스 신청 상세 정보")

if st.session_state.selected_request_data:
    request = st.session_state.selected_request_data
    
    # 탭으로 구분
    tab1, tab2 = st.tabs([
        "기본 정보", "전체 데이터"
    ])
    
    with tab1:
        st.markdown("#### 기본 정보")
        
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            st.text_input("신청 ID", value=request.get("id", ""), disabled=True, key="view_req_id")
            st.text_input("서비스명", value=request.get("serviceName", request.get("name", "-")), disabled=True, key="view_service_name")
            st.text_input("서비스 타입", value=request.get("serviceType", "-"), disabled=True, key="view_service_type")
            amount = request.get("amount", request.get("price", 0))
            st.text_input("금액", value=f"${amount:,.0f}" if amount else "-", disabled=True, key="view_amount")
            st.text_area("서비스 설명", value=request.get("description", ""), disabled=True, height=100, key="view_service_description")
        
        with col_info2:
            st.text_input("신청자명", value=request.get("applicantName", request.get("applicant", "-")), disabled=True, key="view_applicant")
            st.text_input("이메일", value=request.get("applicantEmail", request.get("email", "-")), disabled=True, key="view_email")
            st.text_input("전화번호", value=request.get("phone", request.get("phoneNumber", "-")), disabled=True, key="view_phone")
            st.text_input("회사명", value=request.get("company", "-"), disabled=True, key="view_company")
            status = request.get("status", "pending")
            status_options = {
                "pending": "⏳ 대기",
                "approved": "✅ 승인",
                "rejected": "❌ 거부",
                "processing": "⚙️ 처리중",
                "completed": "✅ 완료"
            }
            st.text_input("상태", value=status_options.get(status, status), disabled=True, key="view_status")
            st.text_input("신청일", value=format_datetime(request.get("createdAt")), disabled=True, key="view_created_at")
            if request.get("updatedAt"):
                st.text_input("수정일", value=format_datetime(request.get("updatedAt")), disabled=True, key="view_updated_at")
            if request.get("rejectionReason"):
                st.text_area("거부 사유", value=request.get("rejectionReason", ""), disabled=True, height=80, key="view_rejection_reason")
        
        # 추가 정보
        if request.get("requirements") or request.get("notes"):
            st.markdown("#### 추가 정보")
            if request.get("requirements"):
                st.text_area("요구사항", value=format_value(request.get("requirements")), disabled=True, height=100, key="view_requirements")
            if request.get("notes"):
                st.text_area("메모", value=request.get("notes", ""), disabled=True, height=100, key="view_notes")
    
    with tab2:
        st.markdown("#### 전체 데이터 (JSON)")
        request_json = convert_firestore_data(request)
        st.json(request_json)
    
    # 액션 버튼
    st.markdown("---")
    col_action1, col_action2, col_action3, col_action4 = st.columns(4)
    
    current_status = request.get("status", "pending")
    
    with col_action1:
        if current_status == "pending":
            if st.button("✅ 승인", use_container_width=True, type="primary"):
                if approve_paid_service_request(st.session_state.selected_request_id):
                    st.success("유료 서비스 신청이 승인되었습니다!")
                    get_all_paid_service_requests.clear()
                    get_paid_service_request_by_id.clear()
                    st.rerun()
    
    with col_action2:
        if current_status == "pending":
            if st.session_state.get('show_rejection_form_paid', False):
                rejection_reason = st.text_input("거부 사유", key="rejection_reason_paid")
                col_reject1, col_reject2 = st.columns(2)
                with col_reject1:
                    if st.button("✅ 거부 확인", use_container_width=True, type="primary"):
                        if reject_paid_service_request(st.session_state.selected_request_id, rejection_reason):
                            st.success("유료 서비스 신청이 거부되었습니다!")
                            st.session_state.show_rejection_form_paid = False
                            get_all_paid_service_requests.clear()
                            get_paid_service_request_by_id.clear()
                            st.rerun()
                with col_reject2:
                    if st.button("❌ 취소", use_container_width=True):
                        st.session_state.show_rejection_form_paid = False
                        st.rerun()
            else:
                if st.button("❌ 거부", use_container_width=True):
                    st.session_state.show_rejection_form_paid = True
                    st.rerun()
    
    with col_action3:
        if current_status == "approved":
            if st.button("⚙️ 처리중으로 변경", use_container_width=True):
                if update_paid_service_request(st.session_state.selected_request_id, {"status": "processing"}):
                    st.success("상태가 '처리중'으로 변경되었습니다!")
                    get_all_paid_service_requests.clear()
                    get_paid_service_request_by_id.clear()
                    st.rerun()
        elif current_status == "processing":
            if st.button("✅ 완료로 변경", use_container_width=True):
                if update_paid_service_request(st.session_state.selected_request_id, {"status": "completed"}):
                    st.success("상태가 '완료'로 변경되었습니다!")
                    get_all_paid_service_requests.clear()
                    get_paid_service_request_by_id.clear()
                    st.rerun()
    
    with col_action4:
        if st.session_state.get('confirm_delete_paid', False):
            if st.button("✅ 확인 (삭제)", use_container_width=True, type="primary"):
                if delete_paid_service_request(st.session_state.selected_request_id):
                    st.success("삭제 완료!")
                    st.session_state.selected_request_data = None
                    st.session_state.selected_request_id = None
                    st.session_state.confirm_delete_paid = False
                    get_all_paid_service_requests.clear()
                    get_paid_service_request_by_id.clear()
                    st.rerun()
            if st.button("❌ 취소", use_container_width=True):
                st.session_state.confirm_delete_paid = False
                st.rerun()
        else:
            if st.button("🗑️ 삭제하기", use_container_width=True):
                st.session_state.confirm_delete_paid = True
                st.warning("⚠️ 정말 삭제하시겠습니까? 확인 버튼을 클릭하면 삭제됩니다.")
                st.rerun()
else:
    st.info("👆 위의 테이블에서 행을 선택하여 유료 서비스 신청 상세 정보를 조회하세요.")

# 사이드바 통계
with st.sidebar:
    st.markdown("### 📊 통계")
    
    # 전체 신청 수
    st.metric("전체 신청 수", f"{len(all_requests):,}개")
    
    # 상태별 통계
    if all_requests:
        st.markdown("#### 상태별 분포")
        status_counts = {}
        for request in all_requests:
            status = request.get("status", "pending")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in status_counts.items():
            status_name = {
                "pending": "⏳ 대기",
                "approved": "✅ 승인",
                "rejected": "❌ 거부",
                "processing": "⚙️ 처리중",
                "completed": "✅ 완료"
            }.get(status, status)
            st.write(f"**{status_name}**: {count}개")
        
        # 총 금액 계산
        total_amount = sum(
            float(request.get("amount", request.get("price", 0)) or 0)
            for request in all_requests
            if request.get("status") in ["approved", "processing", "completed"]
        )
        st.markdown("---")
        st.metric("승인된 서비스 총 금액", f"${total_amount:,.0f}")
    
    # 캐시 초기화
    if st.button("🔄 캐시 초기화", use_container_width=True):
        get_all_paid_service_requests.clear()
        get_paid_service_request_by_id.clear()
        st.success("캐시가 초기화되었습니다!")
        st.rerun()

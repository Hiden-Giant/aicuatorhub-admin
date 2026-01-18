"""
유료 서비스 신청 관련 CRUD 함수
"""
import streamlit as st
from firebase_admin import firestore
from typing import List, Dict, Optional, Any
from .firebase import get_db
from .config import COLLECTIONS
from .utils import convert_firestore_data


@st.cache_data(ttl=300)  # 5분 캐시
def get_all_paid_service_requests() -> List[Dict[str, Any]]:
    """
    모든 유료 서비스 신청 조회 (캐시됨)
    
    Returns:
        List[Dict]: 유료 서비스 신청 리스트
    """
    db = get_db()
    if db is None:
        return []
    
    try:
        # applications/paid-service-requests 컬렉션 또는 applications 컬렉션의 paid-service-requests 서브컬렉션
        try:
            # 먼저 applications/paid-service-requests 경로 시도
            requests_ref = db.collection(COLLECTIONS["PAID_SERVICE_REQUESTS"])
            docs = requests_ref.stream()
        except:
            # applications 컬렉션의 paid-service-requests 서브컬렉션 시도
            applications_ref = db.collection(COLLECTIONS["APPLICATIONS"])
            paid_services_ref = applications_ref.document("paid-service-requests").collection("requests")
            docs = paid_services_ref.stream()
        
        requests = []
        for doc in docs:
            req_data = doc.to_dict()
            req_data["id"] = doc.id
            req_data = convert_firestore_data(req_data)
            requests.append(req_data)
        return requests
    except Exception as e:
        # 단일 컬렉션으로 시도
        try:
            requests_ref = db.collection("paid-service-requests")
            docs = requests_ref.stream()
            requests = []
            for doc in docs:
                req_data = doc.to_dict()
                req_data["id"] = doc.id
                req_data = convert_firestore_data(req_data)
                requests.append(req_data)
            return requests
        except Exception as e2:
            st.warning(f"유료 서비스 신청 조회 실패: {e}. 컬렉션 경로를 확인해주세요.")
            return []


@st.cache_data(ttl=60)  # 1분 캐시
def get_paid_service_request_by_id(request_id: str) -> Optional[Dict[str, Any]]:
    """
    특정 유료 서비스 신청 조회 (캐시됨)
    
    Args:
        request_id: 신청 ID
        
    Returns:
        Dict: 신청 데이터 또는 None
    """
    db = get_db()
    if db is None:
        return None
    
    try:
        # 여러 경로 시도
        paths = [
            db.collection(COLLECTIONS["PAID_SERVICE_REQUESTS"]).document(request_id),
            db.collection("paid-service-requests").document(request_id),
            db.collection(COLLECTIONS["APPLICATIONS"]).document("paid-service-requests").collection("requests").document(request_id)
        ]
        
        for doc_ref in paths:
            try:
                doc = doc_ref.get()
                if doc.exists:
                    req_data = doc.to_dict()
                    req_data["id"] = doc.id
                    req_data = convert_firestore_data(req_data)
                    return req_data
            except:
                continue
        
        return None
    except Exception as e:
        st.error(f"유료 서비스 신청 조회 실패: {e}")
        return None


def update_paid_service_request(request_id: str, data: Dict[str, Any]) -> bool:
    """
    유료 서비스 신청 정보 업데이트
    
    Args:
        request_id: 신청 ID
        data: 업데이트할 데이터
        
    Returns:
        bool: 성공 여부
    """
    db = get_db()
    if db is None:
        return False
    
    try:
        # 여러 경로 시도
        paths = [
            db.collection(COLLECTIONS["PAID_SERVICE_REQUESTS"]).document(request_id),
            db.collection("paid-service-requests").document(request_id),
            db.collection(COLLECTIONS["APPLICATIONS"]).document("paid-service-requests").collection("requests").document(request_id)
        ]
        
        data["updatedAt"] = firestore.SERVER_TIMESTAMP
        
        for doc_ref in paths:
            try:
                doc_ref.update(data)
                # 캐시 무효화
                get_all_paid_service_requests.clear()
                get_paid_service_request_by_id.clear()
                return True
            except:
                continue
        
        return False
    except Exception as e:
        st.error(f"유료 서비스 신청 업데이트 실패: {e}")
        return False


def approve_paid_service_request(request_id: str) -> bool:
    """
    유료 서비스 신청 승인
    
    Args:
        request_id: 신청 ID
        
    Returns:
        bool: 성공 여부
    """
    return update_paid_service_request(request_id, {
        "status": "approved",
        "approvedAt": firestore.SERVER_TIMESTAMP
    })


def reject_paid_service_request(request_id: str, reason: str = "") -> bool:
    """
    유료 서비스 신청 거부
    
    Args:
        request_id: 신청 ID
        reason: 거부 사유
        
    Returns:
        bool: 성공 여부
    """
    return update_paid_service_request(request_id, {
        "status": "rejected",
        "rejectedAt": firestore.SERVER_TIMESTAMP,
        "rejectionReason": reason
    })


def delete_paid_service_request(request_id: str) -> bool:
    """
    유료 서비스 신청 삭제
    
    Args:
        request_id: 신청 ID
        
    Returns:
        bool: 성공 여부
    """
    db = get_db()
    if db is None:
        return False
    
    try:
        # 여러 경로 시도
        paths = [
            db.collection(COLLECTIONS["PAID_SERVICE_REQUESTS"]).document(request_id),
            db.collection("paid-service-requests").document(request_id),
            db.collection(COLLECTIONS["APPLICATIONS"]).document("paid-service-requests").collection("requests").document(request_id)
        ]
        
        for doc_ref in paths:
            try:
                doc_ref.delete()
                # 캐시 무효화
                get_all_paid_service_requests.clear()
                get_paid_service_request_by_id.clear()
                return True
            except:
                continue
        
        return False
    except Exception as e:
        st.error(f"유료 서비스 신청 삭제 실패: {e}")
        return False

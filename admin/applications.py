"""
등록 신청 관련 CRUD 함수
"""
import streamlit as st
from firebase_admin import firestore
from typing import List, Dict, Optional, Any
from .firebase import get_db
from .config import COLLECTIONS
from .utils import convert_firestore_data


@st.cache_data(ttl=300)  # 5분 캐시
def get_all_tool_registrations() -> List[Dict[str, Any]]:
    """
    모든 도구 등록 신청 조회 (캐시됨)
    
    Returns:
        List[Dict]: 등록 신청 리스트
    """
    db = get_db()
    if db is None:
        return []
    
    try:
        # applications/tool-registrations 컬렉션 또는 applications 컬렉션의 tool-registrations 서브컬렉션
        try:
            # 먼저 applications/tool-registrations 경로 시도
            registrations_ref = db.collection(COLLECTIONS["TOOL_REGISTRATIONS"])
            docs = registrations_ref.stream()
        except:
            # applications 컬렉션의 tool-registrations 서브컬렉션 시도
            applications_ref = db.collection(COLLECTIONS["APPLICATIONS"])
            tool_regs_ref = applications_ref.document("tool-registrations").collection("requests")
            docs = tool_regs_ref.stream()
        
        registrations = []
        for doc in docs:
            reg_data = doc.to_dict()
            reg_data["id"] = doc.id
            reg_data = convert_firestore_data(reg_data)
            registrations.append(reg_data)
        return registrations
    except Exception as e:
        # 단일 컬렉션으로 시도
        try:
            registrations_ref = db.collection("tool-registrations")
            docs = registrations_ref.stream()
            registrations = []
            for doc in docs:
                reg_data = doc.to_dict()
                reg_data["id"] = doc.id
                reg_data = convert_firestore_data(reg_data)
                registrations.append(reg_data)
            return registrations
        except Exception as e2:
            st.warning(f"등록 신청 조회 실패: {e}. 컬렉션 경로를 확인해주세요.")
            return []


@st.cache_data(ttl=60)  # 1분 캐시
def get_registration_by_id(registration_id: str) -> Optional[Dict[str, Any]]:
    """
    특정 등록 신청 조회 (캐시됨)
    
    Args:
        registration_id: 등록 신청 ID
        
    Returns:
        Dict: 등록 신청 데이터 또는 None
    """
    db = get_db()
    if db is None:
        return None
    
    try:
        # 여러 경로 시도
        paths = [
            db.collection(COLLECTIONS["TOOL_REGISTRATIONS"]).document(registration_id),
            db.collection("tool-registrations").document(registration_id),
            db.collection(COLLECTIONS["APPLICATIONS"]).document("tool-registrations").collection("requests").document(registration_id)
        ]
        
        for doc_ref in paths:
            try:
                doc = doc_ref.get()
                if doc.exists:
                    reg_data = doc.to_dict()
                    reg_data["id"] = doc.id
                    reg_data = convert_firestore_data(reg_data)
                    return reg_data
            except:
                continue
        
        return None
    except Exception as e:
        st.error(f"등록 신청 조회 실패: {e}")
        return None


def update_registration(registration_id: str, data: Dict[str, Any]) -> bool:
    """
    등록 신청 정보 업데이트
    
    Args:
        registration_id: 등록 신청 ID
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
            db.collection(COLLECTIONS["TOOL_REGISTRATIONS"]).document(registration_id),
            db.collection("tool-registrations").document(registration_id),
            db.collection(COLLECTIONS["APPLICATIONS"]).document("tool-registrations").collection("requests").document(registration_id)
        ]
        
        data["updatedAt"] = firestore.SERVER_TIMESTAMP
        
        for doc_ref in paths:
            try:
                doc_ref.update(data)
                # 캐시 무효화
                get_all_tool_registrations.clear()
                get_registration_by_id.clear()
                return True
            except:
                continue
        
        return False
    except Exception as e:
        st.error(f"등록 신청 업데이트 실패: {e}")
        return False


def approve_registration(registration_id: str) -> bool:
    """
    등록 신청 승인
    
    Args:
        registration_id: 등록 신청 ID
        
    Returns:
        bool: 성공 여부
    """
    return update_registration(registration_id, {
        "status": "approved",
        "approvedAt": firestore.SERVER_TIMESTAMP
    })


def reject_registration(registration_id: str, reason: str = "") -> bool:
    """
    등록 신청 거부
    
    Args:
        registration_id: 등록 신청 ID
        reason: 거부 사유
        
    Returns:
        bool: 성공 여부
    """
    return update_registration(registration_id, {
        "status": "rejected",
        "rejectedAt": firestore.SERVER_TIMESTAMP,
        "rejectionReason": reason
    })


def delete_registration(registration_id: str) -> bool:
    """
    등록 신청 삭제
    
    Args:
        registration_id: 등록 신청 ID
        
    Returns:
        bool: 성공 여부
    """
    db = get_db()
    if db is None:
        return False
    
    try:
        # 여러 경로 시도
        paths = [
            db.collection(COLLECTIONS["TOOL_REGISTRATIONS"]).document(registration_id),
            db.collection("tool-registrations").document(registration_id),
            db.collection(COLLECTIONS["APPLICATIONS"]).document("tool-registrations").collection("requests").document(registration_id)
        ]
        
        for doc_ref in paths:
            try:
                doc_ref.delete()
                # 캐시 무효화
                get_all_tool_registrations.clear()
                get_registration_by_id.clear()
                return True
            except:
                continue
        
        return False
    except Exception as e:
        st.error(f"등록 신청 삭제 실패: {e}")
        return False

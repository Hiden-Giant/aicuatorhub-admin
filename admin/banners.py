"""
배너 관련 CRUD 함수
"""
import streamlit as st
from firebase_admin import firestore
from typing import List, Dict, Optional, Any
from datetime import datetime
from .firebase import get_db
from .config import COLLECTIONS
from .utils import convert_firestore_data


@st.cache_data(ttl=300)  # 5분 캐시
def get_all_banners() -> List[Dict[str, Any]]:
    """
    모든 배너 조회 (캐시됨)
    
    Returns:
        List[Dict]: 배너 리스트
    """
    db = get_db()
    if db is None:
        return []
    
    try:
        banners_ref = db.collection(COLLECTIONS["BANNERS"])
        docs = banners_ref.stream()
        banners = []
        for doc in docs:
            banner_data = doc.to_dict()
            banner_data["id"] = doc.id
            banner_data = convert_firestore_data(banner_data)
            banners.append(banner_data)
        return banners
    except Exception as e:
        st.error(f"배너 조회 실패: {e}")
        return []


@st.cache_data(ttl=60)  # 1분 캐시
def get_banners_by_spot(spot_id: str) -> List[Dict[str, Any]]:
    """
    특정 위치의 배너 목록 조회 (우선순위 순으로 정렬)
    
    Args:
        spot_id: 배너 위치 ID
        
    Returns:
        List[Dict]: 배너 리스트 (우선순위 순)
    """
    all_banners = get_all_banners()
    spot_banners = [
        b for b in all_banners
        if b.get("spotId") == spot_id
    ]
    # 우선순위 순으로 정렬
    spot_banners.sort(key=lambda x: x.get("priority", 999))
    return spot_banners


@st.cache_data(ttl=60)  # 1분 캐시
def get_banner_by_id(banner_id: str) -> Optional[Dict[str, Any]]:
    """
    특정 배너 조회 (캐시됨)
    
    Args:
        banner_id: 배너 ID
        
    Returns:
        Dict: 배너 데이터 또는 None
    """
    db = get_db()
    if db is None:
        return None
    
    try:
        doc_ref = db.collection(COLLECTIONS["BANNERS"]).document(banner_id)
        doc = doc_ref.get()
        if doc.exists:
            banner_data = doc.to_dict()
            banner_data["id"] = doc.id
            banner_data = convert_firestore_data(banner_data)
            return banner_data
        return None
    except Exception as e:
        st.error(f"배너 조회 실패: {e}")
        return None


def update_banner(banner_id: str, data: Dict[str, Any]) -> bool:
    """
    배너 정보 업데이트
    
    Args:
        banner_id: 배너 ID
        data: 업데이트할 데이터
        
    Returns:
        bool: 성공 여부
    """
    db = get_db()
    if db is None:
        return False
    
    try:
        doc_ref = db.collection(COLLECTIONS["BANNERS"]).document(banner_id)
        data["updatedAt"] = firestore.SERVER_TIMESTAMP
        doc_ref.update(data)
        # 캐시 무효화
        get_all_banners.clear()
        get_banners_by_spot.clear()
        get_banner_by_id.clear()
        return True
    except Exception as e:
        st.error(f"배너 업데이트 실패: {e}")
        return False


def create_banner(banner_id: str, data: Dict[str, Any]) -> bool:
    """
    새 배너 생성
    
    Args:
        banner_id: 배너 ID
        data: 배너 데이터
        
    Returns:
        bool: 성공 여부
    """
    db = get_db()
    if db is None:
        return False
    
    try:
        doc_ref = db.collection(COLLECTIONS["BANNERS"]).document(banner_id)
        data["createdAt"] = firestore.SERVER_TIMESTAMP
        data["updatedAt"] = firestore.SERVER_TIMESTAMP
        doc_ref.set(data)
        # 캐시 무효화
        get_all_banners.clear()
        get_banners_by_spot.clear()
        get_banner_by_id.clear()
        return True
    except Exception as e:
        st.error(f"배너 생성 실패: {e}")
        return False


def delete_banner(banner_id: str) -> bool:
    """
    배너 삭제
    
    Args:
        banner_id: 배너 ID
        
    Returns:
        bool: 성공 여부
    """
    db = get_db()
    if db is None:
        return False
    
    try:
        doc_ref = db.collection(COLLECTIONS["BANNERS"]).document(banner_id)
        doc_ref.delete()
        # 캐시 무효화
        get_all_banners.clear()
        get_banners_by_spot.clear()
        get_banner_by_id.clear()
        return True
    except Exception as e:
        st.error(f"배너 삭제 실패: {e}")
        return False


def update_banner_priority(banner_id: str, new_priority: int) -> bool:
    """
    배너 우선순위 업데이트
    
    Args:
        banner_id: 배너 ID
        new_priority: 새로운 우선순위
        
    Returns:
        bool: 성공 여부
    """
    return update_banner(banner_id, {"priority": new_priority})


def get_banner_status(banner: Dict[str, Any]) -> str:
    """
    배너의 현재 상태 계산 (LIVE, SCHEDULED, OFF)
    
    Args:
        banner: 배너 데이터
        
    Returns:
        str: 상태 (live, scheduled, off)
    """
    status = banner.get("status", "off")
    
    if status == "off":
        return "off"
    
    now = datetime.now()
    start_date = banner.get("displayStart")
    end_date = banner.get("displayEnd")
    
    if start_date:
        if isinstance(start_date, str):
            try:
                start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            except:
                pass
        
        if isinstance(start_date, datetime) and start_date > now:
            return "scheduled"
    
    if end_date:
        if isinstance(end_date, str):
            try:
                end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            except:
                pass
        
        if isinstance(end_date, datetime) and end_date < now:
            return "off"
    
    if status == "live":
        return "live"
    elif status == "scheduled":
        return "scheduled"
    else:
        return "off"

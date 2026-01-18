"""
사용자 관련 CRUD 함수
"""
import streamlit as st
from firebase_admin import firestore
from typing import List, Dict, Optional, Any
from .firebase import get_db
from .config import COLLECTIONS
from .utils import convert_firestore_data


@st.cache_data(ttl=300)  # 5분 캐시
def get_all_users() -> List[Dict[str, Any]]:
    """
    모든 사용자 조회 (캐시됨)
    
    Returns:
        List[Dict]: 사용자 리스트
    """
    db = get_db()
    if db is None:
        return []
    
    try:
        users_ref = db.collection(COLLECTIONS["USERS"])
        docs = users_ref.stream()
        users = []
        for doc in docs:
            user_data = doc.to_dict()
            user_data["uid"] = doc.id
            user_data = convert_firestore_data(user_data)
            users.append(user_data)
        return users
    except Exception as e:
        st.error(f"사용자 조회 실패: {e}")
        return []


@st.cache_data(ttl=60)  # 1분 캐시
def get_user_by_id(uid: str) -> Optional[Dict[str, Any]]:
    """
    특정 사용자 조회 (캐시됨)
    
    Args:
        uid: 사용자 UID
        
    Returns:
        Dict: 사용자 데이터 또는 None
    """
    db = get_db()
    if db is None:
        return None
    
    try:
        doc_ref = db.collection(COLLECTIONS["USERS"]).document(uid)
        doc = doc_ref.get()
        if doc.exists:
            user_data = doc.to_dict()
            user_data["uid"] = doc.id
            user_data = convert_firestore_data(user_data)
            return user_data
        return None
    except Exception as e:
        st.error(f"사용자 조회 실패: {e}")
        return None


def get_user_favorites(uid: str) -> List[Dict[str, Any]]:
    """
    사용자의 즐겨찾기 목록 조회
    
    Args:
        uid: 사용자 UID
        
    Returns:
        List[Dict]: 즐겨찾기 리스트
    """
    db = get_db()
    if db is None:
        return []
    
    try:
        favorites_ref = db.collection(COLLECTIONS["USERS"]).document(uid).collection("favorites")
        docs = favorites_ref.stream()
        favorites = []
        for doc in docs:
            fav_data = doc.to_dict()
            fav_data["id"] = doc.id
            fav_data = convert_firestore_data(fav_data)
            favorites.append(fav_data)
        return favorites
    except Exception as e:
        st.error(f"즐겨찾기 조회 실패: {e}")
        return []


def get_user_reviews(uid: str) -> List[Dict[str, Any]]:
    """
    사용자의 리뷰 목록 조회
    
    Args:
        uid: 사용자 UID
        
    Returns:
        List[Dict]: 리뷰 리스트
    """
    db = get_db()
    if db is None:
        return []
    
    try:
        reviews_ref = db.collection(COLLECTIONS["USERS"]).document(uid).collection("reviews")
        docs = reviews_ref.stream()
        reviews = []
        for doc in docs:
            review_data = doc.to_dict()
            review_data["id"] = doc.id
            review_data = convert_firestore_data(review_data)
            reviews.append(review_data)
        return reviews
    except Exception as e:
        st.error(f"리뷰 조회 실패: {e}")
        return []


def get_user_ai_sets(uid: str) -> List[Dict[str, Any]]:
    """
    사용자의 AI 세트 목록 조회
    
    Args:
        uid: 사용자 UID
        
    Returns:
        List[Dict]: AI 세트 리스트
    """
    db = get_db()
    if db is None:
        return []
    
    try:
        sets_ref = db.collection(COLLECTIONS["USERS"]).document(uid).collection("my-ai-sets")
        docs = sets_ref.stream()
        ai_sets = []
        for doc in docs:
            set_data = doc.to_dict()
            set_data["id"] = doc.id
            set_data = convert_firestore_data(set_data)
            ai_sets.append(set_data)
        return ai_sets
    except Exception as e:
        st.error(f"AI 세트 조회 실패: {e}")
        return []


def update_user(uid: str, data: Dict[str, Any]) -> bool:
    """
    사용자 정보 업데이트
    
    Args:
        uid: 사용자 UID
        data: 업데이트할 데이터
        
    Returns:
        bool: 성공 여부
    """
    db = get_db()
    if db is None:
        return False
    
    try:
        doc_ref = db.collection(COLLECTIONS["USERS"]).document(uid)
        data["updatedAt"] = firestore.SERVER_TIMESTAMP
        doc_ref.update(data)
        # 캐시 무효화
        get_all_users.clear()
        get_user_by_id.clear()
        return True
    except Exception as e:
        st.error(f"사용자 업데이트 실패: {e}")
        return False


def delete_user(uid: str) -> bool:
    """
    사용자 삭제 (주의: 서브컬렉션도 함께 삭제해야 함)
    
    Args:
        uid: 사용자 UID
        
    Returns:
        bool: 성공 여부
    """
    db = get_db()
    if db is None:
        return False
    
    try:
        # 서브컬렉션 삭제 (favorites, reviews, my-ai-sets)
        subcollections = ["favorites", "reviews", "my-ai-sets"]
        for subcol in subcollections:
            subcol_ref = db.collection(COLLECTIONS["USERS"]).document(uid).collection(subcol)
            docs = subcol_ref.stream()
            for doc in docs:
                doc.reference.delete()
        
        # 사용자 문서 삭제
        doc_ref = db.collection(COLLECTIONS["USERS"]).document(uid)
        doc_ref.delete()
        
        # 캐시 무효화
        get_all_users.clear()
        get_user_by_id.clear()
        return True
    except Exception as e:
        st.error(f"사용자 삭제 실패: {e}")
        return False

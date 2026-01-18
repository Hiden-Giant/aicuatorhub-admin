"""
AI 레시피 관련 CRUD 함수
"""
import streamlit as st
from firebase_admin import firestore
from typing import List, Dict, Optional, Any
from .firebase import get_db
from .config import COLLECTIONS
from .utils import convert_firestore_data


@st.cache_data(ttl=300)  # 5분 캐시
def get_all_recipes() -> List[Dict[str, Any]]:
    """
    모든 레시피 조회 (캐시됨)
    
    Returns:
        List[Dict]: 레시피 리스트
    """
    db = get_db()
    if db is None:
        return []
    
    try:
        recipes_ref = db.collection(COLLECTIONS["RECIPES"])
        docs = recipes_ref.stream()
        recipes = []
        for doc in docs:
            recipe_data = doc.to_dict()
            recipe_data["id"] = doc.id
            recipe_data = convert_firestore_data(recipe_data)
            recipes.append(recipe_data)
        return recipes
    except Exception as e:
        st.error(f"레시피 조회 실패: {e}")
        return []


@st.cache_data(ttl=60)  # 1분 캐시
def get_recipe_by_id(recipe_id: str) -> Optional[Dict[str, Any]]:
    """
    특정 레시피 조회 (캐시됨)
    
    Args:
        recipe_id: 레시피 ID
        
    Returns:
        Dict: 레시피 데이터 또는 None
    """
    db = get_db()
    if db is None:
        return None
    
    try:
        doc_ref = db.collection(COLLECTIONS["RECIPES"]).document(recipe_id)
        doc = doc_ref.get()
        if doc.exists:
            recipe_data = doc.to_dict()
            recipe_data["id"] = doc.id
            recipe_data = convert_firestore_data(recipe_data)
            return recipe_data
        return None
    except Exception as e:
        st.error(f"레시피 조회 실패: {e}")
        return None


def update_recipe(recipe_id: str, data: Dict[str, Any]) -> bool:
    """
    레시피 정보 업데이트
    
    Args:
        recipe_id: 레시피 ID
        data: 업데이트할 데이터
        
    Returns:
        bool: 성공 여부
    """
    db = get_db()
    if db is None:
        return False
    
    try:
        doc_ref = db.collection(COLLECTIONS["RECIPES"]).document(recipe_id)
        data["updatedAt"] = firestore.SERVER_TIMESTAMP
        doc_ref.update(data)
        # 캐시 무효화
        get_all_recipes.clear()
        get_recipe_by_id.clear()
        return True
    except Exception as e:
        st.error(f"레시피 업데이트 실패: {e}")
        return False


def create_recipe(recipe_id: str, data: Dict[str, Any]) -> bool:
    """
    새 레시피 생성
    
    Args:
        recipe_id: 레시피 ID
        data: 레시피 데이터
        
    Returns:
        bool: 성공 여부
    """
    db = get_db()
    if db is None:
        return False
    
    try:
        doc_ref = db.collection(COLLECTIONS["RECIPES"]).document(recipe_id)
        data["createdAt"] = firestore.SERVER_TIMESTAMP
        data["updatedAt"] = firestore.SERVER_TIMESTAMP
        doc_ref.set(data)
        # 캐시 무효화
        get_all_recipes.clear()
        get_recipe_by_id.clear()
        return True
    except Exception as e:
        st.error(f"레시피 생성 실패: {e}")
        return False


def delete_recipe(recipe_id: str) -> bool:
    """
    레시피 삭제
    
    Args:
        recipe_id: 레시피 ID
        
    Returns:
        bool: 성공 여부
    """
    db = get_db()
    if db is None:
        return False
    
    try:
        doc_ref = db.collection(COLLECTIONS["RECIPES"]).document(recipe_id)
        doc_ref.delete()
        # 캐시 무효화
        get_all_recipes.clear()
        get_recipe_by_id.clear()
        return True
    except Exception as e:
        st.error(f"레시피 삭제 실패: {e}")
        return False


def approve_recipe(recipe_id: str) -> bool:
    """
    레시피 승인
    
    Args:
        recipe_id: 레시피 ID
        
    Returns:
        bool: 성공 여부
    """
    return update_recipe(recipe_id, {"status": "approved", "approvedAt": firestore.SERVER_TIMESTAMP})


def reject_recipe(recipe_id: str, reason: str = "") -> bool:
    """
    레시피 거부
    
    Args:
        recipe_id: 레시피 ID
        reason: 거부 사유
        
    Returns:
        bool: 성공 여부
    """
    return update_recipe(recipe_id, {
        "status": "rejected",
        "rejectedAt": firestore.SERVER_TIMESTAMP,
        "rejectionReason": reason
    })

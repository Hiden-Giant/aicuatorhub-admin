"""
사용자 개인 레시피 관련 함수 (사용자 관리 > 나의 리시피 탭에서 사용)
"""
import streamlit as st
from firebase_admin import firestore
from typing import List, Dict, Optional, Any
from .firebase import get_db
from .config import COLLECTIONS
from .utils import convert_firestore_data


@st.cache_data(ttl=300)  # 5분 캐시
def get_user_recipes(uid: str) -> List[Dict[str, Any]]:
    """
    사용자의 개인 레시피 목록 조회 (캐시됨)
    
    Args:
        uid: 사용자 UID
        
    Returns:
        List[Dict]: 사용자 레시피 리스트
    """
    db = get_db()
    if db is None:
        return []
    
    try:
        # my_recipe 컬렉션에서 해당 사용자의 레시피 조회
        recipes_ref = db.collection(COLLECTIONS["RECIPES"])
        # userId 또는 author 필드로 필터링
        docs = recipes_ref.where("userId", "==", uid).stream()
        recipes = []
        for doc in docs:
            recipe_data = doc.to_dict()
            recipe_data["id"] = doc.id
            recipe_data = convert_firestore_data(recipe_data)
            recipes.append(recipe_data)
        
        # author 필드로도 조회 시도
        docs_author = recipes_ref.where("author", "==", uid).stream()
        for doc in docs_author:
            recipe_data = doc.to_dict()
            recipe_data["id"] = doc.id
            recipe_data = convert_firestore_data(recipe_data)
            # 중복 제거
            if not any(r.get("id") == recipe_data["id"] for r in recipes):
                recipes.append(recipe_data)
        
        return recipes
    except Exception as e:
        st.error(f"사용자 레시피 조회 실패: {e}")
        return []


@st.cache_data(ttl=60)  # 1분 캐시
def get_user_recipe_by_id(uid: str, recipe_id: str) -> Optional[Dict[str, Any]]:
    """
    사용자의 특정 레시피 조회 (캐시됨)
    
    Args:
        uid: 사용자 UID
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
            # 사용자 소유 확인
            if recipe_data.get("userId") == uid or recipe_data.get("author") == uid:
                recipe_data["id"] = doc.id
                recipe_data = convert_firestore_data(recipe_data)
                return recipe_data
        return None
    except Exception as e:
        st.error(f"사용자 레시피 조회 실패: {e}")
        return None

"""
AI 도구 관련 CRUD 함수
"""
import streamlit as st
from firebase_admin import firestore
from typing import List, Dict, Optional, Any
from .firebase import get_db
from .config import COLLECTIONS
from .utils import convert_firestore_data, normalize_id


@st.cache_data(ttl=300)  # 5분 캐시
def get_all_tools() -> List[Dict[str, Any]]:
    """
    모든 도구 조회 (캐시됨)
    
    Returns:
        List[Dict]: 도구 리스트
    """
    db = get_db()
    if db is None:
        return []
    
    try:
        tools_ref = db.collection(COLLECTIONS["AI_TOOLS"])
        docs = tools_ref.stream()
        tools = []
        for doc in docs:
            tool_data = doc.to_dict()
            tool_data["id"] = doc.id
            # Firestore 데이터 변환
            tool_data = convert_firestore_data(tool_data)
            tools.append(tool_data)
        return tools
    except Exception as e:
        st.error(f"도구 조회 실패: {e}")
        return []


@st.cache_data(ttl=60)  # 1분 캐시
def get_tool_by_id(tool_id: str) -> Optional[Dict[str, Any]]:
    """
    특정 도구 조회 (캐시됨)
    
    Args:
        tool_id: 도구 ID
        
    Returns:
        Dict: 도구 데이터 또는 None
    """
    db = get_db()
    if db is None:
        return None
    
    try:
        doc_ref = db.collection(COLLECTIONS["AI_TOOLS"]).document(tool_id)
        doc = doc_ref.get()
        if doc.exists:
            tool_data = doc.to_dict()
            tool_data["id"] = doc.id
            # Firestore 데이터 변환
            tool_data = convert_firestore_data(tool_data)
            return tool_data
        return None
    except Exception as e:
        st.error(f"도구 조회 실패: {e}")
        return None


def update_tool(tool_id: str, data: Dict[str, Any]) -> bool:
    """
    도구 정보 업데이트
    
    Args:
        tool_id: 도구 ID
        data: 업데이트할 데이터
        
    Returns:
        bool: 성공 여부
    """
    db = get_db()
    if db is None:
        return False
    
    try:
        doc_ref = db.collection(COLLECTIONS["AI_TOOLS"]).document(tool_id)
        data["updatedAt"] = firestore.SERVER_TIMESTAMP
        doc_ref.update(data)
        # 캐시 무효화
        get_all_tools.clear()
        get_tool_by_id.clear()
        return True
    except Exception as e:
        st.error(f"도구 업데이트 실패: {e}")
        return False


def create_tool(tool_id: str, data: Dict[str, Any]) -> bool:
    """
    새 도구 생성
    
    Args:
        tool_id: 도구 ID
        data: 도구 데이터
        
    Returns:
        bool: 성공 여부
    """
    db = get_db()
    if db is None:
        return False
    
    try:
        doc_ref = db.collection(COLLECTIONS["AI_TOOLS"]).document(tool_id)
        data["createdAt"] = firestore.SERVER_TIMESTAMP
        data["updatedAt"] = firestore.SERVER_TIMESTAMP
        doc_ref.set(data)
        # 캐시 무효화
        get_all_tools.clear()
        get_tool_by_id.clear()
        return True
    except Exception as e:
        st.error(f"도구 생성 실패: {e}")
        return False


def delete_tool(tool_id: str) -> bool:
    """
    도구 삭제
    
    Args:
        tool_id: 도구 ID
        
    Returns:
        bool: 성공 여부
    """
    db = get_db()
    if db is None:
        return False
    
    try:
        doc_ref = db.collection(COLLECTIONS["AI_TOOLS"]).document(tool_id)
        doc_ref.delete()
        # 캐시 무효화
        get_all_tools.clear()
        get_tool_by_id.clear()
        return True
    except Exception as e:
        st.error(f"도구 삭제 실패: {e}")
        return False


def normalize_tool_id(name: str) -> str:
    """
    도구 이름을 문서 ID로 변환
    
    Args:
        name: 도구 이름
        
    Returns:
        str: 정규화된 ID
    """
    return normalize_id(name)

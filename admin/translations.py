"""
다국어 번역 관련 CRUD 함수
"""
import streamlit as st
from firebase_admin import firestore
from typing import List, Dict, Optional, Any
from .firebase import get_db
from .config import COLLECTIONS, SUPPORTED_LANGUAGES, TRANSLATION_TYPES, ORIGIN_LANGUAGES, REQUIRED_LANGUAGES
from .utils import convert_firestore_data


@st.cache_data(ttl=300)  # 5분 캐시
def get_all_translations() -> List[Dict[str, Any]]:
    """
    모든 번역 데이터 조회 (캐시됨)
    
    Returns:
        List[Dict]: 번역 리스트
    """
    db = get_db()
    if db is None:
        return []
    
    try:
        translations_ref = db.collection(COLLECTIONS["TRANSLATIONS"])
        docs = translations_ref.stream()
        translations = []
        for doc in docs:
            trans_data = doc.to_dict()
            trans_data["id"] = doc.id
            trans_data = convert_firestore_data(trans_data)
            translations.append(trans_data)
        return translations
    except Exception as e:
        st.error(f"번역 조회 실패: {e}")
        return []


@st.cache_data(ttl=60)  # 1분 캐시
def get_translation_by_id(trans_id: str) -> Optional[Dict[str, Any]]:
    """
    특정 번역 조회 (캐시됨)
    
    Args:
        trans_id: 번역 ID
        
    Returns:
        Dict: 번역 데이터 또는 None
    """
    db = get_db()
    if db is None:
        return None
    
    try:
        doc_ref = db.collection(COLLECTIONS["TRANSLATIONS"]).document(trans_id)
        doc = doc_ref.get()
        if doc.exists:
            trans_data = doc.to_dict()
            trans_data["id"] = doc.id
            trans_data = convert_firestore_data(trans_data)
            return trans_data
        return None
    except Exception as e:
        st.error(f"번역 조회 실패: {e}")
        return None


def update_translation(trans_id: str, data: Dict[str, Any]) -> bool:
    """
    번역 정보 업데이트
    
    Args:
        trans_id: 번역 ID
        data: 업데이트할 데이터
        
    Returns:
        bool: 성공 여부
    """
    db = get_db()
    if db is None:
        return False
    
    try:
        doc_ref = db.collection(COLLECTIONS["TRANSLATIONS"]).document(trans_id)
        data["updatedAt"] = firestore.SERVER_TIMESTAMP
        data["updatedBy"] = "admin"  # TODO: 실제 사용자 ID로 변경
        doc_ref.update(data)
        # 캐시 무효화
        get_all_translations.clear()
        get_translation_by_id.clear()
        return True
    except Exception as e:
        st.error(f"번역 업데이트 실패: {e}")
        return False


def create_translation(trans_id: str, data: Dict[str, Any]) -> bool:
    """
    새 번역 생성
    
    Args:
        trans_id: 번역 ID
        data: 번역 데이터
        
    Returns:
        bool: 성공 여부
    """
    db = get_db()
    if db is None:
        return False
    
    try:
        doc_ref = db.collection(COLLECTIONS["TRANSLATIONS"]).document(trans_id)
        data["createdAt"] = firestore.SERVER_TIMESTAMP
        data["updatedAt"] = firestore.SERVER_TIMESTAMP
        data["createdBy"] = "admin"  # TODO: 실제 사용자 ID로 변경
        data["updatedBy"] = "admin"
        doc_ref.set(data)
        # 캐시 무효화
        get_all_translations.clear()
        get_translation_by_id.clear()
        return True
    except Exception as e:
        st.error(f"번역 생성 실패: {e}")
        return False


def delete_translation(trans_id: str) -> bool:
    """
    번역 삭제
    
    Args:
        trans_id: 번역 ID
        
    Returns:
        bool: 성공 여부
    """
    db = get_db()
    if db is None:
        return False
    
    try:
        doc_ref = db.collection(COLLECTIONS["TRANSLATIONS"]).document(trans_id)
        doc_ref.delete()
        # 캐시 무효화
        get_all_translations.clear()
        get_translation_by_id.clear()
        return True
    except Exception as e:
        st.error(f"번역 삭제 실패: {e}")
        return False


def get_translation_text(trans_data: Dict[str, Any], lang_code: str) -> str:
    """
    번역 데이터에서 특정 언어의 텍스트 가져오기
    
    Args:
        trans_data: 번역 데이터
        lang_code: 언어 코드
        
    Returns:
        str: 번역 텍스트 또는 빈 문자열
    """
    if not trans_data:
        return ""
    
    # 언어 코드에 따른 필드명 매핑
    lang_field_map = {
        "ko": "ko",
        "en": "en",
        "ja": "ja",
        "zh": "zh",
        "ru": "ru",
        "es": "es",
        "pt": "pt",
        "ar": "ar",
        "ms": "ms",
        "id": "id"
    }
    
    field_name = lang_field_map.get(lang_code, lang_code)
    return trans_data.get(field_name, trans_data.get(lang_code, ""))


def format_translation_for_display(trans_data: Dict[str, Any], max_length: int = 50) -> Dict[str, str]:
    """
    번역 데이터를 표시용으로 포맷팅
    
    Args:
        trans_data: 번역 데이터
        max_length: 최대 표시 길이
        
    Returns:
        Dict: 포맷된 번역 데이터
    """
    formatted = {}
    for lang_code in SUPPORTED_LANGUAGES.keys():
        text = get_translation_text(trans_data, lang_code)
        if text and len(text) > max_length:
            text = text[:max_length] + "..."
        formatted[lang_code] = text or "-"
    return formatted


# ============================================================================
# AI 도구 콘텐츠 번역 (tool_translations) 관련 함수
# ============================================================================

@st.cache_data(ttl=300)  # 5분 캐시
def get_all_tool_translations() -> List[Dict[str, Any]]:
    """
    모든 AI 도구 번역 데이터 조회 (tool_translations 컬렉션)
    
    Returns:
        List[Dict]: 번역 리스트
    """
    db = get_db()
    if db is None:
        return []
    
    try:
        translations_ref = db.collection(COLLECTIONS["TOOL_TRANSLATIONS"])
        docs = translations_ref.stream()
        translations = []
        for doc in docs:
            trans_data = doc.to_dict()
            trans_data["id"] = doc.id
            trans_data = convert_firestore_data(trans_data)
            translations.append(trans_data)
        return translations
    except Exception as e:
        st.error(f"AI 도구 번역 조회 실패: {e}")
        return []


@st.cache_data(ttl=60)  # 1분 캐시
def get_tool_translation_by_id(tool_id: str, lang: str) -> Optional[Dict[str, Any]]:
    """
    특정 도구의 특정 언어 번역 조회
    
    Args:
        tool_id: 도구 ID
        lang: 언어 코드
        
    Returns:
        Dict: 번역 데이터 또는 None
    """
    db = get_db()
    if db is None:
        return None
    
    try:
        # 문서 ID 형식: {toolId}_{lang}
        doc_id = f"{tool_id}_{lang}"
        doc_ref = db.collection(COLLECTIONS["TOOL_TRANSLATIONS"]).document(doc_id)
        doc = doc_ref.get()
        if doc.exists:
            trans_data = doc.to_dict()
            trans_data["id"] = doc.id
            trans_data = convert_firestore_data(trans_data)
            return trans_data
        return None
    except Exception as e:
        st.error(f"AI 도구 번역 조회 실패: {e}")
        return None


@st.cache_data(ttl=60)  # 1분 캐시
def get_tool_translations_by_tool_id(tool_id: str) -> List[Dict[str, Any]]:
    """
    특정 도구의 모든 언어 번역 조회
    
    Args:
        tool_id: 도구 ID
        
    Returns:
        List[Dict]: 번역 리스트
    """
    db = get_db()
    if db is None:
        return []
    
    try:
        translations_ref = db.collection(COLLECTIONS["TOOL_TRANSLATIONS"])
        query = translations_ref.where("toolId", "==", tool_id)
        docs = query.stream()
        translations = []
        for doc in docs:
            trans_data = doc.to_dict()
            trans_data["id"] = doc.id
            trans_data = convert_firestore_data(trans_data)
            translations.append(trans_data)
        return translations
    except Exception as e:
        st.error(f"AI 도구 번역 조회 실패: {e}")
        return []


@st.cache_data(ttl=60)  # 1분 캐시
def get_tool_translations_by_language(lang: str) -> List[Dict[str, Any]]:
    """
    특정 언어의 모든 도구 번역 조회
    
    Args:
        lang: 언어 코드
        
    Returns:
        List[Dict]: 번역 리스트
    """
    db = get_db()
    if db is None:
        return []
    
    try:
        translations_ref = db.collection(COLLECTIONS["TOOL_TRANSLATIONS"])
        query = translations_ref.where("lang", "==", lang)
        docs = query.stream()
        translations = []
        for doc in docs:
            trans_data = doc.to_dict()
            trans_data["id"] = doc.id
            trans_data = convert_firestore_data(trans_data)
            translations.append(trans_data)
        return translations
    except Exception as e:
        st.error(f"AI 도구 번역 조회 실패: {e}")
        return []


def update_tool_translation(tool_id: str, lang: str, data: Dict[str, Any]) -> bool:
    """
    AI 도구 번역 정보 업데이트
    
    Args:
        tool_id: 도구 ID
        lang: 언어 코드
        data: 업데이트할 데이터
        
    Returns:
        bool: 성공 여부
    """
    db = get_db()
    if db is None:
        return False
    
    try:
        doc_id = f"{tool_id}_{lang}"
        doc_ref = db.collection(COLLECTIONS["TOOL_TRANSLATIONS"]).document(doc_id)
        data["updatedAt"] = firestore.SERVER_TIMESTAMP
        data["updatedBy"] = "admin"  # TODO: 실제 사용자 ID로 변경
        doc_ref.update(data)
        # 캐시 무효화
        get_all_tool_translations.clear()
        get_tool_translation_by_id.clear()
        get_tool_translations_by_tool_id.clear()
        get_tool_translations_by_language.clear()
        return True
    except Exception as e:
        st.error(f"AI 도구 번역 업데이트 실패: {e}")
        return False


def create_tool_translation(tool_id: str, lang: str, data: Dict[str, Any]) -> bool:
    """
    새 AI 도구 번역 생성
    
    Args:
        tool_id: 도구 ID
        lang: 언어 코드
        data: 번역 데이터
        
    Returns:
        bool: 성공 여부
    """
    db = get_db()
    if db is None:
        return False
    
    try:
        doc_id = f"{tool_id}_{lang}"
        doc_ref = db.collection(COLLECTIONS["TOOL_TRANSLATIONS"]).document(doc_id)
        data["toolId"] = tool_id
        data["lang"] = lang
        data["createdAt"] = firestore.SERVER_TIMESTAMP
        data["updatedAt"] = firestore.SERVER_TIMESTAMP
        data["createdBy"] = "admin"  # TODO: 실제 사용자 ID로 변경
        data["updatedBy"] = "admin"
        doc_ref.set(data)
        # 캐시 무효화
        get_all_tool_translations.clear()
        get_tool_translation_by_id.clear()
        get_tool_translations_by_tool_id.clear()
        get_tool_translations_by_language.clear()
        return True
    except Exception as e:
        st.error(f"AI 도구 번역 생성 실패: {e}")
        return False


def format_tool_translation_for_display(trans_data: Dict[str, Any], max_length: int = 50) -> Dict[str, Any]:
    """
    AI 도구 번역 데이터를 표시용으로 포맷팅
    
    Args:
        trans_data: 번역 데이터
        max_length: 최대 표시 길이
        
    Returns:
        Dict: 포맷된 번역 데이터
    """
    if not trans_data:
        return {}
    
    formatted = {
        "toolId": trans_data.get("toolId", "-"),
        "lang": trans_data.get("lang", "-"),
        "tier": trans_data.get("tier", "-"),
        "docStatus": trans_data.get("docStatus", "-"),
        "translatedFrom": trans_data.get("translatedFrom", "-"),
        "sourceContentVersion": trans_data.get("sourceContentVersion", "-"),
    }
    
    # fields 필드 처리
    fields = trans_data.get("fields", {})
    if fields:
        formatted["fields"] = {}
        for field_name, field_data in fields.items():
            if isinstance(field_data, dict):
                field_text = field_data.get("text", "")
                if isinstance(field_text, list):
                    field_text = ", ".join(str(item) for item in field_text)
                if field_text and len(str(field_text)) > max_length:
                    field_text = str(field_text)[:max_length] + "..."
                formatted["fields"][field_name] = {
                    "text": field_text or "-",
                    "status": field_data.get("status", "-")
                }
            else:
                formatted["fields"][field_name] = str(field_data)
    
    return formatted
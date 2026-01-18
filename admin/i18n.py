"""
간단한 다국어 지원 모듈
"""
import streamlit as st
from typing import Dict

# 번역 딕셔너리
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "ko": {
        "welcome_title": "어드민 시스템에 오신 것을 환영합니다!",
        "welcome_message": "왼쪽 사이드바의 메뉴를 통해 각 기능에 접근할 수 있습니다.\nStreamlit의 Multi-Page 기능을 사용하여 자동으로 메뉴가 생성됩니다.",
        "language_select": "언어 선택 / Select Language",
        "admin_title": "Aicuatorhub Admin",
    },
    "en": {
        "welcome_title": "Welcome to the Admin System!",
        "welcome_message": "You can access each function through the menu on the left sidebar.\nMenus are automatically generated using Streamlit's Multi-Page feature.",
        "language_select": "Language Select / 언어 선택",
        "admin_title": "Aicuatorhub Admin",
    }
}


def get_translation(key: str, lang_code: str = None) -> str:
    """
    번역 텍스트 가져오기
    
    Args:
        key: 번역 키
        lang_code: 언어 코드 (None이면 현재 선택된 언어 사용)
        
    Returns:
        str: 번역된 텍스트
    """
    if lang_code is None:
        lang_code = st.session_state.get("admin_language", "ko")
    
    # 언어 코드가 없으면 한국어 사용
    if lang_code not in TRANSLATIONS:
        lang_code = "ko"
    
    # 번역 키가 없으면 키 자체 반환
    return TRANSLATIONS.get(lang_code, {}).get(key, key)


def t(key: str, lang_code: str = None) -> str:
    """
    번역 함수 (간단한 별칭)
    
    Args:
        key: 번역 키
        lang_code: 언어 코드
        
    Returns:
        str: 번역된 텍스트
    """
    return get_translation(key, lang_code)

"""
메뉴 시스템 관리
"""
from typing import List, Dict, Optional
from .config import COLLECTIONS
from .translations import get_translation_by_id, get_translation_text


def get_menu_items() -> List[Dict[str, str]]:
    """
    메뉴 항목 목록 반환
    
    Returns:
        List[Dict]: 메뉴 항목 리스트
    """
    return [
        {
            "icon": "📊",
            "label": "대시보드",
            "label_en": "Dashboard",
            "page": "dashboard",
            "path": "pages/1_📊_대시보드.py"
        },
        {
            "icon": "🔧",
            "label": "AI 도구 관리",
            "label_en": "AI Tools Management",
            "page": "ai_tools",
            "path": "pages/2_🔧_AI_도구_관리.py"
        },
        {
            "icon": "👥",
            "label": "사용자 관리",
            "label_en": "User Management",
            "page": "users",
            "path": "pages/3_👥_사용자_관리.py"
        },
        {
            "icon": "📝",
            "label": "AI 레시피 관리",
            "label_en": "AI Recipe Management",
            "page": "recipes",
            "path": "pages/4_📝_AI_레시피_관리.py"
        },
        {
            "icon": "🌐",
            "label": "다국어 관리",
            "label_en": "Translation Management",
            "page": "translations",
            "path": "pages/5_🌐_다국어_관리.py"
        },
        {
            "icon": "📦",
            "label": "카테고리 관리",
            "label_en": "Category Management",
            "page": "categories",
            "path": "pages/6_📦_카테고리_관리.py"
        },
        {
            "icon": "📋",
            "label": "등록 신청 관리",
            "label_en": "Registration Management",
            "page": "applications",
            "path": "pages/7_📋_등록_신청_관리.py"
        },
        {
            "icon": "💳",
            "label": "유료 서비스 관리",
            "label_en": "Paid Service Management",
            "page": "paid_services",
            "path": "pages/8_💳_유료_서비스_관리.py"
        },
        {
            "icon": "⚙️",
            "label": "설정",
            "label_en": "Settings",
            "page": "settings",
            "path": "pages/9_⚙️_설정.py"
        }
    ]


def get_menu_translation(page: str, lang_code: str = "ko") -> Optional[str]:
    """
    메뉴 번역 텍스트 가져오기
    
    Args:
        page: 메뉴 페이지 식별자 (예: "dashboard")
        lang_code: 언어 코드 (기본값: "ko")
        
    Returns:
        str: 번역된 텍스트 또는 None
    """
    # Firebase에서 번역 조회 시도
    trans_id = f"menu.{page}"
    trans_data = get_translation_by_id(trans_id)
    
    if trans_data:
        # 번역 데이터에서 해당 언어 텍스트 가져오기
        translated_text = get_translation_text(trans_data, lang_code)
        if translated_text:
            return translated_text
    
    # 번역이 없으면 기본값 반환
    menu_items = get_menu_items()
    for item in menu_items:
        if item.get("page") == page:
            if lang_code == "en":
                return item.get("label_en", item.get("label"))
            else:
                return item.get("label")
    
    return None


def get_current_language() -> str:
    """
    현재 선택된 언어 코드 반환
    
    Returns:
        str: 언어 코드 (기본값: "ko")
    """
    import streamlit as st
    return st.session_state.get("admin_language", "ko")


def get_current_page() -> str:
    """
    현재 페이지 식별자 반환
    
    Returns:
        str: 현재 페이지 식별자
    """
    import streamlit as st
    return st.session_state.get("current_page", "dashboard")

"""
공통 UI 컴포넌트
"""
import streamlit as st
from typing import List, Dict, Optional
from datetime import datetime
from .menu import get_menu_translation, get_current_language
from .config import SUPPORTED_LANGUAGES


def render_header(title: str = "Aicuatorhub Admin"):
    """
    헤더 컴포넌트 렌더링
    
    Args:
        title: 헤더 타이틀
    """
    st.markdown(f"""
    <div style="
        padding: 0.75rem 0;
        border-bottom: 2px solid #6366f1;
        margin-bottom: 1.5rem;
    ">
        <h1 style="
            color: #1e293b;
            font-size: 1.5rem;
            font-weight: 700;
            margin: 0;
        ">{title}</h1>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar_menu(menu_items: List[Dict[str, str]], current_page: str):
    """
    사이드바 메뉴 렌더링
    
    Args:
        menu_items: 메뉴 항목 리스트 [{"icon": "📊", "label": "대시보드", "page": "dashboard"}]
        current_page: 현재 페이지 식별자
    """
    # 언어 선택 UI 추가
    current_lang = get_current_language()
    
    st.sidebar.markdown("""
    <div style="
        padding: 1rem 0;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 0.75rem;
    ">
        <h2 style="
            color: #1e293b;
            font-size: 1.2rem;
            font-weight: 700;
            margin: 0;
            text-align: center;
        ">Aicuatorhub Admin</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # 언어 선택 드롭다운
    st.sidebar.markdown("### 🌐 Language")
    lang_options = {
        "ko": "한국어",
        "en": "English"
    }
    selected_lang = st.sidebar.selectbox(
        "언어 선택 / Select Language",
        options=list(lang_options.keys()),
        format_func=lambda x: lang_options[x],
        index=0 if current_lang == "ko" else 1,
        key="admin_language_selector",
        label_visibility="collapsed"
    )
    
    # 언어 변경 시 세션 상태 업데이트
    if selected_lang != current_lang:
        st.session_state.admin_language = selected_lang
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # 메뉴 항목 렌더링
    for item in menu_items:
        icon = item.get("icon", "")
        page = item.get("page", "")
        
        # 현재 언어에 맞는 메뉴 라벨 가져오기
        label = get_menu_translation(page, current_lang)
        if not label:
            # 번역이 없으면 기본 라벨 사용
            label = item.get("label", "")
        
        is_active = current_page == page
        
        # 활성 메뉴 스타일
        if is_active:
            st.sidebar.markdown(f"""
            <div style="
                background-color: #e0e7ff;
                padding: 0.5rem 0.75rem;
                border-radius: 0.4rem;
                margin: 0.2rem 0;
                border-left: 3px solid #6366f1;
            ">
                <span style="font-size: 1rem;">{icon}</span>
                <span style="
                    color: #6366f1;
                    font-weight: 600;
                    margin-left: 0.4rem;
                    font-size: 12px;
                ">{label}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            # 비활성 메뉴는 Streamlit 버튼 사용 (클릭 가능하도록)
            if st.sidebar.button(
                f"{icon} {label}",
                key=f"menu_{page}",
                use_container_width=True,
                type="secondary" if not is_active else "primary"
            ):
                st.session_state.current_page = page
                st.rerun()


def render_page_header(title: str, description: Optional[str] = None):
    """
    페이지 헤더 렌더링
    
    Args:
        title: 페이지 제목
        description: 페이지 설명 (선택)
    """
    st.markdown(f"## {title}")
    if description:
        st.caption(description)
    st.markdown("---")


def render_info_box(message: str, type: str = "info"):
    """
    정보 박스 렌더링
    
    Args:
        message: 메시지
        type: 박스 타입 (info, success, warning, error)
    """
    colors = {
        "info": "#3b82f6",
        "success": "#10b981",
        "warning": "#f59e0b",
        "error": "#ef4444"
    }
    color = colors.get(type, colors["info"])
    
    st.markdown(f"""
    <div style="
        background-color: {color}15;
        border-left: 3px solid {color};
        padding: 0.75rem;
        border-radius: 0.4rem;
        margin: 0.75rem 0;
    ">
        <p style="margin: 0; color: {color}; font-weight: 500; font-size: 12px;">{message}</p>
    </div>
    """, unsafe_allow_html=True)


def render_stat_card(title: str, value: str, change: Optional[str] = None):
    """
    통계 카드 렌더링
    
    Args:
        title: 카드 제목
        value: 값
        change: 변화량 (선택)
    """
    col1, col2 = st.columns([3, 1])
    with col1:
        st.metric(title, value, change)
    with col2:
        st.write("")  # 공간 확보


def render_language_selector():
    """
    언어 선택 UI 렌더링 (사이드바에 표시)
    """
    current_lang = get_current_language()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🌐 Language")
    
    lang_options = {
        "ko": "한국어",
        "en": "English"
    }
    
    selected_lang = st.sidebar.selectbox(
        "언어 선택 / Select Language",
        options=list(lang_options.keys()),
        format_func=lambda x: lang_options[x],
        index=0 if current_lang == "ko" else 1,
        key="admin_language_selector"
    )
    
    # 언어 변경 시 세션 상태 업데이트
    if selected_lang != current_lang:
        st.session_state.admin_language = selected_lang
        st.rerun()
    
    return selected_lang

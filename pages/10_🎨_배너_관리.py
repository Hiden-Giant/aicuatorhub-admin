"""
배너 관리 페이지
HTML mockup을 기반으로 구현
"""
import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from admin.firebase import get_db
from admin.components import render_page_header
from admin.config import (
    COLLECTIONS, BANNER_SPOTS, BANNER_STATUS, COUNTRIES,
    BANNER_PAGES, SUPPORTED_LANGUAGES
)
from admin.banners import (
    get_all_banners, get_banners_by_spot, get_banner_by_id,
    update_banner, create_banner, delete_banner, update_banner_priority,
    get_banner_status
)
from admin.utils import convert_firestore_data, format_datetime

# 페이지 설정
st.set_page_config(
    page_title="배너 관리 - Aicuatorhub Admin",
    page_icon="🎨",
    layout="wide"
)

# Firebase 연결
db = get_db()
if db is None:
    st.error("⚠️ Firebase 연결에 실패했습니다.")
    st.stop()

# 세션 상태 초기화
if 'selected_spot_id' not in st.session_state:
    st.session_state.selected_spot_id = "web_top"
if 'selected_banner_id' not in st.session_state:
    st.session_state.selected_banner_id = None
if 'selected_banner_data' not in st.session_state:
    st.session_state.selected_banner_data = None
if 'is_new_banner' not in st.session_state:
    st.session_state.is_new_banner = False

# 페이지 헤더
render_page_header("🎨 배너 관리", "웹사이트 및 모바일 배너를 관리할 수 있습니다.")

# 3열 레이아웃 (HTML mockup 기반)
# Streamlit에서는 픽셀 단위가 아닌 비율로 설정
col_spots, col_list, col_detail = st.columns([1.5, 2, 3])

# 1. 좌측: Display Spots (배너 위치)
with col_spots:
    st.markdown("""
    <div style="
        background: white;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #e0e0e0;
        margin-bottom: 10px;
    ">
        <div style="
            padding: 10px;
            border-bottom: 1px solid #e0e0e0;
            font-weight: 700;
            font-size: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        ">
            Display Spots
            <span style="color: #aaa;">🔍</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 배너 위치 목록
    all_banners = get_all_banners()
    
    for spot_id, spot_info in BANNER_SPOTS.items():
        spot_banners = [b for b in all_banners if b.get("spotId") == spot_id]
        count = len(spot_banners)
        
        is_active = st.session_state.selected_spot_id == spot_id
        
        if is_active:
            st.markdown(f"""
            <div style="
                padding: 8px 10px;
                margin-bottom: 4px;
                border-radius: 4px;
                background-color: #e3f2fd;
                color: #4a90e2;
                font-weight: bold;
                display: flex;
                justify-content: space-between;
                align-items: center;
                cursor: pointer;
                font-size: 12px;
            ">
                <div style="display: flex; align-items: center;">
                    <span style="margin-right: 6px; width: 18px; text-align: center;">{spot_info['icon']}</span>
                    {spot_info['name']}
                </div>
                <span style="
                    background: #fff;
                    color: #4a90e2;
                    padding: 2px 6px;
                    border-radius: 10px;
                    font-size: 10px;
                    font-weight: 600;
                ">{count}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            if st.button(f"{spot_info['icon']} {spot_info['name']} ({count})", 
                        key=f"spot_{spot_id}", 
                        use_container_width=True,
                        type="secondary" if not is_active else "primary"):
                st.session_state.selected_spot_id = spot_id
                st.session_state.selected_banner_id = None
                st.session_state.selected_banner_data = None
                st.rerun()

# 2. 중앙: Rotation List (배너 목록)
with col_list:
    st.markdown("""
    <div style="
        background: white;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #e0e0e0;
        margin-bottom: 10px;
    ">
        <div style="
            padding: 10px;
            border-bottom: 1px solid #e0e0e0;
            font-weight: 700;
            font-size: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        ">
            Rotation List
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 새 배너 추가 버튼
    if st.button("➕ 새 배너 추가", use_container_width=True, type="primary"):
        st.session_state.is_new_banner = True
        st.session_state.selected_banner_id = None
        st.session_state.selected_banner_data = None
        st.rerun()
    
    st.caption("💡 배너를 클릭하여 상세 정보를 편집하세요.")
    
    # 선택된 위치의 배너 목록
    spot_banners = get_banners_by_spot(st.session_state.selected_spot_id)
    
    if spot_banners:
        for idx, banner in enumerate(spot_banners, 1):
            banner_status = get_banner_status(banner)
            status_badge = {
                "live": "🟢 LIVE",
                "scheduled": "🟡 SCHEDULED",
                "off": "⚫ OFF"
            }.get(banner_status, "⚫ OFF")
            
            end_date = banner.get("displayEnd")
            end_date_str = ""
            if end_date:
                try:
                    if isinstance(end_date, str):
                        end_date_obj = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                    else:
                        end_date_obj = end_date
                    end_date_str = end_date_obj.strftime("~ %Y.%m.%d")
                except:
                    end_date_str = ""
            page_id = banner.get("pageId") or "all"
            page_label = BANNER_PAGES.get(page_id, {}).get("name", page_id)
            
            is_selected = st.session_state.selected_banner_id == banner.get("id")
            
            if is_selected:
                st.markdown(f"""
                <div style="
                    background: white;
                    border: 2px solid #4a90e2;
                    border-radius: 6px;
                    padding: 8px;
                    margin-bottom: 8px;
                    display: flex;
                    gap: 8px;
                    align-items: center;
                    cursor: pointer;
                ">
                    <div style="
                        font-size: 18px;
                        font-weight: 800;
                        color: #4a90e2;
                        width: 20px;
                        text-align: center;
                    ">{idx}</div>
                    <div style="
                        width: 60px;
                        height: 38px;
                        background-color: #eee;
                        border-radius: 4px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 11px;
                        color: #999;
                    ">이미지</div>
                    <div style="flex: 1; min-width: 0;">
                        <div style="
                            font-weight: 600;
                            font-size: 12px;
                            margin-bottom: 3px;
                            white-space: nowrap;
                            overflow: hidden;
                            text-overflow: ellipsis;
                        ">{banner.get('title', '제목 없음')}</div>
                        <div style="
                            display: flex;
                            align-items: center;
                            gap: 6px;
                            font-size: 11px;
                            color: #666;
                        ">
                            <span style="
                                padding: 2px 5px;
                                border-radius: 3px;
                                font-size: 10px;
                                font-weight: 700;
                            ">{status_badge}</span>
                            <span style="color: #888;">📄 {page_label}</span>
                            <span>{end_date_str}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                if st.button(
                    f"{idx}. {banner.get('title', '제목 없음')[:20]}... [{page_label}]",
                    key=f"banner_{banner.get('id')}",
                    use_container_width=True,
                    help=f"{status_badge} 📄 {page_label} {end_date_str}"
                ):
                    st.session_state.selected_banner_id = banner.get("id")
                    banner_data = get_banner_by_id(banner.get("id"))
                    if banner_data:
                        st.session_state.selected_banner_data = banner_data
                    st.session_state.is_new_banner = False
                    st.rerun()
    else:
        st.info("이 위치에 등록된 배너가 없습니다.")

# 3. 우측: Detail Settings (상세 설정)
with col_detail:
    st.markdown("""
    <div style="
        background: white;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #e0e0e0;
        margin-bottom: 10px;
    ">
        <div style="
            padding: 10px;
            border-bottom: 1px solid #e0e0e0;
            font-weight: 700;
            font-size: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        ">
            Detail Settings
            <span style="font-weight: normal; font-size: 12px; color: #999;">
                ID: {banner_id}
            </span>
        </div>
    </div>
    """.format(banner_id=st.session_state.selected_banner_id or "신규"), unsafe_allow_html=True)
    
    if st.session_state.is_new_banner or st.session_state.selected_banner_data:
        # 탭 메뉴
        tab1, tab2, tab3 = st.tabs([
            "Basic & Schedule", "Content & Link", "Targeting"
        ])
        
        # 기본 데이터
        banner_data = st.session_state.selected_banner_data or {}
        is_new = st.session_state.is_new_banner
        
        with tab1:
            st.markdown("#### 기본 정보 및 일정")
            
            # 배너 제목
            banner_title = st.text_input(
                "배너 제목 (관리자용)",
                value=banner_data.get("title", ""),
                key="banner_title",
                placeholder="배너 제목을 입력하세요"
            )
            
            # 배너 위치 (신규일 때만 선택 가능)
            if is_new:
                spot_options = {f"{info['icon']} {info['name']}": spot_id 
                               for spot_id, info in BANNER_SPOTS.items()}
                selected_spot_name = st.selectbox(
                    "배너 위치",
                    list(spot_options.keys()),
                    key="banner_spot_select"
                )
                selected_spot_id = spot_options[selected_spot_name]
            else:
                current_spot = BANNER_SPOTS.get(banner_data.get("spotId", "web_top"), {})
                st.text_input(
                    "배너 위치",
                    value=f"{current_spot.get('icon', '')} {current_spot.get('name', '')}",
                    disabled=True,
                    key="banner_spot_display"
                )
                selected_spot_id = banner_data.get("spotId", "web_top")
            
            # 노출 페이지 (페이지별 배너 영역 관리)
            page_names = list(BANNER_PAGES.keys())
            page_display = [BANNER_PAGES[pid]["name"] for pid in page_names]
            current_page_id = banner_data.get("pageId", "all")
            if current_page_id not in BANNER_PAGES:
                current_page_id = "all"
            try:
                page_index = page_names.index(current_page_id)
            except ValueError:
                page_index = 0
            selected_page_name = st.selectbox(
                "노출 페이지",
                options=page_display,
                index=page_index,
                key="banner_page_id",
                help="이 배너를 노출할 HTML 페이지. '전체 페이지'면 모든 페이지에 노출됩니다."
            )
            selected_page_id = page_names[page_display.index(selected_page_name)]
            
            # 전시 기간
            col_date1, col_date2 = st.columns(2)
            
            with col_date1:
                display_start = st.date_input(
                    "전시 시작일",
                    value=datetime.fromisoformat(banner_data.get("displayStart", datetime.now().isoformat()).replace("Z", "+00:00")).date() if banner_data.get("displayStart") else date.today(),
                    key="banner_start_date"
                )
                display_start_time = st.time_input(
                    "시작 시간",
                    value=datetime.fromisoformat(banner_data.get("displayStart", datetime.now().isoformat()).replace("Z", "+00:00")).time() if banner_data.get("displayStart") else datetime.now().time(),
                    key="banner_start_time"
                )
            
            with col_date2:
                display_end = st.date_input(
                    "전시 종료일",
                    value=datetime.fromisoformat(banner_data.get("displayEnd", (datetime.now() + timedelta(days=30)).isoformat()).replace("Z", "+00:00")).date() if banner_data.get("displayEnd") else date.today() + timedelta(days=30),
                    key="banner_end_date"
                )
                display_end_time = st.time_input(
                    "종료 시간",
                    value=datetime.fromisoformat(banner_data.get("displayEnd", (datetime.now() + timedelta(days=30)).isoformat()).replace("Z", "+00:00")).time() if banner_data.get("displayEnd") else datetime.now().time(),
                    key="banner_end_time"
                )
            
            # 상태 및 우선순위
            col_status1, col_status2 = st.columns(2)
            
            with col_status1:
                banner_status = st.selectbox(
                    "상태",
                    list(BANNER_STATUS.keys()),
                    index=list(BANNER_STATUS.keys()).index(banner_data.get("status", "live")) if banner_data.get("status") in BANNER_STATUS else 0,
                    format_func=lambda x: BANNER_STATUS[x],
                    key="banner_status"
                )
            
            with col_status2:
                banner_priority = st.number_input(
                    "우선순위",
                    min_value=1,
                    value=int(banner_data.get("priority", 1)),
                    key="banner_priority",
                    help="숫자가 작을수록 먼저 표시됩니다"
                )
        
        with tab2:
            st.markdown("#### 콘텐츠 및 링크")
            
            # 웹용 이미지
            st.markdown("##### 웹용 배너")
            web_image_url = st.text_input(
                "웹 이미지 URL",
                value=banner_data.get("webImageUrl", ""),
                key="web_image_url",
                placeholder="https://example.com/banner-web.jpg"
            )
            web_link_url = st.text_input(
                "웹 링크 URL",
                value=banner_data.get("webLinkUrl", ""),
                key="web_link_url",
                placeholder="https://example.com/page"
            )
            
            if web_image_url:
                try:
                    st.image(web_image_url, width=300, caption="웹 배너 미리보기")
                except:
                    st.warning("이미지를 불러올 수 없습니다.")
            
            st.markdown("---")
            
            # 모바일용 이미지
            st.markdown("##### 모바일용 배너")
            mobile_image_url = st.text_input(
                "모바일 이미지 URL",
                value=banner_data.get("mobileImageUrl", ""),
                key="mobile_image_url",
                placeholder="https://example.com/banner-mobile.jpg"
            )
            mobile_link_url = st.text_input(
                "모바일 링크 URL",
                value=banner_data.get("mobileLinkUrl", ""),
                key="mobile_link_url",
                placeholder="https://example.com/page"
            )
            
            if mobile_image_url:
                try:
                    st.image(mobile_image_url, width=200, caption="모바일 배너 미리보기")
                except:
                    st.warning("이미지를 불러올 수 없습니다.")
        
        with tab3:
            st.markdown("#### 타겟팅 설정")
            
            # 타겟 언어 선택 (요구: 언어 옵션 추가, 프론트에서 언어 우선 적용)
            st.markdown("##### 타겟 언어")
            st.caption("배너를 표시할 언어를 선택하세요. (선택하지 않으면 모든 언어에 표시. 언어/국가 둘 다 설정된 경우 프론트에서는 **언어를 우선** 적용합니다.)")
            selected_langs = banner_data.get("targetLanguages", [])
            if not isinstance(selected_langs, list):
                selected_langs = []
            lang_options = list(SUPPORTED_LANGUAGES.keys())
            lang_selected = []
            cols = st.columns(3)
            for i, lang_code in enumerate(lang_options):
                with cols[i % 3]:
                    info = SUPPORTED_LANGUAGES.get(lang_code, {})
                    label = f"{lang_code} ({info.get('native', info.get('name', lang_code))})"
                    if st.checkbox(label, value=lang_code in selected_langs, key=f"lang_{lang_code}"):
                        lang_selected.append(lang_code)
            all_selected_languages = lang_selected if lang_selected else None
            
            st.markdown("##### 타겟 국가")
            st.caption("배너를 표시할 국가를 선택하세요. (선택하지 않으면 모든 국가에 표시)")
            
            # 국가를 지역별로 그룹화
            asia_countries = ["KR", "JP", "CN", "SG", "MY", "VN", "ID", "TH", "PH", "IN"]
            other_countries = [c for c in COUNTRIES.keys() if c not in asia_countries]
            
            selected_countries = banner_data.get("targetCountries", [])
            if not isinstance(selected_countries, list):
                selected_countries = []
            
            # ASIA Pacific
            with st.expander("🌏 ASIA Pacific", expanded=True):
                asia_selected = []
                for country_code in asia_countries:
                    country_name = COUNTRIES.get(country_code, country_code)
                    is_checked = st.checkbox(
                        f"{country_code} ({country_name})",
                        value=country_code in selected_countries,
                        key=f"country_{country_code}"
                    )
                    if is_checked:
                        asia_selected.append(country_code)
            
            # 기타 국가
            with st.expander("🌍 기타 국가"):
                other_selected = []
                for country_code in other_countries:
                    country_name = COUNTRIES.get(country_code, country_code)
                    is_checked = st.checkbox(
                        f"{country_code} ({country_name})",
                        value=country_code in selected_countries,
                        key=f"country_{country_code}"
                    )
                    if is_checked:
                        other_selected.append(country_code)
            
            all_selected_countries = asia_selected + other_selected
        
        # 저장/삭제 버튼
        st.markdown("---")
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
        
        with col_btn1:
            if st.button("🗑️ 삭제", use_container_width=True, disabled=is_new):
                if st.session_state.get('confirm_delete_banner', False):
                    if delete_banner(st.session_state.selected_banner_id):
                        st.success("배너가 삭제되었습니다!")
                        st.session_state.selected_banner_id = None
                        st.session_state.selected_banner_data = None
                        st.session_state.is_new_banner = False
                        st.session_state.confirm_delete_banner = False
                        st.rerun()
                else:
                    st.session_state.confirm_delete_banner = True
                    st.warning("⚠️ 정말 삭제하시겠습니까? 다시 클릭하면 삭제됩니다.")
                    st.rerun()
        
        with col_btn2:
            if st.button("❌ 취소", use_container_width=True):
                st.session_state.is_new_banner = False
                st.session_state.selected_banner_id = None
                st.session_state.selected_banner_data = None
                st.rerun()
        
        with col_btn3:
            if st.button("💾 저장", use_container_width=True, type="primary"):
                # 날짜/시간 결합
                display_start_dt = datetime.combine(display_start, display_start_time)
                display_end_dt = datetime.combine(display_end, display_end_time)
                
                banner_data_to_save = {
                    "title": banner_title,
                    "spotId": selected_spot_id,
                    "pageId": selected_page_id,
                    "displayStart": display_start_dt.isoformat(),
                    "displayEnd": display_end_dt.isoformat(),
                    "status": banner_status,
                    "priority": banner_priority,
                    "webImageUrl": web_image_url,
                    "webLinkUrl": web_link_url,
                    "mobileImageUrl": mobile_image_url,
                    "mobileLinkUrl": mobile_link_url,
                    "targetLanguages": all_selected_languages,
                    "targetCountries": all_selected_countries if all_selected_countries else None
                }
                
                if is_new:
                    # 새 배너 생성
                    import uuid
                    new_banner_id = f"banner_{uuid.uuid4().hex[:8]}"
                    if create_banner(new_banner_id, banner_data_to_save):
                        st.success("✅ 배너가 생성되었습니다!")
                        st.session_state.is_new_banner = False
                        st.session_state.selected_banner_id = new_banner_id
                        st.session_state.selected_banner_data = get_banner_by_id(new_banner_id)
                        st.rerun()
                else:
                    # 기존 배너 업데이트
                    if update_banner(st.session_state.selected_banner_id, banner_data_to_save):
                        st.success("✅ 배너가 업데이트되었습니다!")
                        st.session_state.selected_banner_data = get_banner_by_id(st.session_state.selected_banner_id)
                        st.rerun()
    else:
        st.info("👆 좌측에서 배너 위치를 선택하고, 중앙에서 배너를 선택하거나 새 배너를 추가하세요.")

# 사이드바 통계
with st.sidebar:
    st.markdown("### 📊 배너 통계")
    
    total_banners = len(all_banners)
    st.metric("전체 배너 수", f"{total_banners:,}개")
    
    # 위치별 배너 수
    st.markdown("#### 위치별 배너 수")
    for spot_id, spot_info in BANNER_SPOTS.items():
        spot_count = len([b for b in all_banners if b.get("spotId") == spot_id])
        st.write(f"{spot_info['icon']} **{spot_info['name']}**: {spot_count}개")
    
    # 상태별 통계
    if all_banners:
        st.markdown("#### 상태별 분포")
        status_counts = {"live": 0, "scheduled": 0, "off": 0}
        for banner in all_banners:
            status = get_banner_status(banner)
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in status_counts.items():
            status_name = BANNER_STATUS.get(status, status)
            st.write(f"**{status_name}**: {count}개")
    
    # 캐시 초기화
    if st.button("🔄 캐시 초기화", use_container_width=True):
        get_all_banners.clear()
        get_banners_by_spot.clear()
        get_banner_by_id.clear()
        st.success("캐시가 초기화되었습니다!")
        st.rerun()

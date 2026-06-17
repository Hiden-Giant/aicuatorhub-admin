"""
배너 관리 페이지
HTML mockup을 기반으로 구현
"""
import streamlit as st
import sys
import os
import html
import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from admin.firebase import get_db
from admin.components import render_page_header
from admin.config import (
    COLLECTIONS, BANNER_SPOTS, BANNER_STATUS, COUNTRIES,
    BANNER_PAGES, SUPPORTED_LANGUAGES, BANNER_DISPLAY_LAYOUTS
)
from admin.banners import (
    get_all_banners, get_banners_by_spot, get_banner_by_id,
    update_banner, create_banner, delete_banner, update_banner_priority,
    get_banner_status, get_banner_slot_setting, upsert_banner_slot_setting,
    get_all_banner_slot_settings,
)
from admin.utils import convert_firestore_data, format_datetime


def _parse_banner_datetime(value, default=None):
    """Firestore/ISO 문자열·datetime 객체를 폼용 naive datetime으로 변환"""
    if default is None:
        default = datetime.now()
    if not value:
        return default
    if isinstance(value, datetime):
        return value.replace(tzinfo=None) if value.tzinfo else value
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt.replace(tzinfo=None) if dt.tzinfo else dt
        except ValueError:
            return default
    return default


# 신규/편집 폼 위젯 키만 초기화 (버튼·레이아웃 위젯은 제외)
_BANNER_FORM_WIDGET_KEYS = (
    "banner_title",
    "banner_spot_select",
    "banner_spot_display",
    "banner_page_id",
    "banner_start_date",
    "banner_start_time",
    "banner_end_date",
    "banner_end_time",
    "banner_status",
    "banner_priority",
    "web_image_url",
    "web_link_url",
    "mobile_image_url",
    "mobile_link_url",
)
_MAX_CONTENT_SLOTS = 4


def _clear_banner_form_widget_state():
    """배너 폼 입력 위젯만 세션 키 초기화 (버튼 key 삭제 방지)"""
    for key in _BANNER_FORM_WIDGET_KEYS:
        if key in st.session_state:
            del st.session_state[key]
    for i in range(1, _MAX_CONTENT_SLOTS + 1):
        for prefix in ("web_image_url_", "web_link_url_", "mobile_image_url_", "mobile_link_url_"):
            key = f"{prefix}{i}"
            if key in st.session_state:
                del st.session_state[key]
    for key in list(st.session_state.keys()):
        if key.startswith("lang_") or key.startswith("country_"):
            del st.session_state[key]


def _get_banner_group(spot_id: str, page_id: str, max_count: int) -> List[Dict[str, Any]]:
    """슬롯+페이지 기준 배너 그룹 (우선순위 순, 최대 max_count)"""
    spot_banners = get_banners_by_spot(spot_id)
    page_banners = _filter_banners_for_page(spot_banners, page_id)
    page_banners = sorted(page_banners, key=lambda x: int(x.get("priority", 999)))
    return page_banners[:max_count]


def _get_group_primary_title(banner: Dict[str, Any]) -> str:
    """그룹 공통 제목 (배너 #1, #2 접미사 제거)"""
    title = (banner.get("title") or "").strip()
    if " #" in title:
        return title.rsplit(" #", 1)[0]
    return title


def _slot_has_content(slot: Dict[str, Any]) -> bool:
    return any((slot.get(k) or "").strip() for k in (
        "webImageUrl", "webLinkUrl", "mobileImageUrl", "mobileLinkUrl"
    ))


def _save_banner_group(
    spot_id: str,
    page_id: str,
    form_max: int,
    common_data: Dict[str, Any],
    content_slots: List[Dict[str, Any]],
) -> tuple:
    """레이아웃 슬롯 수만큼 배너 일괄 생성/수정 (일정·타겟팅 공통)"""
    import uuid
    existing_all = _filter_banners_for_page(get_banners_by_spot(spot_id), page_id)
    saved_ids: List[str] = []
    base_title = (common_data.get("title") or "배너").strip()

    for slot in content_slots:
        priority = int(slot["priority"])
        existing_banner = next(
            (b for b in existing_all if int(b.get("priority", -1)) == priority),
            None,
        )
        if not existing_banner and slot.get("id"):
            existing_banner = get_banner_by_id(slot["id"])

        slot_payload = {
            **common_data,
            "spotId": spot_id,
            "pageId": page_id,
            "priority": priority,
            "title": base_title if form_max == 1 else f"{base_title} #{priority}",
            "webImageUrl": (slot.get("webImageUrl") or "").strip(),
            "webLinkUrl": (slot.get("webLinkUrl") or "").strip(),
            "mobileImageUrl": (slot.get("mobileImageUrl") or "").strip(),
            "mobileLinkUrl": (slot.get("mobileLinkUrl") or "").strip(),
        }

        if _slot_has_content(slot_payload):
            if existing_banner and existing_banner.get("id"):
                if update_banner(existing_banner["id"], slot_payload):
                    saved_ids.append(existing_banner["id"])
            else:
                new_id = f"banner_{uuid.uuid4().hex[:8]}"
                if create_banner(new_id, slot_payload):
                    saved_ids.append(new_id)
        elif existing_banner and existing_banner.get("id"):
            delete_banner(existing_banner["id"])

    for b in existing_all:
        if int(b.get("priority", 0)) > form_max and b.get("id"):
            delete_banner(b["id"])

    return bool(saved_ids), saved_ids


def _delete_banner_group(spot_id: str, page_id: str) -> int:
    """슬롯+페이지 배너 그룹 전체 삭제"""
    group = _filter_banners_for_page(get_banners_by_spot(spot_id), page_id)
    deleted = 0
    for b in group:
        if b.get("id") and delete_banner(b["id"]):
            deleted += 1
    return deleted


def _start_new_banner():
    st.session_state.is_new_banner = True
    st.session_state.selected_banner_id = None
    st.session_state.selected_banner_data = None
    st.session_state.confirm_delete_banner = False
    _clear_banner_form_widget_state()


def _handle_add_new_banner_click():
    """새 배너 추가 버튼 — on_click + rerun 으로 우측 폼 즉시 표시"""
    _start_new_banner()
    st.rerun()


def _render_image_preview(url: str, max_width: int = 300, caption: str = "미리보기"):
    """직접 접근 가능한 이미지 URL 미리보기 (st.image 대신 HTML img 사용)"""
    url = (url or "").strip()
    if not url:
        return
    if not url.startswith(("http://", "https://")):
        st.warning("URL은 `http://` 또는 `https://` 로 시작해야 합니다.")
        return
    safe_url = html.escape(url, quote=True)
    st.markdown(
        f'<p style="font-size:12px;color:#666;margin:8px 0 4px;">{html.escape(caption)}</p>'
        f'<img src="{safe_url}" alt="banner preview" '
        f'style="max-width:{max_width}px;width:100%;border-radius:8px;border:1px solid #ddd;display:block;" '
        f'onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'block\'" />'
        f'<p style="display:none;color:#c0392b;font-size:12px;margin-top:6px;">'
        f'⚠️ 이미지를 불러올 수 없습니다. JPG/PNG/WebP <strong>직접 링크</strong>인지 확인하세요.<br>'
        f'Google Drive 공유 링크·로그인 필요 URL은 사용할 수 없습니다.</p>',
        unsafe_allow_html=True,
    )


def _filter_banners_for_page(banners: List[Dict[str, Any]], page_id: str) -> List[Dict[str, Any]]:
    """특정 페이지(또는 전체)에 노출되는 배너만 필터"""
    return [
        b for b in banners
        if not b.get("pageId") or b.get("pageId") == "all" or b.get("pageId") == page_id
    ]


def _count_live_banners(banners: List[Dict[str, Any]], page_id: str) -> int:
    """페이지 기준 LIVE 배너 수"""
    return sum(
        1 for b in _filter_banners_for_page(banners, page_id)
        if get_banner_status(b) == "live"
    )


def _suggest_next_priority(banners: List[Dict[str, Any]], page_id: str) -> int:
    """같은 슬롯·페이지에 등록된 배너 기준 다음 우선순위"""
    filtered = _filter_banners_for_page(banners, page_id)
    if not filtered:
        return 1
    return max(int(b.get("priority", 1)) for b in filtered) + 1


def _render_registration_status(spot_banners: List[Dict[str, Any]], page_id: str, layout_id: str):
    """레이아웃별 배너 등록 현황 (1배너=1이미지 안내 포함)"""
    info = BANNER_DISPLAY_LAYOUTS.get(layout_id, BANNER_DISPLAY_LAYOUTS["single"])
    max_needed = info["maxBanners"]
    page_banners = _filter_banners_for_page(spot_banners, page_id)
    live_count = sum(1 for b in page_banners if get_banner_status(b) == "live")
    total_count = len(page_banners)
    page_label = BANNER_PAGES.get(page_id, {}).get("name", page_id)

    st.markdown(
        f"**등록 현황** · `{page_label}` · LIVE **{live_count}** / 필요 **{max_needed}**개 "
        f"(전체 등록 {total_count}개)"
    )

    if max_needed > 1:
        st.info(
            f"**{info['name']}** — Content & Link 탭에서 이미지 URL **{max_needed}개**를 한 번에 입력·저장합니다.  \n"
            f"일정·상태·타겟팅은 **{max_needed}개 배너 공통** · 좌→우 우선순위 **1→{max_needed}** 자동 적용."
        )
    else:
        st.caption("이 레이아웃은 이미지 URL **1개**만 입력하면 됩니다.")

    if live_count < max_needed:
        remaining = max_needed - live_count
        st.error(f"⚠️ LIVE 배너가 **{remaining}개** 더 필요합니다. 「배너 등록/편집」에서 URL을 입력하세요.")
    elif live_count >= max_needed:
        st.success(f"✅ LIVE 배너 {live_count}개 — 레이아웃 노출 준비 완료")


def _render_thumbnail_html(banner: Dict[str, Any], size: int = 60) -> str:
    """Rotation List용 썸네일 HTML"""
    img_url = (banner.get("webImageUrl") or banner.get("mobileImageUrl") or "").strip()
    if img_url and img_url.startswith(("http://", "https://")):
        safe_url = html.escape(img_url, quote=True)
        return (
            f'<img src="{safe_url}" style="width:{size}px;height:{size - 22}px;object-fit:cover;'
            f'border-radius:4px;display:block;" '
            f'onerror="this.outerHTML=\'<div style=&quot;width:{size}px;height:{size - 22}px;'
            f'background:#eee;border-radius:4px;display:flex;align-items:center;justify-content:center;'
            f'font-size:10px;color:#999;&quot;>없음</div>\'" />'
        )
    return (
        f'<div style="width:{size}px;height:{size - 22}px;background:#eee;border-radius:4px;'
        f'display:flex;align-items:center;justify-content:center;font-size:10px;color:#999;">없음</div>'
    )


def _render_layout_size_guide(layout_id: str, is_mobile_spot: bool):
    """선택된 디스플레이 레이아웃별 권장 이미지 사이즈 안내"""
    info = BANNER_DISPLAY_LAYOUTS.get(layout_id, BANNER_DISPLAY_LAYOUTS["single"])
    device_label = "모바일" if is_mobile_spot else "웹(PC)"
    size = info["mobileSize"] if is_mobile_spot else info["webSize"]
    multi_hint = ""
    if info["maxBanners"] > 1:
        multi_hint = (
            f"  \n📌 Content & Link 탭에서 **이미지 URL {info['maxBanners']}개**를 한 폼에 입력합니다 "
            f"(일정·타겟팅 공통)."
        )
    st.info(
        f"**{info['name']}** · {device_label} 권장: **{size}**  \n"
        f"슬롯당 최대 **{info['maxBanners']}개** · {info['description']}{multi_hint}"
    )
    st.caption(
        "✅ 사용 가능: Firebase Storage (`?alt=media&token=...`), Imgur, CDN 직접 URL  \n"
        "❌ 사용 불가: Google Drive 공유 링크, HTML 페이지 URL, 로그인 필요 URL"
    )

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
if 'layout_page_id' not in st.session_state:
    st.session_state.layout_page_id = "index"

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
    
    # --- 디스플레이 레이아웃 설정 (슬롯 + 페이지별) ---
    st.markdown("#### 📐 디스플레이 레이아웃")
    layout_page_names = list(BANNER_PAGES.keys())
    layout_page_labels = [BANNER_PAGES[p]["name"] for p in layout_page_names]
    try:
        layout_page_index = layout_page_names.index(st.session_state.layout_page_id)
    except ValueError:
        layout_page_index = layout_page_names.index("index") if "index" in layout_page_names else 0

    selected_layout_page_label = st.selectbox(
        "레이아웃 적용 페이지",
        layout_page_labels,
        index=layout_page_index,
        key="layout_page_select",
        help="선택한 페이지·슬롯 조합에 레이아웃이 적용됩니다.",
    )
    st.session_state.layout_page_id = layout_page_names[layout_page_labels.index(selected_layout_page_label)]

    current_slot_setting = get_banner_slot_setting(
        st.session_state.selected_spot_id,
        st.session_state.layout_page_id,
    )
    layout_keys = list(BANNER_DISPLAY_LAYOUTS.keys())
    current_layout = current_slot_setting.get("displayLayout", "single")
    if current_layout not in layout_keys:
        current_layout = "single"

    selected_layout = st.radio(
        "배너 표시 방식",
        layout_keys,
        index=layout_keys.index(current_layout),
        format_func=lambda x: BANNER_DISPLAY_LAYOUTS[x]["name"],
        key="slot_display_layout",
        horizontal=True,
    )

    is_mobile_spot = st.session_state.selected_spot_id.startswith("mobile_")
    _render_layout_size_guide(selected_layout, is_mobile_spot)

    # 선택된 위치의 배너 목록 (등록 현황 계산용)
    spot_banners_all = get_banners_by_spot(st.session_state.selected_spot_id)
    _render_registration_status(
        spot_banners_all,
        st.session_state.layout_page_id,
        selected_layout,
    )

    if st.button("💾 레이아웃 저장", key="save_slot_layout_btn", use_container_width=True):
        if upsert_banner_slot_setting(
            st.session_state.selected_spot_id,
            st.session_state.layout_page_id,
            selected_layout,
        ):
            st.success("디스플레이 레이아웃이 저장되었습니다!")
            st.rerun()

    st.markdown("---")
    
    # 배너 등록/편집 버튼
    st.button(
        "➕ 배너 등록/편집",
        key="banner_add_new_btn",
        use_container_width=True,
        type="primary",
        on_click=_handle_add_new_banner_click,
    )

    max_for_layout = BANNER_DISPLAY_LAYOUTS.get(selected_layout, {}).get("maxBanners", 1)

    if st.session_state.is_new_banner:
        st.success(
            f"📝 **배너 등록/편집 중** — 우측 **Content & Link** 탭에 "
            f"이미지 URL **{max_for_layout}개** 영역이 표시됩니다. **💾 저장**으로 일괄 등록."
        )
    elif max_for_layout > 1:
        st.caption(
            f"💡 **1줄 {max_for_layout}개** 레이아웃: 「배너 등록/편집」 클릭 후 "
            f"Content & Link에서 URL **{max_for_layout}개**를 한 번에 입력하세요."
        )
    else:
        st.caption("💡 「배너 등록/편집」으로 배너를 추가하거나 목록에서 선택해 편집하세요.")

    filter_page_only = st.checkbox(
        f"「{BANNER_PAGES.get(st.session_state.layout_page_id, {}).get('name', st.session_state.layout_page_id)}」 배너만 보기",
        value=True,
        key="filter_rotation_by_page",
    )

    # 선택된 위치의 배너 목록
    spot_banners = spot_banners_all
    if filter_page_only:
        spot_banners = _filter_banners_for_page(spot_banners, st.session_state.layout_page_id)
        spot_banners = sorted(spot_banners, key=lambda x: x.get("priority", 999))
    
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
            priority = banner.get("priority", idx)
            thumb_html = _render_thumbnail_html(banner)
            
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
                    ">{priority}</div>
                    <div style="flex-shrink:0;">{thumb_html}</div>
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
                btn_label = (
                    f"#{priority} {banner.get('title', '제목 없음')[:18]} "
                    f"[{page_label}] {status_badge}"
                )
                if st.button(
                    btn_label,
                    key=f"banner_{banner.get('id')}",
                    use_container_width=True,
                    help=f"우선순위 {priority} · {status_badge} · 📄 {page_label} {end_date_str}",
                ):
                    st.session_state.selected_banner_id = banner.get("id")
                    banner_data = get_banner_by_id(banner.get("id"))
                    if banner_data:
                        st.session_state.selected_banner_data = banner_data
                    st.session_state.is_new_banner = False
                    st.session_state.confirm_delete_banner = False
                    _clear_banner_form_widget_state()
                    st.rerun()
    else:
        page_label = BANNER_PAGES.get(st.session_state.layout_page_id, {}).get("name", st.session_state.layout_page_id)
        st.info(
            f"「{page_label}」에 등록된 배너가 없습니다.  \n"
            f"**➕ 배너 등록/편집** → Content & Link에서 URL **{max_for_layout}개** 입력 후 저장."
            if max_for_layout > 1 else
            f"「{page_label}」에 등록된 배너가 없습니다. **➕ 배너 등록/편집**으로 등록하세요."
        )

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
    
    if st.session_state.is_new_banner:
        st.success("📝 **배너 등록/편집** — Content & Link 탭에서 레이아웃 수만큼 URL 입력 후 **💾 저장**")
    
    if st.session_state.is_new_banner or st.session_state.selected_banner_data:
        # 탭 메뉴
        tab1, tab2, tab3 = st.tabs([
            "Basic & Schedule", "Content & Link", "Targeting"
        ])
        
        # 기본 데이터
        banner_data = st.session_state.selected_banner_data or {}
        is_new = st.session_state.is_new_banner
        
        # tab1에서 spot/page 결정 후 tab2·tab3·저장에서 공유
        form_layout = "single"
        form_max = 1
        banner_group: List[Dict[str, Any]] = []
        primary_banner: Dict[str, Any] = {}
        content_slots: List[Dict[str, Any]] = []
        
        with tab1:
            st.markdown("#### 기본 정보 및 일정")
            
            # 배너 위치 (신규일 때만 선택 가능, 좌측 선택 위치를 기본값으로)
            if is_new:
                spot_options = {f"{info['icon']} {info['name']}": spot_id 
                               for spot_id, info in BANNER_SPOTS.items()}
                spot_labels = list(spot_options.keys())
                default_spot_id = st.session_state.selected_spot_id
                default_spot_label = next(
                    (label for label, sid in spot_options.items() if sid == default_spot_id),
                    spot_labels[0],
                )
                default_spot_index = spot_labels.index(default_spot_label) if default_spot_label in spot_labels else 0
                selected_spot_name = st.selectbox(
                    "배너 위치",
                    spot_labels,
                    index=default_spot_index,
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
            current_page_id = banner_data.get("pageId", "index" if is_new else "all")
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

            form_layout = get_banner_slot_setting(selected_spot_id, selected_page_id).get("displayLayout", "single")
            form_max = BANNER_DISPLAY_LAYOUTS.get(form_layout, BANNER_DISPLAY_LAYOUTS["single"])["maxBanners"]
            banner_group = _get_banner_group(selected_spot_id, selected_page_id, form_max)
            primary_banner = banner_group[0] if banner_group else (banner_data if not is_new else {})
            default_title = _get_group_primary_title(primary_banner) if banner_group or not is_new else banner_data.get("title", "")
            
            # 배너 제목 (그룹 공통)
            banner_title = st.text_input(
                "배너 제목 (관리자용, 공통)",
                value=default_title,
                key="banner_title",
                placeholder="배너 세트 제목 (예: 메인 홈 프로모션)"
            )
            
            # 전시 기간
            col_date1, col_date2 = st.columns(2)
            start_dt = _parse_banner_datetime(primary_banner.get("displayStart") or banner_data.get("displayStart"))
            end_dt = _parse_banner_datetime(
                primary_banner.get("displayEnd") or banner_data.get("displayEnd"),
                default=datetime.now() + timedelta(days=30),
            )
            
            with col_date1:
                display_start = st.date_input(
                    "전시 시작일",
                    value=start_dt.date(),
                    key="banner_start_date"
                )
                display_start_time = st.time_input(
                    "시작 시간",
                    value=start_dt.time(),
                    key="banner_start_time"
                )
            
            with col_date2:
                display_end = st.date_input(
                    "전시 종료일",
                    value=end_dt.date(),
                    key="banner_end_date"
                )
                display_end_time = st.time_input(
                    "종료 시간",
                    value=end_dt.time(),
                    key="banner_end_time"
                )
            
            # 상태 및 우선순위
            col_status1, col_status2 = st.columns(2)
            
            with col_status1:
                _status_default = primary_banner.get("status") or banner_data.get("status", "live")
                banner_status = st.selectbox(
                    "상태 (공통)",
                    list(BANNER_STATUS.keys()),
                    index=list(BANNER_STATUS.keys()).index(_status_default) if _status_default in BANNER_STATUS else 0,
                    format_func=lambda x: BANNER_STATUS[x],
                    key="banner_status"
                )
            
            with col_status2:
                if form_max > 1:
                    st.metric("레이아웃 슬롯", f"{form_max}개", help="Content & Link 탭에서 URL 입력")
                    st.caption("우선순위 1→N 자동 · 일정·타겟팅 **공통**")
                    banner_priority = 1
                else:
                    suggested_priority = _suggest_next_priority(
                        get_banners_by_spot(selected_spot_id), selected_page_id
                    )
                    default_priority = (
                        suggested_priority if is_new
                        else int(banner_data.get("priority", suggested_priority))
                    )
                    banner_priority = st.number_input(
                        "우선순위",
                        min_value=1,
                        value=default_priority,
                        key="banner_priority",
                        help="숫자가 작을수록 먼저 표시됩니다.",
                    )
        
        with tab2:
            st.markdown("#### 콘텐츠 및 링크")
            st.caption(
                f"레이아웃 **{form_max}칸** — 아래 **{form_max}개** URL 영역에 이미지·링크를 입력하세요. "
                f"(Basic & Schedule · Targeting 설정은 **공통** 적용)"
            )
            _render_layout_size_guide(form_layout, selected_spot_id.startswith("mobile_"))

            content_slots = []
            for slot_idx in range(1, form_max + 1):
                slot_banner = next(
                    (b for b in banner_group if int(b.get("priority", 0)) == slot_idx),
                    None,
                )
                if slot_banner is None and slot_idx <= len(banner_group):
                    slot_banner = banner_group[slot_idx - 1]
                slot_data = slot_banner or {}

                pos_label = {1: "좌1", 2: "좌2", 3: "좌3", 4: "좌4"}.get(slot_idx, str(slot_idx))
                st.markdown(f"##### 🖼️ 배너 #{slot_idx} ({pos_label})")
                col_web, col_mob = st.columns(2)
                with col_web:
                    st.markdown("**웹**")
                    web_image_url = st.text_input(
                        "웹 이미지 URL",
                        value=slot_data.get("webImageUrl", ""),
                        key=f"web_image_url_{slot_idx}",
                        placeholder="https://firebasestorage.googleapis.com/.../banner.jpg?alt=media&token=...",
                    )
                    web_link_url = st.text_input(
                        "웹 링크 URL",
                        value=slot_data.get("webLinkUrl", ""),
                        key=f"web_link_url_{slot_idx}",
                        placeholder="https://example.com/page",
                    )
                    _render_image_preview(web_image_url, max_width=320, caption=f"#{slot_idx} 웹 미리보기")
                with col_mob:
                    st.markdown("**모바일**")
                    mobile_image_url = st.text_input(
                        "모바일 이미지 URL",
                        value=slot_data.get("mobileImageUrl", ""),
                        key=f"mobile_image_url_{slot_idx}",
                        placeholder="https://firebasestorage.googleapis.com/.../banner-mobile.jpg?alt=media&token=...",
                    )
                    mobile_link_url = st.text_input(
                        "모바일 링크 URL",
                        value=slot_data.get("mobileLinkUrl", ""),
                        key=f"mobile_link_url_{slot_idx}",
                        placeholder="https://example.com/page",
                    )
                    _render_image_preview(mobile_image_url, max_width=240, caption=f"#{slot_idx} 모바일 미리보기")

                content_slots.append({
                    "id": slot_data.get("id"),
                    "priority": slot_idx,
                    "webImageUrl": web_image_url,
                    "webLinkUrl": web_link_url,
                    "mobileImageUrl": mobile_image_url,
                    "mobileLinkUrl": mobile_link_url,
                })
                if slot_idx < form_max:
                    st.markdown("---")
        
        with tab3:
            st.markdown("#### 타겟팅 설정")
            
            # 타겟 언어 선택 (요구: 언어 옵션 추가, 프론트에서 언어 우선 적용)
            st.markdown("##### 타겟 언어")
            st.caption("배너를 표시할 언어를 선택하세요. (선택하지 않으면 모든 언어에 표시. 언어/국가 둘 다 설정된 경우 프론트에서는 **언어를 우선** 적용합니다.)")
            selected_langs = primary_banner.get("targetLanguages") or banner_data.get("targetLanguages", [])
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
            
            selected_countries = primary_banner.get("targetCountries") or banner_data.get("targetCountries", [])
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
            delete_label = "🗑️ 세트 삭제" if form_max > 1 and banner_group else "🗑️ 삭제"
            if st.button(delete_label, use_container_width=True, disabled=is_new and not banner_group):
                if st.session_state.get('confirm_delete_banner', False):
                    if form_max > 1 and banner_group:
                        deleted = _delete_banner_group(selected_spot_id, selected_page_id)
                        if deleted:
                            st.success(f"배너 {deleted}개가 삭제되었습니다!")
                    elif st.session_state.selected_banner_id:
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
            if st.button("❌ 취소", use_container_width=True, key="banner_cancel_btn"):
                st.session_state.is_new_banner = False
                st.session_state.selected_banner_id = None
                st.session_state.selected_banner_data = None
                st.session_state.confirm_delete_banner = False
                _clear_banner_form_widget_state()
                st.rerun()
        
        with col_btn3:
            if st.button("💾 저장", use_container_width=True, type="primary"):
                display_start_dt = datetime.combine(display_start, display_start_time)
                display_end_dt = datetime.combine(display_end, display_end_time)

                common_data = {
                    "title": banner_title,
                    "displayStart": display_start_dt.isoformat(),
                    "displayEnd": display_end_dt.isoformat(),
                    "status": banner_status,
                    "targetLanguages": all_selected_languages,
                    "targetCountries": all_selected_countries if all_selected_countries else None,
                }

                if form_max > 1:
                    ok, saved_ids = _save_banner_group(
                        selected_spot_id,
                        selected_page_id,
                        form_max,
                        common_data,
                        content_slots,
                    )
                    if ok:
                        st.success(f"✅ 배너 {len(saved_ids)}개가 저장되었습니다!")
                        st.session_state.is_new_banner = False
                        if saved_ids:
                            st.session_state.selected_banner_id = saved_ids[0]
                            st.session_state.selected_banner_data = get_banner_by_id(saved_ids[0])
                        st.rerun()
                    else:
                        st.warning("저장할 이미지 URL이 없습니다. Content & Link 탭에서 URL을 입력하세요.")
                else:
                    slot = content_slots[0] if content_slots else {}
                    banner_data_to_save = {
                        **common_data,
                        "spotId": selected_spot_id,
                        "pageId": selected_page_id,
                        "priority": banner_priority,
                        "webImageUrl": slot.get("webImageUrl", ""),
                        "webLinkUrl": slot.get("webLinkUrl", ""),
                        "mobileImageUrl": slot.get("mobileImageUrl", ""),
                        "mobileLinkUrl": slot.get("mobileLinkUrl", ""),
                    }
                    if is_new:
                        import uuid
                        new_banner_id = f"banner_{uuid.uuid4().hex[:8]}"
                        if create_banner(new_banner_id, banner_data_to_save):
                            st.success("✅ 배너가 생성되었습니다!")
                            st.session_state.is_new_banner = False
                            st.session_state.selected_banner_id = new_banner_id
                            st.session_state.selected_banner_data = get_banner_by_id(new_banner_id)
                            st.rerun()
                    else:
                        if update_banner(st.session_state.selected_banner_id, banner_data_to_save):
                            st.success("✅ 배너가 업데이트되었습니다!")
                            st.session_state.selected_banner_data = get_banner_by_id(st.session_state.selected_banner_id)
                            st.rerun()
    else:
        st.info(
            "👆 **➕ 배너 등록/편집** 을 클릭하면 우측에 입력 폼이 나타납니다.  \n"
            "1줄 4개 레이아웃은 Content & Link 탭에서 **URL 4개**를 한 번에 입력·저장합니다."
        )

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
        get_all_banner_slot_settings.clear()
        get_banner_slot_setting.clear()
        st.success("캐시가 초기화되었습니다!")
        st.rerun()

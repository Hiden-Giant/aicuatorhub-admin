"""
카테고리 관련 함수
"""
import streamlit as st
from firebase_admin import firestore
from typing import List, Dict, Optional, Any
from .firebase import get_db
from .config import COLLECTIONS, CATEGORIES
from .tools import get_all_tools
from .utils import convert_firestore_data


@st.cache_data(ttl=300)  # 5분 캐시
def get_category_statistics() -> Dict[str, int]:
    """
    카테고리별 도구 수 통계
    
    Returns:
        Dict: 카테고리 ID별 도구 수
    """
    all_tools = get_all_tools()
    
    stats = {}
    for category_id in CATEGORIES.keys():
        if category_id == "전체":
            stats["all"] = len(all_tools)
        else:
            stats[CATEGORIES[category_id]["id"]] = 0
    
    # primaryCategory 기준으로 집계
    for tool in all_tools:
        primary_cat = tool.get("primaryCategory", "")
        if primary_cat:
            # 카테고리 이름을 ID로 매핑
            for cat_name, cat_info in CATEGORIES.items():
                if cat_name == primary_cat or cat_info["id"] in str(primary_cat).lower():
                    stats[cat_info["id"]] = stats.get(cat_info["id"], 0) + 1
                    break
    
    # categories 배열 기준으로도 집계
    for tool in all_tools:
        categories_list = tool.get("categories", [])
        if categories_list:
            for cat in categories_list:
                cat_lower = str(cat).lower()
                for cat_name, cat_info in CATEGORIES.items():
                    if cat_info["id"] in cat_lower or cat_name.lower() in cat_lower:
                        stats[cat_info["id"]] = stats.get(cat_info["id"], 0) + 1
    
    return stats


def get_tools_by_category(category_id: str) -> List[Dict[str, Any]]:
    """
    특정 카테고리의 도구 목록 조회
    
    Args:
        category_id: 카테고리 ID
        
    Returns:
        List[Dict]: 도구 리스트
    """
    all_tools = get_all_tools()
    
    if category_id == "all":
        return all_tools
    
    # 카테고리 이름 찾기
    category_name = None
    for cat_name, cat_info in CATEGORIES.items():
        if cat_info["id"] == category_id:
            category_name = cat_name
            break
    
    if not category_name:
        return []
    
    filtered_tools = []
    for tool in all_tools:
        primary_cat = tool.get("primaryCategory", "")
        categories_list = tool.get("categories", [])
        
        # primaryCategory로 매칭
        if primary_cat == category_name:
            filtered_tools.append(tool)
            continue
        
        # categories 배열로 매칭
        if categories_list:
            for cat in categories_list:
                if category_name in str(cat) or category_id in str(cat).lower():
                    filtered_tools.append(tool)
                    break
    
    return filtered_tools


def get_all_categories() -> List[Dict[str, Any]]:
    """
    모든 카테고리 정보 조회 (config 기반)
    
    Returns:
        List[Dict]: 카테고리 리스트
    """
    categories = []
    stats = get_category_statistics()
    
    for cat_name, cat_info in CATEGORIES.items():
        if cat_name == "전체":
            continue
        
        category_data = {
            "id": cat_info["id"],
            "name": cat_name,
            "nameKr": cat_name,
            "nameEn": cat_name,  # TODO: 영문명 추가 필요
            "icon": cat_info["icon"],
            "color": cat_info["color"],
            "toolCount": stats.get(cat_info["id"], 0),
            "order": list(CATEGORIES.keys()).index(cat_name)
        }
        categories.append(category_data)
    
    return categories


def update_category(category_id: str, data: Dict[str, Any]) -> bool:
    """
    카테고리 정보 업데이트 (Firebase categories 컬렉션에 저장)
    
    Args:
        category_id: 카테고리 ID
        data: 업데이트할 데이터
        
    Returns:
        bool: 성공 여부
    """
    db = get_db()
    if db is None:
        return False
    
    try:
        doc_ref = db.collection(COLLECTIONS["CATEGORIES"]).document(category_id)
        data["updatedAt"] = firestore.SERVER_TIMESTAMP
        doc_ref.set(data, merge=True)  # merge=True로 부분 업데이트
        # 캐시 무효화
        get_category_statistics.clear()
        return True
    except Exception as e:
        st.error(f"카테고리 업데이트 실패: {e}")
        return False

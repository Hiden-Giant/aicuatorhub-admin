"""
공통 유틸리티 함수
"""
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional


def normalize_id(name: str) -> str:
    """
    이름을 문서 ID로 변환
    
    Args:
        name: 변환할 이름
        
    Returns:
        str: 정규화된 ID
    """
    if not name:
        return ""
    name = str(name).lower()
    name = re.sub(r"[().·•]", "", name)
    name = re.sub(r"\s+", "-", name)
    name = re.sub(r"[^a-z0-9\-]", "", name)
    return name


def convert_firestore_data(data: Any) -> Any:
    """
    Firestore 데이터를 JSON 직렬화 가능한 형태로 변환
    
    Args:
        data: 변환할 데이터
        
    Returns:
        변환된 데이터
    """
    if isinstance(data, dict):
        converted = {}
        for key, value in data.items():
            converted[key] = convert_firestore_data(value)
        return converted
    elif isinstance(data, list):
        return [convert_firestore_data(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    elif hasattr(data, 'isoformat'):  # datetime 또는 DatetimeWithNanoseconds
        try:
            return data.isoformat()
        except:
            try:
                if hasattr(data, 'strftime'):
                    return data.strftime('%Y-%m-%d %H:%M:%S')
                return str(data)
            except:
                return str(data)
    elif hasattr(data, '__dict__'):
        # DocumentReference나 다른 Firestore 객체들을 문자열로 변환
        return str(data)
    else:
        return data


def format_value(value: Any) -> str:
    """
    값을 표시 가능한 문자열로 변환
    
    Args:
        value: 변환할 값
        
    Returns:
        str: 포맷된 문자열
    """
    if value is None:
        return ""
    if isinstance(value, list):
        if len(value) == 0:
            return ""
        return ", ".join(str(v) for v in value)
    if isinstance(value, dict):
        if len(value) == 0:
            return ""
        return json.dumps(value, ensure_ascii=False, default=str)
    if isinstance(value, bool):
        return "✅" if value else "❌"
    return str(value)


def validate_url(url: str) -> bool:
    """
    URL 유효성 검사
    
    Args:
        url: 검사할 URL
        
    Returns:
        bool: 유효한 URL인지 여부
    """
    if not url:
        return False
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None


def format_datetime(dt: Any, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    날짜/시간 포맷팅
    
    Args:
        dt: 날짜/시간 객체
        format_str: 포맷 문자열
        
    Returns:
        str: 포맷된 날짜/시간 문자열
    """
    if dt is None:
        return ""
    if isinstance(dt, str):
        return dt
    if hasattr(dt, 'strftime'):
        try:
            return dt.strftime(format_str)
        except:
            return str(dt)
    return str(dt)

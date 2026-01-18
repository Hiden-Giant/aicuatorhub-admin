"""
Firebase 초기화 및 DB 클라이언트 관리
"""
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
from .config import FIREBASE_SERVICE_ACCOUNT_KEY_PATH, FIREBASE_SERVICE_ACCOUNT_KEY_JSON


@st.cache_resource
def init_firebase():
    """
    Firebase 초기화 (캐시됨)
    
    Returns:
        firestore.Client: Firestore 클라이언트 또는 None
    """
    try:
        if not firebase_admin._apps:
            # Streamlit Cloud Secrets에서 우선 읽기 (st.secrets)
            # 그 다음 환경 변수 (os.getenv), 마지막으로 파일 경로
            service_key_json = None
            service_key_path = None
            
            # 1순위: Streamlit Secrets (Streamlit Cloud)
            try:
                if "FIREBASE_SERVICE_ACCOUNT_KEY_JSON" in st.secrets:
                    service_key_json = st.secrets["FIREBASE_SERVICE_ACCOUNT_KEY_JSON"]
            except (AttributeError, KeyError, TypeError):
                # st.secrets가 없거나 접근할 수 없는 경우 (로컬 개발 환경)
                pass
            
            # 2순위: 환경 변수
            if not service_key_json:
                service_key_json = FIREBASE_SERVICE_ACCOUNT_KEY_JSON
            
            # 3순위: 파일 경로
            if not service_key_json:
                service_key_path = FIREBASE_SERVICE_ACCOUNT_KEY_PATH
            
            # JSON 문자열로 제공된 경우
            if service_key_json:
                try:
                    # 문자열인 경우 JSON 파싱, 이미 dict인 경우 그대로 사용
                    if isinstance(service_key_json, str):
                        key_dict = json.loads(service_key_json)
                    else:
                        key_dict = service_key_json
                    cred = credentials.Certificate(key_dict)
                except (json.JSONDecodeError, TypeError) as e:
                    st.error(f"FIREBASE_SERVICE_ACCOUNT_KEY_JSON이 유효한 JSON 형식이 아닙니다: {e}")
                    return None
            # 파일 경로로 제공된 경우
            elif service_key_path and os.path.exists(service_key_path):
                cred = credentials.Certificate(service_key_path)
            else:
                raise FileNotFoundError(
                    f"Firebase 서비스 계정 키를 찾을 수 없습니다. "
                    f"Streamlit Secrets, 환경 변수 FIREBASE_SERVICE_ACCOUNT_KEY_JSON 또는 "
                    f"FIREBASE_SERVICE_ACCOUNT_KEY_PATH를 설정하거나 "
                    f"{service_key_path} 파일이 존재해야 합니다."
                )
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"Firebase 초기화 실패: {e}")
        return None


def get_db():
    """
    Firestore DB 클라이언트 반환
    
    Returns:
        firestore.Client: Firestore 클라이언트 또는 None
    """
    return init_firebase()

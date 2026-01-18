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
            # 환경 변수에서 Firebase 서비스 계정 키 경로 또는 JSON 문자열 가져오기
            service_key_path = FIREBASE_SERVICE_ACCOUNT_KEY_PATH
            service_key_json = FIREBASE_SERVICE_ACCOUNT_KEY_JSON
            
            if service_key_json:
                # 환경 변수에서 JSON 문자열로 제공된 경우
                try:
                    key_dict = json.loads(service_key_json)
                    cred = credentials.Certificate(key_dict)
                except json.JSONDecodeError:
                    st.error("FIREBASE_SERVICE_ACCOUNT_KEY_JSON이 유효한 JSON 형식이 아닙니다.")
                    return None
            elif os.path.exists(service_key_path):
                # 파일 경로로 제공된 경우
                cred = credentials.Certificate(service_key_path)
            else:
                raise FileNotFoundError(
                    f"Firebase 서비스 계정 키를 찾을 수 없습니다. "
                    f"환경 변수 FIREBASE_SERVICE_ACCOUNT_KEY_JSON 또는 "
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

#!/usr/bin/env python3
"""
평점 4.5 이상 도구 개수 확인 스크립트
실행: python scripts/count_rating_tools.py (프로젝트 루트에서)
"""
import os
import sys
import json

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    import firebase_admin
    from firebase_admin import credentials, firestore
    
    # Firebase 초기화 (admin/config와 동일한 방식)
    if not firebase_admin._apps:
        key_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_JSON")
        key_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH", "serviceAccountKey.json")
        
        if key_json:
            cred = credentials.Certificate(json.loads(key_json))
        elif os.path.exists(key_path):
            cred = credentials.Certificate(key_path)
        else:
            print("오류: Firebase 키가 필요합니다. FIREBASE_SERVICE_ACCOUNT_KEY_JSON 또는 FIREBASE_SERVICE_ACCOUNT_KEY_PATH 설정")
            sys.exit(1)
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    tools_ref = db.collection("ai-tools")
    
    # rating >= 4.5 쿼리 (loadRatedAITools와 동일)
    query = tools_ref.where("rating", ">=", 4.5).order_by("rating", direction=firestore.Query.DESCENDING)
    docs = list(query.stream())
    
    print(f"평점 4.5 이상 도구: {len(docs)}개")
    print(f"→ limit(12)로 조회하면 12개만 반환됨 (충분함)")

if __name__ == "__main__":
    main()

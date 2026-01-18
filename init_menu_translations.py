"""
어드민 메뉴 번역 초기 데이터 생성 스크립트
다국어 정책에 따라 메뉴 번역 데이터를 Firebase에 추가합니다.
"""
import sys
import os
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from admin.firebase import get_db
from admin.menu import get_menu_items
from admin.config import COLLECTIONS, ORIGIN_LANGUAGES, REQUIRED_LANGUAGES, TRANSLATION_TYPES
from firebase_admin import firestore

# 메뉴 번역 데이터 (한국어와 영어)
MENU_TRANSLATIONS = {
    "dashboard": {
        "ko": "대시보드",
        "en": "Dashboard"
    },
    "ai_tools": {
        "ko": "AI 도구 관리",
        "en": "AI Tools Management"
    },
    "users": {
        "ko": "사용자 관리",
        "en": "User Management"
    },
    "recipes": {
        "ko": "AI 레시피 관리",
        "en": "AI Recipe Management"
    },
    "translations": {
        "ko": "다국어 관리",
        "en": "Translation Management"
    },
    "categories": {
        "ko": "카테고리 관리",
        "en": "Category Management"
    },
    "applications": {
        "ko": "등록 신청 관리",
        "en": "Registration Management"
    },
    "paid_services": {
        "ko": "유료 서비스 관리",
        "en": "Paid Service Management"
    },
    "settings": {
        "ko": "설정",
        "en": "Settings"
    }
}


def create_menu_translations():
    """
    메뉴 번역 데이터를 Firebase에 생성
    """
    db = get_db()
    if db is None:
        print("❌ Firebase 연결에 실패했습니다.")
        return False
    
    translations_ref = db.collection(COLLECTIONS["TRANSLATIONS"])
    created_count = 0
    updated_count = 0
    
    print("📝 메뉴 번역 데이터 생성 시작...")
    print("-" * 50)
    
    for page, translations in MENU_TRANSLATIONS.items():
        trans_id = f"menu.{page}"
        doc_ref = translations_ref.document(trans_id)
        doc = doc_ref.get()
        
        # 번역 데이터 구성
        trans_data = {
            "type": TRANSLATION_TYPES["menu"],
            "ko": translations.get("ko", ""),
            "en": translations.get("en", ""),
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
            "createdBy": "admin",
            "updatedBy": "admin"
        }
        
        if doc.exists:
            # 기존 문서 업데이트
            doc_ref.update({
                "ko": trans_data["ko"],
                "en": trans_data["en"],
                "updatedAt": firestore.SERVER_TIMESTAMP,
                "updatedBy": "admin"
            })
            updated_count += 1
            print(f"✅ 업데이트: {trans_id} - {translations['ko']} / {translations['en']}")
        else:
            # 새 문서 생성
            doc_ref.set(trans_data)
            created_count += 1
            print(f"➕ 생성: {trans_id} - {translations['ko']} / {translations['en']}")
    
    print("-" * 50)
    print(f"📊 완료: {created_count}개 생성, {updated_count}개 업데이트")
    return True


if __name__ == "__main__":
    print("=" * 50)
    print("어드민 메뉴 번역 데이터 초기화")
    print("=" * 50)
    print()
    
    if create_menu_translations():
        print()
        print("✅ 메뉴 번역 데이터가 성공적으로 생성되었습니다!")
        print()
        print("다음 단계:")
        print("1. 어드민 패널에서 '다국어 관리' 메뉴로 이동")
        print("2. '메뉴' 타입의 번역 데이터를 확인")
        print("3. 필요시 다른 언어로 번역 추가")
    else:
        print()
        print("❌ 메뉴 번역 데이터 생성에 실패했습니다.")

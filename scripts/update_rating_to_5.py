#!/usr/bin/env python3
"""
지정된 AI 도구들의 평점을 5점으로 일괄 업데이트하는 스크립트

실행:
  python scripts/update_rating_to_5.py              # 매칭 확인 후 y 입력 시 업데이트
  python scripts/update_rating_to_5.py --dry-run    # 실제 업데이트 없이 매칭된 도구만 확인
  python scripts/update_rating_to_5.py --yes       # 확인 없이 바로 업데이트

요구사항: Firebase 서비스 계정 키 (FIREBASE_SERVICE_ACCOUNT_KEY_JSON 또는 serviceAccountKey.json)
"""
import os
import sys
import json

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 평점 5점으로 변경할 도구 목록 (이름 기반 부분 매칭)
TOOL_NAME_PATTERNS = [
    # 1. 종합 지능형 비서 및 텍스트
    "ChatGPT", "Claude", "Gemini", "Bing Chat", "DeepSeek",
    # 2. 업무 생산성 및 문서 관리
    "Notion AI", "ClickUp", "ChatPDF", "AskYourPDF", "Explainpaper",
    "Coda AI", "Akiflow",
    # 3. 디자인 및 이미지/비디오 생성
    "Canva", "Adobe Firefly", "DALL-E", "Midjourney", "ClipDrop",
    "D-ID", "Designs.ai", "Artbreeder",
    # 4. 개발 및 데이터 분석
    "Cursor", "GitHub Copilot", "Akkio", "Databricks", "Alteryx",
    # 5. 오디오, 번역 및 마케팅
    "ElevenLabs", "DeepL", "Descript", "Writesonic", "Anyword",
]

# 포함에서 제외할 패턴 (예: ChatGPT는 포함하되 WebChatGPT는 제외)
EXCLUDE_PATTERNS = ["WebChatGPT"]


def main():
    dry_run = "--dry-run" in sys.argv
    auto_yes = "--yes" in sys.argv

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

    # 모든 도구 조회
    docs = list(tools_ref.stream())
    print(f"전체 도구 수: {len(docs)}개")

    # 매칭된 도구 찾기
    matched = []
    for doc in docs:
        data = doc.to_dict()
        name = (data.get("name") or "").strip()
        if not name:
            continue
        name_lower = name.lower()
        # 제외 패턴 확인
        if any(exc.lower() in name_lower for exc in EXCLUDE_PATTERNS):
            continue
        for pattern in TOOL_NAME_PATTERNS:
            if pattern.lower() in name_lower:
                matched.append((doc.id, name, data.get("rating")))
                break

    if not matched:
        print("매칭되는 도구가 없습니다. TOOL_NAME_PATTERNS를 확인하세요.")
        return

    print(f"\n평점 5점으로 업데이트할 도구: {len(matched)}개")
    for tool_id, name, old_rating in matched:
        print(f"  - {name} (id: {tool_id}) rating: {old_rating} → 5.0")

    if dry_run:
        print("\n[--dry-run] 실제 업데이트는 수행하지 않았습니다.")
        return

    # 확인 후 업데이트 (--yes 옵션 시 생략)
    if not auto_yes:
        confirm = input("\n위 도구들의 평점을 5점으로 업데이트할까요? (y/N): ").strip().lower()
        if confirm != "y":
            print("취소되었습니다.")
            return

    updated = 0
    for doc in docs:
        data = doc.to_dict()
        name = (data.get("name") or "").strip()
        if not name:
            continue
        name_lower = name.lower()
        if any(exc.lower() in name_lower for exc in EXCLUDE_PATTERNS):
            continue
        for pattern in TOOL_NAME_PATTERNS:
            if pattern.lower() in name_lower:
                try:
                    tools_ref.document(doc.id).update({
                        "rating": 5.0,
                        "updatedAt": firestore.SERVER_TIMESTAMP
                    })
                    updated += 1
                    print(f"  [OK] {name} (id: {doc.id})")
                except Exception as e:
                    print(f"  [FAIL] {name} (id: {doc.id}): {e}")
                break

    print(f"\n완료: {updated}개 도구 평점이 5점으로 업데이트되었습니다.")


if __name__ == "__main__":
    main()

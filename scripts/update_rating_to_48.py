#!/usr/bin/env python3
"""
추가 추천 AI 제품 20선의 평점을 4.8점으로 일괄 업데이트하는 스크립트

실행:
  python scripts/update_rating_to_48.py              # 매칭 확인 후 y 입력 시 업데이트
  python scripts/update_rating_to_48.py --dry-run   # 실제 업데이트 없이 매칭된 도구만 확인
  python scripts/update_rating_to_48.py --yes      # 확인 없이 바로 업데이트

요구사항: Firebase 서비스 계정 키 (FIREBASE_SERVICE_ACCOUNT_KEY_JSON 또는 serviceAccountKey.json)
"""
import os
import sys
import json

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TARGET_RATING = 4.8

# 평점 4.8점으로 변경할 도구 목록 (추가 추천 AI 제품 20선)
TOOL_NAME_PATTERNS = [
    # 1. 업무 자동화 및 에이전트
    "Zapier Central", "Make", "n8n", "Fireflies", "Motion",
    # 2. 디자인 및 비주얼 창작
    "Leonardo.ai", "Uizard", "Luma Dream Machine", "HeyGen", "Gamma App",
    # 3. 연구, 학습 및 검색
    "Perplexity", "NotebookLM", "Consensus", "Glean",
    # 4. 특수 목적 전문 도구
    "Replit Agent", "Tabnine", "Jasper", "Suno AI", "Wix ADI", "Grammarly",
]

# 포함에서 제외할 패턴 (Make가 ClipMaker, Remaker 등에 매칭되지 않도록)
EXCLUDE_PATTERNS = ["ClipMaker", "Remaker"]


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
        if any(exc.lower() in name_lower for exc in EXCLUDE_PATTERNS):
            continue
        for pattern in TOOL_NAME_PATTERNS:
            if pattern.lower() in name_lower:
                matched.append((doc.id, name, data.get("rating")))
                break

    if not matched:
        print("매칭되는 도구가 없습니다. TOOL_NAME_PATTERNS를 확인하세요.")
        return

    print(f"\n평점 {TARGET_RATING}점으로 업데이트할 도구: {len(matched)}개")
    for tool_id, name, old_rating in matched:
        print(f"  - {name} (id: {tool_id}) rating: {old_rating} -> {TARGET_RATING}")

    if dry_run:
        print("\n[--dry-run] 실제 업데이트는 수행하지 않았습니다.")
        return

    # 확인 후 업데이트 (--yes 옵션 시 생략)
    if not auto_yes:
        confirm = input(f"\n위 도구들의 평점을 {TARGET_RATING}점으로 업데이트할까요? (y/N): ").strip().lower()
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
                        "rating": TARGET_RATING,
                        "updatedAt": firestore.SERVER_TIMESTAMP
                    })
                    updated += 1
                    print(f"  [OK] {name} (id: {doc.id})")
                except Exception as e:
                    print(f"  [FAIL] {name} (id: {doc.id}): {e}")
                break

    print(f"\n완료: {updated}개 도구 평점이 {TARGET_RATING}점으로 업데이트되었습니다.")


if __name__ == "__main__":
    main()

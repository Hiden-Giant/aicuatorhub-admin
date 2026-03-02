#!/usr/bin/env python3
"""
지정된 AI 도구를 Firestore에서 완전히 삭제합니다.
- ai-tools 컬렉션의 해당 도구 문서 삭제
- tool_translations 컬렉션에서 해당 도구의 모든 언어 번역 문서 삭제

실행:
  python scripts/delete_tool.py coqui-tts              # 확인 후 삭제
  python scripts/delete_tool.py coqui-tts --dry-run   # 삭제 대상만 확인
  python scripts/delete_tool.py coqui-tts --yes        # 확인 없이 삭제

요구사항: Firebase 서비스 계정 키 (FIREBASE_SERVICE_ACCOUNT_KEY_JSON 또는 serviceAccountKey.json)
"""
import os
import sys
import json

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from admin.config import COLLECTIONS


def main():
    if len(sys.argv) < 2:
        print("사용법: python scripts/delete_tool.py <tool_id> [--dry-run] [--yes]")
        print("예: python scripts/delete_tool.py coqui-tts --yes")
        sys.exit(1)

    tool_id = sys.argv[1].strip()
    if not tool_id:
        print("오류: tool_id를 입력하세요.")
        sys.exit(1)

    dry_run = "--dry-run" in sys.argv
    auto_yes = "--yes" in sys.argv

    import firebase_admin
    from firebase_admin import credentials, firestore

    # Firebase 초기화 (admin/config와 동일한 방식)
    if not firebase_admin._apps:
        key_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_JSON")
        key_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH", "serviceAccountKey.json")
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if not key_path.startswith("/") and not os.path.isabs(key_path):
            key_path = os.path.join(project_root, key_path)

        if key_json:
            cred = credentials.Certificate(json.loads(key_json))
        elif os.path.exists(key_path):
            cred = credentials.Certificate(key_path)
        else:
            print("오류: Firebase 키가 필요합니다. FIREBASE_SERVICE_ACCOUNT_KEY_JSON 또는 serviceAccountKey.json")
            sys.exit(1)
        firebase_admin.initialize_app(cred)

    db = firestore.client()
    tools_ref = db.collection(COLLECTIONS["AI_TOOLS"])
    trans_ref = db.collection(COLLECTIONS["TOOL_TRANSLATIONS"])

    # 1) ai-tools 문서 존재 여부 확인
    tool_doc = tools_ref.document(tool_id).get()
    if not tool_doc.exists:
        print(f"ai-tools에 '{tool_id}' 문서가 없습니다. (이미 삭제되었거나 존재하지 않음)")
    else:
        data = tool_doc.to_dict()
        name = (data.get("name") or tool_id)
        print(f"[ai-tools] 삭제 대상: doc id = {tool_id}, name = {name}")

    # 2) tool_translations에서 해당 도구의 모든 언어 문서 조회
    trans_docs = list(trans_ref.where("toolId", "==", tool_id).stream())
    print(f"[tool_translations] 삭제 대상: {len(trans_docs)}개 (언어별 문서)")
    for d in trans_docs:
        data = d.to_dict()
        lang = data.get("lang", "?")
        print(f"  - {d.id} (lang: {lang})")

    if dry_run:
        print("\n[--dry-run] 실제 삭제는 수행하지 않았습니다.")
        return

    if not tool_doc.exists and not trans_docs:
        print("삭제할 데이터가 없습니다.")
        return

    if not auto_yes:
        confirm = input("\n위 데이터를 모두 삭제할까요? (y/N): ").strip().lower()
        if confirm != "y":
            print("취소되었습니다.")
            return

    deleted_tool = 0
    deleted_trans = 0

    # ai-tools 문서 삭제
    if tool_doc.exists:
        try:
            tools_ref.document(tool_id).delete()
            deleted_tool = 1
            print(f"  [OK] ai-tools/{tool_id} 삭제됨")
        except Exception as e:
            print(f"  [FAIL] ai-tools/{tool_id}: {e}")

    # tool_translations 문서 일괄 삭제
    for d in trans_docs:
        try:
            trans_ref.document(d.id).delete()
            deleted_trans += 1
            print(f"  [OK] tool_translations/{d.id} 삭제됨")
        except Exception as e:
            print(f"  [FAIL] tool_translations/{d.id}: {e}")

    print(f"\n완료: ai-tools {deleted_tool}건, tool_translations {deleted_trans}건 삭제되었습니다.")


if __name__ == "__main__":
    main()

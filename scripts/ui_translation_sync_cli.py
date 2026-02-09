"""
A6: UI 텍스트 ↔ 프론트 JSON 동기화 CLI

배포/빌드 단계에서 실행 가능:
  python scripts/ui_translation_sync_cli.py export   # translations → public/lang/*.json
  python scripts/ui_translation_sync_cli.py import   # public/lang/*.json → translations

프로젝트 루트(ai_curatorhub_admin)에서 실행하거나, PYTHONPATH에 루트를 추가하세요.
"""
import sys
import os

# 프로젝트 루트를 path에 추가
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Firebase 초기화를 위해 get_db 호출 (export/import 시 사용)
from admin.firebase import get_db
from admin.ui_translation_sync import export_ui_translations_to_json, import_ui_translations_from_json


def main():
    if len(sys.argv) < 2:
        print("사용법: python scripts/ui_translation_sync_cli.py export | import")
        sys.exit(1)
    cmd = sys.argv[1].strip().lower()
    if cmd == "export":
        get_db()  # Firebase 연결
        ok, msg = export_ui_translations_to_json()
        print(msg)
        sys.exit(0 if ok else 1)
    elif cmd == "import":
        get_db()
        ok, msg = import_ui_translations_from_json()
        print(msg)
        sys.exit(0 if ok else 1)
    else:
        print("사용법: python scripts/ui_translation_sync_cli.py export | import")
        sys.exit(1)


if __name__ == "__main__":
    main()

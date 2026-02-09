"""
A6: UI 텍스트 번역 ↔ 프론트 public/lang/*.json 동기화

- export_ui_translations_to_json: Firestore translations 컬렉션 → public/lang/{lang}.json
- import_ui_translations_from_json: public/lang/{lang}.json → Firestore translations 컬렉션
"""
import os
import json
from typing import Tuple

from .config import SUPPORTED_LANGUAGES, FRONT_LANG_JSON_DIR
from .translations import get_all_translations, get_translation_by_id, update_translation, create_translation


def export_ui_translations_to_json(front_lang_dir: str = None) -> Tuple[bool, str]:
    """
    translations 컬렉션 데이터를 프론트 public/lang/{lang}.json 형식으로 내보냅니다.
    각 문서: id=키, ko/en/ja/...=값 → lang별로 { "키": "값" } JSON 파일 생성.

    Args:
        front_lang_dir: 대상 디렉터리 (기본: config.FRONT_LANG_JSON_DIR)

    Returns:
        (성공 여부, 메시지)
    """
    target_dir = front_lang_dir or FRONT_LANG_JSON_DIR
    if not os.path.isdir(target_dir):
        return False, f"대상 디렉터리가 없습니다: {target_dir}"

    try:
        all_trans = get_all_translations()
        # lang별로 { key: value } 구성 (문서 id가 키, 문서[lang]이 값)
        by_lang = {lang: {} for lang in SUPPORTED_LANGUAGES.keys()}
        all_keys = set()
        for doc in all_trans:
            key = doc.get("id") or doc.get("key")
            if not key:
                continue
            all_keys.add(key)
            for lang in SUPPORTED_LANGUAGES.keys():
                val = doc.get(lang)
                if val is not None:
                    by_lang[lang][key] = val
                else:
                    by_lang[lang][key] = ""

        # 모든 lang 파일에 동일 키 집합 유지 (빈 문자열로 채움)
        for lang in SUPPORTED_LANGUAGES.keys():
            for k in all_keys:
                if k not in by_lang[lang]:
                    by_lang[lang][k] = ""

        written = []
        for lang, key_values in by_lang.items():
            path = os.path.join(target_dir, f"{lang}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(key_values, f, ensure_ascii=False, indent=2)
            written.append(f"{lang}.json")

        return True, f"내보내기 완료: {len(written)}개 파일 ({', '.join(written)})"
    except Exception as e:
        return False, f"내보내기 실패: {e}"


def import_ui_translations_from_json(front_lang_dir: str = None) -> Tuple[bool, str]:
    """
    프론트 public/lang/{lang}.json 파일을 읽어 Firestore translations 컬렉션에 반영합니다.
    각 (키, 값)에 대해: 문서가 있으면 해당 lang 필드만 업데이트, 없으면 새 문서 생성.

    Args:
        front_lang_dir: 소스 디렉터리 (기본: config.FRONT_LANG_JSON_DIR)

    Returns:
        (성공 여부, 메시지)
    """
    target_dir = front_lang_dir or FRONT_LANG_JSON_DIR
    if not os.path.isdir(target_dir):
        return False, f"소스 디렉터리가 없습니다: {target_dir}"

    try:
        updated = 0
        created = 0
        for lang in SUPPORTED_LANGUAGES.keys():
            path = os.path.join(target_dir, f"{lang}.json")
            if not os.path.isfile(path):
                continue
            with open(path, "r", encoding="utf-8") as f:
                key_values = json.load(f)
            if not isinstance(key_values, dict):
                continue
            for key, value in key_values.items():
                if not key or not isinstance(key, str):
                    continue
                existing = get_translation_by_id(key)
                if existing:
                    update_translation(key, {lang: value})
                    updated += 1
                else:
                    create_translation(key, {lang: value, "type": "other"})
                    created += 1

        return True, f"가져오기 완료: 업데이트 {updated}건, 신규 {created}건"
    except Exception as e:
        return False, f"가져오기 실패: {e}"

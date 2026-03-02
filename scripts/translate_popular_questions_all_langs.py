#!/usr/bin/env python3
"""
Popular Questions를 지원 언어별로 영어(en) 기준 번역하여 Firestore에 저장.

- 소스: seed_popular_questions.POPULAR_QUESTIONS (promptEn)
- 대상: ko, en 제외한 모든 SUPPORTED_LANGS (ja, zh, ru, es, pt, ar, vi, id, fr, hi, ms, it, de, tr)
- API: MyMemory (무료, rate limit 고려)

실행:
  python scripts/translate_popular_questions_all_langs.py --dry-run
  python scripts/translate_popular_questions_all_langs.py --yes

사전: seed_popular_questions.py 로 popular_questions + en 번역이 이미 올라와 있어야 함.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
from typing import Dict, Any, List

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 시드 데이터 사용 (단일 소스)
from seed_popular_questions import POPULAR_QUESTIONS

# 프론트/어드민과 동일한 지원 언어 (ko=원본, en=시드에 있음 → 번역 대상 제외)
SUPPORTED_LANGS = [
    "ko", "en", "ja", "zh", "ru", "es", "pt", "ar", "vi", "id", "fr", "hi", "ms", "it", "de", "tr"
]
# en 제외한 번역 대상 (ko는 popular_questions.promptKo 사용)
TARGET_LANGS = [l for l in SUPPORTED_LANGS if l not in ("ko", "en")]

# MyMemory API 언어 코드 (일부만 다름)
MYMEMORY_LANG = {
    "ja": "ja", "zh": "zh-CN", "ru": "ru", "es": "es", "pt": "pt", "ar": "ar",
    "vi": "vi", "id": "id", "fr": "fr", "hi": "hi", "ms": "ms", "it": "it", "de": "de", "tr": "tr",
}
CHUNK_SIZE = 450
RATE_DELAY_SEC = 0.35


def init_firebase():
    import firebase_admin
    from firebase_admin import credentials, firestore

    if not firebase_admin._apps:
        key_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_JSON")
        key_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH", "serviceAccountKey.json")

        if key_json:
            cred = credentials.Certificate(json.loads(key_json))
        elif os.path.exists(key_path):
            cred = credentials.Certificate(key_path)
        else:
            print("오류: Firebase 키가 필요합니다.")
            sys.exit(1)

        firebase_admin.initialize_app(cred)

    return firestore.client(), firestore


def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """MyMemory API로 텍스트 번역. 실패 시 원문 반환."""
    if not text or not text.strip():
        return text
    src = MYMEMORY_LANG.get(source_lang, source_lang)
    tgt = MYMEMORY_LANG.get(target_lang, target_lang)
    if src == tgt:
        return text

    # 긴 문장은 잘라서 요청 (MyMemory 제한 고려)
    text = text.strip()
    if len(text) > CHUNK_SIZE:
        parts = [text[i : i + CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
        results = []
        for part in parts:
            results.append(translate_text(part, source_lang, target_lang))
            time.sleep(RATE_DELAY_SEC)
        return "".join(results)

    try:
        url = "https://api.mymemory.translated.net/get?q=" + urllib.parse.quote(text) + "&langpair=en|" + tgt
        req = urllib.request.Request(url, headers={"User-Agent": "PopularQuestionsTranslate/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        if data.get("responseStatus") == 200 and data.get("responseData", {}).get("translatedText"):
            return data["responseData"]["translatedText"].strip()
    except Exception as e:
        print(f"  [WARN] 번역 실패 ({target_lang}): {e}")
    return text


def upsert_translation(db, firestore, question_id: str, lang: str, prompt_text: str, *, dry_run: bool):
    doc_id = f"{question_id}_{lang}"
    ref = db.collection("popular_question_translations").document(doc_id)

    doc = {
        "questionId": question_id,
        "lang": lang,
        "fields": {
            "prompt": {
                "text": prompt_text,
                "status": "reviewed",
                "updatedAt": firestore.SERVER_TIMESTAMP,
                "editedBy": "translate_popular_questions_all_langs.py",
            }
        },
        "docStatus": "reviewed",
        "updatedAt": firestore.SERVER_TIMESTAMP,
        "editedBy": "translate_popular_questions_all_langs.py",
    }

    if dry_run:
        print(f"  [DRY] {doc_id} <- {prompt_text[:50]}...")
        return

    snap = ref.get()
    if not snap.exists:
        doc["createdAt"] = firestore.SERVER_TIMESTAMP
    ref.set(doc, merge=True)


def main():
    dry_run = "--dry-run" in sys.argv
    auto_yes = "--yes" in sys.argv

    if not auto_yes and not dry_run:
        confirm = input(
            "모든 Popular Questions를 지원 언어로 번역해 DB에 저장할까요? (MyMemory API 사용) [y/N]: "
        ).strip().lower()
        if confirm != "y":
            print("취소되었습니다.")
            return

    db, firestore = init_firebase()

    total = len(POPULAR_QUESTIONS) * len(TARGET_LANGS)
    print(f"질문 수: {len(POPULAR_QUESTIONS)}, 번역 대상 언어: {len(TARGET_LANGS)} (en 제외)")
    print(f"총 번역 수: {total} (rate limit {RATE_DELAY_SEC}s 간격)")
    if dry_run:
        print("[--dry-run] 실제 API 호출 및 저장 없이 진행합니다.\n")

    done = 0
    for item in POPULAR_QUESTIONS:
        qid = item["id"]
        source_text = item.get("promptEn") or ""
        if not source_text.strip():
            print(f"[SKIP] {qid}: promptEn 없음")
            continue

        for lang in TARGET_LANGS:
            done += 1
            print(f"[{done}/{total}] {qid} -> {lang} ... ", end="", flush=True)
            if dry_run:
                translated = source_text  # skip API in dry-run
            else:
                translated = translate_text(source_text, "en", lang)
                time.sleep(RATE_DELAY_SEC)
            # Windows 콘솔 인코딩 대응
            try:
                print(translated[:50] + "..." if len(translated) > 50 else translated)
            except UnicodeEncodeError:
                print(f"<{len(translated)} chars>")
            upsert_translation(db, firestore, qid, lang, translated, dry_run=dry_run)

    if dry_run:
        print("\n[--dry-run] 실제 API/저장은 수행하지 않았습니다.")
    else:
        print("\n✅ 번역 및 저장 완료.")


if __name__ == "__main__":
    main()

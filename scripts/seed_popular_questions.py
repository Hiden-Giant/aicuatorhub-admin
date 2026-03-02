#!/usr/bin/env python3
"""
Firestore에 Albatross '인기 있는 질문들' 초기 데이터(ko 원본 + en 번역)를 업로드하는 Seed 스크립트.

단일 소스: POPULAR_QUESTIONS 리스트가 질문 목록·한국어·영어의 기준입니다.
- 질문 추가/수정 시 이 리스트만 수정한 뒤 본 시드 실행 → 이어서 translate_popular_questions_all_langs.py 실행.

컬렉션:
 - popular_questions (원본: ko, 메타데이터)
 - popular_question_translations (번역: 문서 ID = {questionId}_{lang})

실행:
  python scripts/seed_popular_questions.py --dry-run
  python scripts/seed_popular_questions.py --yes

전체 언어 번역: 시드 실행 후 scripts/translate_popular_questions_all_langs.py 실행.

요구사항:
 - FIREBASE_SERVICE_ACCOUNT_KEY_JSON 또는 FIREBASE_SERVICE_ACCOUNT_KEY_PATH (또는 serviceAccountKey.json)
"""

import os
import sys
import json
from typing import Dict, Any, List

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


POPULAR_QUESTIONS: List[Dict[str, Any]] = [
    # VIDEO (3)
    {
        "id": "pq_video_001",
        "categoryId": "video",
        "order": 10,
        "promptKo": "인스타그램 릴스 자동 편집 도구",
        "promptEn": "Instagram Reels auto-editing tool",
        "tags": ["reels", "shorts", "auto-edit", "video"],
    },
    {
        "id": "pq_video_002",
        "categoryId": "video",
        "order": 20,
        "promptKo": "쇼츠/릴스 자동 자막 생성 + 배경 소음 제거 도구",
        "promptEn": "Auto-generate captions and remove background noise for Shorts/Reels",
        "tags": ["captions", "noise", "shorts", "reels", "video"],
    },
    {
        "id": "pq_video_003",
        "categoryId": "video",
        "order": 30,
        "promptKo": "유튜브 브이로그 자동 하이라이트/전환 편집 도구",
        "promptEn": "Auto-highlight and add transitions for YouTube vlogs",
        "tags": ["youtube", "vlog", "highlights", "transitions", "video"],
    },
    # PRODUCTIVITY (3)
    {
        "id": "pq_productivity_001",
        "categoryId": "productivity",
        "order": 10,
        "promptKo": "회의록을 자동으로 요약하는 AI",
        "promptEn": "AI that automatically summarizes meeting notes",
        "tags": ["meeting", "minutes", "summary", "productivity"],
    },
    {
        "id": "pq_productivity_002",
        "categoryId": "productivity",
        "order": 20,
        "promptKo": "긴 PDF 요약 + 액션 아이템/핵심 키워드 추출 도구",
        "promptEn": "Summarize a long PDF and extract action items / keywords",
        "tags": ["pdf", "summary", "action-items", "keywords", "productivity"],
    },
    {
        "id": "pq_productivity_003",
        "categoryId": "productivity",
        "order": 30,
        "promptKo": "회의 녹음 → 회의록 + Notion/Slack 업무 정리 도구",
        "promptEn": "Turn meeting recordings into minutes and tasks (Notion/Slack)",
        "tags": ["notion", "slack", "tasks", "meeting", "productivity"],
    },
    # DESIGN (3)
    {
        "id": "pq_design_001",
        "categoryId": "design",
        "order": 10,
        "promptKo": "무료로 사용 가능한 로고 디자인",
        "promptEn": "Free logo design tool",
        "tags": ["logo", "free", "design"],
    },
    {
        "id": "pq_design_002",
        "categoryId": "design",
        "order": 20,
        "promptKo": "브랜드 가이드라인 + SNS 템플릿 자동 생성 도구",
        "promptEn": "Generate brand guidelines and reusable social media templates",
        "tags": ["brand", "guidelines", "templates", "social", "design"],
    },
    {
        "id": "pq_design_003",
        "categoryId": "design",
        "order": 30,
        "promptKo": "제품 목업 이미지 생성(배경/조명 스타일 통일) 도구",
        "promptEn": "Create product mockups with consistent background/lighting style",
        "tags": ["mockup", "product", "lighting", "background", "design"],
    },
    # ANALYTICS (3)
    {
        "id": "pq_analytics_001",
        "categoryId": "analytics",
        "order": 10,
        "promptKo": "엑셀 데이터 시각화 자동화 툴",
        "promptEn": "Excel data visualization automation tool",
        "tags": ["excel", "charts", "dashboard", "analytics"],
    },
    {
        "id": "pq_analytics_002",
        "categoryId": "analytics",
        "order": 20,
        "promptKo": "CSV 매출 데이터 분석 + KPI 대시보드 자동 생성",
        "promptEn": "Analyze sales CSV and auto-build a KPI dashboard",
        "tags": ["csv", "sales", "kpi", "dashboard", "analytics"],
    },
    {
        "id": "pq_analytics_003",
        "categoryId": "analytics",
        "order": 30,
        "promptKo": "주간 리포트 자동 생성(이상치 감지 + 인사이트 요약)",
        "promptEn": "Generate a weekly report with anomaly detection and insights",
        "tags": ["weekly", "report", "anomaly", "insights", "analytics"],
    },
]


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
            print("오류: Firebase 키가 필요합니다. FIREBASE_SERVICE_ACCOUNT_KEY_JSON 또는 FIREBASE_SERVICE_ACCOUNT_KEY_PATH 설정")
            sys.exit(1)

        firebase_admin.initialize_app(cred)

    return firestore.client(), firestore


def upsert_question(db, firestore, item: Dict[str, Any], *, dry_run: bool):
    qid = item["id"]
    qref = db.collection("popular_questions").document(qid)
    existing = qref.get()

    base_doc: Dict[str, Any] = {
        "categoryId": item["categoryId"],
        "promptKo": item["promptKo"],
        "tags": item.get("tags", []),
        "status": "active",
        "order": int(item.get("order", 0)),
        "usageCount": 0,
        "updatedAt": firestore.SERVER_TIMESTAMP,
        "updatedBy": "seed_popular_questions.py",
    }
    if not existing.exists:
        base_doc["createdAt"] = firestore.SERVER_TIMESTAMP

    trans_id = f"{qid}_en"
    tref = db.collection("popular_question_translations").document(trans_id)
    t_existing = tref.get()
    trans_doc: Dict[str, Any] = {
        "questionId": qid,
        "lang": "en",
        "fields": {
            "prompt": {
                "text": item["promptEn"],
                "status": "reviewed",
                "updatedAt": firestore.SERVER_TIMESTAMP,
                "editedBy": "seed_popular_questions.py",
            }
        },
        "docStatus": "reviewed",
        "updatedAt": firestore.SERVER_TIMESTAMP,
        "editedBy": "seed_popular_questions.py",
    }
    if not t_existing.exists:
        trans_doc["createdAt"] = firestore.SERVER_TIMESTAMP

    if dry_run:
        print(f"[DRY] popular_questions/{qid}  (category={item['categoryId']}, order={item.get('order')})")
        print(f"[DRY] popular_question_translations/{trans_id} (lang=en)")
        return

    qref.set(base_doc, merge=True)
    tref.set(trans_doc, merge=True)


def main():
    dry_run = "--dry-run" in sys.argv
    auto_yes = "--yes" in sys.argv

    if not auto_yes and not dry_run:
        confirm = input("popular_questions / popular_question_translations에 Seed 데이터를 업로드할까요? (y/N): ").strip().lower()
        if confirm != "y":
            print("취소되었습니다.")
            return

    db, firestore = init_firebase()

    print(f"Seed 대상 질문 수: {len(POPULAR_QUESTIONS)}")
    for item in POPULAR_QUESTIONS:
        upsert_question(db, firestore, item, dry_run=dry_run)

    if dry_run:
        print("\n[--dry-run] 실제 업로드는 수행하지 않았습니다.")
    else:
        print("\n✅ Seed 업로드 완료")


if __name__ == "__main__":
    main()


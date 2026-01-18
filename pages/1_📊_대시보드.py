"""
대시보드 페이지 - 통계 및 시각화
"""
import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from admin.firebase import get_db
from admin.components import render_page_header, render_language_selector
from admin.config import COLLECTIONS, CATEGORIES
from admin.tools import get_all_tools
from admin.users import get_all_users
from admin.public_recipes import get_all_public_recipes as get_all_recipes
from admin.categories import get_category_statistics
from admin.utils import format_datetime

# 페이지 설정
st.set_page_config(
    page_title="대시보드 - Aicuatorhub Admin",
    page_icon="📊",
    layout="wide"
)

# Firebase 연결
db = get_db()
if db is None:
    st.error("⚠️ Firebase 연결에 실패했습니다.")
    st.stop()

# 언어 선택 UI (사이드바에 표시)
render_language_selector()

# 페이지 헤더
render_page_header("📊 대시보드", "전체 시스템 통계 및 현황을 확인할 수 있습니다.")

# 데이터 로드
with st.spinner("데이터를 불러오는 중..."):
    all_tools = get_all_tools()
    all_users = get_all_users()
    all_recipes = get_all_recipes()
    category_stats = get_category_statistics()

# 주요 지표 카드
st.markdown("### 📈 주요 지표")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    tools_count = len(all_tools)
    st.metric("전체 AI 도구", f"{tools_count:,}개")

with col2:
    users_count = len(all_users)
    st.metric("전체 사용자", f"{users_count:,}명")

with col3:
    recipes_count = len(all_recipes)
    st.metric("전체 레시피", f"{recipes_count:,}개")

with col4:
    active_tools = sum(1 for tool in all_tools if tool.get("status") == "active")
    st.metric("활성 도구", f"{active_tools:,}개")

with col5:
    verified_tools = sum(1 for tool in all_tools if tool.get("verified", False))
    st.metric("검증된 도구", f"{verified_tools:,}개")

st.markdown("---")

# 첫 번째 행: 카테고리별 분포 및 상태별 분포
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.markdown("#### 📦 카테고리별 도구 분포")
    
    # 카테고리별 도구 수 데이터 준비
    category_data = []
    for cat_name, cat_info in CATEGORIES.items():
        if cat_name == "전체":
            continue
        count = category_stats.get(cat_info["id"], 0)
        if count > 0:  # 도구가 있는 카테고리만 표시
            category_data.append({
                "카테고리": cat_name,
                "도구 수": count,
                "아이콘": cat_info["icon"]
            })
    
    if category_data:
        category_df = pd.DataFrame(category_data)
        category_df = category_df.sort_values("도구 수", ascending=False)
        
        # 파이 차트
        fig_pie = px.pie(
            category_df,
            values="도구 수",
            names="카테고리",
            title="카테고리별 도구 분포",
            hole=0.4
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # 막대 그래프
        fig_bar = px.bar(
            category_df,
            x="카테고리",
            y="도구 수",
            title="카테고리별 도구 수",
            color="도구 수",
            color_continuous_scale="Blues"
        )
        fig_bar.update_xaxes(tickangle=-45)
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("카테고리별 데이터가 없습니다.")

with col_chart2:
    st.markdown("#### 📊 도구 상태별 분포")
    
    # 상태별 도구 수
    status_counts = {}
    for tool in all_tools:
        status = tool.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    if status_counts:
        status_df = pd.DataFrame([
            {"상태": k, "개수": v} for k, v in status_counts.items()
        ])
        
        # 파이 차트
        fig_status = px.pie(
            status_df,
            values="개수",
            names="상태",
            title="도구 상태별 분포",
            hole=0.4
        )
        fig_status.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_status, use_container_width=True)
        
        # 검증/추천 도구 통계
        st.markdown("#### ✅ 검증/추천 도구")
        col_verify1, col_verify2 = st.columns(2)
        with col_verify1:
            verified_count = sum(1 for tool in all_tools if tool.get("verified", False))
            st.metric("검증된 도구", f"{verified_count}개", f"{verified_count/tools_count*100:.1f}%")
        with col_verify2:
            featured_count = sum(1 for tool in all_tools if tool.get("featured", False))
            st.metric("추천 도구", f"{featured_count}개", f"{featured_count/tools_count*100:.1f}%")
    else:
        st.info("상태별 데이터가 없습니다.")

st.markdown("---")

# 두 번째 행: 인기 도구 및 최근 활동
col_chart3, col_chart4 = st.columns(2)

with col_chart3:
    st.markdown("#### ⭐ 인기 도구 (상위 10개)")
    
    # 평점 및 리뷰 수 기준으로 정렬
    popular_tools = []
    for tool in all_tools:
        rating = float(tool.get("rating", 0))
        review_count = int(tool.get("reviewCount", 0))
        if rating > 0 or review_count > 0:
            # 인기 점수 계산 (평점 * 리뷰 수)
            popularity_score = rating * review_count if review_count > 0 else rating * 10
            popular_tools.append({
                "이름": tool.get("name", "-"),
                "평점": rating,
                "리뷰 수": review_count,
                "인기 점수": popularity_score
            })
    
    if popular_tools:
        popular_df = pd.DataFrame(popular_tools)
        popular_df = popular_df.sort_values("인기 점수", ascending=False).head(10)
        
        # 막대 그래프
        fig_popular = px.bar(
            popular_df,
            x="이름",
            y="인기 점수",
            title="인기 도구 Top 10",
            color="평점",
            color_continuous_scale="YlOrRd",
            text="평점"
        )
        fig_popular.update_xaxes(tickangle=-45)
        fig_popular.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        st.plotly_chart(fig_popular, use_container_width=True)
        
        # 테이블
        st.dataframe(
            popular_df[["이름", "평점", "리뷰 수", "인기 점수"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("인기 도구 데이터가 없습니다.")

with col_chart4:
    st.markdown("#### 📅 최근 활동")
    
    # 최근 등록된 도구 (최근 7일)
    recent_tools = []
    for tool in all_tools:
        created_at = tool.get("createdAt")
        if created_at:
            try:
                if isinstance(created_at, str):
                    created_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                else:
                    created_date = created_at
                
                if isinstance(created_date, datetime):
                    days_ago = (datetime.now() - created_date.replace(tzinfo=None)).days
                    if days_ago <= 7:
                        recent_tools.append({
                            "이름": tool.get("name", "-"),
                            "등록일": created_date.strftime("%Y-%m-%d") if isinstance(created_date, datetime) else str(created_date),
                            "일수": days_ago
                        })
            except:
                pass
    
    if recent_tools:
        recent_df = pd.DataFrame(recent_tools)
        recent_df = recent_df.sort_values("일수", ascending=True).head(10)
        st.dataframe(recent_df[["이름", "등록일"]], use_container_width=True, hide_index=True)
        st.caption(f"최근 7일간 {len(recent_tools)}개의 도구가 등록되었습니다.")
    else:
        st.info("최근 등록된 도구가 없습니다.")
    
    st.markdown("---")
    
    # 최근 가입한 사용자 (최근 7일)
    st.markdown("#### 👥 최근 가입 사용자")
    recent_users = []
    for user in all_users:
        registered_date = user.get("registeredDate")
        if registered_date:
            try:
                if isinstance(registered_date, str):
                    reg_date = datetime.fromisoformat(registered_date.replace("Z", "+00:00"))
                else:
                    reg_date = registered_date
                
                if isinstance(reg_date, datetime):
                    days_ago = (datetime.now() - reg_date.replace(tzinfo=None)).days
                    if days_ago <= 7:
                        recent_users.append({
                            "이메일": user.get("email", "-"),
                            "가입일": reg_date.strftime("%Y-%m-%d") if isinstance(reg_date, datetime) else str(reg_date),
                            "일수": days_ago
                        })
            except:
                pass
    
    if recent_users:
        recent_users_df = pd.DataFrame(recent_users)
        recent_users_df = recent_users_df.sort_values("일수", ascending=True).head(10)
        st.dataframe(recent_users_df[["이메일", "가입일"]], use_container_width=True, hide_index=True)
        st.caption(f"최근 7일간 {len(recent_users)}명의 사용자가 가입했습니다.")
    else:
        st.info("최근 가입한 사용자가 없습니다.")

st.markdown("---")

# 세 번째 행: 레시피 통계 및 사용자 통계
col_chart5, col_chart6 = st.columns(2)

with col_chart5:
    st.markdown("#### 📝 레시피 상태별 분포")
    
    if all_recipes:
        recipe_status_counts = {}
        for recipe in all_recipes:
            status = recipe.get("status", "pending")
            recipe_status_counts[status] = recipe_status_counts.get(status, 0) + 1
        
        if recipe_status_counts:
            recipe_status_df = pd.DataFrame([
                {"상태": k, "개수": v} for k, v in recipe_status_counts.items()
            ])
            
            # 막대 그래프
            fig_recipe = px.bar(
                recipe_status_df,
                x="상태",
                y="개수",
                title="레시피 상태별 분포",
                color="개수",
                color_continuous_scale="Greens"
            )
            st.plotly_chart(fig_recipe, use_container_width=True)
            
            # 상태별 상세 정보
            for status, count in recipe_status_counts.items():
                status_name = {
                    "pending": "⏳ 대기",
                    "approved": "✅ 승인",
                    "rejected": "❌ 거부",
                    "draft": "📝 초안"
                }.get(status, status)
                st.write(f"**{status_name}**: {count}개")
        else:
            st.info("레시피 상태 데이터가 없습니다.")
    else:
        st.info("레시피 데이터가 없습니다.")

with col_chart6:
    st.markdown("#### 👥 사용자 통계")
    
    if all_users:
        # 회원 타입별 분포
        member_type_counts = {}
        for user in all_users:
            member_type = user.get("memberType", "unknown")
            member_type_counts[member_type] = member_type_counts.get(member_type, 0) + 1
        
        if member_type_counts:
            member_type_df = pd.DataFrame([
                {"회원 타입": k, "개수": v} for k, v in member_type_counts.items()
            ])
            
            # 파이 차트
            fig_member = px.pie(
                member_type_df,
                values="개수",
                names="회원 타입",
                title="회원 타입별 분포",
                hole=0.4
            )
            fig_member.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_member, use_container_width=True)
        
        # 국가별 분포 (상위 5개)
        country_counts = {}
        for user in all_users:
            country = user.get("country", "unknown")
            country_counts[country] = country_counts.get(country, 0) + 1
        
        if country_counts:
            st.markdown("#### 🌍 국가별 분포 (상위 5개)")
            sorted_countries = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            country_data = [{"국가": k, "사용자 수": v} for k, v in sorted_countries]
            country_df = pd.DataFrame(country_data)
            
            fig_country = px.bar(
                country_df,
                x="국가",
                y="사용자 수",
                title="국가별 사용자 수",
                color="사용자 수",
                color_continuous_scale="Purples"
            )
            st.plotly_chart(fig_country, use_container_width=True)
    else:
        st.info("사용자 데이터가 없습니다.")

st.markdown("---")

# 네 번째 행: 종합 통계 테이블
st.markdown("### 📋 종합 통계")

col_table1, col_table2 = st.columns(2)

with col_table1:
    st.markdown("#### 카테고리별 상세 통계")
    
    category_detail_data = []
    for cat_name, cat_info in CATEGORIES.items():
        if cat_name == "전체":
            continue
        count = category_stats.get(cat_info["id"], 0)
        category_detail_data.append({
            "카테고리": cat_name,
            "아이콘": cat_info["icon"],
            "도구 수": count,
            "비율": f"{count/tools_count*100:.1f}%" if tools_count > 0 else "0%"
        })
    
    if category_detail_data:
        category_detail_df = pd.DataFrame(category_detail_data)
        category_detail_df = category_detail_df.sort_values("도구 수", ascending=False)
        st.dataframe(category_detail_df, use_container_width=True, hide_index=True)

with col_table2:
    st.markdown("#### 평점별 도구 분포")
    
    rating_distribution = {}
    for tool in all_tools:
        rating = float(tool.get("rating", 0))
        if rating > 0:
            rating_range = f"{int(rating)}-{int(rating)+1}"
            rating_distribution[rating_range] = rating_distribution.get(rating_range, 0) + 1
    
    if rating_distribution:
        rating_df = pd.DataFrame([
            {"평점 범위": k, "도구 수": v} for k, v in rating_distribution.items()
        ])
        rating_df = rating_df.sort_values("평점 범위")
        
        fig_rating = px.bar(
            rating_df,
            x="평점 범위",
            y="도구 수",
            title="평점별 도구 분포",
            color="도구 수",
            color_continuous_scale="Reds"
        )
        st.plotly_chart(fig_rating, use_container_width=True)
    else:
        st.info("평점 데이터가 없습니다.")

# 사이드바
with st.sidebar:
    st.markdown("### 📊 빠른 통계")
    
    st.metric("전체 AI 도구", f"{tools_count:,}개")
    st.metric("전체 사용자", f"{users_count:,}명")
    st.metric("전체 레시피", f"{recipes_count:,}개")
    
    st.markdown("---")
    
    st.markdown("### 🔄 새로고침")
    if st.button("🔄 데이터 새로고침", use_container_width=True):
        get_all_tools.clear()
        get_all_users.clear()
        get_all_recipes.clear()
        get_category_statistics.clear()
        st.success("데이터가 새로고침되었습니다!")
        st.rerun()
    
    st.markdown("---")
    st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

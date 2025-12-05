# app/routers/insight.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db import SessionLocal
from openai import OpenAI
import os

router = APIRouter(prefix="/insight", tags=["Insight"])

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 🧠 전략 문구 생성 API
@router.get("/strategy")
def get_strategy(dong: str, db: Session = Depends(get_db)):

    if not dong:
        raise HTTPException(status_code=400, detail="dong parameter is required")

    dong = dong.strip().replace(" ", "")

    # 1) 유동인구 최고 시간 조회
    flow_query = text("""
        SELECT DATE_FORMAT(measure_time, '%H') AS hour,
               SUM(visitor) AS v
        FROM flow_population
        WHERE dong_name LIKE CONCAT('%', :dong, '%')
        GROUP BY hour
        ORDER BY v DESC
        LIMIT 1;
    """)

    peak = db.execute(flow_query, {"dong": dong}).fetchone()

    peak_hour = f"{peak.hour}시" if peak else "정보 없음"

    # 2) 주요 소비층 계산 (30대 비중 가장 높은 기준)
    sales_query = text("""
        SELECT 
            age_10_amount, age_20_amount, age_30_amount,
            age_40_amount, age_50_amount, age_60_amount
        FROM age_sales
        WHERE dong_name LIKE CONCAT('%', :dong, '%')
        ORDER BY year_quarter DESC
        LIMIT 1;
    """)

    sales = db.execute(sales_query, {"dong": dong}).fetchone()

    if sales:
        amounts = [
            sales.age_10_amount,
            sales.age_20_amount,
            sales.age_30_amount,
            sales.age_40_amount,
            sales.age_50_amount,
            sales.age_60_amount,
        ]
        max_age_idx = amounts.index(max(amounts))
        age_label = ["10대", "20대", "30대", "40대", "50대", "60대 이상"][max_age_idx]
    else:
        age_label = "정보 없음"

    # 3) 업종 1위 조회
    shop_query = text("""
        SELECT mid_category_name, COUNT(*) AS c
        FROM shop_info
        WHERE dong_name LIKE CONCAT('%', :dong, '%')
        GROUP BY mid_category_name
        ORDER BY c DESC
        LIMIT 1;
    """)

    shop = db.execute(shop_query, {"dong": dong}).fetchone()

    top_shop = shop.mid_category_name if shop else "정보 없음"

    # --------------------------
    # LLM 사용해 인사이트 생성
    # --------------------------

    prompt = f"""
    다음 상권 정보를 기반으로 소상공인을 위한 전략 문구를 2~3줄로 자연스럽게 작성해줘.

    🏙 지역: {dong}
    👥 방문 가장 많은 시간: {peak_hour}
    🎯 주요 소비층: {age_label}
    🏆 경쟁 치열 업종: {top_shop}
ㄹㄹㄹㄹㄹㄹㄹㄹㄹㄹㄹㄹㄹㄹㄹㄹㄹㄹㄹㄹㄹㄹㄹㄹㄹㄹㄹㄹㄹㄹ
    조건:
    - 너무 길지 않게
    - 분석가 스타일
    - 실질적인 전략 한 가지 포함
    """

    llm_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    insight_text = llm_response.choices[0].message.content

    return {
        "dong": dong,
        "peak_hour": peak_hour,
        "main_age": age_label,
        "top_category": top_shop,
        "insight": insight_text
    }

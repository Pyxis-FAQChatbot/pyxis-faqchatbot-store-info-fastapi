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
당신은 '소상공인 상권 전략 분석 전문가'입니다.
다음 상권 데이터를 기반으로 **현실적인 실행전략을 2~3줄**로 작성해주세요.

📍 지역: {dong}
⏰ 방문 피크 시간대: {peak_hour}
👥 주요 소비층: {age_label}
🏆 경쟁 치열 업종: {top_shop}

[전략 작성 조건]
- 신사동 소비자 특성과 연령대별 소비 성향을 반영해 구체적으로 작성
- 실제 소상공인이 바로 적용할 수 있는 실행전략 2~3개 제안
- "고객 맞춤형 서비스" 같은 추상적인 표현 금지 → 반드시 구체적 행동 지침으로 작성
- 예시 성공 사례 1개 포함 (단순 참고용이 아닌, 전략의 신뢰도를 높이는 방식으로)
- 퇴근시간대·연령별 소비패턴·업종 경쟁도 등을 활용해서 실제 매장에서 바로 적용 가능한 팁 중심으로 작성
- **마크다운을 활용하여 구조화해.** 특히, **핵심 내용은 마크다운 목록(\`*\`)을 사용해 분리**하고, 중요한 키워드는 **볼드(\`**\`) 처리**해.
- **각 항목의 시작 부분에 내용과 관련된 적절한 이모지(Emoji)를 붙여서** 문장이 너무 길어지지 않도록 개행하여("\n") 가독성을 최우선으로 해. 
[예시 전략 스타일]
- “신사동 50대 고객은 18시 퇴근 직후 빠르게 해결할 수 있는 서비스를 선호하는 경향이 있어,
  ‘20분 컷 간단 시술 + 예약 고객 음료 제공’ 옵션을 만들면 전환율을 높일 수 있습니다.”
- “유사 지역(예: 압구정)에서는 ‘퇴근길 즉시 상담·즉시 시술’ 프로모션을 운영했을 때 단골 전환이 22% 증가한 사례가 있습니다.”

위 조건을 적용하여 전략 문구를 생성하세요.
"""

    llm_response = client.chat.completions.create(
        model="gpt-4o",
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

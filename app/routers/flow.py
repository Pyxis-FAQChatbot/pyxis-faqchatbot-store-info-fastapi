# app/routers/flow.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db import SessionLocal

router = APIRouter(prefix="/flow", tags=["Flow Population"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 📌 특정 동의 시간대별 유동인구 조회
@router.get("/hourly")
def get_flow_hourly(dong: str, db: Session = Depends(get_db)):

    if not dong:
        raise HTTPException(status_code=400, detail="dong parameter is required")

    dong = dong.strip().replace(" ", "") # 공백 제거

    query = text("""
        SELECT 
            DATE_FORMAT(measure_time, '%Y-%m-%d %H:00') AS hour,
            SUM(visitor) AS visitor_sum
        FROM flow_population
        WHERE dong_name LIKE CONCAT('%', :dong, '%')
        GROUP BY hour
        ORDER BY hour
    """)

    result = db.execute(query, {"dong": dong}).fetchall()
    return {
        "dong": dong,
        "data": [dict(row._mapping) for row in result]
    }

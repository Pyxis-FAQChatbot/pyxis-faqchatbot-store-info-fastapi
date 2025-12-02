# app/routers/shop.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db import SessionLocal

router = APIRouter(prefix="/shop", tags=["Shop Info"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 📌 업종 수 조회 API
@router.get("/count")
def get_shop_count(dong: str, db: Session = Depends(get_db)):
    
    if not dong:
        raise HTTPException(status_code=400, detail="dong parameter is required")

    dong = dong.strip().replace(" ", "") # 공백 제거

    query = text("""
        SELECT mid_category_name AS category,
               COUNT(*) AS cnt
        FROM shop_info
        WHERE dong_name = :dong
        GROUP BY category
        ORDER BY cnt DESC
    """)

    rows = db.execute(query, {"dong": dong}).fetchall()
    return {"dong": dong, "data": [dict(row._mapping) for row in rows]}

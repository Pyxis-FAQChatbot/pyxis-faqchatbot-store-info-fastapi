# app/routers/sales.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db import SessionLocal

router = APIRouter(prefix="/sales", tags=["Age Sales"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 📌 1) 연령대별 매출
@router.get("/age")
def get_age_sales(dong: str, db: Session = Depends(get_db)):

    if not dong:
        raise HTTPException(status_code=400, detail="dong parameter is required")

    query = text("""
        SELECT year_quarter,
               age_10_amount,
               age_20_amount,
               age_30_amount,
               age_40_amount,
               age_50_amount,
               age_60_amount
        FROM age_sales
        WHERE dong_name = :dong
        ORDER BY year_quarter
    """)

    result = db.execute(query, {"dong": dong}).fetchall()
    return {"dong": dong, "data": [dict(row._mapping) for row in result]}


# 📌 2) 연령대별 매출 건수
@router.get("/age-count")
def get_age_sales_count(dong: str, db: Session = Depends(get_db)):

    if not dong:
        raise HTTPException(status_code=400, detail="dong parameter is required")

    query = text("""
        SELECT year_quarter,
               age_10_count,
               age_20_count,
               age_30_count,
               age_40_count,
               age_50_count,
               age_60_count
        FROM age_sales
        WHERE dong_name = :dong
        ORDER BY year_quarter
    """)

    result = db.execute(query, {"dong": dong}).fetchall()
    return {"dong": dong, "data": [dict(row._mapping) for row in result]}

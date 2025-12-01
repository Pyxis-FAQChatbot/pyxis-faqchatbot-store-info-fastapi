from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

DATABASE_URL = (
    f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}?charset=utf8mb4"
)

# 서버 환경을 위한 연결 풀 설정 추가
# pool_size: 풀에 유지할 연결 개수 (동시 워커 수에 맞춰 설정)
# max_overflow: pool_size 초과 시 허용할 임시 연결 개수
# pool_timeout: 풀에서 연결을 대기하는 최대 시간 (초)
# pool_recycle: 연결이 재활용되기 전 유지될 최대 시간 (초)
engine = create_engine(
    DATABASE_URL, 
    pool_recycle=3600,
    pool_size=10,         # 동시 워커 수에 따라 조정
    max_overflow=20,      # 최대 허용 초과 연결 수
    pool_timeout=30       # 연결 대기 시간
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
"""SQLAlchemy sync engine + session.

동기 DB 접근 전략:
- FastAPI 엔드포인트는 def (not async def)로 정의
- FastAPI가 자동으로 threadpool에서 실행하여 이벤트 루프 블로킹 방지
- 1 worker MVP에 충분. Async 전환은 추후 stretch goal.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from edupulse.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=3,
    max_overflow=2,
    pool_recycle=1800,
)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass

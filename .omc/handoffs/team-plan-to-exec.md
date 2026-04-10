## Handoff: team-plan → team-exec
- **Decided**: 통합 패키지 구조(edupulse/), Sync DB(psycopg2+def), Alembic 마이그레이션, constants.py 단일 소스, threading.Lock 모델 서빙
- **Rejected**: Async DB(복잡도 과다), Flat 구조(CWD 의존), pytest-asyncio(불필요), Base.metadata.create_all(스키마 변경 불가)
- **Risks**: psutil이 requirements에 없음(health 라우터에서 대체 필요), DB 없이 테스트 가능해야 함
- **Files**: `.omc/plans/edupulse-backend.md` (v2, 전체 계획)
- **Remaining**: Phase 2(데이터+모델), Phase 3(API 라우터), Phase 4(Docker)는 Phase 1 검증 후 진행

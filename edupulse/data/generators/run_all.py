"""전체 합성 데이터 일괄 생성.

Usage:
    python -m edupulse.data.generators.run_all
"""
import os
from pathlib import Path

import pandas as pd

from edupulse.data.generators.enrollment_generator import generate_enrollment_history
from edupulse.data.generators.external_generator import (
    generate_job_postings,
    generate_search_trends,
)

# 출력 경로
INTERNAL_DIR = Path("edupulse/data/raw/internal")
EXTERNAL_DIR = Path("edupulse/data/raw/external")


def run(n_years: int = 8, start_year: int = 2018) -> None:
    """합성 데이터 전체 생성 및 저장."""
    INTERNAL_DIR.mkdir(parents=True, exist_ok=True)
    EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)

    # 1. 수강 이력 생성
    print("1. 수강 이력 생성 중...")
    enrollment_df = generate_enrollment_history(n_years=n_years, start_year=start_year)
    enrollment_path = INTERNAL_DIR / "enrollment_history.csv"
    enrollment_df.to_csv(enrollment_path, index=False)
    print(f"   저장: {enrollment_path} ({len(enrollment_df)}행)")
    print(f"   분야별 평균 등록 수:")
    for field, mean in enrollment_df.groupby("field")["enrollment_count"].mean().items():
        print(f"     {field}: {mean:.1f}명")

    # 수요 등급 분포 출력
    from edupulse.constants import classify_demand
    tiers = enrollment_df["enrollment_count"].apply(classify_demand).value_counts()
    total = len(enrollment_df)
    print(f"   수요 등급 분포: ", end="")
    for tier, count in tiers.items():
        print(f"{tier.value} {count/total*100:.0f}%", end="  ")
    print()

    # 2. 검색 트렌드 생성
    print("2. 검색 트렌드 생성 중...")
    search_df = generate_search_trends(enrollment_df)
    search_path = EXTERNAL_DIR / "search_trends.csv"
    search_df.to_csv(search_path, index=False)
    print(f"   저장: {search_path} ({len(search_df)}행)")
    print(f"   분야별 평균 검색량:")
    for field, mean in search_df.groupby("field")["search_volume"].mean().items():
        print(f"     {field}: {mean:.1f}")

    # 3. 채용 공고 생성
    print("3. 채용 공고 생성 중...")
    jobs_df = generate_job_postings(enrollment_df)
    jobs_path = EXTERNAL_DIR / "job_postings.csv"
    jobs_df.to_csv(jobs_path, index=False)
    print(f"   저장: {jobs_path} ({len(jobs_df)}행)")
    print(f"   분야별 평균 채용 공고:")
    for field, mean in jobs_df.groupby("field")["job_count"].mean().items():
        print(f"     {field}: {mean:.1f}")

    print("\n합성 데이터 생성 완료.")


def main():
    """run_pipeline.py에서 호출되는 진입점."""
    run()


if __name__ == "__main__":
    main()

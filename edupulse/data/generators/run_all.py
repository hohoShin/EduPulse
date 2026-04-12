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
from edupulse.data.generators.internal_generator import (
    generate_consultation_logs,
    generate_student_profiles,
    generate_web_logs,
)
from edupulse.data.generators.events_generator import (
    generate_cert_exam_schedule,
    generate_competitor_data,
    generate_seasonal_events,
)

# 출력 경로
INTERNAL_DIR = Path("edupulse/data/raw/internal")
EXTERNAL_DIR = Path("edupulse/data/raw/external")


def run(n_years: int | None = None, start_year: int = 2018) -> None:
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

    # 4. 상담 로그 생성
    print("4. 상담 로그 생성 중...")
    consultation_df = generate_consultation_logs(enrollment_df)
    consultation_path = INTERNAL_DIR / "consultation_logs.csv"
    consultation_df.to_csv(consultation_path, index=False)
    print(f"   저장: {consultation_path} ({len(consultation_df)}행)")
    print(f"   분야별 평균 상담 건수:")
    for field, mean in consultation_df.groupby("field")["consultation_count"].mean().items():
        print(f"     {field}: {mean:.1f}건")

    # 5. 학생 프로필 생성
    print("5. 학생 프로필 생성 중...")
    student_profile_df = generate_student_profiles(enrollment_df)
    student_profile_path = INTERNAL_DIR / "student_profiles.csv"
    student_profile_df.to_csv(student_profile_path, index=False)
    print(f"   저장: {student_profile_path} ({len(student_profile_df)}행)")
    print(f"   분야별 평균 20대 비율:")
    for field, mean in student_profile_df.groupby("field")["age_20s_ratio"].mean().items():
        print(f"     {field}: {mean:.3f}")

    # 6. 웹 로그 생성
    print("6. 웹 로그 생성 중...")
    web_log_df = generate_web_logs(enrollment_df)
    web_log_path = INTERNAL_DIR / "web_logs.csv"
    web_log_df.to_csv(web_log_path, index=False)
    print(f"   저장: {web_log_path} ({len(web_log_df)}행)")
    print(f"   분야별 평균 페이지뷰:")
    for field, mean in web_log_df.groupby("field")["page_views"].mean().items():
        print(f"     {field}: {mean:.1f}")

    # 7. 자격증 시험 일정 생성
    print("7. 자격증 시험 일정 생성 중...")
    cert_exam_df = generate_cert_exam_schedule(start_year=start_year, n_years=n_years)
    cert_exam_path = EXTERNAL_DIR / "cert_exam_schedule.csv"
    cert_exam_df.to_csv(cert_exam_path, index=False)
    print(f"   저장: {cert_exam_path} ({len(cert_exam_df)}행)")
    print(f"   분야별 시험 있는 주 비율:")
    for field, ratio in cert_exam_df.groupby("field")["has_cert_exam"].mean().items():
        print(f"     {field}: {ratio:.3f}")

    # 8. 경쟁 학원 데이터 생성
    print("8. 경쟁 학원 데이터 생성 중...")
    competitor_df = generate_competitor_data(enrollment_df)
    competitor_path = EXTERNAL_DIR / "competitor_data.csv"
    competitor_df.to_csv(competitor_path, index=False)
    print(f"   저장: {competitor_path} ({len(competitor_df)}행)")
    print(f"   분야별 평균 경쟁 학원 개강 수:")
    for field, mean in competitor_df.groupby("field")["competitor_openings"].mean().items():
        print(f"     {field}: {mean:.1f}")

    # 9. 계절성 이벤트 생성
    print("9. 계절성 이벤트 생성 중...")
    seasonal_df = generate_seasonal_events(start_year=start_year, n_years=n_years)
    seasonal_path = EXTERNAL_DIR / "seasonal_events.csv"
    seasonal_df.to_csv(seasonal_path, index=False)
    print(f"   저장: {seasonal_path} ({len(seasonal_df)}행)")
    print(f"   방학 주 비율: {seasonal_df['is_vacation'].mean():.3f}")
    print(f"   시험 시즌 주 비율: {seasonal_df['is_exam_season'].mean():.3f}")
    print(f"   학기 시작 주 비율: {seasonal_df['is_semester_start'].mean():.3f}")

    print("\n합성 데이터 생성 완료.")


def main():
    """run_pipeline.py에서 호출되는 진입점."""
    run()


if __name__ == "__main__":
    main()

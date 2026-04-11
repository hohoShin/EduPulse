"""합성 데이터 생성기 테스트."""
import pandas as pd
import numpy as np
import pytest

from edupulse.data.generators.enrollment_generator import generate_enrollment_history
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


# --- 공통 픽스처 ---

@pytest.fixture(scope="module")
def enrollment_df():
    """테스트용 소규모 수강 이력 DataFrame (2년치)."""
    return generate_enrollment_history(n_years=2, start_year=2022, seed=42)


# --- 상담 로그 테스트 ---

def test_generate_consultation_logs_schema(enrollment_df):
    """상담 로그에 필수 컬럼과 올바른 타입이 있어야 한다."""
    df = generate_consultation_logs(enrollment_df, seed=44)
    assert set(["date", "field", "consultation_count", "ds", "y"]).issubset(df.columns)
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
    assert pd.api.types.is_integer_dtype(df["consultation_count"])


def test_generate_consultation_logs_seed_reproducibility(enrollment_df):
    """동일 seed로 실행하면 동일한 상담 로그가 생성되어야 한다."""
    df1 = generate_consultation_logs(enrollment_df, seed=44)
    df2 = generate_consultation_logs(enrollment_df, seed=44)
    pd.testing.assert_frame_equal(df1, df2)


# --- 학생 프로필 테스트 ---

def test_generate_student_profiles_ratios_sum_to_one(enrollment_df):
    """연령대 비율과 수강 목적 비율이 각각 합산하여 ~1.0이어야 한다."""
    df = generate_student_profiles(enrollment_df, seed=45)
    age_sum = df["age_20s_ratio"] + df["age_30s_ratio"] + df["age_40plus_ratio"]
    purpose_sum = df["purpose_career"] + df["purpose_hobby"] + df["purpose_cert"]
    assert (age_sum - 1.0).abs().max() < 1e-3
    assert (purpose_sum - 1.0).abs().max() < 1e-3


def test_student_profiles_fields_coverage(enrollment_df):
    """4개 분야(coding, security, game, art) 모두 학생 프로필이 생성되어야 한다."""
    df = generate_student_profiles(enrollment_df, seed=45)
    assert set(["coding", "security", "game", "art"]).issubset(df["field"].unique())


# --- 웹 로그 테스트 ---

def test_generate_web_logs_schema(enrollment_df):
    """웹 로그에 필수 컬럼이 있어야 한다."""
    df = generate_web_logs(enrollment_df, seed=46)
    assert set(["date", "field", "page_views", "ds", "y"]).issubset(df.columns)


def test_generate_web_logs_value_ranges(enrollment_df):
    """page_views >= 1 이어야 한다."""
    df = generate_web_logs(enrollment_df, seed=46)
    assert (df["page_views"] >= 1).all()


# --- 자격증 시험 일정 테스트 ---

def test_generate_cert_exam_deterministic():
    """자격증 시험 일정은 seed 무관하게 동일한 결과를 반환해야 한다."""
    df1 = generate_cert_exam_schedule(start_year=2022, n_years=2, seed=0)
    df2 = generate_cert_exam_schedule(start_year=2022, n_years=2, seed=99)
    pd.testing.assert_frame_equal(df1, df2)


def test_generate_cert_exam_weeks_to_exam_range():
    """weeks_to_exam 값이 0 이상 26 이하여야 한다."""
    df = generate_cert_exam_schedule(start_year=2022, n_years=2, seed=47)
    assert (df["weeks_to_exam"] >= 0).all()
    assert (df["weeks_to_exam"] <= 26).all()


# --- 경쟁 학원 데이터 테스트 ---

def test_generate_competitor_price_non_negative(enrollment_df):
    """competitor_avg_price 값이 0 이상이어야 한다."""
    df = generate_competitor_data(enrollment_df, seed=48)
    assert (df["competitor_avg_price"] >= 0).all()


# --- 계절성 이벤트 테스트 ---

def test_generate_seasonal_events_no_field_column():
    """계절성 이벤트 DataFrame에는 'field' 컬럼이 없어야 한다 (전체 공통 적용)."""
    df = generate_seasonal_events(start_year=2022, n_years=2)
    assert "field" not in df.columns
    assert set(["date", "is_vacation", "is_exam_season", "is_semester_start"]).issubset(df.columns)


def test_generate_seasonal_events_deterministic():
    """계절성 이벤트는 seed 무관하게 동일한 결과를 반환해야 한다."""
    df1 = generate_seasonal_events(start_year=2022, n_years=2, seed=0)
    df2 = generate_seasonal_events(start_year=2022, n_years=2, seed=99)
    pd.testing.assert_frame_equal(df1, df2)


# --- 공통: seed 파라미터 ---

def test_all_generators_accept_seed(enrollment_df):
    """6개 생성기 모두 seed 파라미터를 받아야 한다."""
    generate_consultation_logs(enrollment_df, seed=0)
    generate_student_profiles(enrollment_df, seed=0)
    generate_web_logs(enrollment_df, seed=0)
    generate_cert_exam_schedule(start_year=2022, n_years=2, seed=0)
    generate_competitor_data(enrollment_df, seed=0)
    generate_seasonal_events(start_year=2022, n_years=2, seed=0)


# --- run_all 통합 테스트 ---

def test_run_all_produces_nine_csvs(tmp_path, monkeypatch):
    """run_all.run()이 9개의 CSV 파일을 생성해야 한다."""
    from edupulse.data.generators import run_all

    # 출력 경로를 tmp_path로 리다이렉트
    monkeypatch.setattr(run_all, "INTERNAL_DIR", tmp_path / "internal")
    monkeypatch.setattr(run_all, "EXTERNAL_DIR", tmp_path / "external")

    run_all.run(n_years=1, start_year=2023)

    internal_csvs = list((tmp_path / "internal").glob("*.csv"))
    external_csvs = list((tmp_path / "external").glob("*.csv"))
    total = len(internal_csvs) + len(external_csvs)
    assert total == 9, f"예상 9개, 실제 {total}개: internal={[f.name for f in internal_csvs]}, external={[f.name for f in external_csvs]}"

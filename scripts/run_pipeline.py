"""전체 데이터 파이프라인 오케스트레이션.

Usage:
    python -m scripts.run_pipeline
    python -m scripts.run_pipeline --skip-generate
    python -m scripts.run_pipeline --model xgboost --version 1
"""
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="EduPulse full pipeline: generate → preprocess → train")
    parser.add_argument("--skip-generate", action="store_true", help="기존 raw 데이터 사용 (생성 건너뜀)")
    parser.add_argument("--model", default="xgboost", help="학습할 모델 (default: xgboost)")
    parser.add_argument("--version", type=int, default=1, help="모델 버전 (default: 1)")
    args = parser.parse_args()

    # 1단계: 합성 데이터 생성
    if not args.skip_generate:
        print("[pipeline] Step 1: Generating synthetic data...")
        try:
            from edupulse.data.generators import run_all
            run_all.main()
        except Exception as e:
            print(f"[pipeline] ERROR in data generation: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("[pipeline] Step 1: Skipped (--skip-generate)")

    # 2단계: 전처리 → warehouse
    print("[pipeline] Step 2: Building training dataset...")
    try:
        from edupulse.preprocessing.merger import build_training_dataset
        build_training_dataset()
    except Exception as e:
        print(f"[pipeline] ERROR in preprocessing: {e}", file=sys.stderr)
        sys.exit(1)

    # 3단계: 모델 학습 → 저장
    print(f"[pipeline] Step 3: Training {args.model} model (version {args.version})...")
    try:
        from edupulse.model.train import train_model
        train_model(model_name=args.model, version=args.version)
    except Exception as e:
        print(f"[pipeline] ERROR in model training: {e}", file=sys.stderr)
        sys.exit(1)

    print("[pipeline] Pipeline completed successfully.")


if __name__ == "__main__":
    main()

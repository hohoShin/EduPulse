"""재학습 스케줄러 — cron 호출 대상 스크립트.

Usage:
    python -m edupulse.model.retrain --model xgboost
    python -m edupulse.model.retrain --model xgboost --dry-run
    python -m edupulse.model.retrain --model xgboost --version 2
"""
import argparse
import sys


def retrain(model_name: str = "xgboost", version: int = 1, dry_run: bool = False) -> None:
    """전처리 → 학습 → 평가 파이프라인 실행.

    Args:
        model_name: 재학습할 모델 이름
        version: 저장할 모델 버전 번호
        dry_run: True이면 실제 실행 없이 메시지만 출력
    """
    if dry_run:
        print(f"Dry run: would retrain {model_name} with latest data")
        return

    print(f"[retrain] Starting retraining: model={model_name}, version={version}")

    # 1단계: 전처리 파이프라인 → warehouse
    print("[retrain] Step 1: Building training dataset...")
    try:
        from edupulse.preprocessing.merger import build_training_dataset
        build_training_dataset()
        print("[retrain] Dataset built successfully.")
    except Exception as e:
        print(f"[retrain] ERROR in preprocessing: {e}", file=sys.stderr)
        sys.exit(1)

    # 2단계: 모델 학습
    print(f"[retrain] Step 2: Training {model_name} model...")
    try:
        from edupulse.model.train import train_model
        train_model(model_name=model_name, version=version)
        print(f"[retrain] Model trained and saved (v{version}).")
    except Exception as e:
        print(f"[retrain] ERROR in training: {e}", file=sys.stderr)
        sys.exit(1)

    # 3단계: 모델 평가
    print("[retrain] Step 3: Evaluating model...")
    try:
        from edupulse.model.evaluate import evaluate_model
        results = evaluate_model(model_name=model_name)
        print(f"[retrain] Evaluation complete — MAPE: {results['mape']:.2f}%")
    except Exception as e:
        print(f"[retrain] WARNING: Evaluation failed: {e}", file=sys.stderr)
        # 평가 실패는 치명적이지 않음 — 학습은 성공했으므로 계속

    print(f"[retrain] Retraining complete: {model_name} v{version}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EduPulse model retraining scheduler")
    parser.add_argument("--model", default="xgboost", help="Model to retrain (default: xgboost)")
    parser.add_argument("--version", type=int, default=1, help="Model version to save (default: 1)")
    parser.add_argument("--dry-run", action="store_true", help="Print action without executing")
    args = parser.parse_args()

    retrain(model_name=args.model, version=args.version, dry_run=args.dry_run)

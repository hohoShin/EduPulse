"""재학습 스케줄러 — cron 호출 대상 스크립트.

Usage:
    python -m edupulse.model.retrain --model xgboost
    python -m edupulse.model.retrain --model xgboost --dry-run
    python -m edupulse.model.retrain --model xgboost --version 2
    python -m edupulse.model.retrain --model xgboost --version auto
"""
import argparse
import sys

# 모델 이름 → 저장 경로 매핑
_MODEL_SAVE_DIRS = {
    "xgboost": "edupulse/model/saved/xgboost",
    "prophet": "edupulse/model/saved/prophet",
    "lstm": "edupulse/model/saved/lstm",
}


def _resolve_version(model_name: str, version: int | None) -> int:
    """버전 번호를 결정. None이면 최신 버전 + 1로 자동 증가.

    Args:
        model_name: 모델 이름
        version: 명시적 버전 또는 None (자동)

    Returns:
        사용할 버전 번호
    """
    if version is not None:
        return version
    from edupulse.model.utils import find_latest_version
    save_dir = _MODEL_SAVE_DIRS.get(model_name, f"edupulse/model/saved/{model_name}")
    latest = find_latest_version(save_dir)
    return latest + 1


def retrain(model_name: str = "xgboost", version: int | None = None, dry_run: bool = False) -> None:
    """전처리 → 학습 → 평가 파이프라인 실행.

    Args:
        model_name: 재학습할 모델 이름
        version: 저장할 모델 버전 번호 (None이면 자동 증가)
        dry_run: True이면 실제 실행 없이 메시지만 출력
    """
    version = _resolve_version(model_name, version)

    if dry_run:
        print(f"Dry run: would retrain {model_name} v{version} with latest data")
        return

    print(f"[retrain] Starting retraining: model={model_name}, version={version}")

    print("[retrain] Step 1: Building training dataset...")
    try:
        from edupulse.preprocessing.merger import build_training_dataset
        build_training_dataset()
        print("[retrain] Dataset built successfully.")
    except Exception as e:
        print(f"[retrain] ERROR in preprocessing: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[retrain] Step 2: Training {model_name} model...")
    try:
        from edupulse.model.train import train_model
        train_model(model_name=model_name, version=version)
        print(f"[retrain] Model trained and saved (v{version}).")
    except Exception as e:
        print(f"[retrain] ERROR in training: {e}", file=sys.stderr)
        sys.exit(1)

    print("[retrain] Step 3: Evaluating model (K-Fold on training data)...")
    try:
        from edupulse.model.evaluate import evaluate_model
        results = evaluate_model(model_name=model_name)
        print(f"[retrain] Evaluation complete — MAPE: {results['mape']:.2f}%")
    except Exception as e:
        print(f"[retrain] WARNING: Evaluation failed: {e}", file=sys.stderr)

    try:
        from edupulse.model.predict import clear_model_cache
        clear_model_cache()
        print("[retrain] Model cache cleared.")
    except Exception:
        pass

    print(f"[retrain] Retraining complete: {model_name} v{version}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EduPulse model retraining scheduler")
    parser.add_argument("--model", default="xgboost", help="Model to retrain (default: xgboost)")
    parser.add_argument(
        "--version", default="auto",
        help="Model version to save. 'auto' = latest+1 (default: auto)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print action without executing")
    args = parser.parse_args()

    version = None if args.version == "auto" else int(args.version)
    retrain(model_name=args.model, version=version, dry_run=args.dry_run)

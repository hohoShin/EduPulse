"""모델 학습 스크립트.

Usage:
    python -m edupulse.model.train
    python -m edupulse.model.train --model xgboost --version 1
    python -m edupulse.model.train --model prophet --version 1
    python -m edupulse.model.train --model lstm --version 1
    python -m edupulse.model.train --model all --version 1
"""
import argparse
import sys

import pandas as pd


def train_model(
    model_name: str = "xgboost",
    data_path: str = "edupulse/data/warehouse/training_dataset.csv",
    version: int = 1,
) -> None:
    """warehouse CSV 로딩 → 모델 학습 → 저장.

    Args:
        model_name: 학습할 모델 이름 ('xgboost', 'prophet', 'lstm', 'all')
        data_path: 학습 데이터 경로
        version: 저장할 모델 버전 번호
    """
    print(f"[train] Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    print(f"[train] Loaded {len(df)} rows")

    targets = ["xgboost", "prophet", "lstm"] if model_name == "all" else [model_name]

    for target in targets:
        _train_single(target, df, version)


def _train_single(model_name: str, df: pd.DataFrame, version: int) -> None:
    """단일 모델 학습, 평가, 메타데이터 포함 저장.

    Args:
        model_name: 모델 이름
        df: 학습 DataFrame
        version: 저장 버전
    """
    if model_name == "xgboost":
        from edupulse.model.xgboost_model import XGBoostForecaster

        model = XGBoostForecaster()
        model.train(df)
        _evaluate_quietly(model, df)
        save_path = "edupulse/model/saved/xgboost"
        model.save(save_path, version=version, df=df)
        print(f"[train] XGBoost model saved → {save_path}/v{version}/")

    elif model_name == "prophet":
        try:
            from edupulse.model.prophet_model import ProphetForecaster

            model = ProphetForecaster()
            model.train(df)
            _evaluate_quietly(model, df)
            save_path = "edupulse/model/saved/prophet"
            model.save(save_path, version=version, df=df)
            print(f"[train] Prophet model saved → {save_path}/v{version}/")
        except ImportError as exc:
            print(f"[train] Prophet 미설치 — 건너뜀: {exc}", file=sys.stderr)

    elif model_name == "lstm":
        try:
            from edupulse.model.lstm_model import LSTMForecaster

            model = LSTMForecaster()
            model.train(df)
            _evaluate_quietly(model, df)
            save_path = "edupulse/model/saved/lstm"
            model.save(save_path, version=version, df=df)
            print(f"[train] LSTM model saved → {save_path}/v{version}/")
        except ImportError as exc:
            print(f"[train] PyTorch 미설치 — 건너뜀: {exc}", file=sys.stderr)

    else:
        print(f"[train] Unknown model: {model_name}", file=sys.stderr)
        sys.exit(1)


def _evaluate_quietly(model, df: pd.DataFrame, n_splits: int = 3) -> None:
    """학습 직후 MAPE 평가 (실패해도 학습 저장에 영향 없음).

    Args:
        model: 학습된 BaseForecaster 인스턴스
        df: 평가용 DataFrame
        n_splits: K-Fold 분할 수 (빠른 평가를 위해 기본 3)
    """
    try:
        result = model.evaluate(df, n_splits=n_splits)
        mape = result.get("mape")
        if mape is not None:
            print(f"[train] Quick evaluation MAPE: {mape:.2f}% (n_splits={n_splits})")
    except Exception as exc:
        print(f"[train] Evaluation skipped: {exc}", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EduPulse model training")
    parser.add_argument(
        "--model",
        default="xgboost",
        choices=["xgboost", "prophet", "lstm", "all"],
        help="Model to train",
    )
    parser.add_argument("--version", type=int, default=1, help="Model version")
    parser.add_argument(
        "--data",
        default="edupulse/data/warehouse/training_dataset.csv",
        help="Path to training dataset CSV",
    )
    args = parser.parse_args()
    train_model(model_name=args.model, data_path=args.data, version=args.version)

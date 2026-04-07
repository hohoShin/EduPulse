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
    """단일 모델 학습 및 저장.

    Args:
        model_name: 모델 이름
        df: 학습 DataFrame
        version: 저장 버전
    """
    if model_name == "xgboost":
        from edupulse.model.xgboost_model import XGBoostForecaster

        model = XGBoostForecaster()
        model.train(df)
        save_path = "edupulse/model/saved/xgboost"
        model.save(save_path, version=version)
        print(f"[train] XGBoost model saved → {save_path}/v{version}/model.joblib")

    elif model_name == "prophet":
        try:
            from edupulse.model.prophet_model import ProphetForecaster

            model = ProphetForecaster()
            model.train(df)
            save_path = "edupulse/model/saved/prophet"
            model.save(save_path, version=version)
            print(f"[train] Prophet model saved → {save_path}/v{version}/model.joblib")
        except ImportError as exc:
            print(f"[train] Prophet 미설치 — 건너뜀: {exc}", file=sys.stderr)

    elif model_name == "lstm":
        try:
            from edupulse.model.lstm_model import LSTMForecaster

            model = LSTMForecaster()
            model.train(df)
            save_path = "edupulse/model/saved/lstm"
            model.save(save_path, version=version)
            print(f"[train] LSTM model saved → {save_path}/v{version}/model.pt")
        except ImportError as exc:
            print(f"[train] PyTorch 미설치 — 건너뜀: {exc}", file=sys.stderr)

    else:
        print(f"[train] Unknown model: {model_name}", file=sys.stderr)
        sys.exit(1)


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

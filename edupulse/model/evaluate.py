"""모델 평가 스크립트 — MAPE, 시계열 K-Fold.

Usage:
    python -m edupulse.model.evaluate
    python -m edupulse.model.evaluate --model xgboost
    python -m edupulse.model.evaluate --model prophet
    python -m edupulse.model.evaluate --model lstm
    python -m edupulse.model.evaluate --model all
"""
import argparse
import sys

import pandas as pd


def evaluate_model(
    model_name: str = "xgboost",
    data_path: str = "edupulse/data/warehouse/training_dataset.csv",
    n_splits: int = 5,
) -> dict:
    """TimeSeriesSplit K-Fold 교차검증으로 MAPE 평가.

    Args:
        model_name: 평가할 모델 이름 ('xgboost', 'prophet', 'lstm', 'all')
        data_path: 평가 데이터 경로
        n_splits: K-Fold 분할 수

    Returns:
        단일 모델: {'mape': float, 'n_splits': int}
        'all': {'model_mapes': dict, 'comparison_table': str}
    """
    print(f"[evaluate] Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    print(f"[evaluate] Loaded {len(df)} rows")

    if model_name == "all":
        return _evaluate_all(df, n_splits)

    return _evaluate_single(model_name, df, n_splits)


def _evaluate_single(model_name: str, df: pd.DataFrame, n_splits: int) -> dict:
    """단일 모델 평가.

    Args:
        model_name: 모델 이름
        df: 평가 DataFrame
        n_splits: K-Fold 분할 수

    Returns:
        {'mape': float, 'n_splits': int}
    """
    if model_name == "xgboost":
        from edupulse.model.xgboost_model import XGBoostForecaster

        model = XGBoostForecaster()
        results = model.evaluate(df, n_splits=n_splits)
        print(f"[evaluate] XGBoost MAPE: {results['mape']:.2f}% (n_splits={n_splits})")
        return results

    elif model_name == "prophet":
        try:
            from edupulse.model.prophet_model import ProphetForecaster

            model = ProphetForecaster()
            results = model.evaluate(df, n_splits=n_splits)
            print(f"[evaluate] Prophet MAPE: {results['mape']:.2f}% (n_splits={n_splits})")
            return results
        except ImportError as exc:
            print(f"[evaluate] Prophet 미설치 — 건너뜀: {exc}", file=sys.stderr)
            return {"mape": float("nan"), "n_splits": n_splits}

    elif model_name == "lstm":
        try:
            from edupulse.model.lstm_model import LSTMForecaster

            model = LSTMForecaster()
            results = model.evaluate(df, n_splits=n_splits)
            print(f"[evaluate] LSTM MAPE: {results['mape']:.2f}% (n_splits={n_splits})")
            return results
        except ImportError as exc:
            print(f"[evaluate] PyTorch 미설치 — 건너뜀: {exc}", file=sys.stderr)
            return {"mape": float("nan"), "n_splits": n_splits}

    else:
        print(f"[evaluate] Unknown model: {model_name}", file=sys.stderr)
        sys.exit(1)


def _evaluate_all(df: pd.DataFrame, n_splits: int) -> dict:
    """모든 모델을 평가하고 비교 테이블 출력.

    Args:
        df: 평가 DataFrame
        n_splits: K-Fold 분할 수

    Returns:
        {'model_mapes': dict[str, float], 'comparison_table': str, 'n_splits': int}
    """
    model_names = ["xgboost", "prophet", "lstm"]
    model_mapes: dict[str, float] = {}

    for name in model_names:
        result = _evaluate_single(name, df, n_splits)
        model_mapes[name] = result.get("mape", float("nan"))

    # 비교 테이블 출력
    lines = [
        "",
        "=" * 40,
        "  모델 MAPE 비교표",
        "=" * 40,
        f"  {'모델':<12} {'MAPE (%)':>10}",
        "-" * 40,
    ]
    for name, mape in model_mapes.items():
        mape_str = f"{mape:.2f}" if mape == mape else "N/A"  # nan check
        lines.append(f"  {name:<12} {mape_str:>10}")
    lines.append("=" * 40)
    table = "\n".join(lines)
    print(table)

    return {"model_mapes": model_mapes, "comparison_table": table, "n_splits": n_splits}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EduPulse model evaluation")
    parser.add_argument(
        "--model",
        default="xgboost",
        choices=["xgboost", "prophet", "lstm", "all"],
        help="Model to evaluate",
    )
    parser.add_argument("--n-splits", type=int, default=5, help="K-Fold splits")
    parser.add_argument(
        "--data",
        default="edupulse/data/warehouse/training_dataset.csv",
        help="Path to evaluation dataset CSV",
    )
    args = parser.parse_args()
    evaluate_model(model_name=args.model, data_path=args.data, n_splits=args.n_splits)

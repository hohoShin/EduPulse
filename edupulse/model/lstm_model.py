"""LSTM 수요 예측 모델 (MacBook M4 전용 학습, Droplet 추론 가능)."""
from __future__ import annotations

from pathlib import Path

# MPS segfault 방지: torch를 numpy/pandas보다 먼저 import해야 한다.
# Droplet(torch 미설치)에서는 None으로 대체되며, 실제 사용 시 _get_torch()에서 에러를 발생시킨다.
try:
    import torch as _torch
except ImportError:
    _torch = None

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import MinMaxScaler

from edupulse.constants import classify_demand
from edupulse.model.base import (
    BaseForecaster,
    ModelMetadata,
    PredictionResult,
    _extract_data_info,
    _get_package_version,
    ensure_feature_columns,
    load_metadata,
    save_metadata,
    warn_feature_mismatch,
)
from edupulse.model.utils import get_device
from edupulse.model.xgboost_model import FEATURE_COLUMNS, TARGET_COLUMN

SEQUENCE_LENGTH = 12
BATCH_SIZE = 32
HIDDEN_SIZE = 64
NUM_LAYERS = 2
DROPOUT = 0.3
INPUT_SIZE = len(FEATURE_COLUMNS)

# Early Stopping / LR Scheduler 설정
PATIENCE = 7
SCHEDULER_FACTOR = 0.5
SCHEDULER_PATIENCE = 3
MIN_LR = 1e-6
VAL_RATIO = 0.1


def _get_torch():
    """모듈 수준에서 import된 torch를 반환. 미설치 시 ImportError."""
    if _torch is None:
        raise ImportError(
            "PyTorch가 설치되어 있지 않습니다. "
            "MacBook에서 'pip install torch'를 실행하세요."
        )
    return _torch


def _check_feature_compatibility(path: str, version: int, current_features: list[str]) -> None:
    """metadata.json의 피처 수와 현재 피처 수를 비교. 불일치 시 RuntimeError.

    load_state_dict() 전에 호출하여 아키텍처 불일치 크래시를 방지한다.

    Args:
        path: 모델 저장 루트 경로
        version: 버전 번호
        current_features: 현재 코드의 피처 목록
    """
    try:
        meta = load_metadata(path, version)
    except FileNotFoundError:
        return  # metadata 없으면 검증 불가 — 경고만 (기존 동작)

    saved = meta.feature_columns
    if not saved:
        return

    if len(saved) != len(current_features):
        raise RuntimeError(
            f"LSTM 피처 수 불일치: 학습 시 {len(saved)}개 → 현재 {len(current_features)}개. "
            f"저장된 가중치와 아키텍처가 호환되지 않습니다. "
            f"학습: {saved}, 현재: {current_features}"
        )

    if list(saved) != list(current_features):
        raise RuntimeError(
            f"LSTM 피처 순서/구성 불일치: "
            f"학습: {saved}, 현재: {current_features}"
        )


class EnrollmentLSTM:
    """nn.Module 래퍼. torch import를 지연 평가하여 Droplet 호환성 유지."""

    def __new__(cls, *args, **kwargs):  # noqa: D102
        torch = _get_torch()
        nn = torch.nn

        class _LSTMModule(nn.Module):
            """LSTM(input_size, hidden=64, layers=2, dropout=0.3) → Linear(64,1)."""

            def __init__(self):
                super().__init__()
                self.lstm = nn.LSTM(
                    input_size=INPUT_SIZE,
                    hidden_size=HIDDEN_SIZE,
                    num_layers=NUM_LAYERS,
                    dropout=DROPOUT,
                    batch_first=True,
                )
                self.fc = nn.Linear(HIDDEN_SIZE, 1)

            def forward(self, x):
                """x: (batch, seq_len, input_size) → (batch, 1)."""
                out, _ = self.lstm(x)
                return self.fc(out[:, -1, :])

        return _LSTMModule(*args, **kwargs)


def _build_sequences(
    X: np.ndarray,
    y: np.ndarray,
    sequence_length: int,
) -> tuple[np.ndarray, np.ndarray]:
    """슬라이딩 윈도우로 시퀀스 생성.

    Args:
        X: shape (n_samples, n_features)
        y: shape (n_samples,)
        sequence_length: 입력 시퀀스 길이

    Returns:
        xs: shape (n_windows, sequence_length, n_features)
        ys: shape (n_windows,)
    """
    xs, ys = [], []
    for i in range(len(X) - sequence_length):
        xs.append(X[i : i + sequence_length])
        ys.append(y[i + sequence_length])
    return np.array(xs, dtype=np.float32), np.array(ys, dtype=np.float32)


def _build_sequences_per_field(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
    sequence_length: int,
    scaler_X: MinMaxScaler,
    scaler_y: MinMaxScaler,
    fit_scalers: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    """분야별로 시퀀스를 생성하여 경계 오염을 방지한다.

    Args:
        df: field, date, feature_cols, target_col 컬럼 포함 DataFrame
        feature_cols: 피처 컬럼 목록
        target_col: 타겟 컬럼
        sequence_length: 시퀀스 길이
        scaler_X: 피처 스케일러
        scaler_y: 타겟 스케일러
        fit_scalers: True면 스케일러를 fit_transform, False면 transform만

    Returns:
        xs: (n_total_windows, sequence_length, n_features)
        ys: (n_total_windows,)
    """
    df = ensure_feature_columns(df, feature_cols, "LSTM.sequences")
    X_raw = df[feature_cols].fillna(0).values.astype(np.float32)
    y_raw = df[target_col].values.astype(np.float32).reshape(-1, 1)

    if fit_scalers:
        X_scaled = scaler_X.fit_transform(X_raw)
        y_scaled = scaler_y.fit_transform(y_raw).ravel()
    else:
        X_scaled = scaler_X.transform(X_raw)
        y_scaled = scaler_y.transform(y_raw).ravel()

    if "field" not in df.columns or df["field"].nunique() <= 1:
        return _build_sequences(X_scaled, y_scaled, sequence_length)

    all_xs, all_ys = [], []
    for field in df["field"].unique():
        mask = df["field"].values == field
        field_X = X_scaled[mask]
        field_y = y_scaled[mask]
        if len(field_X) > sequence_length:
            xs, ys = _build_sequences(field_X, field_y, sequence_length)
            all_xs.append(xs)
            all_ys.append(ys)

    if not all_xs:
        return np.array([], dtype=np.float32), np.array([], dtype=np.float32)
    return np.concatenate(all_xs), np.concatenate(all_ys)


# 증강 대상 피처: 이름 기반으로 인덱스를 동적 계산 (피처 추가/순서 변경에 안전)
_PROTECTED_NAMES = {"month_sin", "month_cos", "field_encoded"}
PROTECTED_FEATURES = [i for i, c in enumerate(FEATURE_COLUMNS) if c in _PROTECTED_NAMES]
AUGMENTABLE_FEATURES = [i for i, c in enumerate(FEATURE_COLUMNS) if c not in _PROTECTED_NAMES]


def _augment_sequences(
    xs: np.ndarray,
    ys: np.ndarray,
    *,
    jitter_std: float = 0.02,
    scale_range: tuple[float, float] = (0.95, 1.05),
    n_augments: int = 2,
    seed: int = 123,
) -> tuple[np.ndarray, np.ndarray]:
    """Feature-aware 시퀀스 증강 (jittering + scaling).

    연속값 피처(lag, volume)만 증강하고, 순환 인코딩(month_sin/cos)과
    카테고리(field_encoded)는 원본 그대로 유지한다.

    Args:
        xs: 원본 시퀀스, shape (n_windows, seq_len, n_features)
        ys: 원본 타겟, shape (n_windows,)
        jitter_std: 가우시안 노이즈 표준편차
        scale_range: (min_scale, max_scale) 스케일링 범위
        n_augments: 생성할 증강 복사본 수 (총 출력 = 원본 + n_augments)
        seed: 재현성을 위한 난수 시드

    Returns:
        (원본 + 증강) xs, ys 배열
    """
    if len(xs) == 0:
        return xs, ys

    rng = np.random.default_rng(seed)
    aug_xs, aug_ys = [xs], [ys]
    n_aug_features = len(AUGMENTABLE_FEATURES)

    for _ in range(n_augments):
        augmented = xs.copy()

        # Jittering: 연속값 피처에만 가우시안 노이즈 추가
        noise = rng.normal(
            0, jitter_std, size=(len(xs), xs.shape[1], n_aug_features),
        ).astype(np.float32)
        augmented[:, :, AUGMENTABLE_FEATURES] += noise

        # Scaling: 시퀀스별 동일 스케일 팩터로 연속값 피처만 스케일링
        scales = rng.uniform(
            scale_range[0], scale_range[1], size=(len(xs), 1, 1),
        ).astype(np.float32)
        augmented[:, :, AUGMENTABLE_FEATURES] *= scales

        # 타겟도 동일 비율로 스케일링 (lag 피처가 타겟의 시차 파생이므로 유효)
        y_scales = scales.squeeze(axis=(1, 2))
        scaled_ys = ys * y_scales

        aug_xs.append(augmented)
        aug_ys.append(scaled_ys)

    return np.concatenate(aug_xs), np.concatenate(aug_ys)


def _train_loop(
    model,
    X_train,
    y_train,
    X_val,
    y_val,
    *,
    epochs: int,
    learning_rate: float,
    patience: int,
    device,
):
    """Early Stopping + ReduceLROnPlateau 적용 학습 루프.

    Args:
        model: 학습할 LSTM 모델
        X_train: 학습 입력 텐서
        y_train: 학습 타겟 텐서
        X_val: 검증 입력 텐서
        y_val: 검증 타겟 텐서
        epochs: 최대 에포크 수
        learning_rate: 초기 학습률
        patience: 검증 손실 미개선 허용 에포크 수
        device: 학습 디바이스

    Returns:
        최적 가중치가 로딩된 모델
    """
    torch = _get_torch()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=SCHEDULER_FACTOR,
        patience=SCHEDULER_PATIENCE, min_lr=MIN_LR,
    )
    criterion = torch.nn.MSELoss()

    dataset = torch.utils.data.TensorDataset(X_train, y_train)
    loader = torch.utils.data.DataLoader(
        dataset, batch_size=BATCH_SIZE, shuffle=False,
    )

    best_val_loss = float("inf")
    best_state = None
    counter = 0

    for _ in range(epochs):
        model.train()
        for Xb, yb in loader:
            optimizer.zero_grad()
            loss = criterion(model(Xb), yb)
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            val_loss = criterion(model(X_val), y_val).item()

        scheduler.step(val_loss)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            counter = 0
        else:
            counter += 1
            if counter >= patience:
                break

    if best_state is not None:
        model.load_state_dict(best_state)
    return model


class LSTMForecaster(BaseForecaster):
    """LSTM 기반 수강 수요 예측 모델.

    학습은 M4 MacBook(MPS)에서 수행하고 모델 파일을 Droplet으로 전송.
    Droplet에서는 load() → predict() 만 사용.
    """

    def __init__(self):
        super().__init__()
        self._model = None          # EnrollmentLSTM (_LSTMModule 인스턴스)
        self._scaler_X = MinMaxScaler()
        self._scaler_y = MinMaxScaler()
        self._mape: float | None = None
        self._is_fitted: bool = False

    def _prepare_arrays(
        self, df: pd.DataFrame
    ) -> tuple[np.ndarray, np.ndarray]:
        """DataFrame → 정규화된 (X, y) numpy 배열 반환."""
        df = ensure_feature_columns(df, FEATURE_COLUMNS, "LSTM.prepare")
        X_raw = df[FEATURE_COLUMNS].fillna(0).values.astype(np.float32)
        y_raw = df[TARGET_COLUMN].values.astype(np.float32).reshape(-1, 1)
        return X_raw, y_raw

    def _make_model(self):
        """EnrollmentLSTM 인스턴스 생성 (torch 필요)."""
        return EnrollmentLSTM()

    def train(
        self,
        df: pd.DataFrame,
        epochs: int = 100,
        learning_rate: float = 1e-3,
        patience: int = PATIENCE,
        augment: bool = True,
    ) -> None:
        """MinMaxScaler 정규화 → 분야별 시퀀스 생성 → LSTM 학습.

        Early Stopping과 ReduceLROnPlateau 스케줄러를 적용하여
        과적합을 방지하고 학습 안정성을 높인다.

        Args:
            df: FEATURE_COLUMNS + TARGET_COLUMN 포함 DataFrame
            epochs: 최대 학습 에포크 수
            learning_rate: Adam 옵티마이저 초기 학습률
            patience: 검증 손실 미개선 허용 에포크 수
            augment: True면 학습 데이터에 jittering+scaling 증강 적용
        """
        torch = _get_torch()
        device = get_device()

        xs, ys = _build_sequences_per_field(
            df, FEATURE_COLUMNS, TARGET_COLUMN, SEQUENCE_LENGTH,
            self._scaler_X, self._scaler_y, fit_scalers=True,
        )
        if len(xs) == 0:
            raise ValueError(
                f"시퀀스 생성 실패: 데이터({len(df)}행)가 "
                f"sequence_length({SEQUENCE_LENGTH})보다 많아야 합니다."
            )

        val_size = max(1, int(len(xs) * VAL_RATIO))
        xs_train, xs_val = xs[:-val_size], xs[-val_size:]
        ys_train, ys_val = ys[:-val_size], ys[-val_size:]

        if augment:
            xs_train, ys_train = _augment_sequences(xs_train, ys_train)

        X_train_t = torch.tensor(xs_train).to(device)
        y_train_t = torch.tensor(ys_train).unsqueeze(1).to(device)
        X_val_t = torch.tensor(xs_val).to(device)
        y_val_t = torch.tensor(ys_val).unsqueeze(1).to(device)

        self._model = self._make_model().to(device)
        self._model = _train_loop(
            self._model, X_train_t, y_train_t, X_val_t, y_val_t,
            epochs=epochs, learning_rate=learning_rate,
            patience=patience, device=device,
        )
        self._is_fitted = True

    def _predict(self, features: pd.DataFrame) -> PredictionResult:
        """정규화 → LSTM 추론 → 역변환 → PredictionResult 반환.

        Args:
            features: FEATURE_COLUMNS에 해당하는 DataFrame (1행 이상)
        """
        if self._model is None or not self._is_fitted:
            raise RuntimeError(
                "모델이 학습되지 않았습니다. train() 또는 load()를 먼저 호출하세요."
            )

        torch = _get_torch()
        device = get_device()

        features = ensure_feature_columns(features, FEATURE_COLUMNS, "LSTM.predict")
        X_raw = features[FEATURE_COLUMNS].fillna(0).values.astype(np.float32)
        X_scaled = self._scaler_X.transform(X_raw)

        if len(X_scaled) < SEQUENCE_LENGTH:
            # 스케일링된 공간에서 원본 0에 해당하는 값으로 패딩 (raw 0 → scaled)
            zero_row = np.zeros((1, X_raw.shape[1]), dtype=np.float32)
            zero_scaled = self._scaler_X.transform(zero_row)
            pad = np.repeat(zero_scaled, SEQUENCE_LENGTH - len(X_scaled), axis=0)
            X_scaled = np.vstack([pad, X_scaled])

        seq = X_scaled[-SEQUENCE_LENGTH:]
        X_tensor = torch.tensor(seq).unsqueeze(0).to(device)  # (1, seq, feat)

        self._model.eval()
        with torch.no_grad():
            raw_scaled = self._model(X_tensor).item()

        raw_pred = float(
            self._scaler_y.inverse_transform([[raw_scaled]])[0][0]
        )
        raw_pred = max(0.0, raw_pred)
        predicted_enrollment = round(raw_pred)
        demand_tier = classify_demand(predicted_enrollment)

        margin = (
            (self._mape / 100.0 * raw_pred) if self._mape else (raw_pred * 0.15)
        )
        confidence_lower = max(0.0, round(raw_pred - margin, 1))
        confidence_upper = round(raw_pred + margin, 1)

        return PredictionResult(
            predicted_enrollment=predicted_enrollment,
            demand_tier=demand_tier,
            confidence_lower=confidence_lower,
            confidence_upper=confidence_upper,
            model_used="lstm",
            mape=self._mape,
        )

    def evaluate(self, df: pd.DataFrame, n_splits: int = 5) -> dict:
        """TimeSeriesSplit K-Fold 교차검증. 분야별 분리 평가 후 평균 MAPE 반환.

        Args:
            df: FEATURE_COLUMNS + TARGET_COLUMN 포함 DataFrame
            n_splits: K-Fold 분할 수

        Returns:
            {'mape': float, 'n_splits': int}
        """
        if "field" in df.columns and df["field"].nunique() > 1:
            return self._evaluate_per_field(df, n_splits)
        return self._evaluate_single(df, n_splits)

    def _evaluate_fold(
        self, X_raw: np.ndarray, y_raw: np.ndarray, n_splits: int,
    ) -> list[float]:
        """K-Fold 평가 공통 로직. 각 fold의 MAPE 리스트를 반환한다.

        Args:
            X_raw: 피처 배열 (n_samples, n_features)
            y_raw: 타겟 배열 (n_samples, 1)
            n_splits: K-Fold 분할 수

        Returns:
            각 fold의 MAPE 값 리스트
        """
        torch = _get_torch()
        tscv = TimeSeriesSplit(n_splits=n_splits)
        mapes: list[float] = []

        for train_idx, val_idx in tscv.split(X_raw):
            X_tr, X_val = X_raw[train_idx], X_raw[val_idx]
            y_tr, y_val = y_raw[train_idx], y_raw[val_idx]

            scaler_X = MinMaxScaler()
            scaler_y = MinMaxScaler()
            X_tr_s = scaler_X.fit_transform(X_tr)
            y_tr_s = scaler_y.fit_transform(y_tr).ravel()
            X_val_s = scaler_X.transform(X_val)

            xs_tr, ys_tr = _build_sequences(X_tr_s, y_tr_s, SEQUENCE_LENGTH)
            if len(xs_tr) == 0:
                continue

            inner_val_size = max(1, int(len(xs_tr) * VAL_RATIO))
            xs_inner_tr, xs_inner_val = xs_tr[:-inner_val_size], xs_tr[-inner_val_size:]
            ys_inner_tr, ys_inner_val = ys_tr[:-inner_val_size], ys_tr[-inner_val_size:]

            xs_inner_tr, ys_inner_tr = _augment_sequences(xs_inner_tr, ys_inner_tr)

            device = get_device()
            X_t = torch.tensor(xs_inner_tr).to(device)
            y_t = torch.tensor(ys_inner_tr).unsqueeze(1).to(device)
            X_v = torch.tensor(xs_inner_val).to(device)
            y_v = torch.tensor(ys_inner_val).unsqueeze(1).to(device)

            fold_model = self._make_model().to(device)
            fold_model = _train_loop(
                fold_model, X_t, y_t, X_v, y_v,
                epochs=50, learning_rate=1e-3,
                patience=PATIENCE, device=device,
            )

            fold_model.eval()
            preds, actuals = [], []
            for i in range(len(X_val_s) - SEQUENCE_LENGTH):
                seq = X_val_s[i : i + SEQUENCE_LENGTH]
                X_inf = torch.tensor(seq).unsqueeze(0).to(device)
                with torch.no_grad():
                    p = fold_model(X_inf).item()
                preds.append(float(scaler_y.inverse_transform([[p]])[0][0]))
                actuals.append(float(y_val[i + SEQUENCE_LENGTH][0]))

            actuals_arr = np.array(actuals)
            preds_arr = np.array(preds)
            nonzero = actuals_arr != 0
            if nonzero.any():
                fold_mape = float(
                    np.mean(
                        np.abs(
                            (actuals_arr[nonzero] - preds_arr[nonzero])
                            / actuals_arr[nonzero]
                        )
                    )
                    * 100
                )
                mapes.append(fold_mape)

        return mapes

    def _evaluate_single(self, df: pd.DataFrame, n_splits: int) -> dict:
        """단일 시계열 평가."""
        X_raw, y_raw = self._prepare_arrays(df)
        mapes = self._evaluate_fold(X_raw, y_raw, n_splits)
        avg_mape = float(np.mean(mapes)) if mapes else float("nan")
        if self._mape is None:
            self._mape = avg_mape
        return {"mape": avg_mape, "n_splits": n_splits}

    def _evaluate_per_field(self, df: pd.DataFrame, n_splits: int) -> dict:
        """분야별 분리 평가 후 평균 MAPE 반환."""
        all_mapes: list[float] = []
        for field in df["field"].unique():
            field_df = df[df["field"] == field].sort_values("date").reset_index(drop=True)
            X_raw, y_raw = self._prepare_arrays(field_df)
            all_mapes.extend(self._evaluate_fold(X_raw, y_raw, n_splits))
        avg_mape = float(np.mean(all_mapes)) if all_mapes else float("nan")
        if self._mape is None:
            self._mape = avg_mape
        return {"mape": avg_mape, "n_splits": n_splits}

    def save(self, path: str, version: int, df: pd.DataFrame | None = None) -> None:
        """모델 가중치 + 스케일러를 저장.

        Args:
            path: 저장 루트 경로 (예: edupulse/model/saved/lstm)
            version: 버전 번호
            df: 학습 DataFrame (메타데이터 생성용, None이면 메타데이터 생략)
        """
        import joblib

        torch = _get_torch()

        if self._model is None:
            raise RuntimeError("저장할 모델이 없습니다. train()을 먼저 호출하세요.")

        save_dir = Path(path) / f"v{version}"
        save_dir.mkdir(parents=True, exist_ok=True)

        torch.save(self._model.state_dict(), save_dir / "model.pt")
        joblib.dump(
            {
                "scaler_X": self._scaler_X,
                "scaler_y": self._scaler_y,
                "mape": self._mape,
            },
            save_dir / "scalers.joblib",
        )

        if df is not None:
            from datetime import datetime, timezone

            data_info = _extract_data_info(df)
            metadata = ModelMetadata(
                model_name="lstm",
                version=version,
                trained_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                data_rows=data_info["data_rows"],
                data_date_range=data_info["data_date_range"],
                feature_columns=[c for c in FEATURE_COLUMNS if c in df.columns],
                hyperparameters={
                    "sequence_length": SEQUENCE_LENGTH,
                    "hidden_size": HIDDEN_SIZE,
                    "num_layers": NUM_LAYERS,
                    "dropout": DROPOUT,
                    "batch_size": BATCH_SIZE,
                    "input_size": INPUT_SIZE,
                    "patience": PATIENCE,
                    "scheduler_factor": SCHEDULER_FACTOR,
                    "scheduler_patience": SCHEDULER_PATIENCE,
                    "min_lr": MIN_LR,
                    "val_ratio": VAL_RATIO,
                },
                mape=self._mape,
                fields=data_info["fields"],
                package_versions={
                    "torch": _get_package_version("torch"),
                    "scikit-learn": _get_package_version("scikit-learn"),
                },
            )
            save_metadata(path, version, metadata)

    def load(self, path: str, version: int) -> None:
        """저장된 가중치와 스케일러 로딩.

        Args:
            path: 저장 루트 경로 (예: edupulse/model/saved/lstm)
            version: 버전 번호
        """
        import joblib

        torch = _get_torch()

        load_dir = Path(path) / f"v{version}"
        model_pt = load_dir / "model.pt"
        scalers_path = load_dir / "scalers.joblib"

        if not model_pt.exists():
            raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {model_pt}")
        if not scalers_path.exists():
            raise FileNotFoundError(f"스케일러 파일을 찾을 수 없습니다: {scalers_path}")

        device = get_device()

        _check_feature_compatibility(path, version, FEATURE_COLUMNS)

        self._model = self._make_model().to(device)
        self._model.load_state_dict(
            torch.load(model_pt, map_location=device)
        )
        self._model.eval()

        data = joblib.load(scalers_path)
        self._scaler_X = data["scaler_X"]
        self._scaler_y = data["scaler_y"]
        self._mape = data.get("mape")
        self._is_fitted = True

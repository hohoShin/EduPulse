"""LSTM 수요 예측 모델 (MacBook M4 전용 학습, Droplet 추론 가능)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import MinMaxScaler

from edupulse.constants import classify_demand
from edupulse.model.base import BaseForecaster, PredictionResult
from edupulse.model.utils import get_device
from edupulse.model.xgboost_model import FEATURE_COLUMNS, TARGET_COLUMN

SEQUENCE_LENGTH = 4
BATCH_SIZE = 32
HIDDEN_SIZE = 64
NUM_LAYERS = 2
DROPOUT = 0.2
INPUT_SIZE = len(FEATURE_COLUMNS)  # 9


def _get_torch():
    """torch import를 런타임에 시도. Droplet(torch 미설치) 환경에서도 안전."""
    try:
        import torch
        return torch
    except ImportError as exc:
        raise ImportError(
            "PyTorch가 설치되어 있지 않습니다. "
            "MacBook에서 'pip install torch'를 실행하세요."
        ) from exc


class EnrollmentLSTM:
    """nn.Module 래퍼. torch import를 지연 평가하여 Droplet 호환성 유지."""

    def __new__(cls, *args, **kwargs):  # noqa: D102
        torch = _get_torch()
        nn = torch.nn

        class _LSTMModule(nn.Module):
            """LSTM(input_size=9, hidden=64, layers=2, dropout=0.2) → Linear(64,1)."""

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
                out, _ = self.lstm(x)          # (batch, seq, hidden)
                last = out[:, -1, :]           # 마지막 타임스텝
                return self.fc(last)           # (batch, 1)

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

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    def _prepare_arrays(
        self, df: pd.DataFrame
    ) -> tuple[np.ndarray, np.ndarray]:
        """DataFrame → 정규화된 (X, y) numpy 배열 반환."""
        available = [c for c in FEATURE_COLUMNS if c in df.columns]
        X_raw = df[available].fillna(0).values.astype(np.float32)
        y_raw = df[TARGET_COLUMN].values.astype(np.float32).reshape(-1, 1)
        return X_raw, y_raw

    def _make_model(self):
        """EnrollmentLSTM 인스턴스 생성 (torch 필요)."""
        return EnrollmentLSTM()

    # ------------------------------------------------------------------
    # BaseForecaster 구현
    # ------------------------------------------------------------------

    def train(
        self,
        df: pd.DataFrame,
        epochs: int = 50,
        learning_rate: float = 1e-3,
    ) -> None:
        """MinMaxScaler 정규화 → 시퀀스 생성 → LSTM 학습.

        Args:
            df: FEATURE_COLUMNS + TARGET_COLUMN 포함 DataFrame
            epochs: 학습 에포크 수
            learning_rate: Adam 옵티마이저 학습률
        """
        torch = _get_torch()
        device = get_device()

        X_raw, y_raw = self._prepare_arrays(df)

        # 스케일러 fit — 전체 데이터 기준
        X_scaled = self._scaler_X.fit_transform(X_raw)
        y_scaled = self._scaler_y.fit_transform(y_raw).ravel()

        xs, ys = _build_sequences(X_scaled, y_scaled, SEQUENCE_LENGTH)
        if len(xs) == 0:
            raise ValueError(
                f"시퀀스 생성 실패: 데이터({len(df)}행)가 "
                f"sequence_length({SEQUENCE_LENGTH})보다 많아야 합니다."
            )

        X_tensor = torch.tensor(xs).to(device)
        y_tensor = torch.tensor(ys).unsqueeze(1).to(device)

        self._model = self._make_model().to(device)
        optimizer = torch.optim.Adam(self._model.parameters(), lr=learning_rate)
        criterion = torch.nn.MSELoss()

        self._model.train()
        dataset = torch.utils.data.TensorDataset(X_tensor, y_tensor)
        loader = torch.utils.data.DataLoader(
            dataset, batch_size=BATCH_SIZE, shuffle=False
        )

        for _ in range(epochs):
            for X_batch, y_batch in loader:
                optimizer.zero_grad()
                preds = self._model(X_batch)
                loss = criterion(preds, y_batch)
                loss.backward()
                optimizer.step()

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

        available = [c for c in FEATURE_COLUMNS if c in features.columns]
        X_raw = features[available].fillna(0).values.astype(np.float32)
        X_scaled = self._scaler_X.transform(X_raw)

        # sequence_length에 맞게 패딩 (추론 시 데이터가 부족할 수 있음)
        if len(X_scaled) < SEQUENCE_LENGTH:
            pad = np.zeros(
                (SEQUENCE_LENGTH - len(X_scaled), X_scaled.shape[1]),
                dtype=np.float32,
            )
            X_scaled = np.vstack([pad, X_scaled])

        # 마지막 SEQUENCE_LENGTH 행을 시퀀스로 사용
        seq = X_scaled[-SEQUENCE_LENGTH:]
        X_tensor = torch.tensor(seq).unsqueeze(0).to(device)  # (1, seq, feat)

        self._model.eval()
        with torch.no_grad():
            raw_scaled = self._model(X_tensor).item()

        # 역변환
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
        """TimeSeriesSplit K-Fold 교차검증. MAPE 반환.

        시계열 데이터는 절대 랜덤 셔플 금지.

        Args:
            df: FEATURE_COLUMNS + TARGET_COLUMN 포함 DataFrame
            n_splits: K-Fold 분할 수

        Returns:
            {'mape': float, 'n_splits': int}
        """
        torch = _get_torch()

        X_raw, y_raw = self._prepare_arrays(df)
        tscv = TimeSeriesSplit(n_splits=n_splits)
        mapes = []

        for train_idx, val_idx in tscv.split(X_raw):
            X_tr, X_val = X_raw[train_idx], X_raw[val_idx]
            y_tr, y_val = y_raw[train_idx], y_raw[val_idx]

            # fold 단위 스케일러 (데이터 누수 방지)
            scaler_X = MinMaxScaler()
            scaler_y = MinMaxScaler()
            X_tr_s = scaler_X.fit_transform(X_tr)
            y_tr_s = scaler_y.fit_transform(y_tr).ravel()
            X_val_s = scaler_X.transform(X_val)

            xs_tr, ys_tr = _build_sequences(X_tr_s, y_tr_s, SEQUENCE_LENGTH)
            if len(xs_tr) == 0:
                continue

            device = get_device()
            X_t = torch.tensor(xs_tr).to(device)
            y_t = torch.tensor(ys_tr).unsqueeze(1).to(device)

            fold_model = self._make_model().to(device)
            opt = torch.optim.Adam(fold_model.parameters(), lr=1e-3)
            crit = torch.nn.MSELoss()

            fold_model.train()
            dataset = torch.utils.data.TensorDataset(X_t, y_t)
            loader = torch.utils.data.DataLoader(
                dataset, batch_size=BATCH_SIZE, shuffle=False
            )
            for _ in range(30):  # 빠른 fold 학습
                for Xb, yb in loader:
                    opt.zero_grad()
                    loss = crit(fold_model(Xb), yb)
                    loss.backward()
                    opt.step()

            # 검증
            fold_model.eval()
            preds_scaled, actuals = [], []
            for i in range(len(X_val_s) - SEQUENCE_LENGTH):
                seq = X_val_s[i : i + SEQUENCE_LENGTH]
                X_inf = torch.tensor(seq).unsqueeze(0).to(device)
                with torch.no_grad():
                    p = fold_model(X_inf).item()
                pred_inv = float(scaler_y.inverse_transform([[p]])[0][0])
                act_inv = float(y_val[i + SEQUENCE_LENGTH][0])
                preds_scaled.append(pred_inv)
                actuals.append(act_inv)

            actuals = np.array(actuals)
            preds_scaled = np.array(preds_scaled)
            nonzero = actuals != 0
            if nonzero.any():
                fold_mape = float(
                    np.mean(
                        np.abs(
                            (actuals[nonzero] - preds_scaled[nonzero])
                            / actuals[nonzero]
                        )
                    )
                    * 100
                )
                mapes.append(fold_mape)

        avg_mape = float(np.mean(mapes)) if mapes else float("nan")
        self._mape = avg_mape
        return {"mape": avg_mape, "n_splits": n_splits}

    # ------------------------------------------------------------------
    # 저장 / 로딩
    # ------------------------------------------------------------------

    def save(self, path: str, version: int) -> None:
        """모델 가중치 + 스케일러를 저장.

        Args:
            path: 저장 루트 경로 (예: edupulse/model/saved/lstm)
            version: 버전 번호
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

# CLAUDE.md — EduPulse Coding Agent Guide

This file provides context and instructions for the coding agent working on the EduPulse project.

---

## Project Overview

**EduPulse** is an AI-based course enrollment demand forecasting solution for academies specializing in coding, security, game development, and art.
The core goal is to predict per-cohort enrollment demand in advance by integrating internal and external data — including enrollment history, search trends, and job postings — and automatically connecting those predictions to operational, marketing, and strategic decision-making.

---

## Tech Stack

| Area | Technology |
|---|---|
| Data Collection | Python, BeautifulSoup, Selenium, Naver API, Google Trends API |
| Preprocessing | Pandas, NumPy, scikit-learn |
| Modeling | Prophet, PyTorch (LSTM), XGBoost |
| Backend | FastAPI, Docker |
| Frontend | React, Recharts, Plotly |
| Data Storage | PostgreSQL |

---

## Directory Structure

```
edupulse/                              # Project root
│
├── edupulse/                          # Main Python package
│   ├── config.py                      # Environment settings (DB, API keys)
│   ├── constants.py                   # Constants (fields, keywords)
│   ├── database.py                    # DB connection and session management
│   │
│   ├── api/                           # Backend API server
│   │   ├── main.py                    # FastAPI app entry point
│   │   ├── dependencies.py            # Dependency injection
│   │   ├── middleware.py              # Middleware (CORS, etc.)
│   │   ├── routers/
│   │   │   ├── demand.py              # Demand prediction endpoint
│   │   │   ├── schedule.py            # Instructor scheduling endpoint
│   │   │   ├── marketing.py           # Marketing timing endpoint
│   │   │   └── health.py              # Health check endpoint
│   │   └── schemas/                   # Pydantic request/response schemas
│   │       ├── common.py              # Common schemas
│   │       ├── demand.py
│   │       ├── marketing.py
│   │       └── schedule.py
│   │
│   ├── collection/                    # Data collection
│   │   └── api/                       # External API integration
│   │       ├── collect_search_trends.py  # Collection orchestrator (CLI entry point)
│   │       ├── naver_datalab.py       # Naver DataLab search volume (primary source)
│   │       ├── google_trends.py       # Google Trends (cache-only)
│   │       ├── keywords.py            # Field-to-keyword mapping (Korean/English)
│   │       └── quota.py               # Naver API daily quota tracker (KST reset)
│   │
│   ├── data/                          # Data storage and generators
│   │   ├── generators/                # Synthetic data generators
│   │   │   ├── enrollment_generator.py  # Enrollment history synthesis
│   │   │   ├── external_generator.py    # External data synthesis
│   │   │   └── run_all.py             # Run all synthetic data generation
│   │   ├── raw/                       # Raw collected data
│   │   │   ├── internal/              # Internal data (enrollment, consultation logs)
│   │   │   └── external/              # External data (search trends, job postings)
│   │   ├── processed/                 # Preprocessed data
│   │   └── warehouse/                 # Final dataset for model training
│   │
│   ├── db_models/                     # SQLAlchemy DB models
│   │   ├── course.py                  # Course model
│   │   ├── enrollment.py              # Enrollment model
│   │   └── prediction.py              # Prediction result model
│   │
│   ├── model/                         # AI modeling
│   │   ├── base.py                    # Model base class
│   │   ├── train.py                   # Model training
│   │   ├── predict.py                 # Demand prediction (High/Mid/Low + count)
│   │   ├── evaluate.py                # MAPE evaluation, time-series K-Fold
│   │   ├── retrain.py                 # Automatic retraining scheduler
│   │   ├── ensemble.py                # Ensemble model
│   │   ├── prophet_model.py           # Prophet model
│   │   ├── lstm_model.py              # LSTM model
│   │   ├── xgboost_model.py           # XGBoost model
│   │   ├── utils.py                   # Model utilities
│   │   └── saved/                     # Saved trained models
│   │       ├── prophet/
│   │       ├── lstm/
│   │       └── xgboost/
│   │
│   └── preprocessing/                 # Data preprocessing
│       ├── cleaner.py                 # Missing value interpolation, outlier handling
│       ├── transformer.py             # Time-series alignment, lag feature generation
│       └── merger.py                  # Multi-source data join and integration
│
├── alembic/                           # DB migrations
│   └── versions/
│       └── 001_initial.py             # Initial table creation
│
├── scripts/                           # Execution scripts
│   ├── run_pipeline.py                # Full pipeline execution
│   ├── deploy.sh                      # Deployment script
│   └── transfer_lstm.sh               # LSTM model transfer to server
│
├── tests/                             # Tests
│   ├── conftest.py                    # Test fixtures
│   ├── test_collection.py             # Data collection tests
│   ├── test_preprocessing.py          # Preprocessing tests
│   ├── test_model.py                  # Model tests
│   ├── test_demand.py                 # Demand prediction API tests
│   └── test_health.py                 # Health check tests
│
├── frontend/                          # Dashboard frontend (planned)
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx          # Main prediction dashboard
│   │   │   ├── Simulator.jsx          # New course demand simulator
│   │   │   └── Reports.jsx            # Strategic reports
│   │   └── components/
│   │       ├── DemandChart.jsx        # Demand prediction visualization
│   │       ├── AlertPanel.jsx         # Closure risk and ad timing alerts
│   │       └── ScheduleBoard.jsx      # Instructor assignment board
│   └── public/
│
├── notebooks/                         # Jupyter notebooks for analysis
│   ├── eda.ipynb                      # Exploratory data analysis
│   ├── feature_engineering.ipynb      # Feature experimentation
│   ├── model_comparison.ipynb         # Model performance comparison
│   ├── model_experiments.ipynb        # Hyperparameter tuning experiments
│   └── pipeline_test.ipynb            # End-to-end pipeline test
│
├── docs/                              # Project documentation
│   ├── ai_reports/                    # AI usage reports (#1~#7 + model guide)
│   ├── ai_plans/                      # AI planning documents
│   ├── ai_collaboration_index.md      # AI collaboration document index
│   └── 합성_데이터_생성_가이드.md        # Synthetic data generation guide
│
├── Dockerfile                         # Docker image build
├── docker-compose.yml                 # Service container config
├── docker-compose.dev.yml             # Dev Docker config
├── pyproject.toml                     # Project metadata and build settings
├── requirements.txt                   # Shared Python packages
├── requirements-dev.txt               # Local dev only packages
├── requirements-server.txt            # Server only packages
├── .env.example                       # Environment variable template
└── README.md
```

---

## Data Pipeline

```
[Collection] → [Preprocessing] → [Modeling] → [Service Output]
```

### Collection — Key Notes
- Always check `robots.txt` before crawling; maintain a minimum 1–2 second delay between requests
- Naver DataLab API has a daily call limit (1000/day) — quota tracked in `data/raw/external/.naver_quota.json` (KST reset)
- Include the collection date range in cache filenames (e.g. `naver_coding_20250101_20250407.json`)
- **Naver = primary data source** for `search_trends.csv`; Google Trends = cache-only for future research
- Fallback chain: Naver API → cached Naver JSON → skip (Google never used in pipeline output)
- Run collection: `python -m edupulse.collection.api.collect_search_trends`
- Output writes to same path as synthetic generator (`data/raw/external/search_trends.csv`) — drop-in replacement

### Preprocessing — Key Notes
- Apply linear interpolation (`interpolate(method='linear')`) first for missing values in time-series data
- Use IQR as the default outlier detection method; supplement with Z-score for strongly seasonal data
- Generate lag features at 1-week, 2-week, 4-week, and 8-week intervals; select based on correlation analysis
- Standardize the date column to `date(YYYY-MM-DD)` format when merging internal and external data

### Modeling — Key Notes
- Train all three model candidates (Prophet, LSTM, XGBoost) and compare using MAPE
- Use time-series K-Fold for train/validation splits — random shuffling is strictly prohibited
- Prediction output must always return both the **demand tier (High/Mid/Low)** and the **estimated enrollment count**
- Save models under `model/saved/{model_name}/v{version_number}/` for version control

---

## Core Service Logic

### Demand Prediction API (`routers/demand.py`)
- Input: course name, scheduled start date, course field (coding / security / game / art)
- Output: estimated enrollment count, demand tier (High/Mid/Low), prediction confidence interval

### Instructor Scheduling API (`routers/schedule.py`)
- Takes demand prediction results and automatically calculates required number of instructors and classrooms
- Returns an optimal assignment plan by combining with instructor availability from the DB

### Marketing Timing API (`routers/marketing.py`)
- Returns recommended ad launch timing (N weeks before course start) based on demand predictions
- Suggests dynamic early-bird period length and discount rate based on demand tier

---

## Environment Variables (.env)

```
# DB
DATABASE_URL=postgresql://user:password@localhost:5432/edupulse

# External API
NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=

# Server
API_HOST=0.0.0.0
API_PORT=8000
```

---

## Coding Conventions

- Python: follow PEP8; docstrings are required for all functions and classes
- Variable names: snake_case (`demand_score`, `enrollment_count`)
- React components: PascalCase (`DemandChart`, `AlertPanel`)
- API router paths: include version prefix `/api/v1/{resource}`
- Commit messages: use prefixes `feat:`, `fix:`, `data:`, `model:`, `docs:`

---

## Git Rules

### Branch Strategy

- `main` — production-ready code only
- `dev` — integration branch for development
- Feature branches from `dev`, merge back to `dev` via PR

| Prefix | Usage | Example |
|---|---|---|
| `feat/` | New feature (frontend + backend 포함 가능) | `feat/demand-api` |
| `fix/` | Bug fix | `fix/prophet-date-format` |
| `data/` | Data collection, preprocessing | `data/job-crawler` |
| `model/` | Model training, tuning | `model/lstm-tuning` |

### Commit Message Format

```
<prefix>: <short summary>

<optional body — explain why, not what>
```

**Prefixes:** `feat:`, `fix:`, `data:`, `model:`, `docs:`, `refactor:`, `test:`, `chore:`

### Commit Rules

- Summary line under 72 characters
- One logical change per commit — do not mix unrelated changes
- Never commit `.env`, API keys, model weight files (`*.pt`, `*.pkl`), or large data files
- Always verify `git diff` before committing

### PR & Merge Rules

- All merges to `main` must go through a PR
- PR title follows the same prefix convention as commit messages
- Squash merge for feature branches to keep `main` history clean
- Delete the branch after merge

### .gitignore Essentials

Ensure the following are always excluded:

```
.env
__pycache__/
*.pyc
model/saved/**/*.pt
model/saved/**/*.pkl
data/raw/
data/processed/
data/warehouse/
*.csv
*.parquet
node_modules/
.DS_Store
```

---

## Environment Strategy — Local vs. Server

Two separate environments are used. Keep their roles clearly separated.

| | M4 MacBook (Local) | Digital Ocean Droplet |
|---|---|---|
| **Purpose** | Development, experimentation, LSTM training | XGBoost & Prophet auto-retraining, API serving |
| **Acceleration** | MPS (Apple Silicon GPU) | CPU |
| **Spec** | M4 | 1 vCPU / 2GB RAM |

### Where Each Model Is Trained

```
M4 MacBook  → Train LSTM manually, then transfer model file to Droplet via scp
              scp model/saved/lstm/model.pt user@your-droplet-ip:/app/model/saved/lstm/
Droplet     → Auto-retrain XGBoost and Prophet (retrain.py)
              Save retrained models locally under model/saved/
```

The Droplet (1 vCPU / 2GB RAM) is not capable of retraining LSTM.
Follow this flow: **train on MacBook → transfer via scp → load and serve on Droplet**.

### Device Detection — Never Hardcode

```python
import torch

def get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")       # Future-proofing for GPU server plan
    elif torch.backends.mps.is_available():
        return torch.device("mps")        # M4 MacBook
    else:
        return torch.device("cpu")        # Droplet default

device = get_device()
```

### Requirements Files

```
requirements.txt          # Shared packages
requirements-dev.txt      # Local dev only (jupyter, plotly, etc.)
requirements-server.txt   # Droplet only (lightweight, no jupyter)
```

### PyTorch MPS Setup (MacBook Local Only)

```python
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"Using device: {device}")  # Verify before proceeding

model = model.to(device)

# Move data to the same device
X_train = X_train.to(device)
y_train = y_train.to(device)
```

### Package Installation

```bash
# XGBoost — native Apple Silicon support, no extra config needed
pip install xgboost

# Prophet — try pip first; fall back to conda if build fails
pip install prophet
# If pip fails (C++ build errors on ARM64):
conda install -c conda-forge prophet

# PyTorch — MPS-supported build
pip install torch torchvision
```

### Memory Notes

M4 uses a Unified Memory architecture where RAM and GPU memory are shared.
Using large batch sizes during LSTM training may cause memory pressure.

```python
# Recommended starting batch size
BATCH_SIZE = 32  # Increase to 64 if memory allows
```

### Estimated Training Times

| Model | M4 MacBook | Droplet (1 vCPU / 2GB) |
|---|---|---|
| XGBoost | 30s – 2min | 2 – 10min |
| Prophet | 3 – 10min | 10 – 30min |
| LSTM | 10 – 30min | ❌ Manual training only |

---

## Common Pitfalls

- Never randomly shuffle time-series data — this causes data leakage
- Never hardcode API keys in source code — always load from `.env`
- Always preserve raw crawled data under `raw/`; write preprocessed output separately to `processed/`
- Prophet requires columns to be named exactly `ds` (date) and `y` (value)
- Inside Docker containers, reference PostgreSQL by its service name (`db`), not `localhost`
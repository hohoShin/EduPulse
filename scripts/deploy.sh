#!/usr/bin/env bash
set -euo pipefail
# Usage: ./scripts/deploy.sh user@droplet-ip

REMOTE=$1
PROJECT_DIR=/app

ssh $REMOTE "cd $PROJECT_DIR && git pull origin main"
ssh $REMOTE "cd $PROJECT_DIR && docker-compose up --build -d"
ssh $REMOTE "docker-compose -f $PROJECT_DIR/docker-compose.yml exec api python -m edupulse.model.retrain --model xgboost --dry-run"
echo "Deploy complete."

#!/usr/bin/env bash
set -euo pipefail
# Usage: ./scripts/transfer_lstm.sh user@droplet-ip
REMOTE=$1
scp edupulse/model/saved/lstm/model.pt $REMOTE:/app/edupulse/model/saved/lstm/
echo "LSTM model transferred."

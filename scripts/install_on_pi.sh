#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/opt/elephant-detector"
SERVICE_NAME="elephant-detector.service"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}"
TARGET_USER="${SUDO_USER:-pi}"

if [[ $EUID -ne 0 ]]; then
  echo "Please run as root: sudo bash scripts/install_on_pi.sh"
  exit 1
fi

if ! id "$TARGET_USER" >/dev/null 2>&1; then
  echo "ERROR: user '$TARGET_USER' not found. Create it first or run with: sudo -u <user> sudo bash scripts/install_on_pi.sh"
  exit 1
fi

if [[ ! -f "$PWD/.env" ]]; then
  echo "ERROR: .env not found. Run: bash scripts/setup_wizard.sh"
  exit 1
fi

echo "[1/8] Installing system dependencies..."
apt-get update
apt-get install -y python3 python3-venv python3-pip ffmpeg libatlas-base-dev rsync

echo "[2/8] Syncing project to $PROJECT_DIR ..."
mkdir -p "$PROJECT_DIR"
rsync -a --delete \
  --exclude '.git/' \
  --exclude '.venv/' \
  --exclude '__pycache__/' \
  --exclude 'logs/' \
  --exclude 'snapshots/' \
  ./ "$PROJECT_DIR"/
chown -R "$TARGET_USER":"$TARGET_USER" "$PROJECT_DIR"

mkdir -p "$PROJECT_DIR/logs" "$PROJECT_DIR/snapshots"
chown -R "$TARGET_USER":"$TARGET_USER" "$PROJECT_DIR/logs" "$PROJECT_DIR/snapshots"

echo "[3/8] Creating virtual environment and installing Python packages..."
sudo -u "$TARGET_USER" bash -lc "cd '$PROJECT_DIR' && python3 -m venv .venv && source .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

echo "[4/8] Downloading YOLO model (first run cache warm-up)..."
sudo -u "$TARGET_USER" bash -lc "cd '$PROJECT_DIR' && source .venv/bin/activate && python - <<'PY'
from ultralytics import YOLO
YOLO('yolov8n.pt')
print('Model ready.')
PY"

echo "[5/8] Preparing systemd service for user '$TARGET_USER'..."
cp "$PROJECT_DIR/systemd/$SERVICE_NAME" "$SERVICE_FILE"
sed -i "s|^User=.*|User=${TARGET_USER}|" "$SERVICE_FILE"


echo "[6/8] Reloading and enabling service..."
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

echo "[7/8] Starting service..."
systemctl restart "$SERVICE_NAME"

echo "[8/8] Done"
echo "Status: systemctl status $SERVICE_NAME --no-pager"
echo "Logs:   journalctl -u $SERVICE_NAME -f"

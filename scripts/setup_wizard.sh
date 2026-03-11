#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="$ROOT_DIR/.env"
EXAMPLE_FILE="$ROOT_DIR/.env.example"

if [[ ! -f "$EXAMPLE_FILE" ]]; then
  echo "Missing $EXAMPLE_FILE"
  exit 1
fi

if [[ -f "$ENV_FILE" ]]; then
  read -r -p ".env already exists. Overwrite? (y/N): " overwrite
  if [[ ! "$overwrite" =~ ^[Yy]$ ]]; then
    echo "Keeping existing .env"
  else
    rm -f "$ENV_FILE"
  fi
fi

if [[ ! -f "$ENV_FILE" ]]; then
  cp "$EXAMPLE_FILE" "$ENV_FILE"
fi

ask_required() {
  local key="$1"
  local prompt="$2"
  local value
  while true; do
    read -r -p "$prompt: " value
    if [[ -n "$value" ]]; then
      break
    fi
    echo "This value is required."
  done
  sed -i "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
}

ask_optional() {
  local key="$1"
  local prompt="$2"
  local current
  current="$(awk -F= -v k="$key" '$1==k{print substr($0, index($0,$2))}' "$ENV_FILE")"
  read -r -p "$prompt [$current]: " value
  if [[ -n "${value:-}" ]]; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
  fi
}

echo "\n=== Elephant Detector Setup Wizard ==="
ask_required "RTSP_URL" "Enter RTSP URL (example: rtsp://user:pass@ip:554/stream1)"
ask_required "TELEGRAM_BOT_TOKEN" "Enter Telegram bot token"
ask_required "TELEGRAM_CHAT_ID" "Enter Telegram chat id"

ask_optional "CONFIDENCE_THRESHOLD" "Confidence threshold (0.1-0.9)"
ask_optional "FRAMES_BETWEEN_INFERENCE" "Frames between inference (higher=less CPU)"
ask_optional "NOTIFICATION_COOLDOWN_SEC" "Notification cooldown in seconds"

echo "\nSaved config to $ENV_FILE"
echo "Next step on Raspberry Pi:"
echo "  sudo bash scripts/install_on_pi.sh"

# Elephant Detection System (IP Camera + Raspberry Pi + Telegram)

This repository is prepared so you can:
1) **Download or copy it**,
2) Fill your camera/Telegram values,
3) Run one install command,
4) Get automatic elephant alerts on Telegram.

## Super Quick Start (copy-paste)

```bash
git clone <YOUR_REPO_URL> elephant-detector
cd elephant-detector
bash scripts/setup_wizard.sh
sudo bash scripts/install_on_pi.sh
```

After that:

```bash
systemctl status elephant-detector.service --no-pager
journalctl -u elephant-detector.service -f
```

---

## What this project includes

- `app/main.py` → detector app (RTSP stream + YOLO + Telegram alerts)
- `scripts/setup_wizard.sh` → interactive `.env` creator (easy setup)
- `scripts/install_on_pi.sh` → full Raspberry Pi installer
- `systemd/elephant-detector.service` → run automatically on boot
- `run_detector.sh` → manual run script

---

## Requirements

- Raspberry Pi 4 (recommended 4GB+)
- Raspberry Pi OS 64-bit
- IP camera with RTSP stream URL
- Telegram account

---

## Telegram bot setup (one time)

1. Open Telegram → message `@BotFather`
2. Run `/newbot`
3. Copy generated **bot token**
4. Send any message to your bot once
5. Get your chat ID:

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates"
```

Find the numeric value in `"chat":{"id":...}`.

---

## Manual configuration (if not using wizard)

```bash
cp .env.example .env
nano .env
```

Required values:
- `RTSP_URL`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

---

## Service commands

```bash
sudo systemctl restart elephant-detector.service
sudo systemctl stop elephant-detector.service
systemctl status elephant-detector.service --no-pager
journalctl -u elephant-detector.service -f
```

---

## Tuning for Raspberry Pi

In `.env`:

- `FRAMES_BETWEEN_INFERENCE=6` (or higher) → lower CPU usage
- `CONFIDENCE_THRESHOLD=0.50` (or higher) → fewer false alerts
- `NOTIFICATION_COOLDOWN_SEC=60` (or higher) → less alert spam

---

## Output files

- Snapshots: `/opt/elephant-detector/snapshots/`
- Logs: `/opt/elephant-detector/logs/detector.log`

---

## Troubleshooting

### Camera stream fails
- Test your RTSP URL in VLC / ffplay first
- Check username/password and stream path
- Ensure camera and Pi are on same network

### Telegram messages not arriving
- Verify token/chat ID in `.env`
- Ensure you messaged the bot at least once
- Check service logs

### High CPU usage
- Increase `FRAMES_BETWEEN_INFERENCE`
- Lower camera stream resolution
- Keep `MODEL_PATH=yolov8n.pt`

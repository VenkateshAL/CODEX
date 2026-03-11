# Elephant Detection Proof of Concept (USB Camera, Ubuntu)

This repository now contains a quick **real-time elephant detection PoC** using:
- a USB camera (via OpenCV), and
- a pretrained YOLOv8 model (`ultralytics`) trained on COCO classes.

`elephant` is part of COCO, so this is a practical baseline prototype.

## 1) Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 2) Run detection from your USB camera

```bash
python3 elephant_detector.py --camera-index 0
```

Useful flags:

- `--camera-index`: switch if your USB camera is not index `0`.
- `--confidence`: adjust detection sensitivity (default `0.35`).
- `--model`: choose model size, e.g. `yolov8s.pt` for potentially better accuracy.
- `--save-alert-frames`: save frames with elephant detections into `./alerts`.

Example:

```bash
python3 elephant_detector.py --camera-index 0 --confidence 0.4 --save-alert-frames
```

## 3) Notes for real-world reliability

For this PoC stage:
- good daylight and clear elephant visibility matter a lot,
- false positives are possible (especially with small models like `yolov8n`),
- inference speed depends on CPU/GPU.

For production next steps you might add:
- zone-based alerting (only if elephant enters a region),
- alert cooldown logic (avoid duplicate alerts),
- Telegram/SMS notification integration,
- model fine-tuning with your local camera footage.

#!/usr/bin/env python3
"""USB-camera elephant detection proof of concept.

This script uses a pretrained YOLOv8 COCO model and only surfaces detections
for the `elephant` class. It is designed for quick local testing on Ubuntu
with a USB webcam.
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import cv2
from ultralytics import YOLO

ELEPHANT_CLASS_NAME = "elephant"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run real-time elephant detection from a USB camera."
    )
    parser.add_argument(
        "--camera-index",
        type=int,
        default=0,
        help="OpenCV camera index for the USB camera (default: 0).",
    )
    parser.add_argument(
        "--model",
        default="yolov8n.pt",
        help="Path or model name understood by ultralytics YOLO (default: yolov8n.pt).",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.35,
        help="Minimum confidence to display elephant detections (default: 0.35).",
    )
    parser.add_argument(
        "--save-alert-frames",
        action="store_true",
        help="Save frames containing elephants into ./alerts.",
    )
    return parser.parse_args()


def ensure_alert_dir(enabled: bool) -> Path | None:
    if not enabled:
        return None
    alert_dir = Path("alerts")
    alert_dir.mkdir(parents=True, exist_ok=True)
    return alert_dir


def main() -> None:
    args = parse_args()
    model = YOLO(args.model)

    cap = cv2.VideoCapture(args.camera_index)
    if not cap.isOpened():
        raise RuntimeError(
            f"Unable to open camera index {args.camera_index}. "
            "Check USB connection and camera permissions."
        )

    alert_dir = ensure_alert_dir(args.save_alert_frames)
    print("Running elephant detector. Press 'q' to quit.")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("Warning: failed to read frame from camera.")
            continue

        results = model.predict(frame, conf=args.confidence, verbose=False)
        elephant_found = False

        for result in results:
            names = result.names
            for box in result.boxes:
                class_id = int(box.cls.item())
                class_name = names[class_id]
                if class_name != ELEPHANT_CLASS_NAME:
                    continue

                elephant_found = True
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                confidence = float(box.conf.item())

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 140, 255), 2)
                label = f"ELEPHANT {confidence:.2f}"
                cv2.putText(
                    frame,
                    label,
                    (x1, max(y1 - 10, 0)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 140, 255),
                    2,
                )

        status_text = "ELEPHANT DETECTED" if elephant_found else "No elephant"
        status_color = (0, 0, 255) if elephant_found else (0, 255, 0)
        cv2.putText(
            frame,
            status_text,
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            status_color,
            2,
        )

        if elephant_found and alert_dir is not None:
            timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            cv2.imwrite(str(alert_dir / f"elephant_{timestamp}.jpg"), frame)

        cv2.imshow("Elephant Detector POC", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

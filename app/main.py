import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import cv2
import requests
from dotenv import load_dotenv
from ultralytics import YOLO


@dataclass
class Settings:
    rtsp_url: str
    model_path: str
    confidence_threshold: float
    target_class_name: str
    frames_between_inference: int
    notification_cooldown_sec: int
    telegram_bot_token: str
    telegram_chat_id: str
    snapshots_dir: Path
    logs_dir: Path
    image_quality: int

    @staticmethod
    def from_env() -> "Settings":
        load_dotenv()

        rtsp_url = os.getenv("RTSP_URL", "").strip()
        if not rtsp_url:
            raise ValueError("RTSP_URL is required")

        telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        if not telegram_bot_token or not telegram_chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required")

        snapshots_dir = Path(os.getenv("SNAPSHOTS_DIR", "./snapshots")).resolve()
        logs_dir = Path(os.getenv("LOGS_DIR", "./logs")).resolve()
        snapshots_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)

        return Settings(
            rtsp_url=rtsp_url,
            model_path=os.getenv("MODEL_PATH", "yolov8n.pt"),
            confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "0.45")),
            target_class_name=os.getenv("TARGET_CLASS_NAME", "elephant").lower(),
            frames_between_inference=max(1, int(os.getenv("FRAMES_BETWEEN_INFERENCE", "4"))),
            notification_cooldown_sec=max(0, int(os.getenv("NOTIFICATION_COOLDOWN_SEC", "45"))),
            telegram_bot_token=telegram_bot_token,
            telegram_chat_id=telegram_chat_id,
            snapshots_dir=snapshots_dir,
            logs_dir=logs_dir,
            image_quality=max(1, min(100, int(os.getenv("SNAPSHOT_IMAGE_QUALITY", "90")))),
        )


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_base = f"https://api.telegram.org/bot{self.bot_token}"

    def send_message(self, text: str) -> None:
        url = f"{self.api_base}/sendMessage"
        response = requests.post(
            url,
            data={"chat_id": self.chat_id, "text": text},
            timeout=15,
        )
        response.raise_for_status()

    def send_photo(self, caption: str, photo_path: Path) -> None:
        url = f"{self.api_base}/sendPhoto"
        with photo_path.open("rb") as photo_file:
            response = requests.post(
                url,
                data={"chat_id": self.chat_id, "caption": caption},
                files={"photo": photo_file},
                timeout=30,
            )
        response.raise_for_status()


def setup_logging(logs_dir: Path) -> None:
    log_file = logs_dir / "detector.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )


def open_camera_stream(rtsp_url: str) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open stream: {rtsp_url}")
    return cap


def extract_best_elephant_detection(results, target_class_name: str) -> Optional[tuple[float, tuple[int, int, int, int]]]:
    names = results.names
    for box in results.boxes:
        class_id = int(box.cls[0])
        class_name = names[class_id].lower()
        confidence = float(box.conf[0])
        if class_name == target_class_name:
            x1, y1, x2, y2 = [int(value) for value in box.xyxy[0]]
            return confidence, (x1, y1, x2, y2)
    return None


def draw_box(frame, box: tuple[int, int, int, int], label: str):
    x1, y1, x2, y2 = box
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 165, 255), 2)
    cv2.putText(frame, label, (x1, max(20, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)


def save_snapshot(frame, snapshots_dir: Path, image_quality: int) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    snapshot_path = snapshots_dir / f"elephant_{timestamp}.jpg"
    cv2.imwrite(str(snapshot_path), frame, [int(cv2.IMWRITE_JPEG_QUALITY), image_quality])
    return snapshot_path


def format_alert(confidence: float) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return f"🐘 Elephant detected!\nConfidence: {confidence:.2f}\nTime: {now}"


def run() -> None:
    settings = Settings.from_env()
    setup_logging(settings.logs_dir)

    logging.info("Starting detector with model=%s target=%s", settings.model_path, settings.target_class_name)
    model = YOLO(settings.model_path)
    notifier = TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id)

    last_notification_epoch = 0.0

    while True:
        cap = None
        try:
            cap = open_camera_stream(settings.rtsp_url)
            frame_count = 0

            while True:
                ok, frame = cap.read()
                if not ok or frame is None:
                    logging.warning("Stream frame read failed. Reconnecting in 3 seconds...")
                    time.sleep(3)
                    break

                frame_count += 1
                if frame_count % settings.frames_between_inference != 0:
                    continue

                results_list = model.predict(
                    source=frame,
                    conf=settings.confidence_threshold,
                    verbose=False,
                    imgsz=640,
                )
                if not results_list:
                    continue

                detection = extract_best_elephant_detection(results_list[0], settings.target_class_name)
                if detection is None:
                    continue

                confidence, box = detection
                now = time.time()
                if now - last_notification_epoch < settings.notification_cooldown_sec:
                    continue

                draw_box(frame, box, f"Elephant {confidence:.2f}")
                snapshot_path = save_snapshot(frame, settings.snapshots_dir, settings.image_quality)
                caption = format_alert(confidence)

                try:
                    notifier.send_photo(caption=caption, photo_path=snapshot_path)
                    logging.info("Alert sent successfully: %s", snapshot_path)
                except Exception:
                    logging.exception("Failed to send Telegram photo; sending text fallback")
                    try:
                        notifier.send_message(caption)
                    except Exception:
                        logging.exception("Fallback Telegram message also failed")

                last_notification_epoch = now

        except Exception:
            logging.exception("Fatal loop error. Retrying stream setup in 5 seconds")
            time.sleep(5)
        finally:
            if cap is not None:
                cap.release()


if __name__ == "__main__":
    run()

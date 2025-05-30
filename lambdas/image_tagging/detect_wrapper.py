from ultralytics import YOLO
import supervision as sv
import cv2 as cv
import os
from collections import Counter

model_path = os.path.join(os.path.dirname(__file__), "model", "model.pt")
model = YOLO(model_path)
class_dict = model.names

def detect_birds_from_image(image_path):
    """
    Detect birds from a single image.
    Returns: dict {bird_name: count}
    """
    img = cv.imread(image_path)
    if img is None:
        raise Exception("Image not loaded. Check path.")

    result = model(img)[0]
    detections = sv.Detections.from_ultralytics(result)
    detections = detections[detections.confidence > 0.5]

    class_ids = detections.class_id
    counts = Counter([class_dict[cid] for cid in class_ids])

    return dict(counts)

def detect_birds_from_video(video_path):
    """
    Detect birds from video by sampling 1 frame per second.
    Returns: dict {bird_name: count}
    """
    cap = cv.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception("Could not open video")

    fps = cap.get(cv.CAP_PROP_FPS)
    frame_interval = int(fps)  # capture one frame per second

    counts = Counter()
    frame_id = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_id % frame_interval == 0:
            result = model(frame)[0]
            detections = sv.Detections.from_ultralytics(result)
            detections = detections[detections.confidence > 0.5]
            class_ids = detections.class_id
            frame_counts = Counter([class_dict[cid] for cid in class_ids])
            counts.update(frame_counts)

        frame_id += 1

    cap.release()
    return dict(counts)

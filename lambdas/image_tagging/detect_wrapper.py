# lambdas/image_tagging/detect_wrapper.py

import os
import uuid
import subprocess
from ultralytics import YOLO
from birds_detection import image_prediction, video_prediction
from utils import parse_birdnet_results

def run_tagging(file_path, media_type):
    """
    Dispatches prediction based on media type and returns tag list.
    """
    tmp_filename = f"{uuid.uuid4()}"
    save_dir = "/tmp"

    if media_type == "image":
        image_prediction(file_path, result_filename=tmp_filename + ".jpg", save_dir=save_dir)
        return parse_yolo_prediction(file_path)

    elif media_type == "video":
        video_prediction(file_path, result_filename=tmp_filename + ".avi", save_dir=save_dir)
        return parse_yolo_prediction(file_path)

    elif media_type == "audio":
        return run_birdnet_prediction(file_path)

    else:
        raise Exception("Unsupported media type")

def parse_yolo_prediction(file_path, model_path="./model/model.pt", confidence=0.5):
    """
    Runs YOLO model on image or video file and returns class name + count list.
    """
    model = YOLO(model_path)
    result = model(file_path)[0]  # Get first prediction result (image or frame)
    class_dict = model.names
    tags = {}

    for box in result.boxes:
        if box.conf < confidence:
            continue
        cls_id = int(box.cls)
        cls_name = class_dict.get(cls_id, f"class_{cls_id}")
        tags[cls_name] = tags.get(cls_name, 0) + 1

    return [{"name": name, "count": count} for name, count in tags.items()]

def run_birdnet_prediction(audio_path):
    """
    Run BirdNET-Analyzer CLI on audio file and parse result.
    """
    model_path = os.path.join("model", "birdnet")
    output_dir = "/tmp/birdnet_out"
    os.makedirs(output_dir, exist_ok=True)

    analyze_script = os.path.join(model_path, "analyze.py")
    model_file = os.path.join(model_path, "BirdNET_GLOBAL_6K_V2.3_Model_FP32.tflite")
    label_file = os.path.join(model_path, "labels.txt")
    config_file = os.path.join(model_path, "config.json")

    cmd = [
        "python3", analyze_script,
        "--i", audio_path,
        "--o", output_dir,
        "--lat", "37.7749",  # Change to actual location if needed
        "--lon", "-122.4194",
        "--model", model_file,
        "--labels", label_file,
        "--config", config_file,
        "--threads", "1",
        "--sf", "22050",
        "--locale", "en"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"BirdNET CLI failed: {result.stderr}")

    for filename in os.listdir(output_dir):
        if filename.endswith(".csv"):
            return parse_birdnet_results(os.path.join(output_dir, filename))

    raise Exception("BirdNET output CSV not found.")

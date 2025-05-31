import os
import uuid
from birds_detection import image_prediction, video_prediction
from birdnet_audio_wrapper import run_audio_prediction
import datetime 

def run_tagging(file_path: str, media_type: str):
    """
    file_path: path to the downloaded file from S3
    media_type: one of 'image', 'video', or 'audio'
    """
    if media_type == "image":
        result = image_prediction(file_path)
        result["mediaType"] = "image"
    elif media_type == "video":
        result = video_prediction(file_path)
        result["mediaType"] = "video"
    elif media_type == "audio":
        result = run_audio_prediction(file_path)
        result["mediaType"] = "audio"
    else:
        raise ValueError(f"Unsupported media type: {media_type}")

    result["id"] = str(uuid.uuid4())
    result["uploadedAt"] = result.get("uploadedAt") or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    return result

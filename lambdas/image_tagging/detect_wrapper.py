import os
import uuid
from birds_detection import image_prediction, video_prediction
# from birdnet_audio_wrapper import run_audio_prediction
from datetime import datetime

def run_tagging(file_path: str, media_type: str):
    """
    file_path: path to the downloaded file from S3
    media_type: one of 'image', 'video', or 'audio'
    """

    base_name = os.path.basename(file_path)
    name_only = os.path.splitext(base_name)[0]
    result_filename = f"{name_only}_detected"

    if media_type == "image":
        result = image_prediction(file_path)
        result["mediaType"] = "image"
    elif media_type == "video":
        result = video_prediction(file_path, result_filename=result_filename, frame_skip=24)
        result["mediaType"] = "video"
    # elif media_type == "audio":
    #     result = run_audio_prediction(file_path)
    #     result["mediaType"] = "audio"
    else:
        raise ValueError(f"Unsupported media type: {media_type}")

    local_time = datetime.now()
    result["id"] = str(uuid.uuid4())
    result["uploadedAt"] = result.get("uploadedAt") or local_time.strftime("%d-%m-%Y %H:%M:%S")
    return result

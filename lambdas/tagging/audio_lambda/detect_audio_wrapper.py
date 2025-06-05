import os
from birdnet_audio_wrapper import run_audio_prediction
from datetime import datetime

def run_tagging(file_path: str, media_type: str):
    """
    file_path: path to the downloaded file from S3
    media_type: 'audio'
    """

    base_name = os.path.basename(file_path)
    name_only = os.path.splitext(base_name)[0]
    # extension = os.path.splitext(base_name)[1]
    # result_filename = f"{name_only}_detected"

    # if media_type == "image":
    #     tags = image_prediction(file_path, result_filename=f"{result_filename}{extension}")
    # elif media_type == "video":
    #     tags = video_prediction(file_path, result_filename=result_filename, frame_skip=24)
    if media_type == "audio":
        tags = run_audio_prediction(file_path)
    else:
        raise ValueError(f"Unsupported media type: {media_type}")

    return tags

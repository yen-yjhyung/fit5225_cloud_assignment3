import os
from birdnet_audio_wrapper import run_audio_prediction
from datetime import datetime

def run_audio_tagging(file_path: str, media_type: str):
    """
    file_path: path to the downloaded file from S3
    media_type: 'audio'
    """
    if media_type == "audio":
        tags = run_audio_prediction(file_path)
    else:
        raise ValueError(f"Unsupported media type: {media_type}")

    return tags

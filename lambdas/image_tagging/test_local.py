import os
import json
from detect_wrapper import run_tagging

def test_local_file(file_path, media_type):
    print(f"Running test for: {file_path} ({media_type})\n")
    result = run_tagging(file_path, media_type)
    result["link"] = f"https://dummy-bucket.s3.amazonaws.com/{os.path.basename(file_path)}"
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    
    # Provide test file paths from /model/test_images or /test_videos
    # For audio
    # test_local_file("model/test_audio/soundscape.wav", "audio")

    # For image
    # test_local_file("model/test_images/crows_3.jpg", "image")

    # For video
    test_local_file("model/test_videos/crows.mp4", "video")

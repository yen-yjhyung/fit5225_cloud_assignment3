from detect_wrapper import detect_birds_return_counts
from datetime import datetime
import uuid
import json

# Local path to test image
img_path = "model/test_videos/crows.mp4"

tags = detect_birds_return_counts(img_path)
formatted_tags = [{"name": k, "count": v} for k, v in tags.items()]
item = {
    "id": str(uuid.uuid4()),
    "link": "https://test-bucket.s3.ap-southeast-2.amazonaws.com/crows_1.jpg",
    "tags": formatted_tags,
    "mediaType": "image",
    "uploadedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

print(json.dumps(item, indent=2))

# lambdas/image_tagging/utils.py

import uuid
from datetime import datetime
import csv
import os

def generate_dynamodb_record(s3_url, tags, media_type):
    return {
        "id": str(uuid.uuid4()),
        "link": s3_url,
        "tags": tags,
        "mediaType": media_type,
        "uploadedAt": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    }

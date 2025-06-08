# lambdas/image_tagging/utils.py

import uuid
from datetime import datetime
import csv
import os

# def generate_dynamodb_record(s3_url, tags, media_type):
#     return {
#         "id": str(uuid.uuid4()),
#         "link": s3_url,
#         "tags": tags,
#         "mediaType": media_type,
#         "uploadedAt": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
#     }

def generate_dynamodb_record(bucket, file_id, key, size, media_type, extension, tags, thumbnail_key=None):
    item = {
        "fileId": file_id,
        "key": key,
        "bucket": bucket,
        "size": size,
        "type": media_type,
        "format": extension,
        "tags": [
            {
                "name": tag["name"],
                "count": tag["count"]
            } for tag in tags
        ]
    }

    return item
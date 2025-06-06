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

def generate_dynamodb_record(bucket, file_id, key, size, media_type, format_, tags, thumbnail_key=None):
    tag_list = [
        {
            "M": {
                "name": {"S": tag["name"]},
                "count": {"N": str(tag["count"])}
            }
        } for tag in tags
    ]

    item = {
        "id": {"S": file_id},
        "key": {"S": key},
        "bucket": {"S": bucket},
        "size": {"N": str(size)},
        "type": {"S": media_type},
        "format": {"S": format_},
        "tags": {"L": tag_list},
    }

    if thumbnail_key:
        item["thumbnailKey"] = {"S": thumbnail_key}

    return item

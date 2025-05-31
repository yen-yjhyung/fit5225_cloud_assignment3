# lambdas/image_tagging/utils.py

import uuid
from datetime import datetime
import csv
import os

def parse_birdnet_results(csv_path):
    tag_counts = {}
    if not os.path.exists(csv_path):
        return []

    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            species = row["Scientific name"]
            confidence = float(row["Confidence"])
            if confidence > 0.5:
                tag_counts[species] = tag_counts.get(species, 0) + 1

    return [{"name": k, "count": v} for k, v in tag_counts.items()]

def generate_dynamodb_record(s3_url, tags, media_type):
    return {
        "id": str(uuid.uuid4()),
        "link": s3_url,
        "tags": tags,
        "mediaType": media_type,
        "uploadedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

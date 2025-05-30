import json
import boto3
import os
import uuid
from datetime import datetime
from detect_wrapper import detect_birds_from_image, detect_birds_from_video

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        record = event['Records'][0]['s3']
        bucket = record['bucket']['name']
        key = record['object']['key']
        file_name = key.split("/")[-1]
        ext = file_name.lower().split(".")[-1]

        # Download file to /tmp (Lambda)
        local_path = f"/tmp/{file_name}"
        s3.download_file(bucket, key, local_path)

        # Detect image or video
        if ext in ["mp4", "mov", "avi"]:
            tags = detect_birds_from_video(local_path)
            media_type = "video"
        else:
            tags = detect_birds_from_image(local_path)
            media_type = "image"

        formatted_tags = [{"name": k, "count": v} for k, v in tags.items()]
        region = os.environ.get('AWS_REGION', 'ap-southeast-2')
        s3_url = f"https://{bucket}.s3.{region}.amazonaws.com/{key}"

        item = {
            "id": str(uuid.uuid4()),
            "link": s3_url,
            "tags": formatted_tags,
            "mediaType": media_type,
            "uploadedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        table = dynamodb.Table("BirdTagMetadata")
        table.put_item(Item=item)

        return {
            "statusCode": 200,
            "body": json.dumps(item)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

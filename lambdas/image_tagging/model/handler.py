# lambdas/image_tagging/handler.py

import json
import urllib.parse
import boto3
import mimetypes
import os
from detect_wrapper import run_tagging
from utils import generate_dynamodb_record

# Set up DynamoDB table from environment variable
dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("TABLE_NAME")
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    try:
        # Extract S3 info from the event
        record = event["Records"][0]
        bucket_name = record["s3"]["bucket"]["name"]
        object_key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
        s3_url = f"https://{bucket_name}.s3.amazonaws.com/{object_key}"

        # Download the file from S3 to Lambda's /tmp directory
        s3 = boto3.client("s3")
        local_file_path = f"/tmp/{object_key.split('/')[-1]}"
        s3.download_file(bucket_name, object_key, local_file_path)

        # Detect the media type from the file extension
        mime_type, _ = mimetypes.guess_type(local_file_path)
        if mime_type is None:
            raise Exception("Unable to detect MIME type.")

        if mime_type.startswith("image"):
            media_type = "image"
        elif mime_type.startswith("video"):
            media_type = "video"
        elif mime_type.startswith("audio"):
            media_type = "audio"
        else:
            raise Exception(f"Unsupported file type: {mime_type}")

        # Run prediction and get tags
        tags = run_tagging(local_file_path, media_type)

        # Generate the final DynamoDB record and insert it
        record = generate_dynamodb_record(s3_url, tags, media_type)
        table.put_item(Item=record)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Tagging successful.",
                "record": record
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e)
            })
        }

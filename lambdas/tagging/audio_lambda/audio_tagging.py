import json
import boto3
import os
from detect_audio_wrapper import run_audio_tagging
from utils import generate_dynamodb_record
import soundfile as sf
import tempfile

TABLE_NAME = os.environ.get("TABLE_NAME", "FileMetadata")
REGION = os.environ.get("REGION", "us-east-1")
print(f"Using DynamoDB table: {TABLE_NAME} in region: {REGION}")
dynamodb = boto3.resource("dynamodb", region_name=REGION)
s3_client = boto3.client("s3", region_name=REGION)

# Lambda_handler.V3
def lambda_handler(event, context):
    local_path = None

    try:
        print("Event received:", json.dumps(event, indent=2))
        
        bucket = event["bucket"]
        key = event["key"]
        file_id = event["fileId"]
        size = event["size"]
        media_type = event["type"]
        format_ = event["format"]
        thumbnail_key = event.get("thumbnailKey")  # Optional

        # Download file
        local_path = os.path.join(tempfile.gettempdir(), os.path.basename(key))
        print(f"Downloading from S3: s3://{bucket}/{key} to {local_path}")
        s3 = boto3.client("s3")
        s3.download_file(bucket, key, local_path)
        print(f"Downloaded file size: {os.path.getsize(local_path)} bytes")
        print("File downloaded successfully.")

        # Check if audio is readable
        try:
            info = sf.info(local_path)
            print("Audio file info:", info)
        except Exception as e:
            print("soundfile could not read audio:", str(e))

        # Run tagging
        print("Running audio tagging...")
        result = run_audio_tagging(local_path, media_type)
        tags = result.get("tags", [])
        print(f"Tags generated: {json.dumps(tags, indent=2)}")

        # Generate DynamoDB record
        print("Generating DynamoDB record...")
        record = generate_dynamodb_record(
            bucket=bucket,
            file_id=file_id,
            key=key,
            size=size,
            media_type=media_type,
            extension=format_,
            tags=tags,
            thumbnail_key=thumbnail_key
        )
        print("DynamoDB record to insert:", json.dumps(record, indent=2))

        # dynamodb.put_item(TableName=TABLE_NAME, Item=record)
        table = dynamodb.Table(TABLE_NAME)
        response = table.put_item(Item=record)
        print("DynamoDB response:", response)
        print("Record inserted into DynamoDB.")
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Success", "tags": tags})
        }

    except Exception as e:
        print("Error occurred:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
    finally:
        # Optional cleanup
        if local_path and os.path.exists(local_path):
            os.remove(local_path)
            print(f"file removed: {local_path}")


import json
import boto3
import os
import tempfile
from detect_visual_wrapper import run_tagging
from utils import generate_dynamodb_record

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("TABLE_NAME", "BirdMediaTags")
BUCKET_NAME = os.environ.get("BUCKET_NAME", "birdtagbucket-assfdas")
REGION = os.environ.get("REGION", "us-east-1")

s3_client = boto3.client("s3", region_name=REGION)

def lambda_handler(event, context):
    try:
        record = event["Records"][0]
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
        size = record["s3"]["object"]["size"]

        extension = key.lower().split(".")[-1]
        if extension in ["jpg", "jpeg", "png", "bmp"]:
            media_type = "image"
        elif extension in ["mp4", "mov", "avi", "mkv"]:
            media_type = "video"
        elif extension in ["wav", "mp3", "flac"]:
            media_type = "audio"
        else:
            raise ValueError(f"Unsupported file extension: {extension}")

        # Download S3 file
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            s3_client.download_fileobj(bucket, key, tmp_file)
            tmp_path = tmp_file.name

        tags = run_tagging(tmp_path, media_type)

        # If image, construct thumbnail key
        thumbnail_key = f"thumbnails/{key.rsplit('.',1)[0]}_thumb.jpg" if media_type == "image" else None

        item = generate_dynamodb_record(bucket, key, size, media_type, extension, tags["tags"], thumbnail_key)

        dynamodb.put_item(TableName=TABLE_NAME, Item=item)

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Tagging complete", "key": key})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }


# def lambda_handler(event, context):
#     try:
#         # Extract bucket & key
#         record = event["Records"][0]
#         bucket = record["s3"]["bucket"]["name"]
#         key = record["s3"]["object"]["key"]

#         # Infer media type from file extension
#         extension = key.lower().split(".")[-1]
#         if extension in ["jpg", "jpeg", "png", "bmp"]:
#             media_type = "image"
#         elif extension in ["mp4", "mov", "avi", "mkv"]:
#             media_type = "video"
#         elif extension in ["wav", "mp3", "flac"]:
#             media_type = "audio"
#         else:
#             raise ValueError(f"Unsupported file extension: {extension}")

#         # Download the file to /tmp
#         with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
#             s3_client.download_fileobj(bucket, key, tmp_file)
#             tmp_path = tmp_file.name

#         # Run prediction
#         tags = run_tagging(tmp_path, media_type)


#         s3_url = f"https://{bucket}.s3.amazonaws.com/{key}"

#         # Upload result to DynamoDB
#         result = generate_dynamodb_record(s3_url, tags, media_type )
        
#         return {
#             "statusCode": 200,
#             "body": json.dumps({"message": "Tagging complete", "result": result})
#         }

#     except Exception as e:
#         return {
#             "statusCode": 500,
#             "body": json.dumps({"error": str(e)})
#         }

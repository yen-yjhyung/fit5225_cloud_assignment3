import json
import boto3
import os
import tempfile
from detect_visual_wrapper import run_visual_tagging
from utils import generate_dynamodb_record

TABLE_NAME = os.environ.get("TABLE_NAME", "FileMetadata")
REGION = os.environ.get("REGION", "us-east-1")
print(f"Using DynamoDB table: {TABLE_NAME} in region: {REGION}")
dynamodb = boto3.resource("dynamodb", region_name=REGION)
s3_client = boto3.client("s3", region_name=REGION)

# Initialize SNS client for warm start
sns_client = boto3.client("sns", region_name=REGION)
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "arn:aws:sns:REGION:ACCOUNT_ID:BirdTaggingResultsTopic")

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
        extension = event["format"]
        thumbnail_key = event.get("thumbnailKey")  # Optional

        # Download file
        local_path = os.path.join(tempfile.gettempdir(), os.path.basename(key))
        print(f"Downloading from S3: s3://{bucket}/{key} to {local_path}")
        s3 = boto3.client("s3")
        s3.download_file(bucket, key, local_path)
        print("File downloaded successfully.")

        # Run tagging
        print("Running visual tagging...")
        result = run_visual_tagging(local_path, media_type)
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
            extension=extension,
            tags=tags,
            thumbnail_key=thumbnail_key
        )
        print("DynamoDB record to insert:", json.dumps(record, indent=2))

        # dynamodb.put_item(TableName=TABLE_NAME, Item=record)
        table = dynamodb.Table(TABLE_NAME)
        response = table.put_item(Item=record)
        print(f"Record successfully inserted into DynamoDB. Response: {response}")

        print("Publishing SNS message ... ")
        # Publish to SNS
        message_attributes = {
            "media_type": {
                "DataType": "String",
                "StringValue": media_type
            },
            "file_id": {
                "DataType": "String",
                "StringValue": file_id
            },
            "extension": {
                "DataType": "String",
                "StringValue": extension
            }
        }

        sns_message = {
            "url": f"s3://{bucket}/{key}",
            "bucket": bucket,
            "key": key,
            "file_id": file_id,
            "size": size,
            "media_type": media_type,
            "format": extension,
            "tags": tags,
            "thumbnail_key" : thumbnail_key
        }

        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=json.dumps(sns_message),
            MessageAttributes=message_attributes
        )
        print(f"Published tagging results to SNS topic: {SNS_TOPIC_ARN}")

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
            print(f"Temp file removed: {local_path}")

# Lambda_handler.V2
# def lambda_handler(event, context):
#     print("Event received:", event)

#     try:
#         record = event["Records"][0]
#         bucket = record["s3"]["bucket"]["name"]
#         key = record["s3"]["object"]["key"]
#         size = record["s3"]["object"]["size"]

#         extension = key.lower().split(".")[-1]
#         if extension in ["jpg", "jpeg", "png", "bmp"]:
#             media_type = "image"
#         elif extension in ["mp4", "mov", "avi", "mkv"]:
#             media_type = "video"
#         else:
#             raise ValueError(f"Unsupported file extension: {extension}")

#         # Download S3 file
#         with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
#             s3_client.download_fileobj(bucket, key, tmp_file)
#             tmp_path = tmp_file.name

#         tags = run_visual_tagging(tmp_path, media_type)

#         # If image, construct thumbnail key
#         thumbnail_key = f"thumbnails/{key.rsplit('.',1)[0]}_thumb.jpg" if media_type == "image" else None

#         item = generate_dynamodb_record(bucket, key, size, media_type, extension, tags["tags"], thumbnail_key)

#         dynamodb.put_item(TableName=TABLE_NAME, Item=item)

#         return {
#             "statusCode": 200,
#             "body": json.dumps({"message": "Tagging complete", "key": key})
#         }

#     except Exception as e:
#         return {
#             "statusCode": 500,
#             "body": json.dumps({"error": str(e)})
#         }

# Lambda_handler.V1
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

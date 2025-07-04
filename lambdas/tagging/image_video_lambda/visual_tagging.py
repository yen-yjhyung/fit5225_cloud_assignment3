import json
import boto3
import os
import tempfile
from detect_visual_wrapper import run_visual_tagging
from utils import generate_dynamodb_record

TABLE_NAME = os.environ.get("TABLE_NAME", "FileMetadata")
REGION = os.environ.get("REGION", "ap-southeast-2")
print(f"Using DynamoDB table: {TABLE_NAME} in region: {REGION}")
dynamodb = boto3.resource("dynamodb", region_name=REGION)
s3_client = boto3.client("s3", region_name=REGION)

# Initialize SNS client for warm start
sns_client = boto3.client("sns", region_name=REGION)
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "arn:aws:sns:ap-southeast-2:960005777900:BirdtagDetectionNotifications")

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
        s3 = boto3.client("s3", region_name=REGION)
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
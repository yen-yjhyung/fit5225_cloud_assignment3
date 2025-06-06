import boto3
import os
import tempfile
import cv2
import uuid
import json
from urllib.parse import unquote_plus

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

TABLE_NAME = os.environ['TABLE_NAME']
THUMBNAIL_FOLDER = 'thumbnails/'

def lambda_handler(event, context):
    try:
        print("Event received:", event)

        record = event['Records'][0]
        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])

        if not key.startswith("images/"):
            print("Not an image upload. Skipping.")
            return {'statusCode': 200, 'body': 'Not an image.'}

        file_id = key.split('/')[-1].split('.')[0]

        download_path = f"/tmp/{uuid.uuid4()}.jpg"
        s3.download_file(bucket, key, download_path)

        image = cv2.imread(download_path)
        thumbnail = cv2.resize(image, (128, 128))

        thumbnail_filename = f"{file_id}_thumb.jpeg"
        thumbnail_path = f"/tmp/{thumbnail_filename}"
        cv2.imwrite(thumbnail_path, thumbnail)

        thumbnail_key = f"{THUMBNAIL_FOLDER}{thumbnail_filename}"
        s3.upload_file(thumbnail_path, bucket, thumbnail_key, ExtraArgs={'ContentType': 'image/jpeg'})

        table = dynamodb.Table(TABLE_NAME)
        table.update_item(
            Key={'fileId': file_id},
            UpdateExpression='SET thumbnailKey = :thumb',
            ExpressionAttributeValues={':thumb': thumbnail_key}
        )

        file_size = os.path.getsize(download_path)
        lambda_payload = {
            "bucket": bucket,
            "key": key,
            "fileId": file_id,
            "size": file_size,
            "type": "image",
            "format": key.lower().split('.')[-1],
            "thumbnailKey": thumbnail_key
        }

        lambda_client.invoke(
            FunctionName='birdtag-visual-lambda',  
            InvocationType='Event',
            Payload=json.dumps(lambda_payload)
        )

        return {'statusCode': 200, 'body': 'Thumbnail created and tagging triggered.'}


    except Exception as e:
        print("Error generating thumbnail:", str(e))
        return {'statusCode': 500, 'body': f"Error: {str(e)}"}

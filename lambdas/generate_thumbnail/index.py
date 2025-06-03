import json
import boto3
import os
import cv2
import urllib.parse

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
TABLE_NAME = 'FileMetadata'

def handler(event, context):
    print("Received event:", json.dumps(event))

    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(record['s3']['object']['key'])

        if key.startswith("thumbnails/"):
            print("Skipping thumbnail file to avoid recursion.")
            continue

        filename = os.path.basename(key)
        download_path = f"/tmp/{filename}"
        thumbnail_path = f"/tmp/thumb-{filename}"
        thumbnail_key = f"thumbnails/{filename}"

        try:
            # Download original image from S3
            s3.download_file(bucket, key, download_path)

            # Generate thumbnail using OpenCV
            img = cv2.imread(download_path)
            height, width = img.shape[:2]

            if height > width:
                new_height = 200
                new_width = int((200 / height) * width)
            else:
                new_width = 200
                new_height = int((200 / width) * height)

            resized = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
            cv2.imwrite(thumbnail_path, resized)

            # Upload thumbnail to S3
            s3.upload_file(thumbnail_path, bucket, thumbnail_key)

            # Get metadata of original image
            head = s3.head_object(Bucket=bucket, Key=key)
            file_size = head['ContentLength']
            content_type = head['ContentType']

            # Save metadata to DynamoDB
            table = dynamodb.Table(TABLE_NAME)
            table.put_item(Item={
                'fileId': key,
                'bucket': bucket,
                'type': content_type,
                'size': file_size,
                'thumbnailKey': thumbnail_key
            })

            print(f"Processed & saved metadata for {key}")

        except Exception as e:
            print(f"Error processing {key}: {str(e)}")
            raise e

    return {
        'statusCode': 200,
        'body': json.dumps('Success!')
    }

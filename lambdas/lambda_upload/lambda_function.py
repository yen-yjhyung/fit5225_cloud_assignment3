import os
import boto3
import uuid
import mimetypes
import base64
import json

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

BUCKET_NAME = os.environ['BUCKET_NAME']
TABLE_NAME = os.environ['TABLE_NAME']

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        file = body.get('file')
        file_name = body.get('fileName')

        header, encoded = file.split(',', 1)
        content_type = header.split(':')[1].split(';')[0]
        decoded = base64.b64decode(encoded)

        file_id = str(uuid.uuid4())
        ext = os.path.splitext(file_name)[-1] or mimetypes.guess_extension(content_type) or ''
        ext = ext.replace(".", "")
        mime_type_main = content_type.split('/')[0]

        key = f"images/{file_id}.{ext}"
        thumbnail_key = f"thumbnails/{file_id}_thumb.jpeg"

        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=decoded,
            ContentType=content_type
        )

        table = dynamodb.Table(TABLE_NAME)
        table.put_item(Item={
            'fileId': file_id,
            'key': key,
            'bucket': BUCKET_NAME,
            'size': len(decoded),
            'thumbnailKey': thumbnail_key,
            'type': mime_type_main,
            'format': ext,
            'tags': []  # will be updated later
        })

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': 'Upload successful',
                'fileId': file_id,
                's3Key': key
            })
        }

    except Exception as e:
        print("Error:", str(e))
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'message': f'Internal server error: {str(e)}'})
        }

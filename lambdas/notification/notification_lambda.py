import json
import os
import boto3

# Environment variables - these will be set in CloudFormation
SES_SENDER_EMAIL = os.environ.get("SES_SENDER_EMAIL")
REGION = os.environ.get("AWS_REGION") # Lambda's default region env var

ses_client = boto3.client("ses", region_name=REGION)

def lambda_handler(event, context):
    print("Received event:", json.dumps(event, indent=2))

    try:
        # SNS messages come wrapped in an SNS object within the event records
        sns_message_str = event['Records'][0]['Sns']['Message']
        message_data = json.loads(sns_message_str)

        # Extract data from the message
        file_id = message_data.get('file_id', 'N/A')
        bucket = message_data.get('bucket', 'N/A')
        key = message_data.get('key', 'N/A')
        media_type = message_data.get('media_type', 'N/A')
        tags = message_data.get('tags', [])
        url = message_data.get('url', 'N/A')
        size = message_data.get('size', 'N/A')
        file_format = message_data.get('format', 'N/A')
        thumbnail_key = message_data.get('thumbnail_key', 'N/A')


        # Construct the email subject
        subject = f"BirdTagging Notification: New {media_type} Processed (ID: {file_id})"

        # Construct the email body
        body_html = f"""
        <html>
        <head></head>
        <body>
            <h3>A new {media_type} has been processed and tagged!</h3>
            <p><strong>File ID:</strong> {file_id}</p>
            <p><strong>Location:</strong> s3://{bucket}/{key}</p>
            <p><strong>URL:</strong> <a href="{url}">{url}</a></p>
            <p><strong>Size:</strong> {size} bytes</p>
            <p><strong>Format:</strong> {file_format}</p>
            <p><strong>Tags:</strong> {', '.join(tags) if tags else 'No tags generated'}</p>
            {f'<p><strong>Thumbnail Key:</strong> {thumbnail_key}</p>' if thumbnail_key != 'N/A' else ''}
            <br/>
            <p>This is an automated notification from the BirdTagging system.</p>
        </body>
        </html>
        """
        body_text = f"""
        A new {media_type} has been processed and tagged!
        File ID: {file_id}
        Location: s3://{bucket}/{key}
        URL: {url}
        Size: {size} bytes
        Format: {file_format}
        Tags: {', '.join(tags) if tags else 'No tags generated'}
        {f'Thumbnail Key: {thumbnail_key}' if thumbnail_key != 'N/A' else ''}

        This is an automated notification from the BirdTagging system.
        """

        # Send the email
        response = ses_client.send_email(
            Source=SES_SENDER_EMAIL,
            Destination={
                'ToAddresses': [
                    SES_SENDER_EMAIL, # For demonstration, sending to the sender.
                                      # In a real app, this would be a user's email list from a database.
                ]
            },
            Message={
                'Subject': {'Data': subject},
                'Body': {
                    'Html': {'Data': body_html},
                    'Text': {'Data': body_text}
                }
            }
        )
        print(f"Email sent successfully! MessageId: {response['MessageId']}")

        return {
            'statusCode': 200,
            'body': json.dumps('Email sent successfully!')
        }

    except Exception as e:
        print(f"Error processing message or sending email: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
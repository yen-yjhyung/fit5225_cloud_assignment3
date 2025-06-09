import json
import os
import boto3

# Environment variables - these will be set in CloudFormation
SES_SENDER_EMAIL = os.environ.get("SES_SENDER_EMAIL")
REGION = os.environ.get("AWS_REGION") # Lambda's default region env var
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID")

ses_client = boto3.client("ses", region_name=REGION)
cognito_client = boto3.client("cognito-idp", region_name=REGION)

def get_all_cognito_user_emails(user_pool_id):
    """Fetches all verified email addresses from a Cognito User Pool."""
    user_emails = []
    pagination_token = None

    while True:
        if pagination_token:
            response = cognito_client.list_users(
                UserPoolId=user_pool_id,
                PaginationToken=pagination_token
            )
        else:
            response = cognito_client.list_users(
                UserPoolId=user_pool_id
            )

        for user in response.get('Users', []):
            user_enabled = user.get('Enabled', False)
            user_status = user.get('UserStatus', 'UNKNOWN')

            # Only consider CONFIRMED users who are enabled
            if user_enabled and user_status == 'CONFIRMED':
                for attr in user.get('Attributes', []):
                    if attr['Name'] == 'email' and attr.get('Value'):
                        # Check if email is verified
                        email_verified = False
                        for email_attr in user.get('Attributes', []):
                            if email_attr['Name'] == 'email_verified':
                                if email_attr['Value'] == 'true':
                                    email_verified = True
                                break
                        if email_verified:
                            user_emails.append(attr['Value'])
        
        pagination_token = response.get('PaginationToken')
        if not pagination_token:
            break
    
    return user_emails

def lambda_handler(event, context):
    print("Received event:", json.dumps(event, indent=2))

    try:
        # SNS messages come wrapped in an SNS object within the event records
        sns_message_str = event['Records'][0]['Sns']['Message']
        message_data = json.loads(sns_message_str)

        # Extract data from the message
        file_id = message_data.get('file_id', 'N/A')
        media_type = message_data.get('media_type', 'N/A')
        raw_tags  = message_data.get('tags', [])

        tags_html_list_items = []
        tags_text_list_items = []
        if raw_tags:
            for tag in raw_tags:
                tag_name = tag.get('name', 'Unknown')
                tag_count = tag.get('count', 'N/A') # Assuming 'count' field exists in tags
                tags_html_list_items.append(f'<li><strong>Name:</strong> {tag_name} <strong>Count:</strong> {tag_count}</li>')
                tags_text_list_items.append(f'Name: {tag_name} Count: {tag_count}')
        
        tags_html_display = "".join(tags_html_list_items) if tags_html_list_items else 'No tags generated'
        tags_text_display = "\n".join(tags_text_list_items) if tags_text_list_items else 'No tags generated'

        # Handle inconsistent URL field (url or s3_url)
        display_url = message_data.get('url') # Try 'url' first (from visual_tagging)
        if not display_url or display_url == 'N/A': # If 'url' is not found or is 'N/A'
            display_url = message_data.get('s3_url', 'N/A') # Try 's3_url' (from audio_tagging)

        # --- Do not send email if tags_names is empty ---
        if not tags_html_list_items:
            print(f"No tags generated for file ID {file_id}. Skipping email notification.")
            return {
                'statusCode': 200,
                'body': json.dumps(f'No tags generated for file ID {file_id}. Email not sent.')
            }

        # Get all recipient emails from Cognito
        # Initialize recipient_emails here to ensure it's always defined
        recipient_emails = [] 
        if not COGNITO_USER_POOL_ID:
            print("Error: COGNITO_USER_POOL_ID environment variable is not set. Cannot fetch Cognito users.")
            recipient_emails.append(SES_SENDER_EMAIL) # Fallback
        else:
            fetched_emails = get_all_cognito_user_emails(COGNITO_USER_POOL_ID)
            if not fetched_emails:
                print("No confirmed and enabled users with verified emails found in Cognito User Pool. Sending to SES_SENDER_EMAIL fallback.")
                recipient_emails.append(SES_SENDER_EMAIL) # Fallback
            else:
                print(f"Found {len(fetched_emails)} recipients from Cognito.")
                print(f"Recipient Emails: {fetched_emails}") # Log for debugging
                recipient_emails = fetched_emails # Assign the list

        # Construct the email subject
        subject = f"BirdTagging Notification: New {media_type} Processed (ID: {file_id})"

        # Construct the email body
        body_html = f"""
        <html>
        <head></head>
        <body>
            <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #007bff; text-align: center;"> Hooray! A New Discovery! </h2>
                <p>Good news! Our BirdTagging system has just finished processing a new **{media_type}** file.</p>
                <p>And guess what? It's singing with new information!</p>
                <p style="font-size: 1.1em; font-weight: bold;">We've identified the following tags:</p>
                <ul style="list-style-type: disc; padding-left: 20px; margin: 15px 0;">
                    {tags_html_display}
                </ul>
                <p>Isn't that exciting? Our digital birds are chirping with data!</p>
                <p style="font-style: italic; color: #666;">
                    Keep those files coming! Every upload helps our feathered friends (the AI ones, of course) learn and grow.
                </p>
                <p style="text-align: center; font-size: 0.9em; color: #888; margin-top: 30px;">
                    This is an automated notification from the BirdTagging system.
                </p>
            </div>
        </body>
        </html>
        """

        body_text = f"""
        Hooray! A New Discovery!

        Good news! Our diligent BirdTagging system has just finished processing a new {media_type} file.
        And guess what? It's singing with new information!

        We've identified the following tags:
        {tags_text_display}

        Isn't that exciting? Our digital birds are chirping with data!

        Keep those files coming! Every upload helps our feathered friends (the AI ones, of course) learn and grow.

        This is an automated notification from the BirdTagging system.
        """

        # Send the email
        response = ses_client.send_email(
            Source=SES_SENDER_EMAIL,
            Destination={
                'ToAddresses': recipient_emails, 
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
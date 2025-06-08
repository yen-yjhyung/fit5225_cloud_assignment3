import json
import os
import tempfile
import base64
import mimetypes
from detect_visual_wrapper import run_visual_tagging

# custom setup for mimetypes 
mimetypes.add_type("video/x-msvideo", ".avi")
mimetypes.add_type("video/avi", ".avi")
mimetypes.add_type("video/msvideo", ".avi")

# lambda handler for visual (image/video) query tagging
def lambda_handler(event, context):
    media_type = None

    try:
        print("Event received:", json.dumps(event, indent=2))

        # 1. Get Base64 encoded file data from the request body
        if "body" not in event or not event.get("isBase64Encoded", False):
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Invalid request: Expected base64 encoded body."})
            }
        
        base64_data = event["body"]
        decoded_data = base64.b64decode(base64_data)
        print("File decoded successfully.")

        # 2. Determine media type from Content-Type header
        content_type = event.get("headers", {}).get("Content-Type", "").lower()
        if not content_type:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Content-Type header is missing."})
            }

        # Get media type from content type
        if "image" in content_type:
            media_type = "image"
        elif "video" in content_type:
            media_type = "video"
        else:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": f"Unsupported media type: {content_type}"})
            }
        
        # Map content type to file extension
        extension = mimetypes.guess_extension(content_type)
        if not extension:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": f"Unsupported Content-Type: {content_type}"})
            }
        
        # 3. Write the decode file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension, dir=os.path.join(tempfile.gettempdir(),"file")) as temp_file:
            temp_file.write(decoded_data)
            temp_file_path = temp_file.name
        print(f"File saved to temporary path: {temp_file_path}")

        # 4. Run tagging
        print("Running visual query tagging...")
        result = run_visual_tagging(temp_file_path, media_type)
        tags = result.get("tags", [])
        print(f"Tags generated: {json.dumps(tags, indent=2)}")

        if result.get("mediaType") == "":
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Failed to open media file"})
            }

        # 5. Return Result
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result)
        }

    except Exception as e:
        print("Error occurred:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
    finally:
        # Optional cleanup
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            print(f"{media_type} file removed: {temp_file_path}")

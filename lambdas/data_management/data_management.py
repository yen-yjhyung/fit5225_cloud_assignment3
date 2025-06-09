import os
import json
import urllib.parse
import boto3
from botocore.exceptions import ClientError

TABLE_NAME = os.environ.get("TABLE_NAME", "BirdMediaTags")
BUCKET_NAME = os.environ.get("BUCKET_NAME", "birdtagbucket-assfdas")
REGION     = os.environ.get("REGION", "us-east-1")

dynamodb_client = boto3.client("dynamodb", region_name=REGION)
s3_client = boto3.client("s3", region_name=REGION)

def lambda_handler(event, context):
    """
    Entry point for Lambda.
    Expects POST /update-tags with a JSON body:
    {
      "url": [
        "https://birdtagbucket-assfdas.s3.us-east-1.amazonaws.com/thumbnails/image1-thumb.png",
        "https://birdtagbucket-assfdas.s3.us-east-1.amazonaws.com/thumbnails/image60-thumb.png",
        "https://birdtagbucket-assfdas.s3.us-east-1.amazonaws.com/thumbnails/image23-thumb.png"
      ],
      "operation": "add",   # "add" or "remove"
      "tags": [
        {"name": "crow", "count": 1},
        {"name": "pigeon", "count": 2}
      ]
    }
    """
    try:
        method = event["requestContext"]["http"]["method"]
        path   = event.get("rawPath") or event.get("path", "")
        if path == "/update-tags" and method == "POST":
            return handle_update_tags(event)
        elif path == "/delete-resource" and method == "POST":
            return handle_delete_resource(event)
        else:
            return {
                "statusCode": 404,
                "headers": _cors_headers(),
                "body": json.dumps({"message": "Not Found"})
            }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": _cors_headers(),
            "body": json.dumps({"message": "Internal server error", "error": str(e)})
        }

def handle_update_tags(event):
    """
    Processes bulk add/remove tag requests against items in DynamoDB.
    """
    try:
        body = json.loads(event.get("body", "{}"))
        url_list   = body.get("url", [])
        operation  = body.get("operation", "").lower()
        tag_list   = body.get("tags", [])

        if not isinstance(url_list, list) or len(url_list) == 0:
            return _response(400, {"message": "\"url\" must be a non-empty list"})
        if operation not in ("add", "remove"):
            return _response(400, {"message": "\"operation\" must be \"add\" or \"remove\""})
        if not isinstance(tag_list, list) or len(tag_list) == 0:
            return _response(400, {"message": "\"tags\" must be a non-empty list"})

        normalized_tags = []
        for t in tag_list:
            name = t.get("name", "").strip().lower()
            count = int(t.get("count", 0))
            if not name or count < 1:
                return _response(400, {"message": "Each tag requires a non-empty \"name\" and count >= 1"})
            normalized_tags.append({"name": name, "count": count})

        updated_items = []

        for url in url_list:
            # URL: https://birdtagbucket-assfdas.s3.us-east-1.amazonaws.com/thumbnails/xxx_thumb.
            parsed = urllib.parse.urlparse(url)
            object_key = parsed.path.lstrip("/")  # "thumbnails/xxx_thumb.png"

            resp = dynamodb_client.scan(
                TableName=TABLE_NAME,
                FilterExpression = "thumbnailKey = :tk",
                ExpressionAttributeValues = {
                    ":tk": {"S": object_key}
                }
            )
            items = resp.get("Items", [])
            if not items:
                continue

            for item in items:
                item_id = item["fileId"]["S"]

                existing_tag_map = {}
                for t_elt in item.get("tags", {}).get("L", []):
                    m = t_elt.get("M", {})
                    name = m.get("name", {}).get("S", "").lower()
                    cnt = int(m.get("count", {}).get("N", "0"))
                    if name:
                        existing_tag_map[name] = cnt

                if operation == "add":
                    for t in normalized_tags:
                        nm = t["name"]
                        ct = t["count"]
                        existing_tag_map[nm] = ct
                else:  # operation == "remove"
                    for t in normalized_tags:
                        nm = t["name"]
                        if nm in existing_tag_map:
                            del existing_tag_map[nm]

                new_dynamodb_tags = {"L": []}
                for nm, ct in existing_tag_map.items():
                    new_dynamodb_tags["L"].append({
                        "M": {
                            "name": {"S": nm},
                            "count": {"N": str(ct)}
                        }
                    })

                dynamodb_client.update_item(
                    TableName=TABLE_NAME,
                    Key={ "fileId": {"S": item_id} },
                    UpdateExpression="SET #tg = :newtags",
                    ExpressionAttributeNames={"#tg": "tags"},
                    ExpressionAttributeValues={":newtags": new_dynamodb_tags}
                )

                updated_items_entry = {
                    "fileId": item_id,
                    "tags": [
                        {"name": nm, "count": existing_tag_map[nm]}
                        for nm in existing_tag_map
                    ]
                }
                updated_items.append(updated_items_entry)

        return _response(200, {
            "message": "Tags updated successfully",
            "updated_items": updated_items
        })

    except ClientError as e:
        return _response(500, {"message": "DynamoDB ClientError", "error": str(e)})
    except Exception as e:
        return _response(500, {"message": "Internal error", "error": str(e)})

def handle_delete_resource(event):
    """
    Processes the delete request:
    1. Parse the incoming JSON body for "url" (presigned URL).
    2. Extract S3 object key from that URL.
    3. Scan DynamoDB for an item where "key" == extracted key.
    4. If found:
       - Delete the object from S3 by key.
       - If type == "image", also delete the thumbnail in S3 (thumbnailKey).
       - Delete the DynamoDB item by id.
    5. Return success or appropriate error.
    """
    try:
        body = json.loads(event.get("body", "{}"))
        url  = body.get("url", "").strip()
        if not url:
            return _response(400, {"message": "\"url\" is required"})

        # 1. Parse URL to get S3 object key, e.g. "images/uuid.jpg"
        parsed = urllib.parse.urlparse(url)
        object_key = parsed.path.lstrip("/")  # strip leading "/"

        if not object_key:
            return _response(400, {"message": "Invalid URL format"})

        # 2. Scan DynamoDB for item where "key" equals this object_key
        scan_resp = dynamodb_client.scan(
            TableName=TABLE_NAME,
            FilterExpression="#k = :k",
            ExpressionAttributeNames={"#k": "key"},
            ExpressionAttributeValues={":k": {"S": object_key}}
        )
        items = scan_resp.get("Items", [])
        if not items:
            return _response(404, {"message": "Resource not found in DynamoDB"})

        # 3. Delete every match
        deleted_records = []
        for item in items:
            item_id    = item["fileId"]["S"]
            item_type  = item.get("type", {}).get("S", "")
            thumb_key  = item.get("thumbnailKey", {}).get("S", "")

            # 3.1. Delete main object from S3
            try:
                s3_client.delete_object(Bucket=BUCKET_NAME, Key=object_key)
            except ClientError as e:
                if e.response["Error"]["Code"] != "NoSuchKey":
                    return _response(500, {"message": "Failed to delete S3 object", "error": str(e)})

            # 3.2. If this item is an image and has a thumbnailKey, delete thumbnail
            if item_type.lower() == "image" and thumb_key:
                try:
                    s3_client.delete_object(Bucket=BUCKET_NAME, Key=thumb_key)
                except ClientError as e:
                    if e.response["Error"]["Code"] != "NoSuchKey":
                        return _response(500, {"message": "Failed to delete thumbnail", "error": str(e)})

            # 3.3. Delete item from DynamoDB by primary key "id"
            try:
                dynamodb_client.delete_item(
                    TableName=TABLE_NAME,
                    Key={"fileId": {"S": item_id}}
                )
            except ClientError as e:
                return _response(500, {"message": "Failed to delete DynamoDB record", "error": str(e)})

            deleted_records.append(item_id)

        return _response(200, {
            "message": "Deleted resource successfully",
            "deleted_ids": deleted_records
        })

    except ClientError as e:
        return _response(500, {"message": "DynamoDB/S3 ClientError", "error": str(e)})
    except Exception as e:
        return _response(500, {"message": "Internal error", "error": str(e)})

def _response(status_code, body_obj):
    return {
        "statusCode": status_code,
        "headers": _cors_headers(),
        "body": json.dumps(body_obj, default=str)
    }

def _cors_headers():
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
        "Access-Control-Allow-Headers": "Content-Type,Authorization"
    }

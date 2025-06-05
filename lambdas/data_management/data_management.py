import os
import json
import urllib.parse
import boto3
from botocore.exceptions import ClientError

TABLE_NAME = os.environ.get("TABLE_NAME", "BirdMediaTags")
REGION     = os.environ.get("REGION", "us-east-1")

dynamodb_client = boto3.client("dynamodb", region_name=REGION)

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

        # 1. 参数校验
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
                item_id = item["id"]["S"]

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
                    Key={ "id": {"S": item_id} },
                    UpdateExpression="SET #tg = :newtags",
                    ExpressionAttributeNames={"#tg": "tags"},
                    ExpressionAttributeValues={":newtags": new_dynamodb_tags}
                )

                updated_items_entry = {
                    "id": item_id,
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

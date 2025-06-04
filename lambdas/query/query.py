import json
import os
import boto3
import base64
import urllib.parse
from datetime import datetime
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("TABLE_NAME", "BirdMediaTags")
BUCKET_NAME = os.environ.get("BUCKET_NAME", "birdtagbucket-assfdas")
REGION = os.environ.get("REGION", "us-east-1")

s3_client = boto3.client("s3", region_name=REGION)

def lambda_handler(event, context):
    path = event.get("rawPath") or event.get("path", "")
    method = event["requestContext"]["http"]["method"]

    if path == "/query" and method == "POST":
        return handle_query(event)
    elif path == "/find" and method == "POST":
        return handle_find(event)
    elif path == "/find-full-image" and method == "POST":
            return handle_find_full_image(event)
    else:
        return {
            "statusCode": 404,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Not Found"}),
        }

def handle_query(event):
    try:
        body = json.loads(event.get("body", "{}"))
        filters = body.get("species", [])
        if not isinstance(filters, list) or len(filters) == 0:
            return _response(400, {"message": "species must be a non-empty list"})

        table = dynamodb.Table(TABLE_NAME)

        scan_kwargs = {}
        items = []
        done = False
        start_key = None

        while not done:
            if start_key:
                scan_kwargs["ExclusiveStartKey"] = start_key
            resp = table.scan(**scan_kwargs)
            items.extend(resp.get("Items", []))
            start_key = resp.get("LastEvaluatedKey", None)
            done = start_key is None

        def match_item(item):
            item_tags = { t["name"]: t["count"] for t in item.get("tags", []) }
            for f in filters:
                name = f.get("name")
                cnt = f.get("count", 0)
                if name not in item_tags or item_tags[name] < cnt:
                    return False
            return True

        matched = [item for item in items if match_item(item)]

        return _response(200, {"results": matched})

    except Exception as e:
        print("handle_query error:", e)
        return _response(500, {"message": "Internal Server Error", "error": str(e)})

def handle_find(event):
    """
    Handle POST /find
    Expects JSON body:
      {
        "species": ["crow", "pigeon", ...]
      }
    Returns all items where at least one tag.name matches any species in the list.
    """
    try:
        body = json.loads(event.get("body", "{}"))
        requested = body.get("species", [])
        if not isinstance(requested, list) or len(requested) == 0:
            return _response(400, {"message": "species must be a non-empty list of strings"})

        # Normalize requested species to lowercase
        requested_set = set([s.lower() for s in requested if isinstance(s, str)])

        table = dynamodb.Table(TABLE_NAME)
        # Scan entire table (for small volumes; use GSI/Query in production)
        items = []
        scan_kwargs = {}
        done = False
        last_evaluated_key = None

        while not done:
            if last_evaluated_key:
                scan_kwargs["ExclusiveStartKey"] = last_evaluated_key
            resp = table.scan(**scan_kwargs)
            items.extend(resp.get("Items", []))
            last_evaluated_key = resp.get("LastEvaluatedKey")
            done = last_evaluated_key is None

        # Filter: include an item if any tag.name appears in requested_set
        def has_any_species(item):
            for t in item.get("tags", []):
                name = t.get("name", "").lower()
                if name in requested_set:
                    return True
            return False

        matched = [item for item in items if has_any_species(item)]
        return _response(200, {"results": matched})

    except Exception as e:
        print("handle_find error:", e)
        return _response(500, {"message": "Internal Server Error", "error": str(e)})

def handle_find_full_image(event):
    """
    Extracts the thumbnail key from the presigned URL, infers the full-image key,
    locates it in S3, and returns a new presigned URL for the full-size image.
    """
    try:
        body = json.loads(event.get("body", "{}"))
        thumbnail_url = body.get("thumbnailUrl")
        if not thumbnail_url:
            return _response(400, {"message": "thumbnailUrl is required"})

        # Parse the incoming presigned URL to get the object key
        parsed = urllib.parse.urlparse(thumbnail_url)
        # parsed.path might be like "/thumbnails/xxx_thumb.jpg"
        object_key = parsed.path.lstrip("/")  # e.g. "thumbnails/230a6c42-..._thumb.jpg"

        # Verify that the key indeed lies under "thumbnails/"
        if not object_key.startswith("thumbnails/") or not object_key.endswith("_thumb.jpeg"):
            return _response(400, {"message": "Invalid thumbnail key or format"})

        # Derive the base filename without "_thumb.jpg"
        # e.g. "230a6c42-1757-4bbe-bf17-0ac1fb7ee252"
        base_name = object_key[len("thumbnails/") : -len("_thumb.jpeg")]

        # Now search for the corresponding full-size object under "images/" prefix
        # We list objects with prefix "images/<base_name>"
        prefix = f"images/{base_name}"

        # List up to 5 keys under that prefix to find a match
        resp = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix=prefix
        )

        # If no objects found, return 404
        contents = resp.get("Contents", [])
        if not contents:
            return _response(404, {"message": "Full-size image not found"})

        # Pick the first matching key (there should ideally be exactly one)
        full_key = contents[0]["Key"]  # e.g. "images/230a6c42-1757-4bbe-bf17-0ac1fb7ee252.png"

        # Generate a presigned URL for the full-size image (expiresIn seconds)
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": BUCKET_NAME, "Key": full_key},
            ExpiresIn=3600  # URL valid for 1 hour
        )

        return _response(200, {"imageUrl": presigned_url})

    except ClientError as e:
        return _response(500, {"message": "S3 ClientError", "error": str(e)})
    except Exception as e:
        return _response(500, {"message": "Internal error", "error": str(e)})

def _response(status_code, body_dict):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,GET,PUT,POST,DELETE"
        },
        "body": json.dumps(body_dict, default=str)
    }

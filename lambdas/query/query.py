import json
import os
import boto3
import urllib.parse
from botocore.exceptions import ClientError

# DynamoDB and S3 configuration from environment variables
TABLE_NAME  = os.environ.get("TABLE_NAME", "BirdMediaTags")
BUCKET_NAME = os.environ.get("BUCKET_NAME", "birdtagbucket-assfdas")
REGION      = os.environ.get("REGION", "us-east-1")

# Initialize boto3 resources/clients
dynamodb   = boto3.resource("dynamodb", region_name=REGION)
table      = dynamodb.Table(TABLE_NAME)
s3_client  = boto3.client("s3", region_name=REGION)

def lambda_handler(event, context):
    path   = event.get("rawPath") or event.get("path", "")
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
            "body": json.dumps({"message": "Not Found"})
        }

def handle_query(event):
    """
    Handle POST /query
    Expects JSON body:
      { "species": [ { "name": "...", "count": ... }, ... ] }
    Returns items where each specified species appears at least that many times.
    """
    try:
        body = json.loads(event.get("body", "{}"))
        filters = body.get("species", [])
        if not isinstance(filters, list) or len(filters) == 0:
            return _response(400, {"message": "species must be a non-empty list"})

        # Scan entire table
        scan_kwargs = {}
        items = []
        done = False
        last_evaluated_key = None

        while not done:
            if last_evaluated_key:
                scan_kwargs["ExclusiveStartKey"] = last_evaluated_key
            resp = table.scan(**scan_kwargs)
            items.extend(resp.get("Items", []))
            last_evaluated_key = resp.get("LastEvaluatedKey")
            done = last_evaluated_key is None

        # For each item, build a dict: { tagName: tagCount, ... }
        def match_item(item):
            item_tags = { t["name"].lower(): int(t["count"]) for t in item.get("tags", []) }
            for f in filters:
                name = f.get("name").lower()
                cnt  = int(f.get("count", 0))
                if name not in item_tags or item_tags[name] < cnt:
                    return False
            return True

        matched_raw = [item for item in items if match_item(item)]

        # Transform each item to include presigned URLs
        matched = [ transform_item(item) for item in matched_raw ]

        return _response(200, {"results": matched})

    except Exception as e:
        print("handle_query error:", e)
        return _response(500, {"message": "Internal Server Error", "error": str(e)})

def handle_find(event):
    """
    Handle POST /find
    Expects JSON body:
      {
        "species": [
          { "name": "crow" },
          { "name": "pigeon" }
        ]
      }
    Returns all items where at least one tag.name matches any requested species.
    """
    try:
        body = json.loads(event.get("body", "{}"))
        requested = body.get("species", [])
        if not isinstance(requested, list) or len(requested) == 0:
            return _response(400, {"message": "species must be a non-empty list of {name} objects"})

        # Build a set of lowercase species names from requested list of dicts
        requested_set = set([
            entry.get("name", "").lower()
            for entry in requested
            if isinstance(entry, dict) and entry.get("name", "").strip() != ""
        ])
        if not requested_set:
            return _response(400, {"message": "Each element in species must be a dict with a non-empty 'name'"})

        # Scan entire table
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

        # Filter items: include an item if any of its tags matches requested_set
        def has_any_species(item):
            for t in item.get("tags", []):
                name = t.get("name", "").lower()
                if name in requested_set:
                    return True
            return False

        matched_raw = [item for item in items if has_any_species(item)]
        matched = [ transform_item(item) for item in matched_raw ]

        return _response(200, {"results": matched})

    except Exception as e:
        print("handle_find error:", e)
        return _response(500, {"message": "Internal Server Error", "error": str(e)})

def handle_find_full_image(event):
    """
    Handle POST /find-full-image
    Get presigned full-size image URL given a presigned thumbnail URL.
    """
    try:
        body = json.loads(event.get("body", "{}"))
        thumbnail_url = body.get("thumbnailUrl")
        if not thumbnail_url:
            return _response(400, {"message": "thumbnailUrl is required"})

        parsed = urllib.parse.urlparse(thumbnail_url)
        thumb_key = parsed.path.lstrip("/")  # e.g. "thumbnails/abcd_thumb.jpeg"

        if not thumb_key.startswith("thumbnails/") or not (thumb_key.endswith("_thumb.jpeg") or thumb_key.endswith("_thumb.jpg")):
            return _response(400, {"message": "Invalid thumbnail key or format"})

        base_name = thumb_key[len("thumbnails/"): thumb_key.rfind("_thumb")]

        prefix = f"images/{base_name}"
        resp = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
        contents = resp.get("Contents", [])
        if not contents:
            return _response(404, {"message": "Full-size image not found"})

        full_key = contents[0]["Key"]
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": BUCKET_NAME, "Key": full_key},
            ExpiresIn=3600
        )
        return _response(200, {"imageUrl": presigned_url})

    except ClientError as e:
        return _response(500, {"message": "S3 ClientError", "error": str(e)})
    except Exception as e:
        return _response(500, {"message": "Internal error", "error": str(e)})

def transform_item(item):
    """
    Convert a DynamoDB record into the response format, generating presigned URLs.
    Input `item` example (via boto3.resource):
      {
        "fileId": "84330c77-6964-420b-b461-a18777fceebf",
        "bucket": "birdtagbucket-assfdas",
        "format": "jpg",
        "key": "images/84330c77-...jpg",
        "size": Decimal('82209'),
        "tags": [
          { "name": "crow",   "count": Decimal('2') },
          { "name": "pigeon", "count": Decimal('1') }
        ],
        "thumbnailKey": "thumbnails/84330c77-..._thumb.jpeg",
        "type": "image"
      }

    Output should be:
      {
        "id": "<same id>",
        "mediaType": "<type>",
        "tags": [ { "name": "...", "count": <int> }, ... ],
        "s3Link": "<presigned URL for key>",
        "thumbnailLink": "<presigned URL for thumbnailKey>"  # only if type == "image"
      }
    """
    item_id    = item.get("fileId")
    media_type = item.get("type", "").lower()
    raw_tags   = item.get("tags", [])
    key        = item.get("key")
    thumb_key  = item.get("thumbnailKey", "")

    # Convert tags from Decimal to int
    tags_list = []
    for t in raw_tags:
        name = t.get("name")
        cnt  = int(t.get("count", 0))
        tags_list.append({"name": name, "count": cnt})

    # Generate presigned URL for the main object
    s3_link = ""
    try:
        s3_link = s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": BUCKET_NAME, "Key": key},
            ExpiresIn=3600
        )
    except Exception as e:
        print(f"Error generating presigned for key={key}: {e}")

    result = {
        "id": item_id,
        "mediaType": media_type,
        "tags": tags_list,
        "s3Link": s3_link
    }

    # If this item is an image, provide thumbnailLink as well
    if media_type == "image" and thumb_key:
        thumb_url = ""
        try:
            thumb_url = s3_client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": BUCKET_NAME, "Key": thumb_key},
                ExpiresIn=3600
            )
        except Exception as e:
            print(f"Error generating presigned for thumbnailKey={thumb_key}: {e}")
        result["thumbnailLink"] = thumb_url

    return result

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

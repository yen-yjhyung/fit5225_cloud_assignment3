import json
import os
import boto3
import base64
from datetime import datetime
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")

TABLE_NAME = os.environ.get("TABLE_NAME", "BirdMediaTags")
BUCKET_NAME = os.environ.get("BUCKET_NAME", "my-birdtag-test-data")

def lambda_handler(event, context):
    path = event.get("rawPath") or event.get("path", "")
    method = event["requestContext"]["http"]["method"]

    if path == "/query" and method == "POST":
        return handle_query(event)
    elif path == "/find" and method == "POST":
        return handle_find(event)
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

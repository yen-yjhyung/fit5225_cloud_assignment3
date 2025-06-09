import os
import json
import base64
import boto3
from botocore.exceptions import ClientError

AUDIO_TAG_FUNCTION   = os.environ.get("AUDIO_TAG_FUNCTION", "audioFileQuery")
VISUAL_TAG_FUNCTION  = os.environ.get("VISUAL_TAG_FUNCTION", "visualFileQuery")
QUERY_FUNCTION       = os.environ.get("QUERY_FUNCTION", "birdtagquery")
REGION               = os.environ.get("REGION", "us-east-1")

lambda_client = boto3.client("lambda", region_name=REGION)

def lambda_handler(event, context):
    """
    1) POST /query-by-file API
    2) Based on Content-Type, call audio or visual tagging Lambda
    3) Then Call /query Lambda，return query result
    """
    path   = event.get("rawPath") or event.get("path","")
    method = event["requestContext"]["http"]["method"]

    if path == "/query-by-file" and method == "POST":
        return handle_query_by_file(event)
    else:
        return {
            "statusCode": 404,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Not Found"})
        }

def handle_query_by_file(event):
    try:
        headers = {k.lower(): v for k,v in event.get("headers",{}).items()}
        content_type = headers.get("content-type","")
        if not event.get("isBase64Encoded") or "body" not in event:
            return _response(400, {"error":"Expected base64-encoded body"})

        # choose tagging function based on file type
        if content_type.startswith("audio/"):
            tag_fn = AUDIO_TAG_FUNCTION
        elif content_type.startswith("image/") or content_type.startswith("video/"):
            tag_fn = VISUAL_TAG_FUNCTION
        else:
            return _response(415, {"error":f"Unsupported media type {content_type}"})

        # construct tagging event
        tag_event = {
            "isBase64Encoded": True,
            "body": event["body"],
            "headers": {"Content-Type": content_type},
            "requestContext": {"http":{"method":"POST","path":"/tag"}}
        }
        tag_resp = lambda_client.invoke(
            FunctionName=tag_fn,
            InvocationType="RequestResponse",
            Payload=json.dumps(tag_event).encode()
        )
        tag_payload = json.loads(tag_resp["Payload"].read())
        if tag_payload.get("statusCode", 500)!=200:
            return _response(502, {"error":"Tagging failed","requestId":tag_payload.get("requestId")})

        tags = json.loads(tag_payload["body"]).get("tags",[])
        if not tags:
            return _response(500, {"error":"No tags returned"})

        # 5. Prepare payload for /query Lambda, include rawPath so routing works:
        query_event = {
            "rawPath": "/query",
            "path": "/query",
            "rawQueryString": "",
            "headers": {"Content-Type": "application/json"},
            "isBase64Encoded": False,
            "body": json.dumps({"species": tags}),
            "requestContext": {
                "http": {"method": "POST", "path": "/query"}
            }
        }

        # Invoke /query Lambda
        q_resp = lambda_client.invoke(
            FunctionName=QUERY_FUNCTION,
            InvocationType="RequestResponse",
            Payload=json.dumps(query_event).encode('utf-8')
        )
        q_pay = json.loads(q_resp['Payload'].read())

        # return /query result
        return {
            "statusCode": q_pay.get("statusCode", 500),
            "headers": {"Content-Type": "application/json"},
            "body": q_pay.get("body", "{}")
        }

    except ClientError as e:
        return _response(500, {"error":"AWS ClientError","detail":str(e)})
    except Exception as e:
        return _response(500, {"error":"Internal error","detail":str(e)})

def _response(status, body):
    return {
        "statusCode": status,
        "headers":{
            "Content-Type":"application/json",
            "Access-Control-Allow-Origin":"*",
            "Access-Control-Allow-Methods":"OPTIONS,POST,GET",
            "Access-Control-Allow-Headers":"Content-Type,Authorization"
        },
        "body":json.dumps(body)
    }

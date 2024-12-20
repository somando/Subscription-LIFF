import json, base64, urllib.parse
import html_render as html
import api
from decimal import Decimal

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return int(obj)
    raise TypeError


def lambda_handler(event, context):
    
    path = event.get("routeKey", "").split(" ")[1]
    method = event.get("routeKey", "").split(" ")[0]
    path_params = event.get("pathParameters", {})
    params = event.get("queryStringParameters", {})
    isBase64Encoded = event.get("isBase64Encoded", False)
    if isBase64Encoded:
        body = base64.b64decode(event.get("body", "")).decode("utf-8")
        body_params = urllib.parse.parse_qs(body)
    else:
        body_params = event.get("body", "")
    
    print(event)
    print(path, method, params)
    print(body_params)
    
    if "/subscriptionLINEBotLIFF/api/" in path:
        
        body = api.route(path, method, params, path_params, body_params)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/json'
            },
            'body': json.dumps(body, default=decimal_default)
        }
    
    else:
        
        body = html.route(path, method, params, path_params, body_params)
        
        return {
            'statusCode': 200,
            'isBase64Encoded': False,
            'headers': {
                'Content-Type': 'text/html'
            },
            'body': body
        }

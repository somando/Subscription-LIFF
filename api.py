import boto3, requests, json
from boto3.dynamodb.conditions import Key, Attr

import const

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(const.DYNAMODB_TABLE_NAME)


def convertBodyParams(body):
    return body.get('token')


def verifyIdToken(id_token):
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    body = {
        'id_token': id_token,
        'client_id': const.CLIENT_ID
    }
    
    response = requests.post(
        const.LINE_ENDPOINT.VALIDATE_ID_TOKEN, 
        headers=headers, 
        data=body
    )
    
    return response.json()


def getUserItem(user_id, item_id=None):
    if item_id is not None:
        response = table.query(
            KeyConditionExpression=Key('id').eq(item_id),
            FilterExpression=Attr('user').eq(user_id)
        )
        items = response.get('Items', [])
    else:
        response = table.query(
            IndexName='UserIndex',
            KeyConditionExpression=Key('user').eq(user_id),
            ScanIndexForward=True
        )
        items = response.get('Items', [])
        
        while 'LastEvaluatedKey' in response:
            response = table.query(
                IndexName='UserIndex',
                KeyConditionExpression=Key('user').eq(user_id),
                ScanIndexForward=True,
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response.get('Items', []))
    
    print(items)
    
    return items


def deleteUserItem(user_id, item_id):
    
    print("user_id: '" + user_id + "'")
    print("item_id: '" + item_id + "'")
    
    table.delete_item(
        Key={
            'id': item_id
        },
        ConditionExpression=Attr('user').eq(user_id)
    )
    
    return { "status": True }


def route(path, method, params, path_params, body_params):
    
    print("body_params:", body_params)
    
    if method == "GET":
        token = params.get("token", "")
    elif method == "POST":
        token = convertBodyParams(json.loads(body_params))
    user = verifyIdToken(token)
    print("user:", user)
    
    if path == "/subscriptionLINEBotLIFF/api/items" and method == "GET":
        
        body = getUserItem(user.get("sub"))
    
    elif path == "/subscriptionLINEBotLIFF/api/items/{item_id}" and method == "GET":
        
        body = getUserItem(user.get("sub"), path_params.get("item_id"))
    
    elif path == "/subscriptionLINEBotLIFF/api/items/delete/{item_id}" and method == "POST":
        
        body = deleteUserItem(user.get("sub"), path_params.get("item_id"))
        print("body:", body)
    
    return body
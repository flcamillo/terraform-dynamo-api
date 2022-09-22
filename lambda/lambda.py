from uuid import uuid4
import boto3
import os
import json
from datetime import datetime

# inicializa o cliente do dynamodb
dynamodb = boto3.client("dynamodb")

# identifica o nome da tabela a ser usada
tb_user = os.environ["TB_NAME"]


# converte o valor para o DynamoDB
def to_dynamodb_type(items):
    if type(items) == str:
        return {"S": items}
    if type(items) == int:
        return {"N": str(items)}
    if type(items) == bool:
        return {"BOOL": items}
    if type(items) == dict:
        r = {}
        for k in items:
            r[k] = to_dynamodb_type(items[k])
        return {"M": r}
    if type(items) == list:
        r = []
        for k in items:
            r.append(to_dynamodb_type(k))
        return {"L": r}


# serializa os dados para o DynamoDB
def serialize(items):
    r = {}
    for k in items:
        r[k] = to_dynamodb_type(items[k])
    return r


# converte o tipo de dados do DynamoDB para dados simples
def from_dynamodb_type(item):
    for k in item:
        v = item[k]
        if type(v) == dict:
            r = {}
            for j in v:
                r[j] = from_dynamodb_type(v[j])
            return r
        if type(v) == list:
            r = []
            for j in v:
                r.append(from_dynamodb_type(j))
            return r
        if k == 'S':
            return v
        if k == 'N':
            return int(v)
        if k == 'BOOL':
            return v


# converte os itens retornados pelo DynamoDB em um dicionário
def deserialize(items):
    r = {}
    for k in items:
        r[k] = from_dynamodb_type(items[k])
    return r


# cria um usuário
def create_user(event):
    body = json.loads(event["body"])
    item = serialize({
        "id": str(uuid4()),
        "firstName": body["firstName"],
        "lastName": body["lastName"],
        "email": body["email"],
        "password": body["password"],
        "phone": body["phone"],
        "metadata": body["metadata"],
        "status": 1,
        "created": datetime.now().isoformat(),
        "changed": ""
    })
    dynamodb.put_item(
        TableName=tb_user,
        Item=item
    )
    return {
        "statusCode": 201,
        "body": json.dumps(deserialize(item))
    }


# procura um usuário pelo seu id
def get_user(event):
    parms = event["pathParameters"]
    response = dynamodb.get_item(
        TableName=tb_user,
        Key=serialize({"id": parms["id"]})
    )
    item = response.get("Item")
    if item is None:
        return {
            "statusCode": 400,
            "body": "record not found"
        }
    return {
        "statusCode": 200,
        "body": json.dumps(deserialize(item))
    }


# apaga um usuário pelo seu id
def delete_user(event):
    parms = event["pathParameters"]
    response = dynamodb.delete_item(
        TableName=tb_user,
        ReturnValues="ALL_OLD",
        Key=serialize({"id": parms["id"]})
    )
    item = response.get("Attributes")
    if item is None:
        return {
            "statusCode": 400,
            "body": "record not found"
        }
    return {
        "statusCode": 200,
        "body": json.dumps(deserialize(item))
    }


# atualiza um usuário pelo seu id
def update_user(event):
    parms = event["pathParameters"]
    body = json.loads(event["body"])
    response = dynamodb.get_item(
        TableName=tb_user,
        Key=serialize({"id": parms["id"]})
    )
    item = response.get("Item")
    if item is None:
        return {
            "statusCode": 400,
            "body": "record not found"
        }
    item = deserialize(item)
    v = body.get("firstName")
    if v is not None:
        item["firstName"] = v
    v = body.get("lastName")
    if v is not None:
        item["lastName"] = v
    v = body.get("email")
    if v is not None:
        item["email"] = v
    v = body.get("password")
    if v is not None:
        item["password"] = v
    v = body.get("phone")
    if v is not None:
        item["phone"] = v
    v = body.get("metadata")
    if v is not None:
        item["metadata"] = v
    v = body.get("status")
    if v is not None:
        item["status"] = v
    item["changed"] = datetime.now().isoformat()
    dynamodb.put_item(
        TableName=tb_user,
        Item=serialize(item)
    )
    return {
        "statusCode": 200,
        "body": json.dumps(item)
    }


# função principal da lambda
def lambda_handler(event, context):
    print(event)
    # define as rotas da api
    routes = {
        "/user": {
            "POST": create_user
        },
        "/user/{id}": {
            "PUT": update_user,
            "DELETE": delete_user,
            "GET": get_user
        }
    }
    # executa a rota solicitada
    route = routes.get(event["resource"])
    if route is None:
        return {
            "statusCode": 400
        }
    method = route.get(event["httpMethod"])
    if method is None:
        return {
            "statusCode": 400
        }
    return method(event)

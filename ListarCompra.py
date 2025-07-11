import json
import boto3
import os

dynamodb = boto3.client('dynamodb')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    print("Evento recibido:", json.dumps(event))

    try:
        # Leer parámetros del query string
        params = event.get('queryStringParameters', {}) or {}
        tenant_id = params.get('tenant_id')
        username = params.get('username')
        startKey = params.get('startKey')

        print(f"tenant_id recibido: {tenant_id}")
        print(f"username recibido: {username}")
        print(f"startKey recibido: {startKey}")

        token = event['headers']['Authorization']
        print(f"TOKEN recibido en header: {token}")

        # Validar el token
        payload = {
            "body": json.dumps({
                "tenant_id": tenant_id,
                "token": token
            })
        }

        print("Payload para ValidarTokenAcceso:", json.dumps(payload))

        response = lambda_client.invoke(
            FunctionName=os.environ['VALIDAR_TOKEN_FUNC'], 
            InvocationType="RequestResponse",
            Payload=json.dumps(payload)
        )

        response_payload = json.loads(response['Payload'].read())
        print("Respuesta de ValidarTokenAcceso:", json.dumps(response_payload))

        if response_payload['statusCode'] == 403:
            print("Token inválido, terminando con 403.")
            return {
                'statusCode': 403,
                'body': json.dumps({ "error": "Forbidden - Acceso No Autorizado" })
            }


        # Query en DynamoDB para traer las compras del usuario
        key_condition = "tenant_id = :tenant_id AND begins_with(username#compra_id, :prefix)"
        expression_values = {
            ":tenant_id": {"S": tenant_id},
            ":prefix": {"S": f"{username}#"}
        }

        query_params = {
            "TableName": os.environ['TABLE_NAME_PURCHASES'],
            "KeyConditionExpression": "tenant_id = :tenant_id AND begins_with(#sk, :prefix)",
            "ExpressionAttributeValues": {
                ":tenant_id": {"S": tenant_id},
                ":prefix": {"S": f"{username}#"}
            },
            "ExpressionAttributeNames": {
                "#sk": "username#compra_id"
            },
            "Limit": 10
        }

        if startKey:
            query_params["ExclusiveStartKey"] = {
                "tenant_id": {"S": tenant_id},
                "username_compra_id": {"S": startKey}
            }
            print("Se usará paginación con ExclusiveStartKey:", json.dumps(query_params["ExclusiveStartKey"]))

        print("Parámetros para Query:", json.dumps(query_params))

        result = dynamodb.query(**query_params)
        print("Resultado Query:", json.dumps(result))

        # Formatear los resultados
   
        compras = []
        for item in result.get("Items", []):
            compras.append({
                "tenant_id": item["tenant_id"]["S"],
                "username#compra_id": item["username#compra_id"]["S"],
                "username": item["username"]["S"],
                "items": json.loads(item["items"]["S"]),
                "total": float(item["total"]["N"]),
                "timestamp": item["timestamp"]["S"]
            })

        response_body = {
            "compras": compras
        }


        # Paginación
        if "LastEvaluatedKey" in result:
            last_key = result["LastEvaluatedKey"]
            response_body["lastKey"] = last_key["username_compra_id"]["S"]
            print("Último evaluated key para próxima página:", json.dumps(last_key))

        return {
            'statusCode': 200,
            'body': json.dumps(response_body)
        }

    except Exception as e:
        print("ERROR en ListarCompra:", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({
                "error": "No se pudo listar las compras",
                "details": str(e)
            })
        }

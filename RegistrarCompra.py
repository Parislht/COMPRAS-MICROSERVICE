import json
import boto3
import uuid
import os
from datetime import datetime

# Inicializar clientes
dynamodb = boto3.client('dynamodb')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    print("Evento recibido:", json.dumps(event))

    try:
        # Extraer tenant_id y token
        body = json.loads(event['body'])
        tenant_id = body['tenant_id']
        username = body['username']
        items = body['items']
        total = body['total']

        token = event['headers']['Authorization']

        print(f"tenant_id: {tenant_id}")
        print(f"username: {username}")
        print(f"items: {items}")
        print(f"total: {total}")
        print(f"TOKEN recibido en header: {token}")

        # Validar token
        payload = {
            "body": json.dumps({
                "tenant_id": tenant_id,
                "token": token
            })
        }

        print("Payload para ValidarTokenAcceso:", json.dumps(payload))

        response = lambda_client.invoke(
            FunctionName=os.environ['VALIDAR_TOKEN_FUNC'],#CAMBIAR NOMBRE DE FUNCION LAMBDA OFICIAL
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

        # Registrar compra en DynamoDB
        compra_id = str(uuid.uuid4())
        username_compra_id = f"{username}#{compra_id}"
        timestamp = datetime.utcnow().isoformat()

        print(f"Generado username#compra_id: {username_compra_id}")

        item = {
            "tenant_id": { "S": tenant_id },
            "username#compra_id": { "S": username_compra_id },
            "username": { "S": username },
            "items": { "S": json.dumps(items) },
            "total": { "N": str(total) },
            "timestamp": { "S": timestamp }
        }

        print("Item que se guardará en DynamoDB:", json.dumps(item))

        dynamodb.put_item(
            TableName=os.environ['TABLE_NAME_PURCHASES'],
            Item=item
        )

        print("Compra registrada exitosamente.")

        return {
            'statusCode': 200,
            'body': json.dumps({
                "message": "Compra registrada exitosamente",
                "compra_id": compra_id
            })
        }

    except Exception as e:
        print("ERROR en RegistrarCompra:", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({
                "error": "No se pudo registrar la compra",
                "details": str(e)
            })
        }

import boto3 
import csv
import io
import json
from datetime import datetime

# Cliente S3
s3 = boto3.client('s3')
BUCKET_NAME = 'compras-proyecto-prueba-phlt' #CAMBIAR NOMBRE OFICIAL

def lambda_handler(event, context):

    print("Evento recibido:", json.dumps(event))
    
    try:
        # Buffers en memoria para los dos CSVs
        csv_compras_buffer = io.StringIO()
        csv_items_buffer = io.StringIO()
        
        csv_compras_writer = csv.writer(csv_compras_buffer)
        csv_items_writer = csv.writer(csv_items_buffer)
        
        for record in event['Records']:
            event_name = record['eventName']
            print(f"Procesando evento: {event_name}")
            
            if event_name == 'INSERT':
                new_image = record['dynamodb']['NewImage']
                
                tenant_id = new_image['tenant_id']['S']
                username_compra_id = new_image['username#compra_id']['S']
                username, compra_id = username_compra_id.split('#', 1)
                items_json = new_image['items']['S']
                timestamp_val = new_image['timestamp']['S']
                total = new_image['total']['N']
                
                # CSV de compras (cabecera)
                csv_compras_writer.writerow([tenant_id, username, compra_id, timestamp_val, total])
                
                # CSV de items (detalle)
                items = json.loads(items_json)
                for item in items:
                    libro_id = item['libro_id']
                    cantidad = item['cantidad']
                    csv_items_writer.writerow([compra_id, tenant_id, libro_id, cantidad])
        
        # Generar nombres de archivos
        timestamp_file = datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%S')
        file_compras = f'compras/compras-{timestamp_file}.csv'
        file_items = f'items_comprados/items-{timestamp_file}.csv'
        
        # Subir archivos a S3
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=file_compras,
            Body=csv_compras_buffer.getvalue()
        )
        print(f"Archivo CSV compras guardado en S3: s3://{BUCKET_NAME}/{file_compras}")
        
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=file_items,
            Body=csv_items_buffer.getvalue()
        )
        print(f"Archivo CSV items guardado en S3: s3://{BUCKET_NAME}/{file_items}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Archivos guardados: compras -> s3://{BUCKET_NAME}/{file_compras}, items -> s3://{BUCKET_NAME}/{file_items}'
            })
        }
        
    except Exception as e:
        print("ERROR en ActualizarCompras:", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': "Error procesando el Stream",
                'details': str(e)
            })
        }

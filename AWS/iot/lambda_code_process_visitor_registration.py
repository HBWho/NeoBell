import json
import boto3
import os
import logging
from datetime import datetime, timezone
from urllib.parse import unquote_plus

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Pegue esses valores das variáveis de ambiente da Lambda
PERMISSIONS_TABLE_NAME = os.environ.get('PERMISSIONS_TABLE_NAME', 'Permissions')
NEOBELLDEVICES_TABLE_NAME = os.environ.get('NEOBELLDEVICES_TABLE_NAME', 'NeoBellDevices')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
NOTIFICATION_LAMBDA_NAME = os.environ.get('NOTIFICATION_LAMBDA_NAME', 'NeoBellNotificationHandler')

dynamodb_resource = boto3.resource('dynamodb', region_name=AWS_REGION)
s3_client = boto3.client('s3', region_name=AWS_REGION)
lambda_client = boto3.client('lambda', region_name='us-east-1')

def lambda_handler(event, context):
    logger.info(f"Evento S3 recebido: {json.dumps(event)}")

    permissions_table = dynamodb_resource.Table(PERMISSIONS_TABLE_NAME)
    neobell_devices_table = dynamodb_resource.Table(NEOBELLDEVICES_TABLE_NAME)

    try:
        # Extrair informações do bucket e do objeto do evento S3
        s3_event_record = event['Records'][0]['s3']
        bucket_name = s3_event_record['bucket']['name']
        # A chave do objeto pode ter caracteres especiais (ex: espaços), então decodifique
        object_key = unquote_plus(s3_event_record['object']['key'])

        logger.info(f"Processando objeto '{object_key}' do bucket '{bucket_name}'.")

        # 1. Obter metadados do objeto S3
        # O SBC deve ter enviado os metadados como x-amz-meta-*
        # O S3 armazena as chaves de metadados em minúsculas.
        head_object_response = s3_client.head_object(Bucket=bucket_name, Key=object_key)
        metadata = head_object_response.get('Metadata', {})
        logger.info(f"Metadados do objeto S3: {metadata}")

        sbc_id = metadata.get('sbc-id') # Chave em minúsculas
        face_tag_id = metadata.get('face-tag-id')
        visitor_name = metadata.get('visitor-name')
        permission_level = metadata.get('permission-level')

        if not all([sbc_id, face_tag_id, visitor_name, permission_level]):
            logger.error("Metadados necessários (sbc-id, face-tag-id, visitor-name, permission-level) ausentes no objeto S3.")
            # Você pode querer mover o objeto para uma pasta de 'erros' ou remover
            s3_client.delete_object(Bucket=bucket_name, Key=object_key)
            return {'statusCode': 400, 'body': 'Metadados ausentes'}

        # 2. Consultar a tabela NeoBellDevices para obter o owner_user_id
        device_response = neobell_devices_table.get_item(
            Key={'sbc_id': sbc_id}
        )
        device_item = device_response.get('Item')

        if not device_item or 'owner_user_id' not in device_item:
            logger.error(f"SBC com sbc_id '{sbc_id}' não encontrado na tabela '{NEOBELLDEVICES_TABLE_NAME}' ou owner_user_id ausente.")
            s3_client.delete_object(Bucket=bucket_name, Key=object_key)
            return {'statusCode': 404, 'body': 'SBC não encontrado ou owner_user_id ausente'}

        owner_user_id = device_item['owner_user_id']
        logger.info(f"owner_user_id '{owner_user_id}' encontrado para sbc_id '{sbc_id}'.")

        # 3. Construir e salvar o item na tabela Permissions
        current_time_iso = datetime.now(timezone.utc).isoformat()

        permissions_item = {
            'user_id': owner_user_id,         # PK da tabela Permissions
            'face_tag_id': face_tag_id,       # SK da tabela Permissions
            'visitor_name': visitor_name,
            'permission_level': permission_level,
            'sbc_id_registrar': sbc_id,       # SBC que fez o registro
            'image_s3_bucket': bucket_name,   # Para referência
            'image_s3_key': object_key,       # Para referência
            'created_at': current_time_iso,
            'last_updated_at': current_time_iso
        }

        permissions_table.put_item(Item=permissions_item)
        logger.info(f"Item salvo na tabela '{PERMISSIONS_TABLE_NAME}': {json.dumps(permissions_item)}")

        # Enviar notificação (SNS, via outra Lambda)
        notification_request_payload = {
            "sbc_id": sbc_id,
            "notification_type": "visitor_registration",
            "message_payload": {
                "title": "New Visitor Register!",
                "body": f"You have a new visitor register in the NeoBell via {sbc_id}",
                "data": {
                    "screen_target": "visitor-permission-details",
                    "face_tag_id": face_tag_id,
                }
            }
        }
        try:
            logger.info(f"Invocando NeoBellNotificationHandler para usuários do device {sbc_id} com payload: {json.dumps(notification_request_payload)}")
            response = lambda_client.invoke(
                FunctionName=NOTIFICATION_LAMBDA_NAME,
                InvocationType='Event',  # Invocação Assíncrona (fire and forget)
                Payload=json.dumps(notification_request_payload)
            )
            # Para InvocationType='Event', o status code 202 significa que o evento foi enfileirado com sucesso.
            if response.get('StatusCode') == 202:
                logger.info(f"NeoBellNotificationHandler invocada com sucesso para usuários do device {sbc_id}.")
            else:
                logger.warning(f"Invocação da NeoBellNotificationHandler para usuários do device {sbc_id} retornou status inesperado: {response.get('StatusCode')}. Resposta: {response.get('Payload', '{}').read().decode()}")
        except Exception as e:
            logger.error(f"Erro ao invocar NeoBellNotificationHandler para usuários do device {sbc_id}: {e}")

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Registro de visitante processado com sucesso!', 'item_saved': permissions_item})
        }

    except Exception as e:
        logger.error(f"Erro ao processar evento S3: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # Re-raise a exceção para que a Lambda possa tentar novamente se configurado, ou enviar para DLQ
        raise e
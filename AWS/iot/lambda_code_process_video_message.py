import json
import boto3
import os
import logging
from urllib.parse import unquote_plus
import traceback

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Variáveis de ambiente (a serem configuradas na Lambda)
VIDEOMESSAGES_TABLE_NAME = os.environ.get('VIDEOMESSAGES_TABLE_NAME', 'VideoMessages')
NEOBELLDEVICES_TABLE_NAME = os.environ.get('NEOBELLDEVICES_TABLE_NAME', 'NeoBellDevices')
NOTIFICATION_LAMBDA_NAME = os.environ.get('NOTIFICATION_LAMBDA_NAME', 'NeoBellNotificationHandler')

dynamodb_resource = boto3.resource('dynamodb', region_name="us-east-1")
s3_client = boto3.client('s3', region_name="us-east-1")
lambda_client = boto3.client('lambda', region_name='us-east-1')

def lambda_handler(event, context):
    logger.info(f"Evento S3 recebido: {json.dumps(event)}")

    video_messages_table = dynamodb_resource.Table(VIDEOMESSAGES_TABLE_NAME)
    devices_table = dynamodb_resource.Table(NEOBELLDEVICES_TABLE_NAME)

    try:
        # Extrair informações do bucket e do objeto do evento S3
        s3_event_record = event['Records'][0]['s3']
        bucket_name = s3_event_record['bucket']['name']
        object_key = unquote_plus(s3_event_record['object']['key']) # Decodificar chave

        logger.info(f"Processando objeto '{object_key}' do bucket '{bucket_name}'.")

        # 1. Obter metadados do objeto S3 (enviados pelo SBC)
        # S3 armazena chaves de metadados em minúsculas.
        head_object_response = s3_client.head_object(Bucket=bucket_name, Key=object_key)
        metadata = head_object_response.get('Metadata', {})
        logger.info(f"Metadados do objeto S3: {metadata}")

        # Metadados esperados (chaves em minúsculas)
        sbc_id = metadata.get('sbc-id')
        message_id = metadata.get('message-id')
        recorded_at = metadata.get('recorded-at') # Timestamp ISO8601
        duration_sec_str = metadata.get('duration-sec')
        visitor_face_tag_id = metadata.get('visitor-face-tag-id')

        if not all([sbc_id, message_id, recorded_at, visitor_face_tag_id]):
            logger.error("Metadados essenciais (sbc-id, message-id, recorded-at, visitor_face_tag_id) ausentes.")
            return {'statusCode': 400, 'body': 'Metadados essenciais ausentes'}

        duration_sec = None
        if duration_sec_str:
            try:
                duration_sec = int(duration_sec_str)
            except ValueError:
                logger.warning(f"Valor de duration-sec inválido: {duration_sec_str}. Será armazenado como string ou nulo.")
                duration_sec = duration_sec_str # Ou None, dependendo de como quer tratar

        # 2. Consultar a tabela NeoBellDevices para obter o owner_user_id
        try:
            device_response = devices_table.get_item(Key={'sbc_id': sbc_id})
            if 'Item' not in device_response or 'owner_user_id' not in device_response['Item']:
                logger.error(f"owner_user_id não encontrado para sbc_id: {sbc_id}")
                # Considere mover o objeto S3 para uma pasta de 'erros'
                return {'statusCode': 404, 'body': f"Dispositivo {sbc_id} não encontrado ou sem proprietário."}
            owner_user_id = device_response['Item']['owner_user_id']
        except Exception as e_db_devices:
            logger.error(f"Erro ao consultar DynamoDB (NeoBellDevices): {str(e_db_devices)}", exc_info=True)
            return {'statusCode': 500, 'body': f"Erro interno ao buscar dados do dispositivo: {str(e_db_devices)}."}

        logger.info(f"owner_user_id '{owner_user_id}' encontrado para sbc_id '{sbc_id}'.")

        # 3. Construir e salvar o item na tabela VideoMessages
        video_message_item = {
            'user_id': owner_user_id,           # PK
            'message_id': message_id,           # SK
            'sbc_id': sbc_id,
            'visitor_face_tag_id': visitor_face_tag_id,
            'recorded_at': recorded_at,         # Para GSI sbc-id-recorded-at-index
            's3_bucket_name': bucket_name,
            's3_object_key': object_key,
            'is_viewed': False,                 # Default
        }
        if duration_sec is not None: # Adicionar apenas se existir e for válido
            video_message_item['duration_sec'] = duration_sec

        video_messages_table.put_item(Item=video_message_item)
        logger.info(f"Item salvo na tabela '{VIDEOMESSAGES_TABLE_NAME}': {json.dumps(video_message_item)}")

        # Enviar notificação (SNS, via outra Lambda)
        notification_request_payload = {
            "sbc_id": sbc_id,
            "notification_type": "video_message",
            "message_payload": {
                "title": "New Video Message Received!",
                "body": f"You have a new video message from {sbc_id}",
                "data": {
                    "screen_target": "watch-video",
                    "message_id": message_id
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
            'body': json.dumps({'message': 'Mensagem de vídeo processada com sucesso!', 'item_saved': video_message_item})
        }

    except Exception as e:
        logger.error(f"Erro ao processar evento S3: {str(e)}", exc_info=True)
        # Re-raise a exceção para que a Lambda possa tentar novamente se configurado, ou enviar para DLQ
        raise e
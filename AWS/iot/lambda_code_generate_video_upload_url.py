import json
import boto3
import os
import logging
import uuid
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Variáveis de ambiente (a serem configuradas na Lambda)
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'neobell-videomessages-hbwho')
NEOBELLDEVICES_TABLE_NAME = os.environ.get('NEOBELLDEVICES_TABLE_NAME', 'NeoBellDevices')
PERMISSIONS_TABLE_NAME = os.environ.get('PERMISSIONS_TABLE_NAME', 'Permissions')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

RESPONSE_TOPIC_TEMPLATE = "neobell/sbc/{sbc_id}/messages/upload-url-response"
PRESIGNED_URL_EXPIRATION = 300  # Segundos (5 minutos)
REQUIRED_PERMISSION_FOR_VIDEO = "Allowed"

s3_client = boto3.client('s3', region_name="us-east-1", config=boto3.session.Config(signature_version='s3v4'))
iot_data_client = boto3.client('iot-data', region_name="us-east-1")
dynamodb_resource = boto3.resource('dynamodb', region_name="us-east-1")

def lambda_handler(event, context):
    logger.info(f"NeoBellGenerateVideoUploadUrlHandler - Evento recebido: {json.dumps(event)}")

    # Validação das variáveis de ambiente essenciais
    if not all([S3_BUCKET_NAME, NEOBELLDEVICES_TABLE_NAME, PERMISSIONS_TABLE_NAME]):
        logger.error("Uma ou mais variáveis de ambiente cruciais (S3_BUCKET_NAME, NEOBELLDEVICES_TABLE_NAME, PERMISSIONS_TABLE_NAME) não estão configuradas.")
        return {'statusCode': 500, 'body': json.dumps({'error': 'Configuração interna do servidor incompleta.'})}

    sbc_id = event.get('sbc_id') # Injetado pela Regra IoT (ex: topic(3))
    visitor_face_tag_id = event.get('visitor_face_tag_id')
    if not sbc_id or not visitor_face_tag_id:
        logger.error("Requisição incompleta. sbc_id e visitor_face_tag_id são obrigatórios")
        return {'statusCode': 400, 'body': json.dumps({'error': 'sbc_id e visitor_face_tag_id são obrigatórios'})}

    # Payload esperado do SBC
    duration_sec_str = event.get('duration_sec')
    duration_sec = None
    if duration_sec_str:
        try:
            duration_sec = int(duration_sec_str)
        except ValueError:
            logger.warning(f"Valor de duration_sec inválido: {duration_sec_str}. Será ignorado.")

    try:
            # 1. Consultar NeoBellDevices para obter owner_user_id
        devices_table = dynamodb_resource.Table(NEOBELLDEVICES_TABLE_NAME)
        device_response = devices_table.get_item(Key={'sbc_id': sbc_id})
        if 'Item' not in device_response or 'owner_user_id' not in device_response['Item']:
            logger.error(f"owner_user_id não encontrado para sbc_id: {sbc_id}")
            return {'statusCode': 404, 'body': json.dumps({'error': f"Dispositivo {sbc_id} não registrado ou sem proprietário."})}
        owner_user_id = device_response['Item']['owner_user_id']
        logger.info(f"Dispositivo {sbc_id} pertence ao owner_user_id: {owner_user_id}")

        # 2. Verificar permissão do visitante na tabela Permissions
        permissions_table = dynamodb_resource.Table(PERMISSIONS_TABLE_NAME)
        permission_response = permissions_table.get_item(
            Key={
                'user_id': owner_user_id,       # PK da tabela Permissions
                'face_tag_id': visitor_face_tag_id # SK da tabela Permissions
            }
        )

        if 'Item' not in permission_response:
            logger.warning(f"Permissão não encontrada para owner_user_id: {owner_user_id}, visitor_face_tag_id: {visitor_face_tag_id}. Upload não autorizado.")
            topic_to_publish_error = RESPONSE_TOPIC_TEMPLATE.format(sbc_id=sbc_id)
            error_payload = {'error': 'Visitor not recognized or no permissions set.', 'visitor_face_tag_id': visitor_face_tag_id}
            iot_data_client.publish(topic=topic_to_publish_error, qos=1, payload=json.dumps(error_payload))
            return {'statusCode': 403, 'body': json.dumps({'error': 'Visitante não reconhecido ou sem permissões configuradas.'})}

        visitor_permission = permission_response['Item']
        permission_level = visitor_permission.get('permission_level')
        visitor_name = visitor_permission.get('visitor_name', 'Visitante') # Pegar nome para logs, se disponível

        logger.info(f"Permissão encontrada para {visitor_name} (face_tag: {visitor_face_tag_id}): Nível '{permission_level}'")

        if permission_level != REQUIRED_PERMISSION_FOR_VIDEO:
            logger.warning(f"Visitante {visitor_name} (face_tag: {visitor_face_tag_id}) não tem a permissão '{REQUIRED_PERMISSION_FOR_VIDEO}' (tem '{permission_level}'). Upload não autorizado.")
            topic_to_publish_error = RESPONSE_TOPIC_TEMPLATE.format(sbc_id=sbc_id)
            error_payload = {'error': f'Visitor does not have permission to leave video messages. Required: {REQUIRED_PERMISSION_FOR_VIDEO}, Found: {permission_level}', 'visitor_face_tag_id': visitor_face_tag_id}
            iot_data_client.publish(topic=topic_to_publish_error, qos=1, payload=json.dumps(error_payload))
            return {'statusCode': 403, 'body': json.dumps({'error': 'Visitante não tem permissão para deixar mensagens de vídeo.'})}

        # 2. Gerar message_id e recorded_at timestamp
        message_id = str(uuid.uuid4())
        recorded_at = datetime.now(timezone.utc).isoformat()

        # Gerar partes da data para o caminho S3
        now = datetime.now(timezone.utc)
        ano = now.strftime("%Y")
        mes = now.strftime("%m")
        dia = now.strftime("%d")

        object_key = f"video-messages/{sbc_id}/{owner_user_id}/{ano}-{mes}-{dia}/{message_id}.mp4"
        logger.info(f"Caminho S3 gerado: {object_key}")

        # 3. Metadados que o SBC DEVE incluir no upload para S3
        required_metadata = {
            "sbc-id": sbc_id,
            "message-id": message_id,
            "recorded-at": recorded_at,
            "visitor-face-tag-id": visitor_face_tag_id
        }
        if duration_sec is not None:
            required_metadata["duration-sec"] = str(duration_sec)

        presigned_url_params = {
            'Bucket': S3_BUCKET_NAME,
            'Key': object_key,
            'ContentType': 'video/mp4',
            'Metadata': required_metadata
        }

        presigned_url = s3_client.generate_presigned_url(
            ClientMethod='put_object',
            Params=presigned_url_params,
            ExpiresIn=PRESIGNED_URL_EXPIRATION,
            HttpMethod='PUT'
        )
        logger.info(f"URL pré-assinada gerada: {presigned_url}")

        response_payload_mqtt = {
            'presigned_url': presigned_url,
            'message_id': message_id,
            'object_key': object_key,
            'required_metadata_headers': {f"x-amz-meta-{k.lower()}": v for k,v in required_metadata.items()}
        }

        topic_to_publish = RESPONSE_TOPIC_TEMPLATE.format(sbc_id=sbc_id)
        iot_data_client.publish(
            topic=topic_to_publish,
            qos=1,
            payload=json.dumps(response_payload_mqtt)
        )
        logger.info(f"Resposta publicada no tópico MQTT: {topic_to_publish}")

        return { # Esta é a resposta da invocação da Lambda, não a resposta MQTT
            'statusCode': 200,
            'body': json.dumps({
                'message': 'URL pré-assinada gerada e publicada no MQTT.',
                'published_to_topic': topic_to_publish,
                'mqtt_payload': response_payload_mqtt
            })
        }
    except Exception as e:
        logger.error(f"Erro ao gerar URL pré-assinada ou publicar no MQTT: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f"Erro interno: {str(e)}."})
        }
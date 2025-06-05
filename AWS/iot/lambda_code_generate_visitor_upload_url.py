# lambda_code_generate_visitor_upload_url.py
import json
import boto3
import os
import logging
import traceback

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Variáveis de ambiente esperadas: S3_BUCKET_NAME, AWS_REGION
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'neobell-videomessages-hbwho')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

RESPONSE_TOPIC_TEMPLATE = "neobell/sbc/{sbc_id}/registrations/upload-url-response"
PRESIGNED_URL_EXPIRATION = 300  # Segundos

s3_client = boto3.client('s3', region_name=AWS_REGION, config=boto3.session.Config(signature_version='s3v4'))
iot_data_client = boto3.client('iot-data', region_name=AWS_REGION)

def lambda_handler(event, context):
    logger.info(f"NeoBellGenerateVisitorUploadUrlHandler - Evento recebido: {json.dumps(event)}")

    if not S3_BUCKET_NAME:
        logger.error("Variável de ambiente S3_BUCKET_NAME não configurada.")
        return {'statusCode': 500, 'body': json.dumps({'error': 'Configuração interna do servidor: S3_BUCKET_NAME ausente.'})}

    sbc_id = event.get('sbc_id')
    face_tag_id = event.get('face_tag_id')
    visitor_name = event.get('visitor_name')
    permission_level = event.get('permission_level')
    if not all([sbc_id, face_tag_id, visitor_name]):
        logger.error("Requição incompleta. sbc_id, face_tag_id, visitor_name e permission_level são obrigatório")
        topic_to_publish_error = RESPONSE_TOPIC_TEMPLATE.format(sbc_id=sbc_id)
        error_payload = {
            'error': 'Requição incompleta. sbc_id, face_tag_id, visitor_name e permission_level são obrigatório',
            'sbc_id': sbc_id,
            'face_tag_id': face_tag_id,
            'visitor_name': visitor_name,
            'permission_level': permission_level
        }
        iot_data_client.publish(topic=topic_to_publish_error, qos=1, payload=json.dumps(error_payload))
        return {'statusCode': 400, 'body': json.dumps({'error': 'sbc_id, face_tag_id, visitor_name e permission_level são obrigatório'})}
    

    if permission_level not in ['Allowed', 'Denied']:
        logger.error("Nível de permissão inválido. Deve ser 'Allowed' ou 'Denied'")
        topic_to_publish_error = RESPONSE_TOPIC_TEMPLATE.format(sbc_id=sbc_id)
        error_payload = {
            'error': 'Nível de permissão inválido. Deve ser "Allowed" ou "Denied"',
            'sbc_id': sbc_id,
            'face_tag_id': face_tag_id,
            'visitor_name': visitor_name,
            'permission_level': permission_level
        }
        iot_data_client.publish(topic=topic_to_publish_error, qos=1, payload=json.dumps(error_payload))
        return {'statusCode': 400, 'body': json.dumps({'error': 'Nível de permissão inválido. Deve ser "Allowed" ou "Denied"'})}

    object_key = f"visitor-registrations/{sbc_id}/{face_tag_id}/image.jpg"
    logger.info(f"Caminho S3 gerado: {object_key}")

    required_metadata = {
        "sbc-id": sbc_id,
        "face-tag-id": face_tag_id,
        "visitor-name": visitor_name,
        "permission-level": permission_level
    }
    
    try:
        presigned_url_params = {
            'Bucket': S3_BUCKET_NAME,
            'Key': object_key,
            'ContentType': 'image/jpeg', # O cliente deve tentar corresponder a isso
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
            'object_key': object_key,
            'sbc_id': sbc_id,
            'face_tag_id': face_tag_id,
            'visitor_name': visitor_name,
            'permission_level': permission_level,
            'message': 'Use esta URL para fazer upload da imagem do visitante com os metadados corretos.',
            'required_metadata_headers': {f"x-amz-meta-{k.lower()}": v for k,v in required_metadata.items()}
        }

        topic_to_publish = RESPONSE_TOPIC_TEMPLATE.format(sbc_id=sbc_id)
        iot_data_client.publish(
            topic=topic_to_publish,
            qos=1,
            payload=json.dumps(response_payload_mqtt)
        )
        logger.info(f"Resposta publicada no tópico MQTT: {topic_to_publish}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'URL pré-assinada para imagem de visitante gerada e publicada no MQTT.',
                'published_to_topic': topic_to_publish
            })
        }

    except Exception as e:
        logger.error(f"Erro ao gerar URL pré-assinada ou publicar no MQTT: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f"Erro interno ao processar solicitação de upload de imagem: {str(e)}."})
        }

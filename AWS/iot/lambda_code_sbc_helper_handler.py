import json
import boto3
import os
import logging
import uuid # Para gerar IDs
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Variáveis de ambiente (a serem configuradas na Lambda)
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
NEOBELLDEVICES_TABLE_NAME = os.environ.get('NEOBELLDEVICES_TABLE_NAME', 'NeoBellDevices')
PERMISSIONS_TABLE_NAME = os.environ.get('PERMISSIONS_TABLE_NAME', 'Permissions')
EXPECTEDDELIVERIES_TABLE_NAME = os.environ.get('EXPECTEDDELIVERIES_TABLE_NAME', 'ExpectedDeliveries')
EVENTLOGS_TABLE_NAME = os.environ.get('EVENTLOGS_TABLE_NAME', 'EventLogs')
DEVICEUSERLINKS_TABLE_NAME = os.environ.get('DEVICEUSERLINKS_TABLE_NAME', 'DeviceUserLinks')
USER_NFC_TAGS_TABLE_NAME = os.environ.get('USER_NFC_TAGS_TABLE_NAME', 'UserNFCTags')
NOTIFICATION_LAMBDA_NAME_ENV = os.environ.get('NOTIFICATION_LAMBDA_NAME', 'NeoBellNotificationHandler')

# Tópicos de resposta MQTT (parciais, sbc_id será formatado)
PERMISSIONS_RESPONSE_TOPIC_TPL = "neobell/sbc/{sbc_id}/permissions/response"
PACKAGES_RESPONSE_TOPIC_TPL = "neobell/sbc/{sbc_id}/packages/response"
NFC_VERIFY_RESPONSE_TOPIC_TPL = "neobell/sbc/{sbc_id}/nfc/verify-tag/response"

# Clientes AWS
dynamodb_resource = boto3.resource('dynamodb', region_name=AWS_REGION)
iot_data_client = boto3.client('iot-data', region_name=AWS_REGION)
lambda_client = boto3.client('lambda', region_name=AWS_REGION)

# --- Funções de Lógica Específica ---

def get_owner_user_id(sbc_id):
    """Busca o owner_user_id de um sbc_id na tabela NeoBellDevices."""
    if not NEOBELLDEVICES_TABLE_NAME:
        logger.error("Nome da tabela NeoBellDevices não configurado nas variáveis de ambiente.")
        raise ValueError("Configuração da tabela de dispositivos ausente.")
    try:
        devices_table = dynamodb_resource.Table(NEOBELLDEVICES_TABLE_NAME)
        response = devices_table.get_item(Key={'sbc_id': sbc_id})
        if 'Item' in response and 'owner_user_id' in response['Item']:
            return response['Item']['owner_user_id']
        else:
            logger.warning(f"owner_user_id não encontrado para sbc_id: {sbc_id}")
            return None
    except Exception as e:
        logger.error(f"Erro ao buscar owner_user_id para {sbc_id}: {str(e)}", exc_info=True)
        raise

def handle_permission_request(sbc_id, payload):
    logger.info(f"Processando requisicao_de_permissao_de_pessoa para sbc_id: {sbc_id}, payload: {payload}")
    if not PERMISSIONS_TABLE_NAME:
        logger.error("Nome da tabela Permissions não configurado.")
        return {"error": "Configuração da tabela de permissões ausente."}

    face_tag_id = payload.get('face_tag_id')
    if not face_tag_id:
        logger.error("face_tag_id ausente no payload para handle_permission_request.")
        return {"error": "face_tag_id ausente no payload."}

    try:
        owner_user_id = get_owner_user_id(sbc_id)
        if not owner_user_id:
            logger.warning(f"Proprietário não encontrado para o dispositivo {sbc_id} ao verificar permissões.")
            return error_response_data

        permissions_table = dynamodb_resource.Table(PERMISSIONS_TABLE_NAME)
        response = permissions_table.get_item(
            Key={'user_id': owner_user_id, 'face_tag_id': face_tag_id}
        )
        
        response_data = {}
        if 'Item' in response:
            response_data = {
                "permission_exists": True,
                "permission_level": response['Item'].get('permission_level'),
                "visitor_name": response['Item'].get('visitor_name', 'N/A'),
                "face_tag_id": face_tag_id
            }
        else:
            response_data = {"permission_exists": False, "face_tag_id": face_tag_id}
        
        logger.info(f"Resposta de permissão: {response_data}")
        return response_data
    except Exception as e:
        logger.error(f"Erro em handle_permission_request para sbc_id {sbc_id}: {str(e)}", exc_info=True)
        error_response_data = {"permission_exists": False, "face_tag_id": face_tag_id, "error": "Erro interno ao processar permissão."}
        return error_response_data


def get_users_for_sbc(sbc_id):
    """
    Busca todos os user_ids vinculados a um sbc_id na tabela DeviceUserLinks.
    """
    if not DEVICEUSERLINKS_TABLE_NAME:
        logger.error("Nome da tabela DeviceUserLinks não configurado.")
        return [] # Retorna lista vazia para indicar falha ou ausência de configuração
    try:
        links_table = dynamodb_resource.Table(DEVICEUSERLINKS_TABLE_NAME)
        response = links_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('sbc_id').eq(sbc_id)
        )
        user_ids = [item['user_id'] for item in response.get('Items', []) if 'user_id' in item] # Garantir que user_id existe
        logger.info(f"Usuários encontrados para sbc_id {sbc_id} em DeviceUserLinks: {user_ids}")
        return user_ids
    except Exception as e:
        logger.error(f"Erro ao buscar usuários para sbc_id {sbc_id} da DeviceUserLinks: {str(e)}", exc_info=True)
        return [] # Retorna lista vazia em caso de erro

def handle_package_request(sbc_id, payload):
    logger.info(f"Processando requisicao_de_pacote para sbc_id: {sbc_id} com payload: {payload} - Lógica Atualizada")
    
    if not EXPECTEDDELIVERIES_TABLE_NAME:
        logger.error("Nome da tabela ExpectedDeliveries não configurado.")
        return {"error": "Configuração da tabela de entregas esperadas ausente."}
    if not DEVICEUSERLINKS_TABLE_NAME: # Já verificado em get_users_for_sbc, mas bom ter aqui também para clareza.
        logger.error("Nome da tabela DeviceUserLinks não configurado.")
        return {"error": "Configuração da tabela de links de dispositivo ausente."}

    identifier_type = payload.get('identifier_type')
    identifier_value = payload.get('identifier_value')

    if not identifier_type or not identifier_value:
        logger.error("identifier_type ou identifier_value ausente no payload para package_request.")
        return {"error": "identifier_type ou identifier_value ausente no payload."}

    found_package_item = None
    response_data = {}

    try:
        linked_user_ids = get_users_for_sbc(sbc_id)
        
        if not linked_user_ids:
            logger.warning(f"Nenhum usuário vinculado encontrado para sbc_id: {sbc_id}. Não é possível verificar encomendas.")
            response_data = {
                "package_found": False,
                "reason": "Nenhum usuário vinculado ao dispositivo para verificar encomendas.",
                "identifier_type": identifier_type,
                "identifier_value": identifier_value,
                "sbc_id_queried": sbc_id
            }
            return response_data

        deliveries_table = dynamodb_resource.Table(EXPECTEDDELIVERIES_TABLE_NAME)

        if identifier_type == "order_id":
            logger.info(f"Buscando por order_id: {identifier_value} para usuários vinculados: {linked_user_ids}")
            for user_id in linked_user_ids:
                logger.debug(f"Tentando GetItem para user_id: {user_id}, order_id: {identifier_value}")
                response = deliveries_table.get_item(
                    Key={'user_id': user_id, 'order_id': identifier_value}
                )
                if 'Item' in response:
                    found_package_item = response['Item']
                    logger.info(f"Encomenda encontrada por order_id para user_id: {user_id}. Item: {found_package_item}")
                    break 
        
        elif identifier_type == "tracking_number":
            logger.info(f"Buscando por tracking_number: {identifier_value} e verificando contra usuários: {linked_user_ids}")
            gsi_response = deliveries_table.query(
                IndexName='tracking-number-index', 
                KeyConditionExpression=boto3.dynamodb.conditions.Key('tracking_number').eq(identifier_value)
            )
            
            if gsi_response.get('Items'):
                logger.info(f"Itens encontrados pelo GSI tracking-number-index para {identifier_value}: {len(gsi_response['Items'])} itens.")
                for item_from_gsi in gsi_response['Items']:
                    user_id_of_package = item_from_gsi.get('user_id')
                    if user_id_of_package in linked_user_ids:
                        found_package_item = item_from_gsi
                        logger.info(f"Encomenda encontrada por tracking_number. User_id: {user_id_of_package}, vinculado ao SBC. Item: {found_package_item}")
                        break 
            else:
                logger.info(f"Nenhum item encontrado pelo GSI tracking-number-index para tracking_number: {identifier_value}")
        else:
            logger.warning(f"identifier_type inválido: {identifier_type}")
            return {"error": f"identifier_type inválido: {identifier_type}"} 

        if found_package_item:
            response_data = {"package_found": True, "details": found_package_item}
        else:
            response_data = {
                "package_found": False,
                "reason": "Encomenda não encontrada para os usuários vinculados com o identificador fornecido.",
                "identifier_type": identifier_type,
                "identifier_value": identifier_value,
                "sbc_id_queried": sbc_id
            }

        logger.info(f"Resposta de pacote: {response_data}")
        return response_data

    except Exception as e:
        logger.error(f"Erro crítico em handle_package_request para sbc_id {sbc_id}: {str(e)}", exc_info=True)
        error_response_data = {
            "package_found": False,
            "error": "Erro interno do servidor ao processar pedido de pacote.",
            "sbc_id_queried": sbc_id,
            "identifier_type": identifier_type, 
            "identifier_value": identifier_value 
        }
        return error_response_data


def handle_log_submission(sbc_id, payload):
    logger.info(f"Processando enviar_log para sbc_id: {sbc_id}, payload: {payload}")
    if not EVENTLOGS_TABLE_NAME:
        logger.error("Nome da tabela EventLogs não configurado.")
        return {'error': 'Configuração da tabela de logs ausente.'}

    log_timestamp = payload.get('log_timestamp') 
    event_type = payload.get('event_type')
    event_details = payload.get('event_details', {})

    if not log_timestamp or not event_type:
        logger.error("log_timestamp ou event_type ausente no payload para log.")
        return {'error': 'Dados de log insuficientes.'}

    try:
        sort_key_value = f"{log_timestamp}_{str(uuid.uuid4())}" 

        event_logs_table = dynamodb_resource.Table(EVENTLOGS_TABLE_NAME)
        item_to_log = {
            'log_source_id': sbc_id,
            'timestamp_uuid': sort_key_value, 
            'event_type': event_type,
            'timestamp': log_timestamp, 
            'received_at': datetime.now(timezone.utc).isoformat(),
            'details': event_details
        }
        
        event_logs_table.put_item(Item=item_to_log)
        logger.info(f"Log salvo na tabela '{EVENTLOGS_TABLE_NAME}': {item_to_log}")

        notification_request_payload = {
            "sbc_id": sbc_id,
            "event_type_source": "sbc_log_submission",
            "log_details": {
                "event_type": event_type,
                "summary": f"Evento '{event_type}' reportado pelo dispositivo {sbc_id}.",
                "details": event_details
            }
        }
        
        if NOTIFICATION_LAMBDA_NAME_ENV:
            try:
                logger.info(f"Invocando NeoBellNotificationHandler ({NOTIFICATION_LAMBDA_NAME_ENV}) com payload: {json.dumps(notification_request_payload)}")
                response = lambda_client.invoke(
                    FunctionName=NOTIFICATION_LAMBDA_NAME_ENV,
                    InvocationType='Event',
                    Payload=json.dumps(notification_request_payload)
                )
                if response.get('StatusCode') == 202:
                    logger.info(f"NeoBellNotificationHandler ({NOTIFICATION_LAMBDA_NAME_ENV}) invocada com sucesso.")
                else:
                    response_payload_str = "N/A"
                    if response.get('Payload'):
                        response_payload_str = response['Payload'].read().decode('utf-8')
                    logger.warning(f"Invocação da NeoBellNotificationHandler ({NOTIFICATION_LAMBDA_NAME_ENV}) retornou status inesperado: {response.get('StatusCode')}. Resposta Payload: {response_payload_str}")
            except Exception as e_invoke:
                logger.error(f"Erro ao invocar NeoBellNotificationHandler ({NOTIFICATION_LAMBDA_NAME_ENV}): {str(e_invoke)}", exc_info=True)
        else:
            logger.warning("Nome da Lambda de Notificação (NOTIFICATION_LAMBDA_NAME_ENV) não configurado.")

        return {'message': 'Log recebido e processado.'}

    except Exception as e:
        logger.error(f"Erro crítico em handle_log_submission para sbc_id {sbc_id}: {str(e)}", exc_info=True)
        return {'error': f"Erro ao salvar log: {str(e)}."}

def handle_verify_nfc_tag(sbc_id, payload):
    """
    Verifica se a tag NFC escaneada é válida para algum usuário associado ao SBC.
    Retorna um dicionário com o resultado da verificação.
    """
    logger.info(f"Processando handle_verify_nfc_tag para sbc_id: {sbc_id}, payload: {payload}")

    nfc_id_scanned = payload.get('nfc_id_scanned')
    if not nfc_id_scanned:
        logger.error("nfc_id_scanned ausente no payload para nfc_verify_request.")
        return {"error": "nfc_id_scanned ausente no payload para nfc_verify_request."}

    logger.info(f"Iniciando verificação da tag NFC: {nfc_id_scanned}")

    if not DEVICEUSERLINKS_TABLE_NAME:
        logger.error("Nome da tabela DeviceUserLinks não configurado.")
        return {"nfc_id_scanned": nfc_id_scanned, "is_valid": False, "error": "Configuração interna: DeviceUserLinks não definida."}
    if not USER_NFC_TAGS_TABLE_NAME:
        logger.error("Nome da tabela UserNFCTags não configurado.")
        return {"nfc_id_scanned": nfc_id_scanned, "is_valid": False, "error": "Configuração interna: UserNFCTags não definida."}

    response_payload = {
        "nfc_id_scanned": nfc_id_scanned,
        "is_valid": False
    }

    try:
        linked_user_ids = get_users_for_sbc(sbc_id)

        if not linked_user_ids:
            logger.warning(f"Nenhum usuário encontrado para o SBC ID: {sbc_id} em DeviceUserLinks ou erro ao buscar. Tag NFC considerada inválida para este SBC.")
            response_payload["reason"] = "Nenhum usuário vinculado ao dispositivo ou falha ao buscar usuários."
            return response_payload

        logger.info(f"Usuários vinculados ao SBC {sbc_id} para verificação NFC: {linked_user_ids}")
        user_nfc_tags_table = dynamodb_resource.Table(USER_NFC_TAGS_TABLE_NAME)

        for user_id in linked_user_ids:
            logger.info(f"Verificando tag NFC {nfc_id_scanned} para user_id: {user_id}")
            try:
                tag_response = user_nfc_tags_table.get_item(
                    Key={
                        'user_id': user_id,
                        'nfc_id_scanned': nfc_id_scanned
                    }
                )

                if 'Item' in tag_response:
                    tag_item = tag_response['Item']
                    logger.info(f"Tag NFC válida encontrada para user_id: {user_id}. Item: {tag_item}")
                    response_payload["is_valid"] = True
                    response_payload["user_id_associated"] = user_id
                    response_payload["tag_friendly_name"] = tag_item.get("tag_friendly_name", "")
                    return response_payload

            except Exception as e_get:
                logger.error(f"Erro ao consultar UserNFCTags para user_id {user_id} e tag {nfc_id_scanned}: {str(e_get)}", exc_info=True)
        
        logger.info(f"Tag NFC {nfc_id_scanned} não é válida para nenhum usuário associado ao SBC {sbc_id} após verificar todos os vinculados.")
        response_payload["reason"] = "Tag não associada a nenhum usuário deste dispositivo."
        return response_payload

    except Exception as e_general: 
        logger.error(f"Erro geral durante a verificação da tag NFC para sbc_id {sbc_id} e tag {nfc_id_scanned}: {str(e_general)}", exc_info=True)
        response_payload["error"] = "Erro interno do servidor ao verificar tag."
        return response_payload

# --- Handler Principal (Roteador) ---
def lambda_handler(event, context):
    logger.info(f"NeoBellSBCHelperHandler recebeu evento: {json.dumps(event)}")
    
    sbc_id = event.get('sbc_id') 
    invoking_topic = event.get('invoking_topic')
    
    if not sbc_id:
        logger.error("sbc_id não foi fornecido pela Regra IoT no evento.")
        return {'statusCode': 400, 'body': json.dumps({'error': 'sbc_id ausente no evento'})}

    action_type = None
    # Determinar a ação com base no tópico de invocação
    if invoking_topic:
        topic_parts = invoking_topic.split('/')
        
        # Formato: neobell/sbc/{sbc_id_from_topic}/nfc/verify-tag/request (6 partes)
        if len(topic_parts) == 6 and \
           topic_parts[0] == 'neobell' and topic_parts[1] == 'sbc' and \
           topic_parts[3] == 'nfc' and topic_parts[4] == 'verify-tag' and \
           topic_parts[5] == 'request':
            action_type = 'nfc_verify_request'
        
        # Formato: neobell/sbc/{sbc_id_from_topic}/action_keyword/verb (5 partes)
        elif len(topic_parts) == 5 : 
            potential_action_keyword = topic_parts[3] # permissions, packages, logs
            verb = topic_parts[4] # request, submit

            if potential_action_keyword == 'permissions' and verb == 'request':
                action_type = 'permissions_request'
            elif potential_action_keyword == 'packages' and verb == 'request':
                action_type = 'package_request'
            elif potential_action_keyword == 'logs' and verb == 'submit':
                action_type = 'log_submission'
            
        if not action_type: 
            logger.warning(f"Não foi possível determinar action_type a partir do invoking_topic: {invoking_topic}. Tentando campo 'action_type' no payload.")
            action_type = event.get('action_type') 
    else:
        logger.warning("invoking_topic não fornecido no evento. Tentando campo 'action_type' no payload.")
        action_type = event.get('action_type') 
    
    if not action_type:
        logger.error("action_type não fornecido nem derivável. Verifique a Regra IoT e o payload MQTT.")
        return {'statusCode': 400, 'body': json.dumps({'error': 'action_type ausente ou não reconhecido'})}

    result_payload_for_lambda_body = {}
    lambda_response_status_code = 200 
    response_topic = None

    if action_type == 'permissions_request':
        response_topic = PERMISSIONS_RESPONSE_TOPIC_TPL.format(sbc_id=sbc_id)
        result_payload_for_lambda_body = handle_permission_request(sbc_id, event)
    elif action_type == 'package_request':
        response_topic = PACKAGES_RESPONSE_TOPIC_TPL.format(sbc_id=sbc_id)
        result_payload_for_lambda_body = handle_package_request(sbc_id, event)
    elif action_type == 'log_submission':
        result_payload_for_lambda_body = handle_log_submission(sbc_id, event)
    elif action_type == 'nfc_verify_request':
        response_topic = NFC_VERIFY_RESPONSE_TOPIC_TPL.format(sbc_id=sbc_id)
        result_payload_for_lambda_body = handle_verify_nfc_tag(sbc_id, event)
    else:
        logger.error(f"Tipo de ação desconhecido: {action_type} para sbc_id: {sbc_id}")
        result_payload_for_lambda_body = {"error": f"Tipo de ação desconhecido: {action_type}"}
        lambda_response_status_code = 400

    if lambda_response_status_code == 200 and isinstance(result_payload_for_lambda_body, dict) and "error" in result_payload_for_lambda_body:
        error_message = result_payload_for_lambda_body["error"]
        if "Configuração da tabela" in error_message or \
           "Erro interno" in error_message or \
           "Configuração interna" in error_message :
            lambda_response_status_code = 500 
        else:
            lambda_response_status_code = 400

    if response_topic and lambda_response_status_code != 200 and isinstance(result_payload_for_lambda_body, dict):
        try:
            iot_data_client.publish(topic=response_topic, qos=1, payload=json.dumps(result_payload_for_lambda_body))
        except Exception as e_pub_err:
            logger.error(f"Falha ao publicar erro de payload ausente para NFC para {response_topic}: {str(e_pub_err)}")
            
    return {'statusCode': lambda_response_status_code, 'body': json.dumps(result_payload_for_lambda_body)}


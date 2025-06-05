# lambda_function.py para NeoBellActivityLogHandler
import json
import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import datetime
import logging
import re
from decimal import Decimal # Para lidar com números do DynamoDB
import heapq # Para mesclar resultados ordenados

# Configurar logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Inicializar clientes AWS (fora do handler para reutilização)
DYNAMODB_CLIENT = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

# Nomes das Tabelas DynamoDB (de variáveis de ambiente)
EVENT_LOGS_TABLE_NAME = os.environ.get('EVENT_LOGS_TABLE', 'EventLogs')
DEVICE_USER_LINKS_TABLE_NAME = os.environ.get('DEVICE_USER_LINKS_TABLE', 'DeviceUserLinks')

event_logs_table = DYNAMODB_CLIENT.Table(EVENT_LOGS_TABLE_NAME)
device_user_links_table = DYNAMODB_CLIENT.Table(DEVICE_USER_LINKS_TABLE_NAME)

# Nomes de Índices
DEVICE_USER_LINKS_USER_ID_INDEX = "user-id-sbc-id-index" # GSI na DeviceUserLinks

# --- Funções Utilitárias ---
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return int(o) if o % 1 == 0 else float(o)
        return super(DecimalEncoder, self).default(o)

def get_user_id(event):
    try:
        return event['requestContext']['authorizer']['claims']['sub']
    except KeyError:
        logger.error("User ID (sub) não encontrado no evento.")
        return None

def format_response(status_code, body_data):
    if not isinstance(body_data, str):
        body = json.dumps(body_data, cls=DecimalEncoder)
    else:
        body = body_data
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'OPTIONS,GET' # Apenas GET para este handler
        },
        'body': body
    }

def format_error_response(status_code, error_message, details=None):
    error_body = {'error': error_message}
    if details: error_body['details'] = details
    return format_response(status_code, error_body)

def get_accessible_sbc_ids(user_id):
    """Busca todos os sbc_ids aos quais o usuário tem acesso."""
    sbc_ids = []
    try:
        response = device_user_links_table.query(
            IndexName=DEVICE_USER_LINKS_USER_ID_INDEX,
            KeyConditionExpression=Key('user_id').eq(user_id),
            ProjectionExpression='sbc_id'
        )
        sbc_ids = [item['sbc_id'] for item in response.get('Items', [])]
    except ClientError as e:
        logger.error(f"Erro ao buscar sbc_ids acessíveis para {user_id}: {e}")
    return sbc_ids

def parse_datetime_to_timestamp_uuid_prefix(dt_str):
    """Converte uma string de data/hora ISO8601 para o prefixo do timestamp_uuid."""
    try:
        # Tenta analisar com milissegundos e Z
        dt_obj = datetime.datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        try:
            # Tenta analisar sem milissegundos e Z
            dt_obj = datetime.datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            logger.error(f"Formato de data/hora inválido: {dt_str}. Use ISO8601 com Z (ex: YYYY-MM-DDTHH:MM:SSZ).")
            raise ValueError("Formato de data/hora inválido")
    return dt_obj.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z" # Formato com 3 casas de ms + Z

# --- Manipulador de Endpoint ---

def handle_get_activity_logs(requesting_user_id, path_params, query_params, body):
    logger.info(f"handle_get_activity_logs para user_id: {requesting_user_id}, query: {query_params}")

    event_types_str = query_params.get('event_types')
    filter_sbc_id = query_params.get('sbc_id')
    start_date_str = query_params.get('start_date') # Esperado YYYY-MM-DDTHH:mm:ssZ
    end_date_str = query_params.get('end_date')     # Esperado YYYY-MM-DDTHH:mm:ssZ
    
    limit_per_source = 10 # Limite interno por fonte de log antes da mesclagem
    try:
        limit_final = int(query_params.get('limit', '20')) # Limite final para o cliente
        if limit_final <=0 : limit_final = 20
    except ValueError:
        return format_error_response(400, "Parâmetro 'limit' inválido.")

    # Paginação é complexa aqui. Este exemplo não implementa paginação robusta entre múltiplas fontes.
    # last_evaluated_key seria um objeto complexo contendo chaves para cada fonte.
    # Para simplificar, este exemplo busca os N mais recentes de cada fonte e mescla.

    log_sources_to_query = []
    if filter_sbc_id:
        # Verifica se o usuário tem acesso ao sbc_id específico
        accessible_sbcs = get_accessible_sbc_ids(requesting_user_id)
        if filter_sbc_id not in accessible_sbcs:
            return format_error_response(403, f"Acesso negado ao dispositivo {filter_sbc_id}.")
        log_sources_to_query.append(filter_sbc_id)
    else:
        # Adiciona o próprio user_id como fonte (para logs de ações do app)
        log_sources_to_query.append(requesting_user_id)
        # Adiciona todos os sbc_ids acessíveis
        log_sources_to_query.extend(get_accessible_sbc_ids(requesting_user_id))
    
    if not log_sources_to_query:
        return format_response(200, {"items": [], "message": "Nenhuma fonte de log encontrada para o usuário."})

    all_logs = []
    
    # Construir KeyConditionExpression para o range de datas no SK (timestamp_uuid)
    key_condition_sk = None
    try:
        if start_date_str and end_date_str:
            key_condition_sk = Key('timestamp_uuid').between(
                parse_datetime_to_timestamp_uuid_prefix(start_date_str) + "_0", # Adiciona sufixo mínimo
                parse_datetime_to_timestamp_uuid_prefix(end_date_str) + "_z"  # Adiciona sufixo máximo
            )
        elif start_date_str:
            key_condition_sk = Key('timestamp_uuid').gte(parse_datetime_to_timestamp_uuid_prefix(start_date_str) + "_0")
        elif end_date_str:
            key_condition_sk = Key('timestamp_uuid').lte(parse_datetime_to_timestamp_uuid_prefix(end_date_str) + "_z")
    except ValueError as ve:
        return format_error_response(400, str(ve))


    # Construir FilterExpression para event_types
    filter_expression_parts = []
    expression_attribute_values = {}
    if event_types_str:
        event_types_list = [et.strip() for et in event_types_str.split(',')]
        if event_types_list:
            # Usar IN para múltiplos tipos de evento
            # DynamoDB IN operator pode ter até 100 operandos.
            # Se precisar de mais, pode ser necessário múltiplas condições OR.
            placeholders = [f":et{i}" for i in range(len(event_types_list))]
            filter_expression_parts.append(f"event_type IN ({', '.join(placeholders)})")
            for i, et_type in enumerate(event_types_list):
                expression_attribute_values[placeholders[i]] = et_type
    
    final_filter_expression = None
    if filter_expression_parts:
        final_filter_expression = " AND ".join(filter_expression_parts) # Adicionar outros filtros aqui se necessário

    for source_id in set(log_sources_to_query): # Usar set para evitar duplicatas se user_id for também um sbc_id
        try:
            query_args = {
                'KeyConditionExpression': Key('log_source_id').eq(source_id),
                'ScanIndexForward': False, # Mais recentes primeiro
                'Limit': limit_per_source 
            }
            if key_condition_sk:
                query_args['KeyConditionExpression'] &= key_condition_sk
            
            if final_filter_expression:
                query_args['FilterExpression'] = final_filter_expression
                if expression_attribute_values: # Só adicionar se houver valores
                     query_args['ExpressionAttributeValues'] = expression_attribute_values
            
            response = event_logs_table.query(**query_args)
            all_logs.extend(response.get('Items', []))
        except ClientError as e:
            logger.error(f"Erro ao consultar logs para source_id {source_id}: {e}")
            # Continuar para outras fontes em caso de erro em uma
        except Exception as ex: # Capturar outros erros inesperados
            logger.error(f"Erro inesperado ao consultar logs para source_id {source_id}: {ex}")


    # Ordenar todos os logs coletados pelo atributo 'timestamp' (principal) em ordem decrescente.
    # O 'timestamp_uuid' (SK) já garante a ordem dentro de cada source_id se ScanIndexForward=False.
    # A ordenação aqui é para mesclar resultados de diferentes source_ids.
    # O atributo 'timestamp' deve ser o campo primário para ordenação de exibição.
    try:
        # Certificar que 'timestamp' existe e é comparável (string ISO8601)
        all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    except TypeError as te:
        logger.error(f"Erro de tipo ao ordenar logs, verifique o formato do campo 'timestamp': {te}")
        # Retornar logs não ordenados ou um erro
        # return format_error_response(500, "Erro ao processar logs (ordenação).")


    # Aplicar o limite final
    paginated_logs = all_logs[:limit_final]

    # A implementação de 'last_evaluated_key' para esta agregação é complexa e omitida aqui.
    # Uma abordagem real poderia envolver cursores para cada fonte ou uma estratégia de indexação diferente.
    
    return format_response(200, {"items": paginated_logs})


# --- Handler Principal do Lambda ---
def lambda_handler(event, context):
    logger.info(f"Evento recebido: {json.dumps(event, indent=2)}")

    requesting_user_id = get_user_id(event)
    if not requesting_user_id:
        return format_error_response(401, "Não autorizado. Identificador de usuário ausente.")

    http_method = event.get('httpMethod')
    path = event.get('path')
    
    path_params = event.get('pathParameters') if event.get('pathParameters') else {}
    query_params = event.get('queryStringParameters') if event.get('queryStringParameters') else {}
    request_body_str = event.get('body') # Não usado para GET /activity-logs

    if path == '/activity-logs' and http_method == 'GET':
        return handle_get_activity_logs(requesting_user_id, path_params, query_params, request_body_str)
            
    logger.warning(f"Nenhuma rota correspondente para {http_method} {path}")
    return format_error_response(404, "Endpoint da API não encontrado ou método não permitido para este caminho.")


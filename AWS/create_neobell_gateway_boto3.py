import boto3
import json
import time
import logging

# Configurar logging básico
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# --- Configuração - Substitua estes placeholders ---
AWS_REGION = 'us-east-1'
ACCOUNT_ID = 'ACCOUNT_ID' # Substitua pelo seu AWS Account ID
YOUR_COGNITO_USER_POOL_ARN = 'arn:aws:cognito-idp:us-east-1{ACCOUNT_ID}userpool/us-east-1_7s5Ur8SOU' # Ex: arn:aws:cognito-idp:us-east-1:123456789012:userpool/us-east-1_xxxxxxxxx
API_NAME = 'NeoBellAPI'
API_STAGE_NAME = 'dev'

# ARNs das Lambdas fornecidos pelo usuário
LAMBDA_ARNS = {
    "NeoBellUserHandler": "arn:aws:lambda:us-east-1{ACCOUNT_ID}function:NeoBellUserHandler",
    "NeoBellDeviceHandler": "arn:aws:lambda:us-east-1{ACCOUNT_ID}function:NeoBellDeviceHandler",
    "NeoBellMessageHandler": "arn:aws:lambda:us-east-1{ACCOUNT_ID}function:NeoBellMessageHandler",
    "NeoBellDeliveryHandler": "arn:aws:lambda:us-east-1{ACCOUNT_ID}function:NeoBellDeliveryHandler",
    "NeoBellVisitorHandler": "arn:aws:lambda:us-east-1{ACCOUNT_ID}function:NeoBellVisitorHandler",
    "NeoBellActivityLogHandler": "arn:aws:lambda:us-east-1{ACCOUNT_ID}function:NeoBellActivityLogHandler"
}
# --- Fim da Configuração ---

# Definições da API (simplificado - idealmente parseado do seu documento)
# Formato: (HTTP_METHOD, PATH, TARGET_LAMBDA_KEY, HAS_PATH_PARAMS)
# HAS_PATH_PARAMS é um booleano para ajudar a determinar se criamos um recurso com {}
# TARGET_LAMBDA_KEY é a chave no dicionário LAMBDA_ARNS
API_ENDPOINTS = [
    # NeoBellUserHandler
    ("GET", "/users/me", "NeoBellUserHandler", False),
    ("PUT", "/users/me", "NeoBellUserHandler", False),
    ("POST", "/users/device-token", "NeoBellUserHandler", False),
    ("POST", "/users/me/nfc-tags", "NeoBellUserHandler", False),
    ("GET", "/users/me/nfc-tags", "NeoBellUserHandler", False),
    ("PUT", "/users/me/nfc-tags/{nfc_id_scanned}", "NeoBellUserHandler", True), # Path param: nfc_id_scanned
    ("DELETE", "/users/me/nfc-tags/{nfc_id_scanned}", "NeoBellUserHandler", True),

    # NeoBellDeviceHandler
    ("GET", "/devices", "NeoBellDeviceHandler", False),
    ("GET", "/devices/{sbc_id}", "NeoBellDeviceHandler", True), # Path param: sbc_id
    ("PUT", "/devices/{sbc_id}", "NeoBellDeviceHandler", True),
    ("DELETE", "/devices/{sbc_id}", "NeoBellDeviceHandler", True),
    ("GET", "/devices/{sbc_id}/users", "NeoBellDeviceHandler", True),
    ("POST", "/devices/{sbc_id}/users", "NeoBellDeviceHandler", True),
    ("DELETE", "/devices/{sbc_id}/users/{user_id_to_remove}", "NeoBellDeviceHandler", True), # Path params: sbc_id, user_id_to_remove

    # NeoBellMessageHandler
    ("GET", "/messages", "NeoBellMessageHandler", False),
    ("GET", "/messages/{message_id}", "NeoBellMessageHandler", True), # Path param: message_id
    ("POST", "/messages/{message_id}/view-url", "NeoBellMessageHandler", True),
    ("DELETE", "/messages/{message_id}", "NeoBellMessageHandler", True),

    # NeoBellDeliveryHandler
    ("GET", "/deliveries", "NeoBellDeliveryHandler", False),
    ("POST", "/deliveries", "NeoBellDeliveryHandler", False),
    ("GET", "/deliveries/{order_id}", "NeoBellDeliveryHandler", True), # Path param: order_id
    ("PUT", "/deliveries/{order_id}", "NeoBellDeliveryHandler", True),
    ("DELETE", "/deliveries/{order_id}", "NeoBellDeliveryHandler", True),

    # NeoBellVisitorHandler
    ("GET", "/visitors", "NeoBellVisitorHandler", False),
    ("PUT", "/visitors/{face_tag_id}", "NeoBellVisitorHandler", True), # Path param: face_tag_id
    ("DELETE", "/visitors/{face_tag_id}", "NeoBellVisitorHandler", True),

    # NeoBellActivityLogHandler
    ("GET", "/activity-logs", "NeoBellActivityLogHandler", False),
]


apigateway_client = boto3.client('apigateway', region_name=AWS_REGION)
lambda_client = boto3.client('lambda', region_name=AWS_REGION)

def get_rest_api_id(api_name):
    """Busca o ID de uma REST API existente pelo nome."""
    apis = apigateway_client.get_rest_apis()
    for api in apis.get('items', []):
        if api['name'] == api_name:
            return api['id']
    return None

def create_or_get_rest_api(api_name):
    """Cria uma nova REST API ou retorna o ID de uma existente."""
    rest_api_id = get_rest_api_id(api_name)
    if rest_api_id:
        logger.info(f"API '{api_name}' já existe com ID: {rest_api_id}")
        return rest_api_id
    
    logger.info(f"Criando API: {api_name}")
    response = apigateway_client.create_rest_api(
        name=api_name,
        description=f"{api_name} para o Projeto NeoBell",
        endpointConfiguration={'types': ['REGIONAL']},
        tags={'Project': 'NeoBell', 'Name': api_name}
    )
    rest_api_id = response['id']
    logger.info(f"API '{api_name}' criada com ID: {rest_api_id}")
    return rest_api_id

def create_cognito_authorizer(rest_api_id, cognito_user_pool_arn):
    """Cria um autorizador do tipo COGNITO_USER_POOLS."""
    authorizer_name = "NeoBellCognitoAuthorizer"
    # Verificar se já existe
    try:
        authorizers = apigateway_client.get_authorizers(restApiId=rest_api_id)
        for auth in authorizers.get('items', []):
            if auth['name'] == authorizer_name:
                logger.info(f"Autorizador '{authorizer_name}' já existe com ID: {auth['id']}")
                return auth['id']
    except Exception as e:
        logger.warning(f"Não foi possível buscar autorizadores existentes: {e}")

    logger.info(f"Criando autorizador '{authorizer_name}' para a API ID {rest_api_id}")
    response = apigateway_client.create_authorizer(
        restApiId=rest_api_id,
        name=authorizer_name,
        type='COGNITO_USER_POOLS',
        providerARNs=[cognito_user_pool_arn],
        identitySource='method.request.header.Authorization', # Token JWT virá neste header
        authType='cognito_user_pools',
        authorizerResultTtlInSeconds=300
    )
    authorizer_id = response['id']
    logger.info(f"Autorizador '{authorizer_name}' criado com ID: {authorizer_id}")
    return authorizer_id

def get_or_create_resource(rest_api_id, parent_id, path_part):
    """Obtém ou cria um recurso sob um pai. path_part NÃO deve ter '/' no início/fim."""
    resources = apigateway_client.get_resources(restApiId=rest_api_id, limit=500).get('items', [])
    
    # Encontrar o recurso existente que corresponde ao path_part sob o parent_id
    for resource in resources:
        if resource.get('parentId') == parent_id and resource.get('pathPart') == path_part:
            logger.debug(f"Recurso '{path_part}' encontrado sob parent_id '{parent_id}' com ID: {resource['id']}")
            return resource['id']

    # Se não encontrado, criar
    logger.info(f"Criando recurso '{path_part}' sob parent_id '{parent_id}' para API ID {rest_api_id}")
    response = apigateway_client.create_resource(
        restApiId=rest_api_id,
        parentId=parent_id,
        pathPart=path_part
    )
    logger.info(f"Recurso '{path_part}' criado com ID: {response['id']}")
    return response['id']

def add_cors_to_resource(rest_api_id, resource_id, methods_with_auth):
    """Adiciona um método OPTIONS para CORS a um recurso."""
    try:
        logger.info(f"Configurando CORS para o recurso ID: {resource_id}")
        apigateway_client.put_method(
            restApiId=rest_api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            authorizationType='NONE', # OPTIONS não requer autenticação
            apiKeyRequired=False
        )
        
        # Integração MOCK para OPTIONS
        apigateway_client.put_integration(
            restApiId=rest_api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            type='MOCK',
            requestTemplates={
                'application/json': '{"statusCode": 200}'
            }
        )
        
        # Headers de resposta para OPTIONS
        # Os métodos permitidos devem refletir os métodos reais definidos para este recurso
        allowed_methods_str = ",".join(methods_with_auth + ['OPTIONS'])

        apigateway_client.put_method_response(
            restApiId=rest_api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Headers': True,
                'method.response.header.Access-Control-Allow-Methods': True,
                'method.response.header.Access-Control-Allow-Origin': True
            },
            responseModels={'application/json': 'Empty'} # Modelo vazio é suficiente
        )
        
        apigateway_client.put_integration_response(
            restApiId=rest_api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                'method.response.header.Access-Control-Allow-Methods': f"'{allowed_methods_str}'",
                'method.response.header.Access-Control-Allow-Origin': "'*'" # Seja específico em produção
            },
            responseTemplates={'application/json': ''} # Corpo vazio
        )
        logger.info(f"Método OPTIONS e respostas CORS configurados para o recurso ID: {resource_id}")

    except Exception as e:
        logger.error(f"Erro ao adicionar CORS ao recurso ID {resource_id}: {e}")


def main():
    if 'ACCOUNT_ID' in ACCOUNT_ID or 'YOUR_COGNITO_USER_POOL_ARN' in YOUR_COGNITO_USER_POOL_ARN:
        logger.error("ERRO: Por favor, substitua os placeholders ACCOUNT_ID e YOUR_COGNITO_USER_POOL_ARN no script.")
        return

    rest_api_id = create_or_get_rest_api(API_NAME)
    if not rest_api_id:
        logger.error(f"Não foi possível criar ou obter a API {API_NAME}.")
        return

    cognito_authorizer_id = create_cognito_authorizer(rest_api_id, YOUR_COGNITO_USER_POOL_ARN)
    if not cognito_authorizer_id:
        logger.error("Não foi possível criar o autorizador do Cognito.")
        return

    # Obter o ID do recurso raiz '/'
    root_resource_id = None
    resources = apigateway_client.get_resources(restApiId=rest_api_id).get('items', [])
    for resource in resources:
        if resource['path'] == '/':
            root_resource_id = resource['id']
            break
    if not root_resource_id:
        logger.error("Não foi possível encontrar o recurso raiz da API.")
        return
    
    # Cache para IDs de recursos já criados/obtidos para evitar chamadas repetidas
    # Chave: path completo, Valor: resource_id
    resource_ids_cache = {'/': root_resource_id}
    
    # Agrupar métodos por caminho para adicionar CORS corretamente
    methods_by_path = {}
    for http_method, path, _, _ in API_ENDPOINTS:
        # Normalizar o caminho para ser a chave do recurso pai
        # Se /a/b/c, o recurso é 'c', pai é /a/b
        # Se /a/{id}/c, o recurso é 'c', pai é /a/{id}
        path_parts = [part for part in path.strip('/').split('/') if part]
        current_path_key_for_methods = "/" + "/".join(path_parts)
        if current_path_key_for_methods not in methods_by_path:
            methods_by_path[current_path_key_for_methods] = []
        if http_method not in methods_by_path[current_path_key_for_methods]:
             methods_by_path[current_path_key_for_methods].append(http_method)


    # Criar recursos e métodos
    for http_method, path, target_lambda_key, _ in API_ENDPOINTS:
        logger.info(f"\nConfigurando endpoint: {http_method} {path} -> {target_lambda_key}")
        lambda_function_arn = LAMBDA_ARNS[target_lambda_key]
        lambda_function_name = lambda_function_arn.split(':')[-1] # Extrai nome da função do ARN

        current_parent_id = root_resource_id
        current_path_processed = "" # Para rastrear o caminho completo para o cache

        path_parts = [part for part in path.strip('/').split('/') if part] # Remove / do início/fim e divide
        
        resource_id_for_method = root_resource_id # Default para path '/' (não usado nos nossos endpoints)

        for i, part in enumerate(path_parts):
            current_path_processed += "/" + part
            if current_path_processed in resource_ids_cache:
                resource_id = resource_ids_cache[current_path_processed]
            else:
                resource_id = get_or_create_resource(rest_api_id, current_parent_id, part)
                resource_ids_cache[current_path_processed] = resource_id
            
            current_parent_id = resource_id # O recurso atual se torna o pai para a próxima parte
            if i == len(path_parts) - 1: # É a última parte do caminho, este é o recurso para o método
                resource_id_for_method = resource_id

        logger.info(f"Definindo método {http_method} para o recurso ID {resource_id_for_method} (path: {path})")
        
        # Adicionar o método HTTP
        try:
            apigateway_client.put_method(
                restApiId=rest_api_id,
                resourceId=resource_id_for_method,
                httpMethod=http_method,
                authorizationType='COGNITO_USER_POOLS',
                authorizerId=cognito_authorizer_id,
                apiKeyRequired=False
            )
        except Exception as e:
            logger.error(f"Erro ao definir método {http_method} para {path}: {e}")
            continue # Pular para o próximo endpoint

        # Configurar Integração Lambda Proxy
        # URI da integração Lambda: arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations
        integration_uri = f"arn:aws:apigateway:{AWS_REGION}:lambda:path/2015-03-31/functions/{lambda_function_arn}/invocations"
        
        try:
            apigateway_client.put_integration(
                restApiId=rest_api_id,
                resourceId=resource_id_for_method,
                httpMethod=http_method,
                type='AWS_PROXY', # Integração Lambda Proxy
                integrationHttpMethod='POST', # Sempre POST para Lambda Proxy
                uri=integration_uri,
                #credentials=None, # Para AWS_PROXY, as permissões são baseadas em recursos
                timeoutInMillis=29000 # Um pouco menos que o timeout do Lambda (30s)
            )
        except Exception as e:
            logger.error(f"Erro ao definir integração para {http_method} {path}: {e}")
            continue

        # Adicionar resposta do método (necessário para a integração funcionar corretamente)
        try:
            apigateway_client.put_method_response(
                restApiId=rest_api_id,
                resourceId=resource_id_for_method,
                httpMethod=http_method,
                statusCode='200', # Resposta padrão de sucesso
                # Adicionar aqui headers de resposta se necessário, ex: CORS
                responseParameters={
                     'method.response.header.Access-Control-Allow-Origin': True # Habilitar para a resposta real
                },
                responseModels={'application/json': 'Empty'} 
            )
            # Adicionar resposta da integração
            apigateway_client.put_integration_response(
                restApiId=rest_api_id,
                resourceId=resource_id_for_method,
                httpMethod=http_method,
                statusCode='200',
                responseParameters={
                    # Mapear o header da resposta da integração para o header da resposta do método
                    'method.response.header.Access-Control-Allow-Origin': "'*'" 
                },
                responseTemplates={'application/json': ''} # Para proxy, o corpo é passado diretamente
            )
        except Exception as e:
            logger.error(f"Erro ao definir respostas para {http_method} {path}: {e}")
            continue
            
        # Adicionar permissão para o API Gateway invocar a função Lambda
        statement_id = f"apigateway-{API_NAME}-{http_method.replace('/', '_')}-{path.replace('/', '_').replace('{','_').replace('}','_')}-{lambda_function_name}"
        # Truncar statement_id se for muito longo (máx 100 chars, e deve ser único)
        statement_id = (statement_id[:95] + '...') if len(statement_id) > 100 else statement_id
        statement_id = "".join(c if c.isalnum() or c in ['-','_'] else "_" for c in statement_id) # Sanitizar

        try:
            # Remover permissão existente com o mesmo StatementId, se houver, para evitar conflito
            try:
                lambda_client.remove_permission(FunctionName=lambda_function_name, StatementId=statement_id)
                logger.info(f"Permissão existente '{statement_id}' removida para {lambda_function_name}.")
            except lambda_client.exceptions.ResourceNotFoundException:
                pass # Permissão não existia, tudo bem.
            except Exception as e_rm_perm:
                logger.warning(f"Não foi possível remover permissão antiga '{statement_id}' (pode não existir): {e_rm_perm}")


            source_arn = f"arn:aws:execute-api:{AWS_REGION}:{ACCOUNT_ID}:{rest_api_id}/*/{http_method}{path}"
            
            lambda_client.add_permission(
                FunctionName=lambda_function_name,
                StatementId=statement_id,
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=source_arn
            )
            logger.info(f"Permissão adicionada para API Gateway invocar {lambda_function_name} para {http_method} {path}")
        except Exception as e:
            logger.error(f"Erro ao adicionar permissão para Lambda {lambda_function_name} (StatementId: {statement_id}): {e}")
            logger.error(f"Tentativa de SourceArn: {source_arn}")

    # Adicionar CORS para cada recurso que tem métodos definidos
    # Precisamos dos resource_ids únicos. O resource_ids_cache contém path -> id.
    # Iterar sobre resource_ids_cache.values() não é o ideal porque queremos os paths.
    unique_resource_paths_for_cors = set(methods_by_path.keys())

    for resource_path_key in unique_resource_paths_for_cors:
        if resource_path_key in resource_ids_cache:
            resource_id_for_cors = resource_ids_cache[resource_path_key]
            actual_methods_for_resource = methods_by_path[resource_path_key]
            add_cors_to_resource(rest_api_id, resource_id_for_cors, actual_methods_for_resource)
        else:
            logger.warning(f"Não foi possível encontrar o resource_id para o path {resource_path_key} no cache para adicionar CORS.")


    # Implantar a API
    try:
        logger.info(f"Implantando API ID {rest_api_id} no estágio {API_STAGE_NAME}...")
        apigateway_client.create_deployment(
            restApiId=rest_api_id,
            stageName=API_STAGE_NAME,
            description=f"Implantação para o estágio {API_STAGE_NAME}"
        )
        logger.info(f"API implantada com sucesso no estágio {API_STAGE_NAME}.")
        # A URL de invocação será: https://{rest_api_id}.execute-api.{region}.amazonaws.com/{stage_name}
        invoke_url = f"https://{rest_api_id}.execute-api.{AWS_REGION}.amazonaws.com/{API_STAGE_NAME}"
        logger.info(f"URL de Invocação da API: {invoke_url}")
    except Exception as e:
        logger.error(f"Erro ao implantar API: {e}")

if __name__ == '__main__':
    main()


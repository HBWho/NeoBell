import boto3
import json
import os
import zipfile
import time
import logging

# Configurar logging básico
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configurações ---
AWS_REGION = "us-east-1" # Defina sua região AWS
SNS_PLATFORM_APP_NAME = "NeoBellFCMPlatformApp-Android"
LAMBDA_FUNCTION_NAME = "NeoBellNotificationHandler"
LAMBDA_HANDLER_FILE = "neobell_notification_handler_code.py" # Nome do arquivo Python com o código da Lambda
LAMBDA_HANDLER_FUNCTION = "lambda_function.lambda_handler" # Handler no arquivo Python (nome_do_arquivo.nome_da_funcao)
LAMBDA_RUNTIME = "python3.9"
LAMBDA_ROLE_NAME = "NeoBellNotificationHandlerRole"
LAMBDA_MEMORY_SIZE = 128  # MB
LAMBDA_TIMEOUT = 30       # Segundos

# Nomes das tabelas DynamoDB (usados nas variáveis de ambiente da Lambda e na política IAM)
DYNAMODB_USERS_TABLE_NAME = "NeoBellUsers"
DYNAMODB_DEVICE_USER_LINK_TABLE_NAME = "DeviceUserLink"

# Tags para os recursos
COMMON_TAGS = [
    {'Key': 'Project', 'Value': 'NeoBell'},
    {'Key': 'Purpose', 'Value': 'NotificationHandler'},
]

# Inicializar clientes AWS
iam_client = boto3.client('iam', region_name=AWS_REGION)
sns_client = boto3.client('sns', region_name=AWS_REGION)
lambda_client = boto3.client('lambda', region_name=AWS_REGION)
sts_client = boto3.client('sts', region_name=AWS_REGION)

def get_ACCOUNT_ID():
    """Obtém o ID da conta AWS atual."""
    try:
        return sts_client.get_caller_identity()["Account"]
    except Exception as e:
        logging.error(f"Erro ao obter o ID da conta AWS: {e}")
        raise

ACCOUNT_ID = get_ACCOUNT_ID()

def create_sns_platform_application(fcm_service_account_json_content):
    """Cria a Platform Application no SNS para FCM."""
    logging.info(f"Tentando criar/obter SNS Platform Application: {SNS_PLATFORM_APP_NAME}")
    try:
        # Tentar obter a aplicação de plataforma para verificar se já existe
        # Construir o ARN esperado para verificar
        expected_arn = f"arn:aws:sns:{AWS_REGION}:{ACCOUNT_ID}:app/FCM/{SNS_PLATFORM_APP_NAME}"
        try:
            response = sns_client.get_platform_application_attributes(PlatformApplicationArn=expected_arn)
            logging.info(f"SNS Platform Application '{SNS_PLATFORM_APP_NAME}' já existe com ARN: {expected_arn}")
            return expected_arn
        except sns_client.exceptions.NotFoundException:
            logging.info(f"SNS Platform Application '{SNS_PLATFORM_APP_NAME}' não encontrada. Criando...")
            response = sns_client.create_platform_application(
                Name=SNS_PLATFORM_APP_NAME,
                Platform='FCM',
                Attributes={
                    'PlatformCredential': fcm_service_account_json_content
                }
            )
            platform_application_arn = response['PlatformApplicationArn']
            logging.info(f"SNS Platform Application '{SNS_PLATFORM_APP_NAME}' criada com sucesso. ARN: {platform_application_arn}")
            
            if COMMON_TAGS:
                sns_client.tag_resource(ResourceArn=platform_application_arn, Tags=COMMON_TAGS)
                logging.info(f"Tags adicionadas à SNS Platform Application '{SNS_PLATFORM_APP_NAME}'.")
            return platform_application_arn
            
    except Exception as e:
        logging.error(f"Erro ao criar/obter SNS Platform Application: {e}")
        raise
    return None


def create_lambda_execution_role(platform_application_arn):
    """Cria a IAM Role para a execução da Lambda."""
    logging.info(f"Tentando criar/obter IAM Role: {LAMBDA_ROLE_NAME}")
    
    assume_role_policy_document = json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    })

    try:
        role_response = iam_client.get_role(RoleName=LAMBDA_ROLE_NAME)
        role_arn = role_response['Role']['Arn']
        logging.info(f"IAM Role '{LAMBDA_ROLE_NAME}' já existe com ARN: {role_arn}")
    except iam_client.exceptions.NoSuchEntityException:
        logging.info(f"IAM Role '{LAMBDA_ROLE_NAME}' não encontrada. Criando...")
        role_response = iam_client.create_role(
            RoleName=LAMBDA_ROLE_NAME,
            AssumeRolePolicyDocument=assume_role_policy_document,
            Description="Role para a Lambda NeoBellNotificationHandler",
            Tags=COMMON_TAGS
        )
        role_arn = role_response['Role']['Arn']
        logging.info(f"IAM Role '{LAMBDA_ROLE_NAME}' criada com sucesso. ARN: {role_arn}")
        # Pequena espera para garantir que a role esteja propagada antes de anexar políticas
        time.sleep(10) 
    except Exception as e:
        logging.error(f"Erro ao criar/obter IAM Role '{LAMBDA_ROLE_NAME}': {e}")
        raise

    # Anexar política gerenciada para logs básicos
    try:
        iam_client.attach_role_policy(
            RoleName=LAMBDA_ROLE_NAME,
            PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
        )
        logging.info(f"Política AWSLambdaBasicExecutionRole anexada à role '{LAMBDA_ROLE_NAME}'.")
    except Exception as e:
        # Pode falhar se já estiver anexada, o que é aceitável em alguns casos.
        logging.warning(f"Não foi possível anexar AWSLambdaBasicExecutionRole (pode já estar anexada): {e}")


    # Política em linha para DynamoDB e SNS
    lambda_permissions_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "dynamodb:GetItem",
                "Resource": f"arn:aws:dynamodb:{AWS_REGION}:{ACCOUNT_ID}:table/{DYNAMODB_USERS_TABLE_NAME}"
            },
            {
                "Effect": "Allow",
                "Action": "dynamodb:Query",
                "Resource": f"arn:aws:dynamodb:{AWS_REGION}:{ACCOUNT_ID}:table/{DYNAMODB_DEVICE_USER_LINK_TABLE_NAME}"
            },
            {
                "Effect": "Allow",
                "Action": "sns:Publish",
                "Resource": f"{platform_application_arn}/*" # Permite publicar em qualquer endpoint sob esta app
            }
        ]
    }
    try:
        iam_client.put_role_policy(
            RoleName=LAMBDA_ROLE_NAME,
            PolicyName='NeoBellNotificationHandlerPermissions',
            PolicyDocument=json.dumps(lambda_permissions_policy)
        )
        logging.info(f"Política em linha 'NeoBellNotificationHandlerPermissions' adicionada à role '{LAMBDA_ROLE_NAME}'.")
    except Exception as e:
        logging.error(f"Erro ao adicionar política em linha à role '{LAMBDA_ROLE_NAME}': {e}")
        raise
        
    return role_arn

def package_lambda_code(source_file, zip_name='lambda_package.zip'):
    """Empacota o código da Lambda em um arquivo .zip."""
    logging.info(f"Empacotando o código da Lambda de '{source_file}' para '{zip_name}'...")
    try:
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Adiciona o arquivo Python diretamente na raiz do zip
            zf.write(source_file, arcname=os.path.basename(source_file))
        logging.info("Código da Lambda empacotado com sucesso.")
        return zip_name
    except Exception as e:
        logging.error(f"Erro ao empacotar o código da Lambda: {e}")
        raise

def create_lambda_function(role_arn, zip_file_path):
    """Cria a função Lambda."""
    logging.info(f"Tentando criar/obter função Lambda: {LAMBDA_FUNCTION_NAME}")

    try:
        # Verificar se a função já existe
        lambda_client.get_function_configuration(FunctionName=LAMBDA_FUNCTION_NAME)
        logging.info(f"Função Lambda '{LAMBDA_FUNCTION_NAME}' já existe. Nenhuma ação de criação será tomada.")
        # Opcional: Adicionar lógica para atualizar a função se ela existir.
        # Por enquanto, este script foca na criação.
        return f"arn:aws:lambda:{AWS_REGION}:{ACCOUNT_ID}:function:{LAMBDA_FUNCTION_NAME}"
    except lambda_client.exceptions.ResourceNotFoundException:
        logging.info(f"Função Lambda '{LAMBDA_FUNCTION_NAME}' não encontrada. Criando...")
        try:
            with open(zip_file_path, 'rb') as f:
                zipped_code = f.read()

            response = lambda_client.create_function(
                FunctionName=LAMBDA_FUNCTION_NAME,
                Runtime=LAMBDA_RUNTIME,
                Role=role_arn,
                Handler=LAMBDA_HANDLER_FUNCTION,
                Code={'ZipFile': zipped_code},
                Description='Lambda para enviar notificações push para o NeoBell via SNS',
                Timeout=LAMBDA_TIMEOUT,
                MemorySize=LAMBDA_MEMORY_SIZE,
                Publish=True, # Publica uma versão inicial
                Environment={
                    'Variables': {
                        'AWS_REGION': AWS_REGION,
                        'DYNAMODB_USERS_TABLE_NAME': DYNAMODB_USERS_TABLE_NAME,
                        'DYNAMODB_DEVICE_USER_LINK_TABLE_NAME': DYNAMODB_DEVICE_USER_LINK_TABLE_NAME
                    }
                },
                Tags={tag['Key']: tag['Value'] for tag in COMMON_TAGS} if COMMON_TAGS else {}
            )
            lambda_arn = response['FunctionArn']
            logging.info(f"Função Lambda '{LAMBDA_FUNCTION_NAME}' criada com sucesso. ARN: {lambda_arn}")
            return lambda_arn
        except Exception as e:
            logging.error(f"Erro ao criar função Lambda '{LAMBDA_FUNCTION_NAME}': {e}")
            raise
    except Exception as e:
        logging.error(f"Erro ao verificar a função Lambda '{LAMBDA_FUNCTION_NAME}': {e}")
        raise
    return None

def main():
    """Função principal para orquestrar a criação dos recursos."""
    logging.info("Iniciando o script de provisionamento...")

    # 1. Obter conteúdo do arquivo JSON da conta de serviço FCM
    fcm_json_path = input("Por favor, insira o caminho completo para o arquivo JSON da sua conta de serviço Firebase: ")
    if not os.path.exists(fcm_json_path):
        logging.error(f"Arquivo JSON FCM não encontrado em: {fcm_json_path}")
        return
    try:
        with open(fcm_json_path, 'r') as f:
            fcm_service_account_json_content = f.read()
    except Exception as e:
        logging.error(f"Erro ao ler o arquivo JSON FCM: {e}")
        return

    # 2. Criar SNS Platform Application
    platform_app_arn = create_sns_platform_application(fcm_service_account_json_content)
    if not platform_app_arn:
        logging.error("Falha ao criar a SNS Platform Application. Abortando.")
        return

    # 3. Criar IAM Role para a Lambda
    lambda_role_arn = create_lambda_execution_role(platform_app_arn)
    if not lambda_role_arn:
        logging.error("Falha ao criar a IAM Role para a Lambda. Abortando.")
        return
    
    logging.info(f"Aguardando um momento para a propagação da IAM role ({lambda_role_arn})...")
    time.sleep(15) # Espera adicional para garantir que a role esteja totalmente disponível para a Lambda

    # 4. Empacotar o código da Lambda
    if not os.path.exists(LAMBDA_HANDLER_FILE):
        logging.error(f"Arquivo de código da Lambda '{LAMBDA_HANDLER_FILE}' não encontrado. Certifique-se de que ele está no mesmo diretório que este script.")
        return
    
    zip_file = package_lambda_code(LAMBDA_HANDLER_FILE)
    if not zip_file:
        logging.error("Falha ao empacotar o código da Lambda. Abortando.")
        return

    # 5. Criar a Função Lambda
    lambda_function_arn = create_lambda_function(lambda_role_arn, zip_file)
    if not lambda_function_arn:
        logging.error("Falha ao criar a função Lambda. Abortando.")
    else:
        logging.info(f"Função Lambda '{LAMBDA_FUNCTION_NAME}' configurada com ARN: {lambda_function_arn}")

    # Limpar arquivo zip temporário
    if os.path.exists(zip_file):
        try:
            os.remove(zip_file)
            logging.info(f"Arquivo zip temporário '{zip_file}' removido.")
        except Exception as e:
            logging.warning(f"Não foi possível remover o arquivo zip temporário '{zip_file}': {e}")

    logging.info("Script de provisionamento concluído.")

if __name__ == "__main__":
    main()

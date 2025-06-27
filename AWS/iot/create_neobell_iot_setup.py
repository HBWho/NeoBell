# neobell_aws_setup.py
import boto3
import json
import os
import zipfile
import time

# --- Configurações Globais ---
AWS_REGION = "us-east-1"
ACCOUNT_ID = "YOUR_ACCOUNT_ID"  # Ex: "123456789012"

# Estas roles devem ter as políticas de confiança e permissões básicas necessárias.
# O script tentará anexar políticas específicas a elas ou usá-las.
LAMBDA_EXECUTION_ROLE_ARN = f"arn:aws:iam::{ACCOUNT_ID}:role/NeoBellLambdaExecutionRole" # Substitua se o nome for diferente
IOT_RULE_ACTION_ROLE_ARN = f"arn:aws:iam::{ACCOUNT_ID}:role/NeoBellIoTRuleActionRole"   # Substitua se o nome for diferente

# Nome do dispositivo IoT a ser criado
SBC_THING_NAME = "NeoBellSBC-Device-01"
SBC_THING_TYPE_NAME = "NeoBellSBCDeviceType"

# Nomes das Políticas
IOT_DEVICE_POLICY_NAME = "NeoBellSBCBasePolicy"
LAMBDA_IOT_ACCESS_POLICY_NAME = "NeoBellLambdaIoTAccessPolicy" # Política para Lambdas acessarem IoT Data Plane

# Nomes das Funções Lambda
LAMBDA_GEN_VISITOR_URL_NAME = "NeoBellGenerateVisitorUploadUrlHandler"
LAMBDA_PROCESS_VISITOR_NAME = "NeoBellProcessVisitorRegistrationHandler"
LAMBDA_GEN_VIDEO_URL_NAME = "NeoBellGenerateVideoUploadUrlHandler"
LAMBDA_PROCESS_VIDEO_NAME = "NeoBellProcessVideoMessageHandler"
LAMBDA_SBC_HELPER_NAME = "NeoBellSBCHelperHandler"

# Nomes dos arquivos de código Lambda (devem estar no mesmo diretório do script)
LAMBDA_CODE_FILES = {
    LAMBDA_GEN_VISITOR_URL_NAME: "lambda_code_generate_visitor_upload_url.py",
    LAMBDA_PROCESS_VISITOR_NAME: "lambda_code_process_visitor_registration.py",
    LAMBDA_GEN_VIDEO_URL_NAME: "lambda_code_generate_video_upload_url.py",
    LAMBDA_PROCESS_VIDEO_NAME: "lambda_code_process_video_message.py",
    LAMBDA_SBC_HELPER_NAME: "lambda_code_sbc_helper_handler.py",
}

# Nomes das Regras do IoT
IOT_RULE_VISITOR_UPLOAD_REQ = "NeoBellRequestVisitorUploadUrlRule"
IOT_RULE_VIDEO_UPLOAD_REQ = "NeoBellRequestVideoUploadUrlRule"
IOT_RULE_PERMISSIONS_REQ = "NeoBellRequestVisitorPermissionRule"
IOT_RULE_PACKAGES_REQ = "NeoBellRequestPackageInfoRule"
IOT_RULE_LOGS_SUBMIT = "NeoBellSubmitDeviceLogRule"

# Bucket S3 (EXISTENTE)
S3_BUCKET_NAME = "neobell-videomessages-hbwho"

# Configurações de VPC para Lambdas que rodam na VPC
# Se não quiser VPC para alguma delas, deixe as strings vazias ou ajuste a lógica.
# Estas são para NeoBellProcessVisitorRegistrationHandler e NeoBellProcessVideoMessageHandler
LAMBDA_VPC_SUBNET_IDS = "subnet-xxxxxxxxxxxxxxxxx,subnet-yyyyyyyyyyyyyyyyy"
LAMBDA_VPC_SECURITY_GROUP_IDS = "sg-zzzzzzzzzzzzzzzzz"

# Nomes de Tabelas DynamoDB 
DDB_PERMISSIONS_TABLE = "Permissions"
DDB_NEOBELLDEVICES_TABLE = "NeoBellDevices"
DDB_VIDEOMESSAGES_TABLE = "VideoMessages"
DDB_EXPECTEDDELIVERIES_TABLE = "ExpectedDeliveries"
DDB_EVENTLOGS_TABLE = "EventLogs"
# ==============================================================================

# --- Inicializar Clientes Boto3 ---
iam_client = boto3.client('iam', region_name=AWS_REGION)
iot_client = boto3.client('iot', region_name=AWS_REGION)
lambda_client = boto3.client('lambda', region_name=AWS_REGION)
s3_client = boto3.client('s3', region_name=AWS_REGION)

# --- Funções Auxiliares ---
def create_zip_file(source_file, zip_name):
    """Cria um arquivo .zip a partir de um arquivo fonte."""
    if not os.path.exists(source_file):
        print(f"ERRO: Arquivo de código Lambda '{source_file}' não encontrado.")
        return None
    try:
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(source_file, os.path.basename(source_file))
        print(f"Arquivo ZIP '{zip_name}' criado com sucesso a partir de '{source_file}'.")
        return zip_name
    except Exception as e:
        print(f"Erro ao criar arquivo ZIP '{zip_name}': {e}")
        return None

def get_lambda_arn(function_name):
    return f"arn:aws:lambda:{AWS_REGION}:{ACCOUNT_ID}:function:{function_name}"

# --- Funções de Criação/Atualização de Recursos ---

def create_or_update_iot_device_policy():
    """Cria ou atualiza a política base para dispositivos SBC."""
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "iot:Connect",
                "Resource": f"arn:aws:iot:{AWS_REGION}:{ACCOUNT_ID}:client/${{iot:ClientId}}"
            },
            {
                "Effect": "Allow",
                "Action": "iot:Publish",
                "Resource": [
                    f"arn:aws:iot:{AWS_REGION}:{ACCOUNT_ID}:topic/neobell/sbc/${{iot:ClientId}}/registrations/request-upload-url",
                    f"arn:aws:iot:{AWS_REGION}:{ACCOUNT_ID}:topic/neobell/sbc/${{iot:ClientId}}/messages/request-upload-url",
                    f"arn:aws:iot:{AWS_REGION}:{ACCOUNT_ID}:topic/neobell/status",
                    f"arn:aws:iot:{AWS_REGION}:{ACCOUNT_ID}:topic/neobell/sbc/${{iot:ClientId}}/permissions/request",
                    f"arn:aws:iot:{AWS_REGION}:{ACCOUNT_ID}:topic/neobell/sbc/${{iot:ClientId}}/packages/request",
                    f"arn:aws:iot:{AWS_REGION}:{ACCOUNT_ID}:topic/neobell/sbc/${{iot:ClientId}}/logs/submit"
                ]
            },
            {
                "Effect": "Allow",
                "Action": "iot:Subscribe",
                "Resource": [
                    f"arn:aws:iot:{AWS_REGION}:{ACCOUNT_ID}:topicfilter/neobell/sbc/${{iot:ClientId}}/registrations/upload-url-response",
                    f"arn:aws:iot:{AWS_REGION}:{ACCOUNT_ID}:topicfilter/neobell/sbc/${{iot:ClientId}}/messages/upload-url-response",
                    f"arn:aws:iot:{AWS_REGION}:{ACCOUNT_ID}:topicfilter/neobell/commands",
                    f"arn:aws:iot:{AWS_REGION}:{ACCOUNT_ID}:topicfilter/neobell/sbc/${{iot:ClientId}}/permissions/response",
                    f"arn:aws:iot:{AWS_REGION}:{ACCOUNT_ID}:topicfilter/neobell/sbc/${{iot:ClientId}}/packages/response"
                ]
            },
            {
                "Effect": "Allow",
                "Action": "iot:Receive",
                "Resource": [
                    f"arn:aws:iot:{AWS_REGION}:{ACCOUNT_ID}:topic/neobell/sbc/${{iot:ClientId}}/registrations/upload-url-response",
                    f"arn:aws:iot:{AWS_REGION}:{ACCOUNT_ID}:topic/neobell/sbc/${{iot:ClientId}}/messages/upload-url-response",
                    f"arn:aws:iot:{AWS_REGION}:{ACCOUNT_ID}:topic/neobell/commands",
                    f"arn:aws:iot:{AWS_REGION}:{ACCOUNT_ID}:topic/neobell/sbc/${{iot:ClientId}}/permissions/response",
                    f"arn:aws:iot:{AWS_REGION}:{ACCOUNT_ID}:topic/neobell/sbc/${{iot:ClientId}}/packages/response"
                ]
            }
        ]
    }
    try:
        iot_client.create_policy(
            policyName=IOT_DEVICE_POLICY_NAME,
            policyDocument=json.dumps(policy_document)
        )
        print(f"Política IoT '{IOT_DEVICE_POLICY_NAME}' criada.")
    except iot_client.exceptions.ResourceAlreadyExistsException:
        print(f"Política IoT '{IOT_DEVICE_POLICY_NAME}' já existe. Criando nova versão...")
        try:
            iot_client.create_policy_version(
                policyName=IOT_DEVICE_POLICY_NAME,
                policyDocument=json.dumps(policy_document),
                setAsDefault=True
            )
            print(f"Nova versão da política IoT '{IOT_DEVICE_POLICY_NAME}' criada e definida como padrão.")
        except Exception as e_pv:
            print(f"Erro ao criar nova versão da política IoT '{IOT_DEVICE_POLICY_NAME}': {e_pv}")
    except Exception as e:
        print(f"Erro ao criar/atualizar política IoT '{IOT_DEVICE_POLICY_NAME}': {e}")

def create_iot_thing_and_certificate():
    """Cria o Thing Type, Thing, certificado e anexa tudo."""
    # 1. Thing Type
    try:
        iot_client.create_thing_type(thingTypeName=SBC_THING_TYPE_NAME)
        print(f"Tipo de Coisa IoT '{SBC_THING_TYPE_NAME}' criado.")
    except iot_client.exceptions.ResourceAlreadyExistsException:
        print(f"Tipo de Coisa IoT '{SBC_THING_TYPE_NAME}' já existe.")
    except Exception as e:
        print(f"Erro ao criar Tipo de Coisa IoT '{SBC_THING_TYPE_NAME}': {e}")
        return None, None

    # 2. Thing
    try:
        thing_response = iot_client.create_thing(
            thingName=SBC_THING_NAME,
            thingTypeName=SBC_THING_TYPE_NAME
        )
        thing_arn = thing_response['thingArn']
        print(f"Coisa IoT '{SBC_THING_NAME}' criada com ARN: {thing_arn}.")
    except iot_client.exceptions.ResourceAlreadyExistsException:
        print(f"Coisa IoT '{SBC_THING_NAME}' já existe. Usando existente.")
        thing_desc = iot_client.describe_thing(thingName=SBC_THING_NAME)
        thing_arn = thing_desc['thingArn']
    except Exception as e:
        print(f"Erro ao criar Coisa IoT '{SBC_THING_NAME}': {e}")
        return None, None

    # 3. Certificado e Chaves
    cert_folder = "device_certs"
    if not os.path.exists(cert_folder):
        os.makedirs(cert_folder)
    
    cert_file = os.path.join(cert_folder, f"{SBC_THING_NAME}.pem.crt")
    priv_key_file = os.path.join(cert_folder, f"{SBC_THING_NAME}.private.key")
    pub_key_file = os.path.join(cert_folder, f"{SBC_THING_NAME}.public.key")

    try:
        print(f"Criando novo certificado para {SBC_THING_NAME}...")
        keys_cert_response = iot_client.create_keys_and_certificate(setAsActive=True)
        certificate_arn = keys_cert_response['certificateArn']
        certificate_pem = keys_cert_response['certificatePem']
        private_key = keys_cert_response['keyPair']['PrivateKey']
        public_key = keys_cert_response['keyPair']['PublicKey']

        with open(cert_file, 'w') as f: f.write(certificate_pem)
        with open(priv_key_file, 'w') as f: f.write(private_key)
        with open(pub_key_file, 'w') as f: f.write(public_key)
        
        print(f"Certificado e chaves para '{SBC_THING_NAME}' criados e salvos em '{cert_folder}'. ARN do Certificado: {certificate_arn}")
        print(f"  Certificado: {cert_file}")
        print(f"  Chave Privada: {priv_key_file}")
        print(f"  Chave Pública: {pub_key_file}")
        print("IMPORTANTE: Guarde a chave privada em local seguro!")

        # 4. Anexar Política ao Certificado
        iot_client.attach_policy(policyName=IOT_DEVICE_POLICY_NAME, target=certificate_arn)
        print(f"Política '{IOT_DEVICE_POLICY_NAME}' anexada ao certificado '{certificate_arn}'.")

        # 5. Anexar Certificado ao Thing
        iot_client.attach_thing_principal(thingName=SBC_THING_NAME, principal=certificate_arn)
        print(f"Certificado '{certificate_arn}' anexado à Coisa '{SBC_THING_NAME}'.")
        
        return thing_arn, certificate_arn
    except Exception as e:
        print(f"Erro ao criar/anexar certificado para '{SBC_THING_NAME}': {e}")
        print("Se o certificado já existe e você quer reutilizá-lo, esta parte do script precisaria ser ajustada.")
        return thing_arn, None # Retorna thing_arn se a coisa foi criada/encontrada

def create_or_update_lambda_iot_access_policy():
    """Cria ou atualiza a política IAM para Lambdas acessarem o IoT Data Plane."""
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowNeoBellLambdaToPublishMqtt",
                "Effect": "Allow",
                "Action": "iot:Publish",
                "Resource": f"arn:aws:iot:{AWS_REGION}:{ACCOUNT_ID}:topic/neobell/*"
            }
            # Adicione outras permissões de dados IoT se necessário para as Lambdas
        ]
    }
    policy_arn = f"arn:aws:iam::{ACCOUNT_ID}:policy/{LAMBDA_IOT_ACCESS_POLICY_NAME}"
    try:
        iam_client.create_policy(
            PolicyName=LAMBDA_IOT_ACCESS_POLICY_NAME,
            PolicyDocument=json.dumps(policy_document),
            Description="Policy for NeoBell Lambda functions to publish to AWS IoT topics."
        )
        print(f"Política IAM '{LAMBDA_IOT_ACCESS_POLICY_NAME}' criada.")
    except iam_client.exceptions.EntityAlreadyExistsException:
        print(f"Política IAM '{LAMBDA_IOT_ACCESS_POLICY_NAME}' já existe. Considere atualizar manualmente se necessário.")
        # Para atualizar programaticamente, seria necessário gerenciar versões da política.
    except Exception as e:
        print(f"Erro ao criar política IAM '{LAMBDA_IOT_ACCESS_POLICY_NAME}': {e}")
        return

    # Anexar à role de execução da Lambda
    try:
        lambda_role_name = LAMBDA_EXECUTION_ROLE_ARN.split('/')[-1]
        iam_client.attach_role_policy(
            RoleName=lambda_role_name,
            PolicyArn=policy_arn
        )
        print(f"Política '{LAMBDA_IOT_ACCESS_POLICY_NAME}' anexada à role '{lambda_role_name}'.")
    except Exception as e:
        # Pode falhar se já estiver anexada, o que é ok.
        print(f"Aviso/Erro ao anexar política '{LAMBDA_IOT_ACCESS_POLICY_NAME}' à role '{lambda_role_name}' (pode já estar anexada): {e}")


def create_or_update_lambda_function(function_name, handler, code_file, env_vars, tags, use_vpc=False):
    """Cria ou atualiza uma função Lambda."""
    zip_file_name = f"{function_name}_payload.zip"
    zip_path = create_zip_file(code_file, zip_file_name)
    if not zip_path:
        return None

    lambda_arn = get_lambda_arn(function_name)
    
    vpc_config = {}
    if use_vpc:
        if "subnet-xxxxxxxxxxxxxxxxx" in LAMBDA_VPC_SUBNET_IDS or "sg-zzzzzzzzzzzzzzzzz" in LAMBDA_VPC_SECURITY_GROUP_IDS:
            print(f"AVISO: Placeholders de VPC não substituídos para {function_name}. Não será configurada com VPC.")
        else:
            vpc_config = {
                'SubnetIds': LAMBDA_VPC_SUBNET_IDS.split(','),
                'SecurityGroupIds': LAMBDA_VPC_SECURITY_GROUP_IDS.split(',')
            }
            print(f"Configurando {function_name} com VPC: Subnets {vpc_config['SubnetIds']}, SGs {vpc_config['SecurityGroupIds']}")

    common_params = {
        'FunctionName': function_name,
        'Runtime': 'python3.11',
        'Role': LAMBDA_EXECUTION_ROLE_ARN,
        'Handler': handler,
        'Timeout': 30, # Ajuste conforme necessário
        'MemorySize': 256, # Ajuste conforme necessário
        'Publish': True,
        'Environment': {'Variables': env_vars},
        'Tags': tags,
        'Architectures': ['arm64']
    }
    if vpc_config:
        common_params['VpcConfig'] = vpc_config

    try:
        with open(zip_path, 'rb') as f_zip:
            zip_bytes = f_zip.read()
        
        response = lambda_client.create_function(
            **common_params,
            Code={'ZipFile': zip_bytes}
        )
        created_lambda_arn = response['FunctionArn']
        print(f"Função Lambda '{function_name}' criada com ARN: {created_lambda_arn}.")
        if vpc_config: # Esperar ativação se em VPC
            print(f"Aguardando Lambda '{function_name}' ficar ativa (configuração VPC)...")
            waiter = lambda_client.get_waiter('function_active_v2')
            waiter.wait(FunctionName=function_name, Qualifier=response.get('Version', '$LATEST'))
            print(f"Lambda '{function_name}' está ativa.")
        return created_lambda_arn
    except lambda_client.exceptions.ResourceConflictException:
        print(f"Função Lambda '{function_name}' já existe. Atualizando código e configuração...")
        try:
            with open(zip_path, 'rb') as f_zip_update:
                zip_bytes_update = f_zip_update.read()
            lambda_client.update_function_code(FunctionName=function_name, ZipFile=zip_bytes_update, Publish=True)
            print(f"Código da Lambda '{function_name}' atualizado.")
            
            # Pequena pausa antes de atualizar a configuração
            time.sleep(10) 
            
            config_params_update = {key: value for key, value in common_params.items() if key not in ['FunctionName', 'Publish', 'Architectures']}
            # Runtime e Arquitetura não podem ser atualizados junto com outras configs facilmente ou após criação.
            # Se precisar mudar, pode ser mais fácil recriar ou fazer em passos separados.
            lambda_client.update_function_configuration(**config_params_update)
            print(f"Configuração da Lambda '{function_name}' atualizada.")
            lambda_client.tag_resource(Resource=lambda_arn, Tags=tags) # Reaplicar tags
            return lambda_arn
        except Exception as e_update:
            print(f"Erro ao atualizar Lambda '{function_name}': {e_update}")
            return lambda_arn # Retorna o ARN conhecido
    except Exception as e:
        print(f"Erro ao criar Lambda '{function_name}': {e}")
        return None
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)

def add_lambda_permission_for_iot_rule(lambda_arn, rule_name):
    """Adiciona permissão para uma Regra IoT invocar uma Lambda."""
    statement_id = f"IoT-{rule_name}-Invoke-{function_name.replace('_','-')[:20]}" # ID único
    try:
        # Tenta remover permissão antiga com o mesmo ID para evitar conflito
        lambda_client.remove_permission(FunctionName=lambda_arn, StatementId=statement_id, Qualifiers='$LATEST')
        print(f"Permissão antiga '{statement_id}' removida da Lambda, se existia.")
    except lambda_client.exceptions.ResourceNotFoundException:
        pass # Ok, não existia
    except Exception as e_rem_perm:
        print(f"Aviso ao tentar remover permissão antiga '{statement_id}' da Lambda: {e_rem_perm}")

    try:
        iot_rule_arn = f"arn:aws:iot:{AWS_REGION}:{ACCOUNT_ID}:rule/{rule_name}"
        lambda_client.add_permission(
            FunctionName=lambda_arn,
            StatementId=statement_id,
            Action="lambda:InvokeFunction",
            Principal="iot.amazonaws.com",
            SourceArn=iot_rule_arn
        )
        print(f"Permissão adicionada à Lambda '{lambda_arn.split(':')[-1]}' para ser invocada pela Regra IoT '{rule_name}'.")
    except Exception as e:
        print(f"Erro ao adicionar permissão à Lambda para Regra IoT '{rule_name}': {e}")


def create_or_update_iot_rule(rule_name, sql_query, target_lambda_arn):
    """Cria ou atualiza uma Regra do IoT."""
    rule_payload = {
        'sql': sql_query,
        'actions': [{'lambda': {'functionArn': target_lambda_arn}}],
        'ruleDisabled': False,
        'awsIotSqlVersion': '2016-03-23',
        'errorAction': { # Adicionar uma ação de erro básica para logs
            'cloudwatchLogs': {
                'logGroupName': f"/aws/iot/{rule_name}-errors",
                'roleArn': IOT_RULE_ACTION_ROLE_ARN # Role para a regra escrever logs
            }
        }
    }
    # A role IOT_RULE_ACTION_ROLE_ARN deve ter permissão para lambda:InvokeFunction
    # E também para logs:CreateLogStream e logs:PutLogEvents para a ação de erro.
    # O console geralmente configura a permissão lambda:InvokeFunction na política de recursos da Lambda.
    # O script fará isso explicitamente com add_lambda_permission_for_iot_rule.

    try:
        iot_client.create_topic_rule(ruleName=rule_name, topicRulePayload=rule_payload)
        print(f"Regra IoT '{rule_name}' criada.")
    except iot_client.exceptions.ResourceAlreadyExistsException:
        print(f"Regra IoT '{rule_name}' já existe. Atualizando...")
        iot_client.replace_topic_rule(ruleName=rule_name, topicRulePayload=rule_payload)
        print(f"Regra IoT '{rule_name}' atualizada.")
    except Exception as e:
        print(f"Erro ao criar/atualizar Regra IoT '{rule_name}': {e}")
        return
    
    # Adicionar permissão para a regra invocar a Lambda
    add_lambda_permission_for_iot_rule(target_lambda_arn, rule_name)


def configure_s3_notification(lambda_arn, event_name, s3_prefix, function_name_for_id):
    """Configura uma notificação de evento S3 para uma Lambda."""
    notification_id = f"s3-lambda-{event_name.replace('_','-')}-{function_name_for_id[:10]}"
    
    try:
        # Adicionar permissão para S3 invocar a Lambda
        statement_id_s3 = f"S3Invoke-{function_name_for_id[:20]}-{s3_prefix.replace('/','-')[:10]}"
        try:
            lambda_client.remove_permission(FunctionName=lambda_arn, StatementId=statement_id_s3)
            print(f"Permissão S3 antiga '{statement_id_s3}' removida da Lambda, se existia.")
        except lambda_client.exceptions.ResourceNotFoundException:
            pass
        except Exception as e_rem_s3_perm:
             print(f"Aviso ao tentar remover permissão S3 antiga '{statement_id_s3}': {e_rem_s3_perm}")

        lambda_client.add_permission(
            FunctionName=lambda_arn,
            StatementId=statement_id_s3,
            Action='lambda:InvokeFunction',
            Principal='s3.amazonaws.com',
            SourceArn=f'arn:aws:s3:::{S3_BUCKET_NAME}',
            SourceAccount=ACCOUNT_ID
        )
        print(f"Permissão adicionada à Lambda '{lambda_arn.split(':')[-1]}' para ser invocada pelo S3 bucket '{S3_BUCKET_NAME}'.")

        # Obter configuração de notificação existente para não sobrescrever outras
        try:
            current_config = s3_client.get_bucket_notification_configuration(Bucket=S3_BUCKET_NAME)
            # Remover 'ResponseMetadata' para poder reenviar
            if 'ResponseMetadata' in current_config:
                del current_config['ResponseMetadata']
            
            # Remover configuração antiga com o mesmo ID, se houver
            if 'LambdaFunctionConfigurations' in current_config:
                current_config['LambdaFunctionConfigurations'] = [
                    c for c in current_config['LambdaFunctionConfigurations'] if c.get('Id') != notification_id
                ]
        except s3_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucketNotificationConfiguration': # Erro específico para S3, não genérico
                 current_config = {} # Nenhuma configuração existente
            else:
                print(f"Erro ao obter configuração de notificação S3 existente: {e}")
                current_config = {}


        if 'LambdaFunctionConfigurations' not in current_config:
            current_config['LambdaFunctionConfigurations'] = []
        
        new_lambda_config = {
            'Id': notification_id,
            'LambdaFunctionArn': lambda_arn,
            'Events': ['s3:ObjectCreated:*'], # Ou mais específico como s3:ObjectCreated:Put
            'Filter': {'Key': {'FilterRules': [{'Name': 'prefix', 'Value': s3_prefix}]}}
        }
        current_config['LambdaFunctionConfigurations'].append(new_lambda_config)
        
        s3_client.put_bucket_notification_configuration(
            Bucket=S3_BUCKET_NAME,
            NotificationConfiguration=current_config
        )
        print(f"Notificação S3 '{event_name}' (ID: {notification_id}) configurada para o prefixo '{s3_prefix}' no bucket '{S3_BUCKET_NAME}'.")

    except Exception as e:
        print(f"Erro ao configurar notificação S3 '{event_name}': {e}", exc_info=True)


# --- Função Principal de Setup ---
def main():
    print("--- Iniciando Configuração Completa do NeoBell na AWS ---")

    # Validar placeholders principais
    if "YOUR_ACCOUNT_ID" in ACCOUNT_ID or len(ACCOUNT_ID) != 12:
        print("ERRO CRÍTICO: ACCOUNT_ID não foi substituído ou é inválido. Abortando.")
        return
    if "NeoBellLambdaExecutionRole" not in LAMBDA_EXECUTION_ROLE_ARN or \
       "NeoBellIoTRuleActionRole" not in IOT_RULE_ACTION_ROLE_ARN:
        print("ERRO CRÍTICO: ARNs das roles de execução não parecem corretos. Verifique os placeholders.")
        return

    # 1. Política IoT para Dispositivos
    print("\n--- 1. Configurando Política IoT para Dispositivos ---")
    create_or_update_iot_device_policy()

    # 2. Coisa IoT e Certificado
    print("\n--- 2. Configurando Coisa IoT e Certificado ---")
    thing_arn, cert_arn = create_iot_thing_and_certificate()
    if not thing_arn:
        print("Falha ao configurar Coisa IoT. Algumas etapas subsequentes podem falhar.")
    
    # 3. Política IAM para Lambdas acessarem IoT Data Plane
    print("\n--- 3. Configurando Política IAM para Lambdas (Acesso IoT) ---")
    create_or_update_lambda_iot_access_policy()

    # 4. Funções Lambda
    print("\n--- 4. Configurando Funções Lambda ---")
    
    # Lambda: NeoBellGenerateVisitorUploadUrlHandler (Sem VPC)
    lambda_gen_visitor_url_arn = create_or_update_lambda_function(
        function_name=LAMBDA_GEN_VISITOR_URL_NAME,
        handler="lambda_code_generate_visitor_upload_url.lambda_handler",
        code_file=LAMBDA_CODE_FILES[LAMBDA_GEN_VISITOR_URL_NAME],
        env_vars={'S3_BUCKET_NAME': S3_BUCKET_NAME, 'AWS_REGION': AWS_REGION},
        tags={'Project': 'NeoBell', 'Purpose': 'IoTGenerateVisitorUploadUrl'},
        use_vpc=False
    )

    # Lambda: NeoBellProcessVisitorRegistrationHandler (Com VPC)
    lambda_process_visitor_arn = create_or_update_lambda_function(
        function_name=LAMBDA_PROCESS_VISITOR_NAME,
        handler="lambda_code_process_visitor_registration.lambda_handler",
        code_file=LAMBDA_CODE_FILES[LAMBDA_PROCESS_VISITOR_NAME],
        env_vars={
            'PERMISSIONS_TABLE_NAME': DDB_PERMISSIONS_TABLE,
            'NEOBELLDEVICES_TABLE_NAME': DDB_NEOBELLDEVICES_TABLE,
            'AWS_REGION': AWS_REGION
        },
        tags={'Project': 'NeoBell', 'Purpose': 'IoTProcessVisitorRegistration'},
        use_vpc=True # Habilita configuração VPC
    )

    # Lambda: NeoBellGenerateVideoUploadUrlHandler (Sem VPC)
    lambda_gen_video_url_arn = create_or_update_lambda_function(
        function_name=LAMBDA_GEN_VIDEO_URL_NAME,
        handler="lambda_code_generate_video_upload_url.lambda_handler",
        code_file=LAMBDA_CODE_FILES[LAMBDA_GEN_VIDEO_URL_NAME],
        env_vars={
            'S3_BUCKET_NAME': S3_BUCKET_NAME,
            'AWS_REGION': AWS_REGION,
            'NEOBELLDEVICES_TABLE_NAME': DDB_NEOBELLDEVICES_TABLE
        },
        tags={'Project': 'NeoBell', 'Purpose': 'IoTGenerateVideoUploadUrl'},
        use_vpc=False
    )

    # Lambda: NeoBellProcessVideoMessageHandler (Com VPC)
    lambda_process_video_arn = create_or_update_lambda_function(
        function_name=LAMBDA_PROCESS_VIDEO_NAME,
        handler="lambda_code_process_video_message.lambda_handler",
        code_file=LAMBDA_CODE_FILES[LAMBDA_PROCESS_VIDEO_NAME],
        env_vars={
            'VIDEOMESSAGES_TABLE_NAME': DDB_VIDEOMESSAGES_TABLE,
            'NEOBELLDEVICES_TABLE_NAME': DDB_NEOBELLDEVICES_TABLE,
            'AWS_REGION': AWS_REGION
        },
        tags={'Project': 'NeoBell', 'Purpose': 'IoTProcessVideoMessage'},
        use_vpc=True # Habilita configuração VPC
    )

    # Lambda: NeoBellSBCHelperHandler (Sem VPC)
    lambda_sbc_helper_arn = create_or_update_lambda_function(
        function_name=LAMBDA_SBC_HELPER_NAME,
        handler="lambda_code_sbc_helper_handler.lambda_handler",
        code_file=LAMBDA_CODE_FILES[LAMBDA_SBC_HELPER_NAME],
        env_vars={
            'AWS_REGION': AWS_REGION,
            'NEOBELLDEVICES_TABLE_NAME': DDB_NEOBELLDEVICES_TABLE,
            'PERMISSIONS_TABLE_NAME': DDB_PERMISSIONS_TABLE,
            'EXPECTEDDELIVERIES_TABLE_NAME': DDB_EXPECTEDDELIVERIES_TABLE,
            'EVENTLOGS_TABLE_NAME': DDB_EVENTLOGS_TABLE
        },
        tags={'Project': 'NeoBell', 'Purpose': 'SBCHelperFunctions'},
        use_vpc=False
    )

    # 5. Regras do IoT
    print("\n--- 5. Configurando Regras do IoT ---")
    if lambda_gen_visitor_url_arn:
        create_or_update_iot_rule(
            rule_name=IOT_RULE_VISITOR_UPLOAD_REQ,
            sql_query=f"SELECT *, topic(3) as sbc_id, topic() as invoking_topic FROM 'neobell/sbc/+/registrations/request-upload-url'",
            target_lambda_arn=lambda_gen_visitor_url_arn
        )
    if lambda_gen_video_url_arn:
        create_or_update_iot_rule(
            rule_name=IOT_RULE_VIDEO_UPLOAD_REQ,
            sql_query=f"SELECT *, topic(3) as sbc_id, topic() as invoking_topic FROM 'neobell/sbc/+/messages/request-upload-url'",
            target_lambda_arn=lambda_gen_video_url_arn
        )
    if lambda_sbc_helper_arn:
        create_or_update_iot_rule(
            rule_name=IOT_RULE_PERMISSIONS_REQ,
            sql_query=f"SELECT *, topic(3) as sbc_id, topic() as invoking_topic FROM 'neobell/sbc/+/permissions/request'",
            target_lambda_arn=lambda_sbc_helper_arn
        )
        create_or_update_iot_rule(
            rule_name=IOT_RULE_PACKAGES_REQ,
            sql_query=f"SELECT *, topic(3) as sbc_id, topic() as invoking_topic FROM 'neobell/sbc/+/packages/request'",
            target_lambda_arn=lambda_sbc_helper_arn
        )
        create_or_update_iot_rule(
            rule_name=IOT_RULE_LOGS_SUBMIT,
            sql_query=f"SELECT *, topic(3) as sbc_id, topic() as invoking_topic FROM 'neobell/sbc/+/logs/submit'",
            target_lambda_arn=lambda_sbc_helper_arn
        )

    # 6. Notificações de Evento S3
    print("\n--- 6. Configurando Notificações de Evento S3 ---")
    if lambda_process_visitor_arn:
        configure_s3_notification(
            lambda_arn=lambda_process_visitor_arn,
            event_name="NeoBellVisitorImageUploadedTrigger",
            s3_prefix="visitor-registrations/",
            function_name_for_id=LAMBDA_PROCESS_VISITOR_NAME
        )
    if lambda_process_video_arn:
        configure_s3_notification(
            lambda_arn=lambda_process_video_arn,
            event_name="NeoBellVideoMessageUploadedTrigger",
            s3_prefix="video-messages/",
            function_name_for_id=LAMBDA_PROCESS_VIDEO_NAME
        )

    print("\n--- Configuração Completa do NeoBell na AWS (Boto3) CONCLUÍDA ---")
    print("Verifique os logs para quaisquer erros ou avisos.")
    if cert_arn:
        print(f"Certificado para {SBC_THING_NAME} (ARN: {cert_arn}) foi criado/referenciado.")
        print(f"Os arquivos do certificado estão em: ./{cert_folder}/")


if __name__ == "__main__":
    # Validação inicial de placeholders críticos
    if "YOUR_ACCOUNT_ID" == ACCOUNT_ID or \
       "YOUR_LAMBDA_EXECUTION_ROLE_ARN_PLACEHOLDER" == LAMBDA_EXECUTION_ROLE_ARN or \
       "YOUR_IOT_RULE_ACTION_ROLE_ARN_PLACEHOLDER" == IOT_RULE_ACTION_ROLE_ARN:
        print("="*70)
        print("ERRO: PLACEHOLDERS CRÍTICOS NÃO FORAM SUBSTITUÍDOS NO SCRIPT!")
        print("Por favor, edite o script e substitua ACCOUNT_ID, LAMBDA_EXECUTION_ROLE_ARN, e IOT_RULE_ACTION_ROLE_ARN.")
        print("Se estiver usando Lambdas em VPC, substitua também LAMBDA_VPC_SUBNET_IDS e LAMBDA_VPC_SECURITY_GROUP_IDS.")
        print("="*70)
    else:
        main()


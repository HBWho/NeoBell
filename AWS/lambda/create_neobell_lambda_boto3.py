import boto3
import zipfile
import os
import time

# --- Configuration - Replace these placeholders ---
AWS_REGION = 'us-east-1'
LAMBDA_EXECUTION_ROLE_ARN = 'arn:aws:iam:{ACCOUNT_ID}role/NeoBellLambdaExecutionRole'
VPC_ID = 'vpc-03d539628deb8a6f0' # Not directly used by lambda.create_function, but for VpcConfig
SUBNET_IDS = ['subnet-08a088e1f7b5881d7', 'subnet-0647c7fe2233622c8']
SECURITY_GROUP_IDS = ['sg-07fc7ab37c32d7bb6']
# --- End Configuration ---

LAMBDA_RUNTIME = 'python3.11'
LAMBDA_ARCHITECTURE = 'arm64'
LAMBDA_MEMORY_SIZE = 128  # MB
LAMBDA_TIMEOUT = 30  # seconds

# Nova estrutura para definir Lambdas e seus arquivos de código
lambda_definitions = [
    {
        "FunctionName": "NeoBellUserHandler",
        "HandlerFileName": "lambda_function_NeoBellUserHandler.py", # Nome do arquivo .py específico
        "HandlerFunction": "lambda_function_NeoBellUserHandler.lambda_handler", # Módulo.função
        "Description": "Handles user management, profile, and NFC tag operations for NeoBell.",
        "PurposeTag": "UserManagement"
    },
    {
        "FunctionName": "NeoBellDeviceHandler",
        "HandlerFileName": "lambda_function_NeoBellDeviceHandler.py",
        "HandlerFunction": "lambda_function_NeoBellDeviceHandler.lambda_handler",
        "Description": "Handles NeoBell device (SBC) management and device-user links.",
        "PurposeTag": "DeviceManagement"
    },
    {
        "FunctionName": "NeoBellMessageHandler",
        "HandlerFileName": "lambda_function_NeoBellMessageHandler.py",
        "HandlerFunction": "lambda_function_NeoBellMessageHandler.lambda_handler",
        "Description": "Handles video message metadata, access, and S3 URL generation.",
        "PurposeTag": "MessageManagement"
    },
    {
        "FunctionName": "NeoBellDeliveryHandler",
        "HandlerFileName": "lambda_function_NeoBellDeliveryHandler.py",
        "HandlerFunction": "lambda_function_NeoBellDeliveryHandler.lambda_handler",
        "Description": "Handles expected package delivery management.",
        "PurposeTag": "DeliveryManagement"
    },
    {
        "FunctionName": "NeoBellVisitorHandler",
        "HandlerFileName": "lambda_function_NeoBellVisitorHandler.py",
        "HandlerFunction": "lambda_function_NeoBellVisitorHandler.lambda_handler",
        "Description": "Handles visitor (face tag) permissions management.",
        "PurposeTag": "VisitorManagement"
    },
    {
        "FunctionName": "NeoBellActivityLogHandler",
        "HandlerFileName": "lambda_function_NeoBellActivityLogHandler.py",
        "HandlerFunction": "lambda_function_NeoBellActivityLogHandler.lambda_handler", 
        "Description": "Handles retrieval of activity logs for users.",
        "PurposeTag": "ActivityLogging"
    },
    {
        "FunctionName": "NeoBellPostConfirmationHandler",
        "HandlerFileName": "lambda_function_NeoBellPostConfirmationHandler.py",
        "HandlerFunction": "lambda_function_NeoBellPostConfirmationHandler.lambda_handler",
        "Description": "Handles Cognito Post Confirmation trigger to populate NeoBellUsers table.",
        "PurposeTag": "CognitoTrigger"
    }
]

def create_lambda_zip(zip_file_name, python_code_file):
    """Cria um arquivo zip para o código da função Lambda."""
    try:
        # Garante que o python_code_file é apenas o nome do arquivo, não um caminho absoluto dentro do zip
        archive_file_name = os.path.basename(python_code_file)
        with zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(python_code_file, archive_file_name) # O segundo argumento é como ele será nomeado no zip
        print(f"Arquivo zip criado com sucesso: {zip_file_name} a partir de {python_code_file}")
        return True
    except FileNotFoundError:
        print(f"Erro: O arquivo {python_code_file} não foi encontrado.")
        return False
    except Exception as e:
        print(f"Erro ao criar arquivo zip {zip_file_name}: {e}")
        return False

def create_lambda_functions(lambda_client):
    """Cria as funções Lambda definidas em lambda_definitions."""
    created_functions_arns = {}

    for config in lambda_definitions:
        function_name = config["FunctionName"]
        python_code_file = config["HandlerFileName"]
        lambda_handler_path = config["HandlerFunction"] # Ex: "lambda_function_NeoBellUserHandler.lambda_handler"
        
        # Nome do arquivo zip específico para esta função
        zip_file_name = f"{function_name}_package.zip"

        print(f"\nProcessando Lambda function: {function_name} com código de {python_code_file}")

        if not os.path.exists(python_code_file):
            print(f"Erro: Arquivo de código {python_code_file} para {function_name} não encontrado. Pulando.")
            continue

        if not create_lambda_zip(zip_file_name, python_code_file):
            print(f"Falha ao criar zip para {function_name}. Pulando.")
            continue

        try:
            with open(zip_file_name, 'rb') as f:
                zipped_code = f.read()

            print(f"Tentando criar/atualizar {function_name} com handler {lambda_handler_path}")
            
            try:
                response = lambda_client.create_function(
                    FunctionName=function_name,
                    Runtime=LAMBDA_RUNTIME,
                    Role=LAMBDA_EXECUTION_ROLE_ARN,
                    Handler=lambda_handler_path, # Handler path: nome_do_arquivo_no_zip.funcao_handler
                    Code={'ZipFile': zipped_code},
                    Description=config["Description"],
                    Timeout=LAMBDA_TIMEOUT,
                    MemorySize=LAMBDA_MEMORY_SIZE,
                    Publish=True,
                    VpcConfig={
                        'SubnetIds': SUBNET_IDS,
                        'SecurityGroupIds': SECURITY_GROUP_IDS
                    },
                    PackageType='Zip',
                    Architectures=[LAMBDA_ARCHITECTURE],
                    Tags={
                        'Project': 'NeoBell',
                        'Purpose': config["PurposeTag"],
                        'Name': function_name
                    }
                )
                waiter = lambda_client.get_waiter('function_active_v2')
                waiter.wait(FunctionName=function_name, WaiterConfig={'Delay': 5, 'MaxAttempts': 24})
                
                function_arn = response['FunctionArn']
                created_functions_arns[function_name] = function_arn
                print(f"Função Lambda criada com sucesso: {function_name}, ARN: {function_arn}")

            except lambda_client.exceptions.ResourceConflictException:
                print(f"Função Lambda {function_name} já existe. Atualizando configuração e código...")
                try:
                    # Atualizar código da função
                    code_update_response = lambda_client.update_function_code(
                        FunctionName=function_name,
                        ZipFile=zipped_code,
                        Publish=True
                    )
                    waiter_updated = lambda_client.get_waiter('function_updated_v2')
                    waiter_updated.wait(FunctionName=function_name, WaiterConfig={'Delay': 5, 'MaxAttempts': 24})
                    print(f"Código da função atualizado para {function_name}. Nova versão: {code_update_response.get('Version')}")

                    # Atualizar configuração da função (incluindo o Handler)
                    conf_update_response = lambda_client.update_function_configuration(
                        FunctionName=function_name,
                        Role=LAMBDA_EXECUTION_ROLE_ARN,
                        Handler=lambda_handler_path, # Garante que o handler está correto
                        Description=config["Description"],
                        Timeout=LAMBDA_TIMEOUT,
                        MemorySize=LAMBDA_MEMORY_SIZE,
                        VpcConfig={
                            'SubnetIds': SUBNET_IDS,
                            'SecurityGroupIds': SECURITY_GROUP_IDS
                        },
                        Runtime=LAMBDA_RUNTIME,
                        Architectures=[LAMBDA_ARCHITECTURE]
                    )
                    # Esperar a atualização da configuração completar
                    waiter_conf_updated = lambda_client.get_waiter('function_updated_v2')
                    waiter_conf_updated.wait(FunctionName=conf_update_response['FunctionName'], WaiterConfig={'Delay': 5, 'MaxAttempts': 24})
                    print(f"Configuração da função atualizada para {function_name}.")
                    
                    # Obter ARN se não estiver disponível (caso a criação tenha falhado e estejamos apenas atualizando)
                    if function_name not in created_functions_arns:
                        func_details = lambda_client.get_function(FunctionName=function_name)
                        created_functions_arns[function_name] = func_details['Configuration']['FunctionArn']

                    # Atualizar tags
                    lambda_client.tag_resource(
                        Resource=created_functions_arns[function_name],
                        Tags={
                            'Project': 'NeoBell',
                            'Purpose': config["PurposeTag"],
                            'Name': function_name
                        }
                    )
                    print(f"Tags atualizadas para {function_name}.")
                    print(f"Função Lambda {function_name} (ARN: {created_functions_arns[function_name]}) atualizada.")

                except Exception as e_update:
                    print(f"Erro ao atualizar função Lambda {function_name}: {e_update}")
            except Exception as e_create:
                print(f"Erro ao criar função Lambda {function_name}: {e_create}")

        finally:
            # Limpar o arquivo zip após o uso
            if os.path.exists(zip_file_name):
                os.remove(zip_file_name)
                print(f"Arquivo zip {zip_file_name} limpo.")
        
    print("\n--- ARNs das Lambdas (você precisará disso para a configuração do API Gateway) ---")
    for name, arn in created_functions_arns.items():
        print(f"{name}: {arn}")
    
    return created_functions_arns

if __name__ == '__main__':

    # Substitua os placeholders antes de executar
    if 'YOUR_LAMBDA_EXECUTION_ROLE_ARN' in LAMBDA_EXECUTION_ROLE_ARN or \
       'YOUR_VPC_ID' in VPC_ID or \
       'YOUR_PRIVATE_SUBNET_A_ID' in SUBNET_IDS[0] or \
       'YOUR_LAMBDA_SG_ID' in SECURITY_GROUP_IDS[0]:
        print("ERRO: Por favor, substitua os valores placeholder no script antes de executar.")
    else:
        session = boto3.Session(region_name=AWS_REGION)
        lambda_client = session.client('lambda')
        create_lambda_functions(lambda_client)
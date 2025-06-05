import boto3
import json # Adicionado para o exemplo de add_permission

# Initialize the Cognito Identity Provider client
client = boto3.client('cognito-idp', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1') # Cliente Lambda para adicionar permissão

user_pool_name = 'neobell_user_pool'
app_client_name = 'neobell_mobile_app_client'

# --- ★ SUBSTITUA ESTE VALOR PELO ARN REAL DA SUA LAMBDA ★ ---
# Exemplo: arn:aws:lambda:us-east-1:SEU_ACCOUNT_ID:function:NeoBellPostConfirmationHandler
POST_CONFIRMATION_LAMBDA_ARN = 'ARN_DA_SUA_LAMBDA_NEOBELLPOSTCONFIRMATIONHANDLER' 
# Se você ainda não tem o ARN, execute o script de criação de Lambdas primeiro.

# Obtenha seu AWS Account ID (necessário para a permissão do Lambda)
# Você pode obter isso de várias maneiras, por exemplo, usando STS, ou se souber, coloque diretamente.
# Para este exemplo, usarei um placeholder.
ACCOUNT_ID = 'SEU_ACCOUNT_ID' # ★ SUBSTITUA PELO SEU ACCOUNT ID ★

try:
    # 1. Create User Pool
    print(f"Creating User Pool: {user_pool_name}...")
    
    user_pool_params = {
        'PoolName': user_pool_name,
        'Policies': { # ... (suas políticas de senha) ...
            'PasswordPolicy': {
                'MinimumLength': 8,
                'RequireUppercase': True,
                'RequireLowercase': True,
                'RequireNumbers': True,
                'RequireSymbols': True,
                'TemporaryPasswordValidityDays': 7
            }
        },
        'MfaConfiguration': 'OFF',
        'UsernameAttributes': ['email'],
        'AutoVerifiedAttributes': ['email'],
        'AccountRecoverySetting': {
            'RecoveryMechanisms': [
                {'Priority': 1, 'Name': 'verified_email'},
            ]
        },
        'EmailConfiguration': {
            'EmailSendingAccount': 'COGNITO_DEFAULT'
        },
        'AdminCreateUserConfig': {
            'AllowAdminCreateUserOnly': False
        },
        'Schema': [ # ... (seu schema) ...
            {
                'Name': 'email',
                'AttributeDataType': 'String',
                'DeveloperOnlyAttribute': False,
                'Mutable': True, 
                'Required': True,
                'StringAttributeConstraints': { 'MinLength': '0', 'MaxLength': '2048' }
            },
            {
                'Name': 'name',
                'AttributeDataType': 'String',
                'DeveloperOnlyAttribute': False,
                'Mutable': True,
                'Required': True, 
                'StringAttributeConstraints': { 'MinLength': '0', 'MaxLength': '2048' }
            }
        ],
        'UserPoolTags': {
            'Project': 'NeoBell',
            'Name': user_pool_name
        }
    }

    # --- ★ MODIFICAÇÃO PARA ADICIONAR O GATILHO LAMBDA ★ ---
    if POST_CONFIRMATION_LAMBDA_ARN and \
       POST_CONFIRMATION_LAMBDA_ARN != 'ARN_DA_SUA_LAMBDA_NEOBELLPOSTCONFIRMATIONHANDLER' and \
       POST_CONFIRMATION_LAMBDA_ARN.startswith('arn:aws:lambda:'):
        
        user_pool_params['LambdaConfig'] = {
            'PostConfirmation': POST_CONFIRMATION_LAMBDA_ARN
            # Você pode adicionar outros gatilhos aqui, se necessário:
            # 'PreSignUp': 'ARN_DA_LAMBDA_PRE_SIGN_UP',
        }
        print(f"Configurando gatilho Lambda 'PostConfirmation' para: {POST_CONFIRMATION_LAMBDA_ARN}")
    else:
        print("AVISO: ARN da Lambda de Pós-Confirmação inválido ou não fornecido ('YOUR_POST_CONFIRMATION_LAMBDA_ARN'). O gatilho não será configurado.")
        print("       Certifique-se de substituir o placeholder pelo ARN real da sua função Lambda.")
    # --- ★ FIM DA MODIFICAÇÃO ★ ---

    response_user_pool = client.create_user_pool(**user_pool_params)
    user_pool_id = response_user_pool['UserPool']['Id']
    user_pool_arn = response_user_pool['UserPool']['Arn'] # Obter o ARN do User Pool
    print(f"User Pool criado com sucesso! ID: {user_pool_id}, ARN: {user_pool_arn}")

    # --- ★ ADICIONAR PERMISSÃO PARA O COGNITO INVOCAR A LAMBDA DO GATILHO ★ ---
    if POST_CONFIRMATION_LAMBDA_ARN and \
       POST_CONFIRMATION_LAMBDA_ARN != 'ARN_DA_SUA_LAMBDA_NEOBELLPOSTCONFIRMATIONHANDLER' and \
       POST_CONFIRMATION_LAMBDA_ARN.startswith('arn:aws:lambda:') and \
       ACCOUNT_ID and ACCOUNT_ID != 'SEU_ACCOUNT_ID':
        try:
            statement_id = f'CognitoPostConfirmationTriggerPermission-{user_pool_name}'
            # Remover permissão existente para evitar erro se o script for executado múltiplas vezes
            # com o mesmo statement_id (embora o ideal seja que este script só crie uma vez)
            try:
                lambda_client.remove_permission(
                    FunctionName=POST_CONFIRMATION_LAMBDA_ARN,
                    StatementId=statement_id
                )
                print(f"Permissão existente '{statement_id}' removida da Lambda.")
            except lambda_client.exceptions.ResourceNotFoundException:
                pass # Permissão não existia, o que é normal

            lambda_client.add_permission(
                FunctionName=POST_CONFIRMATION_LAMBDA_ARN,
                StatementId=statement_id,
                Action='lambda:InvokeFunction',
                Principal='cognito-idp.amazonaws.com',
                SourceArn=user_pool_arn # Usar o ARN do User Pool como SourceArn
            )
            print(f"Permissão adicionada para Cognito ({user_pool_arn}) invocar a Lambda {POST_CONFIRMATION_LAMBDA_ARN}.")
        except Exception as e_perm:
            print(f"ERRO ao adicionar permissão à Lambda para o gatilho Cognito: {e_perm}")
            print("      Você pode precisar adicionar esta permissão manualmente ou verificar o ARN da Lambda e o Account ID.")
    elif not (ACCOUNT_ID and ACCOUNT_ID != 'SEU_ACCOUNT_ID'):
        print("AVISO: ACCOUNT_ID não configurado. Não foi possível adicionar permissão à Lambda para o gatilho Cognito.")

    # --- FIM DA ADIÇÃO DE PERMISSÃO ---


    # 2. Create User Pool Client (App Client)
    # ... (seu código para criar o App Client continua aqui, sem alterações necessárias para o gatilho) ...
    print(f"Creating App Client: {app_client_name} for User Pool ID: {user_pool_id}...")
    response_app_client = client.create_user_pool_client(
        UserPoolId=user_pool_id,
        ClientName=app_client_name,
        GenerateSecret=False,
        ExplicitAuthFlows=[
            'ALLOW_USER_SRP_AUTH',
            'ALLOW_REFRESH_TOKEN_AUTH',
            'ALLOW_USER_PASSWORD_AUTH' # ★ Adicionado para permitir o fluxo que você estava testando ★
        ],
        SupportedIdentityProviders=[], 
        CallbackURLs=['neobellapp://callback'],
        LogoutURLs=['neobellapp://signout'],
        AllowedOAuthFlowsUserPoolClient=True,
        AllowedOAuthFlows=['implicit', 'code'], # 'code' é geralmente preferido sobre 'implicit'
        AllowedOAuthScopes=['openid', 'email', 'profile'],
        ReadAttributes=['email', 'email_verified', 'name'],
        WriteAttributes=[],
        AccessTokenValidity=60, 
        IdTokenValidity=60,
        RefreshTokenValidity=30,
        TokenValidityUnits={
            'AccessToken': 'minutes',
            'IdToken': 'minutes',
            'RefreshToken': 'days'
        },
        EnableTokenRevocation=True
    )
    app_client_id = response_app_client['UserPoolClient']['ClientId']
    print(f"App Client created successfully! ID: {app_client_id}")
    # ... (resto do seu print) ...

except Exception as e:
    print(f"An error occurred: {e}")
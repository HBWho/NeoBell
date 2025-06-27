import json
import boto3
import os
import datetime

DYNAMODB_CLIENT = boto3.resource('dynamodb')
# Nome da sua tabela NeoBellUsers, idealmente de uma variável de ambiente
USERS_TABLE_NAME = os.environ.get('NEOBELL_USERS_TABLE_NAME', 'NeoBellUsers')
users_table = DYNAMODB_CLIENT.Table(USERS_TABLE_NAME)

def lambda_handler(event, context):
    print(f"Received Cognito PostConfirmation event: {json.dumps(event)}")

    user_attributes = event['request']['userAttributes']
    user_id_cognito_sub = user_attributes.get('sub')
    user_email = user_attributes.get('email')
    user_name = user_attributes.get('name', event.get('userName')) # Pega 'name' ou usa userName como fallback

    if not user_id_cognito_sub:
        print("Erro: 'sub' (user_id) não encontrado no evento do Cognito.")
        # Você pode optar por retornar o evento sem erro para Cognito ou lançar um erro.
        # Retornar o evento sem erro permite que o fluxo do Cognito continue.
        return event

    current_timestamp = datetime.datetime.utcnow().isoformat() + "Z"

    new_user_item = {
        'user_id': user_id_cognito_sub, # Usando o 'sub' do Cognito como PK
        'email': user_email,
        'name': user_name,
        'profile_created_app_at': current_timestamp,
        'profile_last_updated_app': current_timestamp
        # Adicione outros campos padrão aqui, se necessário
        # 'device_tokens': {} # Exemplo de campo inicializado
    }

    try:
        users_table.put_item(Item=new_user_item)
        print(f"Usuário {user_id_cognito_sub} adicionado com sucesso à tabela {USERS_TABLE_NAME}.")
    except Exception as e:
        print(f"Erro ao adicionar usuário {user_id_cognito_sub} à tabela {USERS_TABLE_NAME}: {e}")
        # Decida como lidar com o erro. Lançar uma exceção aqui pode
        # impedir o fluxo de login do Cognito se o Cognito não receber uma resposta válida.
        # Geralmente, para 'PostConfirmation', é melhor logar o erro e retornar o evento.
        # O Cognito não espera uma resposta modificada deste gatilho específico.

    # O Cognito espera que você retorne o objeto de evento original (ou modificado, para outros gatilhos)
    return event
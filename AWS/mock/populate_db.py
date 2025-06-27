
import boto3
from botocore.exceptions import ClientError
import json
import datetime
from decimal import Decimal # Usaremos Decimal para números, se necessário, embora Boto3 geralmente lide bem com int/float.

# --- Configuração ---
AWS_REGION = 'us-east-1' # Ajuste se sua região for diferente

# Nomes das suas tabelas DynamoDB
TABLE_NAMES = {
    "users": "NeoBellUsers",
    "nfc_tags": "UserNFCTags",
    "devices": "NeoBellDevices",
    "device_user_links": "DeviceUserLinks",
    "video_messages": "VideoMessages",
    "deliveries": "ExpectedDeliveries",
    "permissions": "Permissions",
    "event_logs": "EventLogs"
}

# --- Dados Mock ---
# Use os IDs de forma consistente se quiser testar relações
# (user_cognito_sub_1, sbc_device_id_1, etc.)

USER_COGNITO_SUB_1 = "24f8e4c8-b061-70c9-3eb2-91244c7a2b3f"
USER_COGNITO_SUB_2 = "user_cognito_sub_2_example" # Exemplo de ID de usuário Cognito

SBC_DEVICE_ID_1 = "sbc_device_id_1_example" # Exemplo de ID de dispositivo SBC
SBC_DEVICE_ID_2 = "sbc_device_id_2_example" # Exemplo de segundo ID de dispositivo SBC

MOCK_DATA = {
    "NeoBellUsers": [
        {
            "user_id": USER_COGNITO_SUB_1,
            "email": "usuario1@example.com",
            "name": "Alice Wonderland",
            "profile_created_app_at": "2025-05-20T10:00:00Z",
            "profile_last_updated_app": "2025-05-25T14:30:00Z",
            "device_token": "token_android_alice_123"
            
        },
        {
            "user_id": USER_COGNITO_SUB_2,
            "email": "bobbuilder@example.com",
            "name": "Bob Construtor",
            "profile_created_app_at": "2025-05-21T11:00:00Z",
            "profile_last_updated_app": "2025-05-26T09:15:00Z",
            "device_token": "token_android_bob_789"
        }
    ],
    "UserNFCTags": [
        {
            "user_id": USER_COGNITO_SUB_1,
            "nfc_id_scanned": "NFC_ID_ALICE_CHAVEIRO_001",
            "tag_friendly_name": "Chaveiro da Alice",
            "registered_at": "2025-05-22T12:00:00Z",
            "last_updated_at": "2025-05-22T12:00:00Z"
        },
        {
            "user_id": USER_COGNITO_SUB_1,
            "nfc_id_scanned": "NFC_ID_ALICE_CARTEIRA_002",
            "tag_friendly_name": "Cartão NFC na Carteira",
            "registered_at": "2025-05-23T15:30:00Z",
            "last_updated_at": "2025-05-23T15:30:00Z"
        }
    ],
    "NeoBellDevices": [
        {
            "sbc_id": SBC_DEVICE_ID_1,
            "owner_user_id": USER_COGNITO_SUB_1,
            "device_friendly_name": "Porta da Frente Casa",
            "status": "online",
            "firmware_version": "1.3.2",
            "registered_at": "2025-05-20T10:05:00Z",
            "last_seen": "2025-05-26T16:00:00Z",
            "last_updated_app_at": "2025-05-20T10:05:00Z",
            "network_info": {
                "ip_address": "192.168.1.100",
                "wifi_ssid": "MinhaRedeWifi",
                "signal_strength": -55 # Número
            }
        },
        {
            "sbc_id": SBC_DEVICE_ID_2,
            "owner_user_id": USER_COGNITO_SUB_2,
            "device_friendly_name": "Portão Garagem",
            "status": "offline",
            "firmware_version": "1.2.0",
            "registered_at": "2025-05-21T11:10:00Z",
            "last_seen": "2025-05-25T08:00:00Z",
            "last_updated_app_at": "2025-05-21T11:10:00Z",
            "network_info": {
                "ip_address": "192.168.1.101",
                "wifi_ssid": "MinhaRedeWifi",
                "signal_strength": -65 # Número
            }
        }
    ],
    "DeviceUserLinks": [
        {
            "sbc_id": SBC_DEVICE_ID_1,
            "user_id": USER_COGNITO_SUB_1,
            "role": "Owner",
            "access_granted_at": "2025-05-20T10:05:00Z"
        },
        {
            "sbc_id": SBC_DEVICE_ID_1,
            "user_id": USER_COGNITO_SUB_2,
            "role": "Resident",
            "access_granted_at": "2025-05-24T09:00:00Z",
            "granted_by": USER_COGNITO_SUB_1
        },
        {
            "sbc_id": SBC_DEVICE_ID_2,
            "user_id": USER_COGNITO_SUB_2,
            "role": "Owner",
            "access_granted_at": "2025-05-21T11:10:00Z"
        }
    ],
    "VideoMessages": [ # ATUALIZADO AQUI
        {
            "user_id": USER_COGNITO_SUB_1, # PK da tabela (ex: proprietário do dispositivo)
            "message_id": "message_uuid_001", # SK da tabela
            "sbc_id": SBC_DEVICE_ID_1,
            "recorded_at": "2025-05-26T10:15:30Z",
            "duration_sec": 25,
            "s3_bucket_name": "SEU_BUCKET_S3_DE_VIDEOS_AQUI", # ★★★ SUBSTITUA ESTE VALOR ★★★
            "s3_object_key": "videos/sbc_device_id_1/2025/05/26/message_uuid_001.mp4",
            "is_viewed": False,
            "visitor_face_tag_id": "face_uuid_visitante_002" # ID da face (ex: Entregador Regular da tabela Permissions)
        },
        {
            "user_id": USER_COGNITO_SUB_1,
            "message_id": "message_uuid_002",
            "sbc_id": SBC_DEVICE_ID_1,
            "recorded_at": "2025-05-26T14:45:00Z",
            "duration_sec": 15,
            "s3_bucket_name": "SEU_BUCKET_S3_DE_VIDEOS_AQUI", # ★★★ SUBSTITUA ESTE VALOR ★★★
            "s3_object_key": "videos/sbc_device_id_1/2025/05/26/message_uuid_002.mp4",
            "is_viewed": True
            # Sem visitor_face_tag_id se não houve reconhecimento
        }
    ],
    "ExpectedDeliveries": [
        {
            "user_id": USER_COGNITO_SUB_1,
            "order_id": "entrega_alice_uuid_001",
            "item_description": "Componentes Eletrônicos",
            "tracking_number": "123XYZ789",
            "carrier": "LogiFast",
            "status": "pending",
            "added_at": "2025-05-25T10:00:00Z",
            "expected_date": "2025-05-28",
            "last_updated_app_at": "2025-05-25T10:00:00Z"
        },
        {
            "user_id": USER_COGNITO_SUB_2,
            "order_id": "entrega_bob_uuid_002",
            "item_description": "Livro de Receitas",
            "status": "retrieved_by_user",
            "added_at": "2025-05-20T14:00:00Z",
            "expected_date": "2025-05-22",
            "sbc_id_received_at": SBC_DEVICE_ID_2,
            "received_at_timestamp": "2025-05-22T11:30:00Z",
            "last_updated_app_at": "2025-05-23T09:00:00Z"
        }
    ],
    "Permissions": [
        {
            "user_id": USER_COGNITO_SUB_1,
            "face_tag_id": "face_uuid_visitante_001",
            "visitor_name": "Carlos Vizinho",
            "permission_level": "allow_speak",
            "created_at": "2025-05-24T18:00:00Z",
            "last_updated_at": "2025-05-24T18:00:00Z"
        },
        {
            "user_id": USER_COGNITO_SUB_1, # Alice
            "face_tag_id": "face_uuid_visitante_002", # ID usado no mock de VideoMessages
            "visitor_name": "Entregador Regular",
            "permission_level": "notify_only",
            "created_at": "2025-05-25T11:00:00Z",
            "last_updated_at": "2025-05-25T11:00:00Z"
        }
    ],
    "EventLogs": [
        {
            "log_source_id": SBC_DEVICE_ID_1,
            "timestamp_uuid": "2025-05-26T10:15:30.500Z_evt_uuid_001",
            "event_type": "doorbell_pressed",
            "timestamp": "2025-05-26T10:15:30Z",
            "summary": "Campainha tocada na Porta da Frente Casa.",
            "sbc_id_related": SBC_DEVICE_ID_1,
            "user_id_related": USER_COGNITO_SUB_1,
            "details": { "message_id_if_any": "message_uuid_001" }
        },
        {
            "log_source_id": USER_COGNITO_SUB_1,
            "timestamp_uuid": "2025-05-25T14:30:00.123Z_evt_uuid_002",
            "event_type": "user_profile_updated",
            "timestamp": "2025-05-25T14:30:00Z",
            "summary": "Usuário Alice Wonderland atualizou seu nome.",
            "user_id_related": USER_COGNITO_SUB_1,
            "details": { "updated_fields": ["name"] }
        },
        {
            "log_source_id": SBC_DEVICE_ID_2,
            "timestamp_uuid": "2025-05-22T11:30:00.000Z_evt_uuid_003",
            "event_type": "delivery_detected",
            "timestamp": "2025-05-22T11:30:00Z",
            "summary": "Pacote detectado no Portão Garagem para entrega_bob_uuid_002.",
            "sbc_id_related": SBC_DEVICE_ID_2,
            "user_id_related": USER_COGNITO_SUB_2,
            "details": { "order_id": "entrega_bob_uuid_002", "compartment_id": "box1" }
        }
    ]
}

# --- Função Principal ---
def populate_tables():
    """Popula as tabelas DynamoDB com dados mock."""
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

    for table_key, table_name in TABLE_NAMES.items():
        if table_name not in MOCK_DATA or not MOCK_DATA[table_name]:
            print(f"Sem dados mock para a tabela '{table_name}' ou lista de dados vazia. Pulando.")
            continue

        table = dynamodb.Table(table_name)
        print(f"\nPopulando tabela: {table_name}...")
        
        items_to_put = MOCK_DATA[table_name]
        
        for i, item in enumerate(items_to_put):
            try:
                # Boto3 lida com a conversão de tipos Python padrão para tipos DynamoDB.
                # Para números, se você tiver Decimals no seu objeto item, ele os manterá.
                # Se você tiver floats, certifique-se de que a precisão é aceitável ou converta para Decimal.
                # Nosso MOCK_DATA usa int/float/str/bool/dict/list, que são bem tratados.
                
                # Exemplo de como converter floats para Decimal se necessário (não estritamente para este mock):
                # item_decimal = json.loads(json.dumps(item), parse_float=Decimal)
                # table.put_item(Item=item_decimal)
                
                table.put_item(Item=item)
                print(f"  Item {i+1} inserido com sucesso em {table_name}.")
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code")
                error_message = e.response.get("Error", {}).get("Message")
                print(f"  Erro ao inserir item {i+1} em {table_name}: {error_code} - {error_message}")
                print(f"    Item problemático: {json.dumps(item)}")
            except Exception as ex:
                print(f"  Erro inesperado ao inserir item {i+1} em {table_name}: {ex}")
                print(f"    Item problemático: {json.dumps(item)}")

    print("\nProcesso de população de tabelas concluído.")

if __name__ == '__main__':
    # Verificar se os nomes das tabelas no MOCK_DATA correspondem aos em TABLE_NAMES
    for table_name_in_mock in MOCK_DATA.keys():
        if table_name_in_mock not in TABLE_NAMES.values():
            print(f"AVISO: A tabela '{table_name_in_mock}' definida em MOCK_DATA não está listada em TABLE_NAMES com o mesmo nome.")
            print("Certifique-se de que os nomes das chaves em MOCK_DATA correspondem aos valores em TABLE_NAMES.")
            # Exemplo: se TABLE_NAMES["users"] = "NeoBellUsers", então MOCK_DATA deve ter uma chave "NeoBellUsers"
    
    populate_tables()
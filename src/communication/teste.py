import time
import json
import uuid
import os
import threading
import requests # Para upload S3
import logging
from datetime import datetime, timezone

from awscrt.mqtt import Connection, Client, QoS
from awsiot import mqtt_connection_builder

from dotenv import load_dotenv

load_dotenv()

# --- Configurações do Dispositivo SBC ---
SBC_ID = os.getenv("CLIENT_ID")
PORT = os.getenv("PORT")
AWS_IOT_ENDPOINT = os.getenv("AWS_IOT_ENDPOINT")
PATH_TO_ROOT_CA = "certifications/AmazonRootCA1.pem"
PATH_TO_PRIVATE_KEY = "certifications/10da83970c7ac9793d1f4c33c48f082924dc1aaccd0e8e8fd229d13b5caa210e-private.pem.key"
PATH_TO_CERTIFICATE = "certifications/10da83970c7ac9793d1f4c33c48f082924dc1aaccd0e8e8fd229d13b5caa210e-certificate.pem.crt"

# --- Fim das Configurações ---
# Configuração de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Tópicos MQTT ---
# (As chaves correspondem às ações na Lambda, os valores são os tópicos de requisição)
TOPIC_MAP = {
    # Handlers de Upload
    'visitor_registration_request': f"neobell/sbc/{SBC_ID}/registrations/request-upload-url",
    'video_message_request': f"neobell/sbc/{SBC_ID}/messages/request-upload-url",
    
    # Handlers do SBC Helper
    'permissions_request': f"neobell/sbc/{SBC_ID}/permissions/request",
    'package_request': f"neobell/sbc/{SBC_ID}/packages/request",
    'package_status_update': f"neobell/sbc/{SBC_ID}/packages/status-update/request",
    'log_submission': f"neobell/sbc/{SBC_ID}/logs/submit",
    'nfc_verify_request': f"neobell/sbc/{SBC_ID}/nfc/verify-tag/request",
}

# Tópicos de resposta para inscrição
RESPONSE_TOPICS = [
    f"neobell/sbc/{SBC_ID}/registrations/upload-url-response",
    f"neobell/sbc/{SBC_ID}/messages/upload-url-response",
    f"neobell/sbc/{SBC_ID}/permissions/response",
    f"neobell/sbc/{SBC_ID}/packages/response",
    f"neobell/sbc/{SBC_ID}/packages/status-update/response",
    f"neobell/sbc/{SBC_ID}/nfc/verify-tag/response"
]

# Globais para MQTT Connection e Sincronização de Respostas
mqtt_connection = None
response_received_events = {topic: threading.Event() for topic in RESPONSE_TOPICS}
received_payloads = {}

# --- Funções Auxiliares e Callbacks MQTT ---

def on_connection_interrupted(connection, error, **kwargs):
    logger.warning(f"Conexão interrompida. Erro: {error}")

def on_connection_resumed(connection, return_code, session_present, **kwargs):
    logger.info(f"Conexão retomada. Código: {return_code}, Sessão Presente: {session_present}")
    if return_code == Connection.RESUME_RECONNECT_SUCCESS and not session_present:
        logger.info("Sessão não estava presente. Reinscrevendo-se em todos os tópicos de resposta...")
        for topic in RESPONSE_TOPICS:
            subscribe_to_topic(topic)

def on_generic_message_received(topic, payload, dup, qos, retain, **kwargs):
    logger.info(f"Mensagem recebida no tópico '{topic}'")
    decoded_payload = payload.decode('utf-8')
    logger.debug(f"Payload Bruto: {decoded_payload}")
    try:
        json_payload = json.loads(decoded_payload)
        received_payloads[topic] = json_payload
        logger.info(f"Payload JSON Decodificado para '{topic}': {json_payload}")
    except json.JSONDecodeError:
        logger.error(f"Erro ao decodificar JSON do tópico {topic}. Payload: {decoded_payload}")
        received_payloads[topic] = {"error": "JSONDecodeError", "raw_payload": decoded_payload}
    
    if topic in response_received_events:
        response_received_events[topic].set()

def connect_mqtt():
    global mqtt_connection
    if mqtt_connection: return True

    logger.info(f"Tentando conectar ao AWS IoT Endpoint: {AWS_IOT_ENDPOINT} com ClientID: {SBC_ID}")
    try:
        mqtt_connection = mqtt_connection_builder.mtls_from_path(
            endpoint=AWS_IOT_ENDPOINT,
            cert_filepath=PATH_TO_CERTIFICATE,
            pri_key_filepath=PATH_TO_PRIVATE_KEY,
            ca_filepath=PATH_TO_ROOT_CA,
            on_connection_interrupted=on_connection_interrupted,
            on_connection_resumed=on_connection_resumed,
            client_id=SBC_ID,
            clean_session=True,
            keep_alive_secs=30
        )
        connect_future = mqtt_connection.connect()
        connect_future.result(timeout=10.0)
        logger.info("Conectado ao AWS IoT Core!")
        return True
    except Exception as e:
        logger.error(f"Falha ao conectar ao AWS IoT Core: {e}")
        mqtt_connection = None
        return False

def disconnect_mqtt():
    global mqtt_connection
    if mqtt_connection:
        logger.info("Desconectando do AWS IoT Core...")
        disconnect_future = mqtt_connection.disconnect()
        disconnect_future.result(timeout=5.0)
        logger.info("Desconectado.")
        mqtt_connection = None

def subscribe_to_topic(topic, qos=QoS.AT_LEAST_ONCE):
    if not mqtt_connection:
        logger.error("Não conectado. Impossível se inscrever.")
        return False
        
    if topic in response_received_events:
        response_received_events[topic].clear()
    received_payloads.pop(topic, None)

    try:
        logger.info(f"Inscrevendo-se no tópico: {topic}")
        subscribe_future, _ = mqtt_connection.subscribe(
            topic=topic, qos=qos, callback=on_generic_message_received
        )
        subscribe_result = subscribe_future.result(timeout=5.0)
        logger.info(f"Inscrito em '{topic}' com QoS {subscribe_result['qos']}")
        return True
    except Exception as e:
        logger.error(f"Falha ao se inscrever em '{topic}': {e}")
        return False

def publish_and_wait(request_topic_key, payload_dict, response_topic, timeout=15.0):
    if not mqtt_connection:
        logger.error("Não conectado. Impossível executar teste.")
        return None
    
    request_topic = TOPIC_MAP.get(request_topic_key)
    if not request_topic:
        logger.error(f"Chave de tópico inválida: {request_topic_key}")
        return None

    if not subscribe_to_topic(response_topic):
        return None

    logger.info(f"Publicando em '{request_topic}'")
    try:
        publish_future, _ = mqtt_connection.publish(
            topic=request_topic, payload=json.dumps(payload_dict), qos=QoS.AT_LEAST_ONCE
        )
        publish_future.result(timeout=5.0)
        logger.info(f"Mensagem publicada com sucesso em '{request_topic}'.")
    except Exception as e:
        logger.error(f"Falha ao publicar em '{request_topic}': {e}")
        return None

    logger.info(f"Aguardando resposta em '{response_topic}' por até {timeout}s...")
    if response_received_events[response_topic].wait(timeout=timeout):
        logger.info(f"Resposta recebida para '{request_topic_key}'.")
        return received_payloads.get(response_topic)
    else:
        logger.warning(f"Timeout: Nenhuma resposta recebida para '{request_topic_key}' em {timeout}s.")
        return None

def upload_to_s3(presigned_url, file_path, metadata_headers, content_type='application/octet-stream'):
    try:
        logger.info(f"Fazendo upload do arquivo '{file_path}' para S3 via URL pré-assinada.")
        if not os.path.exists(file_path):
            logger.error(f"Arquivo não encontrado: {file_path}")
            return False
            
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        headers_for_s3 = {'Content-Type': content_type}
        if metadata_headers:
            headers_for_s3.update(metadata_headers)

        response = requests.put(presigned_url, data=file_data, headers=headers_for_s3)
        response.raise_for_status()
        logger.info(f"Upload para S3 bem-sucedido! Status: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro no upload para S3: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Resposta do S3 (Erro): {e.response.status_code} - {e.response.text}")
        return False

def create_dummy_file(filename, size_kb=10):
    if not os.path.exists(filename):
        with open(filename, "wb") as f:
            f.write(os.urandom(size_kb * 1024))
        logger.info(f"Arquivo dummy '{filename}' ({size_kb}KB) criado.")
    return filename

# --- Funções de Teste Específicas ---

def testar_cadastro_novo_visitante(visitor_name, permission):
    logger.info(f"\n--- INICIANDO TESTE: Cadastrar Novo Visitante ({visitor_name}, Permissão: {permission}) ---")
    image_file = create_dummy_file("data/dog.jpg", size_kb=50)
    face_tag_id = str(uuid.uuid4())

    payload = {
        "face_tag_id": face_tag_id,
        "visitor_name": visitor_name,
        "permission_level": permission
    }
    
    response = publish_and_wait(
        'visitor_registration_request',
        payload,
        f"neobell/sbc/{SBC_ID}/registrations/upload-url-response"
    )
    
    if response and "presigned_url" in response:
        logger.info(f"URL para cadastro de '{visitor_name}' recebida com sucesso.")
        upload_to_s3(
            response["presigned_url"],
            image_file,
            response.get("required_metadata_headers"),
            content_type='image/jpeg'
        )
        return face_tag_id
    else:
        logger.error(f"Falha ao obter URL para cadastro de '{visitor_name}'. Resposta: {response}")
        return None
    logger.info("--- FIM TESTE: Cadastrar Novo Visitante ---\n")

def testar_envio_mensagem_video(face_id_visitante):
    logger.info(f"\n--- INICIANDO TESTE: Envio de Mensagem de Vídeo (Visitante: {face_id_visitante}) ---")
    video_file = "data/dog_video.mp4"
    
    payload = {
        "visitor_face_tag_id": face_id_visitante,
        "duration_sec": "30"
    }
    
    response = publish_and_wait(
        'video_message_request',
        payload,
        f"neobell/sbc/{SBC_ID}/messages/upload-url-response"
    )
    
    if response and "presigned_url" in response:
        logger.info(f"URL para envio de vídeo do visitante '{face_id_visitante}' recebida.")
        upload_to_s3(
            response["presigned_url"],
            video_file,
            response.get("required_metadata_headers"),
            content_type='video/mp4'
        )
    else:
        logger.error(f"Falha ao obter URL para envio de vídeo. O visitante tem permissão 'Allowed'? Resposta: {response}")
    logger.info("--- FIM TESTE: Envio de Mensagem de Vídeo ---\n")

def testar_verificacao_permissao(face_id_teste="c9b8a712-9b2f-4c3d-9d5e-1f8a7b6c5d4e"):
    logger.info("\n--- INICIANDO TESTE: Verificação de Permissão Existente ---")
    payload = {"face_tag_id": face_id_teste}
    response = publish_and_wait(
        'permissions_request', 
        payload, 
        f"neobell/sbc/{SBC_ID}/permissions/response"
    )
    if response:
        logger.info(f"Resultado do Teste de Verificação de Permissão: {response}")
    logger.info("--- FIM TESTE: Verificação de Permissão Existente ---\n")

def testar_requisicao_pacote(id_type, id_value):
    logger.info(f"\n--- INICIANDO TESTE: Requisição de Pacote (tipo: {id_type}) ---")
    payload = {"identifier_type": id_type, "identifier_value": id_value}
    response = publish_and_wait(
        'package_request', 
        payload, 
        f"neobell/sbc/{SBC_ID}/packages/response"
    )
    if response:
        logger.info(f"Resultado do Teste de Pacote ({id_type}={id_value}): {response}")
    logger.info("--- FIM TESTE: Requisição de Pacote ---\n")

def testar_atualizacao_status_pacote(order_id, new_status):
    logger.info(f"\n--- INICIANDO TESTE: Atualização de Status de Pacote ---")
    payload = {"order_id": order_id, "new_status": new_status}
    response = publish_and_wait(
        'package_status_update',
        payload,
        f"neobell/sbc/{SBC_ID}/packages/status-update/response"
    )
    if response:
        logger.info(f"Resultado da Atualização de Status (order_id={order_id}, status={new_status}): {response}")
    logger.info("--- FIM TESTE: Atualização de Status de Pacote ---\n")

def testar_verificacao_nfc(nfc_id="04:AB:CD:12:34:56:78"):
    logger.info("\n--- INICIANDO TESTE: Verificação de Tag NFC ---")
    payload = {"nfc_id_scanned": nfc_id}
    response = publish_and_wait(
        'nfc_verify_request',
        payload,
        f"neobell/sbc/{SBC_ID}/nfc/verify-tag/response"
    )
    if response:
        logger.info(f"Resultado da Verificação NFC (tag={nfc_id}): {response}")
    logger.info("--- FIM TESTE: Verificação de Tag NFC ---\n")
    
def testar_envio_log():
    logger.info("\n--- INICIANDO TESTE: Envio de Log ---")
    log_payload = {
        "log_timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "USER_INTERACTION", # SUBTITULO(tipo:acao da mensagem) DA MENSAGEM H2
        "summary": "Touchscreen pressed by user.", # TITULO DA MENSAGEM H1
        "event_details": {"component": "screen", "action": "touch"} # Detalhes bem adicionais. Nao eh fixo
    }
    
    request_topic = TOPIC_MAP['log_submission']
    logger.info(f"Publicando em '{request_topic}' (sem esperar resposta)")
    try:
        publish_future, _ = mqtt_connection.publish(
            topic=request_topic, payload=json.dumps(log_payload), qos=QoS.AT_LEAST_ONCE
        )
        publish_future.result(timeout=5.0)
        logger.info("Payload de log enviado com sucesso.")
    except Exception as e:
        logger.error(f"Falha ao enviar payload de log: {e}")
    logger.info("--- FIM TESTE: Envio de Log ---\n")


if __name__ == '__main__':
    if "YOUR_AWS_IOT_ENDPOINT" in AWS_IOT_ENDPOINT:
        logger.error("ERRO: AWS_IOT_ENDPOINT não foi configurado. Edite o script.")
        exit(1)
    if not all(os.path.exists(p) for p in [PATH_TO_ROOT_CA, PATH_TO_PRIVATE_KEY, PATH_TO_CERTIFICATE]):
        logger.error("ERRO: Arquivos de certificado não encontrados. Verifique os caminhos.")
        exit(1)

    if not connect_mqtt():
        exit(1)

    for topic in RESPONSE_TOPICS:
        subscribe_to_topic(topic)
    
    time.sleep(1) 

    try:
        # --- COMENTE/DESCOMENTE AS LINHAS ABAIXO PARA ATIVAR/DESATIVAR TESTES ---

        visitor_face_tag = "634eaa37-5728-451a-8df4-7008bb14a3a9"  # Variável para armazenar o face_tag_id do visitante cadastrado
        
        # PRA VERIFICAR SE TEM CADASTRO BASTA CHAMAR A FUNCAO 3

        # Teste 1: Cadastrar um novo visitante 
        # VISITANTE -> REC. FACIAL -> NAO TEM CADASTRO -> FAZ O CADASTRO + CHAMA FUNCAO ABAIXO
        # visitor_face_tag = testar_cadastro_novo_visitante(visitor_name="Visitante", permission="Allowed")
        # time.sleep(2)

        # Teste 2: Enviar uma mensagem de vídeo (use um face_id que você sabe que tem permissão "Allowed")
        # VISITANTE -> REC. FACIAL -> TEM CADASTRO -> GRAVA VIDEO + CHAMA FUNCAO
        # testar_envio_mensagem_video(face_id_visitante=visitor_face_tag)
        # time.sleep(2)
        
        # Teste 3: Verificar permissão de um visitante existente
        # USAR NO FLOW DE VISITANTE
        # testar_verificacao_permissao(face_id_teste=visitor_face_tag)
        # time.sleep(2)

        # Teste 4: Requisitar info de pacote por ID do pedido
        # testar_requisicao_pacote(id_type="order_id", id_value="1311")
        # time.sleep(2)
        
        # Teste 5: Requisitar info de pacote por número de rastreio
        # CHAMAR QUANDO O CARA MOSTRA O PACOTE NA CAMERA DE FORA
        # ENTREGADOR -> PACOTE + CHAMA FUNCAO
        # testar_requisicao_pacote(id_type="tracking_number", id_value="5463")
        # time.sleep(2)
        
        # Teste 6: Atualizar status de um pacote
        # PACOTE FOI VERIFICADO NO COMP. INTERNO E APÓS ISSO PASSAR COMO ENTREGUE
        # testar_atualizacao_status_pacote(order_id="1311", new_status="delivered")
        # time.sleep(2)

        # Teste 7: Verificar uma tag NFC
        # BATEU A TAG -> VERIFICA COM A FUNCAO
        # testar_verificacao_nfc(nfc_id="c3:bb:4e:2d")
        # testar_verificacao_nfc(nfc_id="c3:bb:4e:2")
        # time.sleep(2)
        
        # Teste 8: Enviar um log do dispositivo
        # MANDAR A MAIORIA DAS COISAS QUE ACONTECEM
        # POR EX.: Radxa ligou; Inicializou; etc...
        # testar_envio_log()
        # time.sleep(2)

    except KeyboardInterrupt:
        logger.info("Teste interrompido pelo usuário.")
    except Exception as e:
        logger.error(f"Um erro inesperado ocorreu durante os testes: {e}", exc_info=True)
    finally:
        disconnect_mqtt()
        logger.info("Script de teste finalizado.")

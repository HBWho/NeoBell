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

# Tópicos MQTT (baseados no SBC_ID)
# Cadastro de Visitante
TOPIC_REG_REQ_UPLOAD_URL = f"neobell/sbc/{SBC_ID}/registrations/request-upload-url"
TOPIC_REG_UPLOAD_URL_RESP = f"neobell/sbc/{SBC_ID}/registrations/upload-url-response"
# Mensagem de Vídeo
TOPIC_MSG_REQ_UPLOAD_URL = f"neobell/sbc/{SBC_ID}/messages/request-upload-url"
TOPIC_MSG_UPLOAD_URL_RESP = f"neobell/sbc/{SBC_ID}/messages/upload-url-response"
# Permissões
TOPIC_PERM_REQ = f"neobell/sbc/{SBC_ID}/permissions/request"
TOPIC_PERM_RESP = f"neobell/sbc/{SBC_ID}/permissions/response"
# Pacotes
TOPIC_PKG_REQ = f"neobell/sbc/{SBC_ID}/packages/request"
TOPIC_PKG_RESP = f"neobell/sbc/{SBC_ID}/packages/response"
# Logs
TOPIC_LOG_SUBMIT = f"neobell/sbc/{SBC_ID}/logs/submit"

# Globais para MQTT Connection e Sincronização de Respostas
mqtt_connection = None
response_received_events = {
    TOPIC_REG_UPLOAD_URL_RESP: threading.Event(),
    TOPIC_MSG_UPLOAD_URL_RESP: threading.Event(),
    TOPIC_PERM_RESP: threading.Event(),
    TOPIC_PKG_RESP: threading.Event(),
}
received_payloads = {}

# --- Callbacks MQTT ---
def on_connection_interrupted(connection, error, **kwargs):
    logger.warning(f"Conexão interrompida. Erro: {error}")

def on_connection_resumed(connection, return_code, session_present, **kwargs):
    logger.info(f"Conexão retomada. Código: {return_code}, Sessão Presente: {session_present}")
    if return_code == Connection.RESUME_RECONNECT_SUCCESS and not session_present:
        logger.info("Sessão não estava presente. Reinscrevendo-se nos tópicos de resposta...")
        # É importante se reinscrever se a sessão não estava presente
        # No entanto, as inscrições são feitas dinamicamente antes de cada teste que espera uma resposta.

def on_generic_message_received(topic, payload, dup, qos, retain, **kwargs):
    logger.info(f"Mensagem recebida no tópico '{topic}'")
    decoded_payload = payload.decode('utf-8')
    logger.debug(f"Payload Bruto: {decoded_payload}")
    try:
        json_payload = json.loads(decoded_payload)
        received_payloads[topic] = json_payload
        logger.info(f"Payload JSON Decodificado: {json_payload}")
    except json.JSONDecodeError:
        logger.error(f"Erro ao decodificar JSON do tópico {topic}. Payload: {decoded_payload}")
        received_payloads[topic] = {"error": "JSONDecodeError", "raw_payload": decoded_payload}
    
    if topic in response_received_events:
        response_received_events[topic].set()

def connect_mqtt():
    global mqtt_connection
    if mqtt_connection:
        try: # Tenta desconectar se já existe uma conexão para evitar problemas
            disconnect_future = mqtt_connection.disconnect()
            disconnect_future.result(timeout=5.0)
            logger.info("Conexão MQTT anterior desconectada.")
        except Exception as e:
            logger.warning(f"Erro ao desconectar conexão MQTT anterior: {e}")
        mqtt_connection = None


    logger.info(f"Tentando conectar ao AWS IoT Endpoint: {AWS_IOT_ENDPOINT} com ClientID: {SBC_ID}")
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=AWS_IOT_ENDPOINT,
        cert_filepath=PATH_TO_CERTIFICATE,
        pri_key_filepath=PATH_TO_PRIVATE_KEY,
        ca_filepath=PATH_TO_ROOT_CA,
        on_connection_interrupted=on_connection_interrupted,
        on_connection_resumed=on_connection_resumed,
        client_id=SBC_ID,
        clean_session=True, # Usar True para testes para garantir estado limpo
        keep_alive_secs=30
    )
    connect_future = mqtt_connection.connect()
    try:
        connect_future.result(timeout=10.0) # Timeout de 10 segundos para conectar
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
        logger.error("Não conectado ao MQTT. Não é possível se inscrever.")
        return False
    try:
        logger.info(f"Inscrevendo-se no tópico: {topic}")
        subscribe_future, packet_id = mqtt_connection.subscribe(
            topic=topic,
            qos=qos,
            callback=on_generic_message_received
        )
        subscribe_result = subscribe_future.result(timeout=5.0)
        logger.info(f"Inscrito no tópico '{topic}' com QoS {subscribe_result['qos']}")
        # Limpar evento e payload anteriores para este tópico
        if topic in response_received_events:
            response_received_events[topic].clear()
        received_payloads.pop(topic, None)
        return True
    except Exception as e:
        logger.error(f"Falha ao se inscrever no tópico '{topic}': {e}")
        return False

def publish_message(topic, payload_dict, qos=QoS.AT_LEAST_ONCE):
    if not mqtt_connection:
        logger.error("Não conectado ao MQTT. Não é possível publicar.")
        return False
    try:
        logger.info(f"Publicando no tópico: {topic}")
        logger.debug(f"Payload da publicação: {json.dumps(payload_dict)}")
        publish_future, _ = mqtt_connection.publish(
            topic=topic,
            payload=json.dumps(payload_dict),
            qos=qos
        )
        publish_future.result(timeout=5.0) # Espera PUBACK para QoS 1
        logger.info(f"Mensagem publicada com sucesso no tópico '{topic}'.")
        return True
    except Exception as e:
        logger.error(f"Falha ao publicar no tópico '{topic}': {e}")
        return False

def wait_for_response(topic, timeout=30.0):
    if topic in response_received_events:
        logger.info(f"Aguardando resposta no tópico '{topic}' por até {timeout}s...")
        if response_received_events[topic].wait(timeout=timeout):
            logger.info(f"Resposta recebida para o tópico '{topic}'.")
            return received_payloads.get(topic)
        else:
            logger.warning(f"Timeout: Nenhuma resposta recebida para o tópico '{topic}' em {timeout}s.")
            return None
    else:
        logger.error(f"Nenhum evento de espera configurado para o tópico '{topic}'.")
        return None

def upload_to_s3(presigned_url, file_path, metadata_headers, content_type='application/octet-stream'):
    try:
        logger.info(f"Fazendo upload do arquivo '{file_path}' para S3 usando URL pré-assinada.")
        logger.debug(f"URL: {presigned_url}")
        logger.debug(f"Cabeçalhos de Metadados: {metadata_headers}")
        
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        headers_for_s3 = {'Content-Type': content_type}
        if metadata_headers: # Adiciona cabeçalhos x-amz-meta-*
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
    except FileNotFoundError:
        logger.error(f"Arquivo não encontrado para upload: {file_path}")
        return False

def create_dummy_file(filename, size_kb=10):
    if not os.path.exists(filename):
        with open(filename, "wb") as f:
            f.write(os.urandom(size_kb * 1024))
        logger.info(f"Arquivo dummy '{filename}' ({size_kb}KB) criado.")
    return filename

# --- Funções de Teste Específicas ---

def testar_cadastro_visitante(
        visitor_name: str,
        permission_level: str,
        image_file: str):
    """Funcao para cadastrar um usuario"""

    logger.info("\n--- INICIANDO TESTE: Cadastro de Visitante ---")
    if not subscribe_to_topic(TOPIC_REG_UPLOAD_URL_RESP): return

    image_file = create_dummy_file(image_file, size_kb=50)
    face_tag_id = str(uuid.uuid4())

    payload_reg_req = {
        "sbc_id": SBC_ID, 
        "face_tag_id": face_tag_id,
        "visitor_name": visitor_name,
        "permission_level": permission_level
    }
    if not publish_message(TOPIC_REG_REQ_UPLOAD_URL, payload_reg_req): return

    response_data = wait_for_response(TOPIC_REG_UPLOAD_URL_RESP)

    if response_data and "presigned_url" in response_data:
        logger.info("URL pré-assinada para cadastro recebida.")
        upload_to_s3(
            response_data["presigned_url"],
            image_file,
            response_data.get("required_metadata_headers"),
            content_type='image/jpeg'
        )
    else:
        logger.error(f"Falha ao obter URL pré-assinada para cadastro. Resposta: {response_data}")
    logger.info("--- FIM TESTE: Cadastro de Visitante ---\n")

def testar_envio_mensagem_video():
    logger.info("\n--- INICIANDO TESTE: Envio de Mensagem de Vídeo ---")
    if not subscribe_to_topic(TOPIC_MSG_UPLOAD_URL_RESP): return

    video_file = create_dummy_file("message_by_Dog.mp4", size_kb=200)
    duration_sec = 10
    visitor_face_tag_id = "f80490f5-a231-4ced-9e07-29083b872c08" # Tag ja registrada


    payload_msg_req = {
        "sbc_id": SBC_ID,
        "duration_sec": str(duration_sec),
        "visitor_face_tag_id": visitor_face_tag_id 
    }
    if not publish_message(TOPIC_MSG_REQ_UPLOAD_URL, payload_msg_req): return

    response_data = wait_for_response(TOPIC_MSG_UPLOAD_URL_RESP)
    if response_data and "presigned_url" in response_data:
        logger.info("URL pré-assinada para vídeo recebida.")
        upload_to_s3(
            response_data["presigned_url"],
            video_file,
            response_data.get("required_metadata_headers"),
            content_type='video/mp4'
        )
    else:
        logger.error(f"Falha ao obter URL pré-assinada para vídeo. Resposta: {response_data}")
    logger.info("--- FIM TESTE: Envio de Mensagem de Vídeo ---\n")

def testar_requisicao_permissao():
    logger.info("\n--- INICIANDO TESTE: Requisição de Permissão de Pessoa ---")
    if not subscribe_to_topic(TOPIC_PERM_RESP): return

    # Use um face_tag_id que você espera que exista ou não, para testar ambos os casos
    # face_tag_id_para_teste = "c9b8a712-9b2f-4c3d-9d5e-1f8a7b6c5d4e" # Exemplo
    face_tag_id_para_teste = "f80490f5-a231-4ced-9e07-29083b872c08"
    
    payload_perm_req = {
        "sbc_id": SBC_ID,
        "face_tag_id": face_tag_id_para_teste
    }
    if not publish_message(TOPIC_PERM_REQ, payload_perm_req): return

    response_data = wait_for_response(TOPIC_PERM_RESP)
    if response_data:
        logger.info(f"Resposta da requisição de permissão: {response_data}")
    else:
        logger.error("Nenhuma resposta para requisição de permissão.")
    logger.info("--- FIM TESTE: Requisição de Permissão de Pessoa ---\n")

def testar_requisicao_pacote():
    logger.info("\n--- INICIANDO TESTE: Requisição de Informação de Pacote ---")
    if not subscribe_to_topic(TOPIC_PKG_RESP): return

    # Teste por order_id
    payload_pkg_req_order = {
        "sbc_id": SBC_ID,
        "identifier_type": "order_id",
        "identifier_value": "ORDER12345" 
    }
    logger.info("Testando por order_id...")
    if publish_message(TOPIC_PKG_REQ, payload_pkg_req_order):
        response_data_order = wait_for_response(TOPIC_PKG_RESP)
        if response_data_order:
            logger.info(f"Resposta da requisição de pacote (order_id): {response_data_order}")
        else:
            logger.error("Nenhuma resposta para requisição de pacote (order_id).")
            
    logger.info("--- FIM TESTE: Requisição de Informação de Pacote ---\n")

def testar_envio_log():
    logger.info("\n--- INICIANDO TESTE: Envio de Log do Dispositivo ---")
    # Não há resposta MQTT esperada para este, então não precisa se inscrever.
    
    log_payload = {
        "sbc_id": SBC_ID,
        "log_timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "NEW_VIDEO",
        "event_details": {
            "firmware_version": "1.2.3",
            "status": "success"
        }
    }
    if publish_message(TOPIC_LOG_SUBMIT, log_payload):
        logger.info("Payload de log enviado.")
    else:
        logger.error("Falha ao enviar payload de log.")
    logger.info("--- FIM TESTE: Envio de Log do Dispositivo ---\n")


if __name__ == '__main__':
    # Validação inicial de placeholders
    if "YOUR_AWS_IOT_ENDPOINT" in AWS_IOT_ENDPOINT:
        logger.error("ERRO: AWS_IOT_ENDPOINT não foi configurado. Edite o script.")
        exit(1)
    if not all(os.path.exists(p) for p in [PATH_TO_ROOT_CA, PATH_TO_PRIVATE_KEY, PATH_TO_CERTIFICATE]):
        logger.error("ERRO: Um ou mais arquivos de certificado/chave não foram encontrados. Verifique os caminhos em PATH_TO_...")
        exit(1)

    # Criar pasta de certificados se não existir (apenas para organização local)
    if not os.path.exists("certs"):
        os.makedirs("certs")
        logger.info("Pasta 'certs' criada. Por favor, coloque seus arquivos de certificado e chave lá.")

    # Conectar ao MQTT
    if not connect_mqtt():
        exit(1) # Sai se não conseguir conectar

    try:
        # testar_cadastro_visitante("Dog", "Allowed", "dog.jpg") # Funcionou
        # time.sleep(2) # Pequena pausa entre testes

        # testar_envio_mensagem_video() # Funcionou
        # time.sleep(2)

        # testar_requisicao_permissao() # Funcionou
        # time.sleep(2)

        testar_requisicao_pacote() # TODO
        # time.sleep(2)
        
        # testar_envio_log() # Funcionou
        # time.sleep(2)

    except KeyboardInterrupt:
        logger.info("Teste interrompido pelo usuário.")
    except Exception as e:
        logger.error(f"Um erro inesperado ocorreu durante os testes: {e}", exc_info=True)
    finally:
        disconnect_mqtt()
        logger.info("Script de teste finalizado.")

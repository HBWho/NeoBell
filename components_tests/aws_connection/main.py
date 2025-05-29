import time
import json
import uuid
import os
import threading
import requests # Para upload S3

from dotenv import load_dotenv
from awscrt.mqtt import Connection, Client, QoS
from awsiot import mqtt_connection_builder

load_dotenv()

# --- Configurações do Dispositivo SBC ---
SBC_ID = os.getenv("CLIENT_ID")
PORT = os.getenv("PORT")
AWS_IOT_ENDPOINT = os.getenv("AWS_IOT_ENDPOINT")
PATH_TO_ROOT_CA = "certifications/AmazonRootCA1.pem"
PATH_TO_PRIVATE_KEY = "certifications/10da83970c7ac9793d1f4c33c48f082924dc1aaccd0e8e8fd229d13b5caa210e-private.pem.key"
PATH_TO_CERTIFICATE = "certifications/10da83970c7ac9793d1f4c33c48f082924dc1aaccd0e8e8fd229d13b5caa210e-certificate.pem.crt"

# Tópicos MQTT (baseados no SBC_ID)
TOPIC_REQUEST_UPLOAD_URL = f"neobell/sbc/{SBC_ID}/registrations/request-upload-url"
TOPIC_UPLOAD_URL_RESPONSE = f"neobell/sbc/{SBC_ID}/registrations/upload-url-response"

# Evento para sincronizar o recebimento da URL pré-assinada
presigned_url_received_event = threading.Event()
presigned_url_data = {}

# --- Callbacks MQTT ---
def on_connection_interrupted(connection, error, **kwargs):
    print(f"Conexão interrompida. Erro: {error}")

def on_connection_resumed(connection, return_code, session_present, **kwargs):
    print(f"Conexão retomada. Código de retorno: {return_code}, Sessão presente: {session_present}")
    if return_code == Connection.RESUME_RECONNECT_SUCCESS and not session_present:
        print("Sessão não estava presente. Reinscrevendo-se nos tópicos...")
        resubscribe_future = mqtt_connection.resubscribe_existing_topics()
        resubscribe_future.add_done_callback(on_resubscribe_complete)

def on_resubscribe_complete(resubscribe_future):
    resubscribe_results = resubscribe_future.result()
    print(f"Resultados da reinscrição: {resubscribe_results}")
    for topic, qos in resubscribe_results['topics']:
        if qos is None:
            print(f"Erro ao se reinscrever no tópico: {topic}")

def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    print(f"Mensagem recebida no tópico '{topic}'")
    print(f"Payload: {payload.decode()}")
    global presigned_url_data
    if topic == TOPIC_UPLOAD_URL_RESPONSE:
        try:
            presigned_url_data = json.loads(payload.decode())
            presigned_url_received_event.set() # Sinaliza que a URL foi recebida
        except json.JSONDecodeError:
            print("Erro ao decodificar JSON da resposta da URL pré-assinada.")
            presigned_url_data = {"error": "JSONDecodeError"} # Marcar erro
            presigned_url_received_event.set() # Sinalizar para não bloquear indefinidamente


# --- Lógica Principal do Dispositivo ---
if __name__ == '__main__':
    print("Inicializando dispositivo SBC NeoBell...")

    # Validação básica dos caminhos dos certificados
    if not all(os.path.exists(p) for p in [PATH_TO_ROOT_CA, PATH_TO_PRIVATE_KEY, PATH_TO_CERTIFICATE]):
        print("ERRO: Um ou mais arquivos de certificado/chave não foram encontrados. Verifique os caminhos.")
        exit(1)
    
    if "YOUR_AWS_IOT_ENDPOINT" in AWS_IOT_ENDPOINT:
        print("ERRO: AWS_IOT_ENDPOINT não configurado. Por favor, edite o script.")
        exit(1)

    # Construir conexão MQTT
    print(f"Tentando conectar ao endpoint: {AWS_IOT_ENDPOINT} com ClientID: {SBC_ID}")
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=AWS_IOT_ENDPOINT,
        cert_filepath=PATH_TO_CERTIFICATE,
        pri_key_filepath=PATH_TO_PRIVATE_KEY,
        ca_filepath=PATH_TO_ROOT_CA,
        on_connection_interrupted=on_connection_interrupted,
        on_connection_resumed=on_connection_resumed,
        client_id=SBC_ID,
        clean_session=False, # Manter sessão para QoS 1 e subscrições persistentes (se desejado)
        keep_alive_secs=30
    )

    connect_future = mqtt_connection.connect()
    try:
        connect_future.result() # Bloqueia até a conexão ser estabelecida ou falhar
        print("Conectado ao AWS IoT Core!")
    except Exception as e:
        print(f"Falha ao conectar ao AWS IoT Core: {e}")
        exit(1)

    # Inscrever-se no tópico de resposta da URL pré-assinada
    print(f"Inscrevendo-se no tópico: {TOPIC_UPLOAD_URL_RESPONSE}")
    subscribe_future, packet_id = mqtt_connection.subscribe(
        topic=TOPIC_UPLOAD_URL_RESPONSE,
        qos=QoS.AT_LEAST_ONCE, # QoS 1
        callback=on_message_received
    )
    subscribe_result = subscribe_future.result()
    print(f"Inscrito com {str(subscribe_result['qos'])}")


    # --- Função enviar_cadastro ---
    def enviar_cadastro(image_filepath, visitor_name, permission_level):
        """
        Simula a captura de uma imagem, solicita URL pré-assinada e faz upload para o S3.
        """
        global presigned_url_data
        presigned_url_data = {} # Limpa dados anteriores
        presigned_url_received_event.clear() # Reseta o evento

        if not os.path.exists(image_filepath):
            print(f"Erro: Arquivo de imagem '{image_filepath}' não encontrado.")
            return False

        face_tag_id = str(uuid.uuid4()) # Gera um ID único para esta face/visitante/registro

        # 1. Preparar payload para solicitar URL
        request_payload = {
            "sbc_id": SBC_ID, # Adicionado para que a Lambda possa usá-lo se não extraído do tópico
            "face_tag_id": face_tag_id,
            "visitor_name": visitor_name,
            "permission_level": str(permission_level) # Enviar como string, Lambda pode converter
        }
        print(f"Publicando solicitação de URL para o tópico: {TOPIC_REQUEST_UPLOAD_URL}")
        print(f"Payload da solicitação: {json.dumps(request_payload)}")
        
        publish_future, _ = mqtt_connection.publish(
            topic=TOPIC_REQUEST_UPLOAD_URL,
            payload=json.dumps(request_payload),
            qos=QoS.AT_LEAST_ONCE # QoS 1
        )
        publish_future.result() # Espera a confirmação do publish (PUBACK para QoS 1)
        print("Solicitação de URL publicada com sucesso.")

        # 2. Esperar pela resposta com a URL pré-assinada
        print("Aguardando resposta com a URL pré-assinada...")
        if presigned_url_received_event.wait(timeout=30.0): # Espera por até 30 segundos
            if "error" in presigned_url_data or "presigned_url" not in presigned_url_data:
                print(f"Erro ao obter URL pré-assinada: {presigned_url_data.get('error', 'Resposta inesperada')}")
                return False
            
            s3_url = presigned_url_data["presigned_url"]
            required_headers = presigned_url_data.get("required_metadata_headers", {})
            print(f"URL pré-assinada recebida: {s3_url}")
            print(f"Cabeçalhos de metadados necessários: {required_headers}")

            # 3. Fazer upload da imagem para S3
            try:
                print(f"Fazendo upload da imagem '{image_filepath}' para S3...")
                with open(image_filepath, 'rb') as image_file:
                    image_data = image_file.read()
                
                # Adicionar Content-Type se não estiver nos required_headers (geralmente não está)
                # A Lambda de geração de URL pode ter especificado que o cliente deve definir.
                headers_for_s3 = {
                    'Content-Type': 'image/jpeg' # Ou o tipo de imagem correto
                }
                headers_for_s3.update(required_headers) # Adiciona os cabeçalhos x-amz-meta-*

                response = requests.put(s3_url, data=image_data, headers=headers_for_s3)
                response.raise_for_status() # Levanta uma exceção para códigos de erro HTTP (4xx ou 5xx)
                
                print(f"Upload para S3 bem-sucedido! Status: {response.status_code}")
                print(f"Imagem do visitante '{visitor_name}' (face_tag: {face_tag_id}) enviada.")
                return True
            except requests.exceptions.RequestException as e:
                print(f"Erro no upload para S3: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"Resposta do S3: {e.response.text}")
                return False
        else:
            print("Timeout: Nenhuma resposta recebida para a URL pré-assinada.")
            return False

    # --- Exemplo de uso da função ---
    try:
        # Simular a existência de uma imagem de visitante
        # Crie um arquivo dummy.jpg no mesmo diretório ou aponte para uma imagem real.
        dummy_image_path = "GABRIEL_SPADAFORA.jpg"
        if not os.path.exists(dummy_image_path):
            with open(dummy_image_path, "wb") as f:
                f.write(os.urandom(1024)) # Cria um arquivo de 1KB
            print(f"Arquivo de imagem dummy criado: {dummy_image_path}")

        # Chamar a função para registrar um visitante
        print("\n--- Testando cadastro de visitante ---")
        success = enviar_cadastro(
            image_filepath=dummy_image_path,
            visitor_name="Gabriel",
            permission_level=2
        )
        if success:
            print("Fluxo de cadastro de visitante concluído com sucesso no dispositivo.")
        else:
            print("Fluxo de cadastro de visitante falhou no dispositivo.")
        
        # Manter o script rodando por um tempo para outros testes ou CTRL+C para sair
        # while True:
        #     time.sleep(1)

    except KeyboardInterrupt:
        print("Saindo...")
    finally:
        if mqtt_connection:
            print("Desconectando do AWS IoT Core...")
            disconnect_future = mqtt_connection.disconnect()
            disconnect_future.result()
            print("Desconectado.")

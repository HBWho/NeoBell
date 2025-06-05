import boto3
import json
import os

# --- Configurações ---
AWS_REGION = "us-east-1"
# O ID da sua conta AWS. Usaremos o que você forneceu na política.
ACCOUNT_ID = "ACCOUNT_ID" # Seu ID de conta AWS
THING_TYPE_NAME = "NeoBellSBCDeviceType"
# Você pode alterar este nome se estiver criando um novo dispositivo via script
THING_NAME_FOR_SCRIPT = "NeoBellSBC-Device-FromScript"
POLICY_NAME = "NeoBellSBCBasePolicy"

# Caminhos para salvar os certificados (opcional, mas recomendado)
CERT_FOLDER = "device_certs_updated" # Nova pasta para não sobrescrever os anteriores, se houver
CERT_FILE = os.path.join(CERT_FOLDER, f"{THING_NAME_FOR_SCRIPT}.pem.crt")
PRIVATE_KEY_FILE = os.path.join(CERT_FOLDER, f"{THING_NAME_FOR_SCRIPT}.private.key")
PUBLIC_KEY_FILE = os.path.join(CERT_FOLDER, f"{THING_NAME_FOR_SCRIPT}.public.key")
ROOT_CA_URL = "https://www.amazontrust.com/repository/AmazonRootCA1.pem"

# --- Inicializar cliente IoT ---
iot_client = boto3.client('iot', region_name=AWS_REGION)

def create_iot_core_resources_updated():
    print(f"Usando a região: {AWS_REGION} e Conta AWS ID: {ACCOUNT_ID}")

    if ACCOUNT_ID == "YOUR_ACCOUNT_ID" or len(ACCOUNT_ID) != 12:
        print("ERRO: Por favor, configure o ACCOUNT_ID corretamente no script.")
        return

    # --- 1. Criar Tipo de Coisa (Thing Type) ---
    try:
        iot_client.create_thing_type(thingTypeName=THING_TYPE_NAME)
        print(f"Tipo de Coisa '{THING_TYPE_NAME}' criado com sucesso.")
    except iot_client.exceptions.ResourceAlreadyExistsException:
        print(f"Tipo de Coisa '{THING_TYPE_NAME}' já existe.")
    except Exception as e:
        print(f"Erro ao criar Tipo de Coisa '{THING_TYPE_NAME}': {e}")
        return

    # --- 2. Criar Coisa (Thing) ---
    try:
        thing_response = iot_client.create_thing(
            thingName=THING_NAME_FOR_SCRIPT,
            thingTypeName=THING_TYPE_NAME
        )
        thing_arn = thing_response['thingArn']
        print(f"Coisa '{THING_NAME_FOR_SCRIPT}' criada com sucesso com ARN: {thing_arn}")
    except iot_client.exceptions.ResourceAlreadyExistsException:
        print(f"Coisa '{THING_NAME_FOR_SCRIPT}' já existe. Tentando obter ARN.")
        try:
            thing_desc = iot_client.describe_thing(thingName=THING_NAME_FOR_SCRIPT)
            thing_arn = thing_desc['thingArn']
            print(f"ARN da Coisa '{THING_NAME_FOR_SCRIPT}': {thing_arn}")
        except Exception as e_desc:
            print(f"Erro ao obter ARN da Coisa existente '{THING_NAME_FOR_SCRIPT}': {e_desc}")
            return
    except Exception as e:
        print(f"Erro ao criar Coisa '{THING_NAME_FOR_SCRIPT}': {e}")
        return

    # --- 3. Criar/Atualizar Política IoT (IoT Policy) ---
    # Usando o ACCOUNT_ID diretamente na definição da política.
    # A variável ${iot:ClientId} será resolvida pelo AWS IoT no momento da conexão/operação.
    policy_document_updated = {
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
            f"arn:aws:iot:{AWS_REGION}:{ACCOUNT_ID}:topic/neobell/status"
          ]
        },
        {
          "Effect": "Allow",
          "Action": "iot:Subscribe",
          "Resource": [
            f"arn:aws:iot:{AWS_REGION}:{ACCOUNT_ID}:topicfilter/neobell/sbc/${{iot:ClientId}}/registrations/upload-url-response",
            f"arn:aws:iot:{AWS_REGION}:{ACCOUNT_ID}:topicfilter/neobell/commands"
          ]
        },
        {
          "Effect": "Allow",
          "Action": "iot:Receive",
          "Resource": [
            f"arn:aws:iot:{AWS_REGION}:{ACCOUNT_ID}:topic/neobell/sbc/${{iot:ClientId}}/registrations/upload-url-response",
            f"arn:aws:iot:{AWS_REGION}:{ACCOUNT_ID}:topic/neobell/commands"
          ]
        }
      ]
    }

    try:
        # Tenta criar a política. Se já existir, uma exceção será levantada.
        policy_response = iot_client.create_policy(
            policyName=POLICY_NAME,
            policyDocument=json.dumps(policy_document_updated)
        )
        policy_arn = policy_response['policyArn']
        print(f"Política IoT '{POLICY_NAME}' criada com sucesso com ARN: {policy_arn}")
    except iot_client.exceptions.ResourceAlreadyExistsException:
        print(f"Política IoT '{POLICY_NAME}' já existe. Tentando atualizar (criando nova versão).")
        # Se a política já existe, você pode querer criar uma nova versão dela
        # ou deletar e recriar se as permissões mudarem drasticamente e não houver versões.
        # Para atualizar, obtenha as versões, delete as não padrão (se houver mais de 5)
        # e então crie uma nova versão.
        try:
            # Obter a versão padrão atual
            # policy_versions = iot_client.list_policy_versions(policyName=POLICY_NAME)
            # default_version = next((v for v in policy_versions.get('policyVersions', []) if v.get('isDefaultVersion')), None)
            
            # Criar uma nova versão da política. Isso se tornará a padrão.
            updated_policy_response = iot_client.create_policy_version(
                policyName=POLICY_NAME,
                policyDocument=json.dumps(policy_document_updated),
                setAsDefault=True # Torna esta nova versão a padrão
            )
            policy_arn = updated_policy_response['policyArn'] # ARN da política base
            print(f"Nova versão da Política IoT '{POLICY_NAME}' criada e definida como padrão. ARN: {policy_arn}, Versão: {updated_policy_response['policyVersionId']}")
            
            # Opcional: Limpar versões antigas não padrão se necessário
            # (AWS IoT mantém até 5 versões de política)
            
        except Exception as e_update_pol:
            print(f"Erro ao criar nova versão da Política IoT '{POLICY_NAME}': {e_update_pol}")
            # Se a atualização falhar, use o ARN conhecido
            policy_arn = f"arn:aws:iot:{AWS_REGION}:{ACCOUNT_ID}:policy/{POLICY_NAME}"


    except Exception as e:
        print(f"Erro ao criar/atualizar Política IoT '{POLICY_NAME}': {e}")
        return

    # --- 4. Gerar Certificado e Chaves ---
    try:
        cert_response = iot_client.create_keys_and_certificate(setAsActive=True)
        certificate_arn = cert_response['certificateArn']
        certificate_pem = cert_response['certificatePem']
        key_pair = cert_response['keyPair']
        private_key = key_pair['PrivateKey']
        public_key = key_pair['PublicKey']

        print(f"Certificado criado com sucesso com ARN: {certificate_arn}")
        print("\n--- CERTIFICADO PEM ---")
        print(certificate_pem)
        print("\n--- CHAVE PRIVADA --- (GUARDE COM SEGURANÇA!)")
        print(private_key)
        print("\n--- CHAVE PÚBLICA ---")
        print(public_key)
        print(f"\nLembre-se de baixar o certificado raiz da CA da AWS: {ROOT_CA_URL}")

        # Opcional: Salvar certificados em arquivos
        if not os.path.exists(CERT_FOLDER):
            os.makedirs(CERT_FOLDER)
        with open(CERT_FILE, 'w') as f:
            f.write(certificate_pem)
        print(f"\nCertificado salvo em: {CERT_FILE}")
        with open(PRIVATE_KEY_FILE, 'w') as f:
            f.write(private_key)
        print(f"Chave Privada salva em: {PRIVATE_KEY_FILE}")
        with open(PUBLIC_KEY_FILE, 'w') as f:
            f.write(public_key)
        print(f"Chave Pública salva em: {PUBLIC_KEY_FILE}")
        print(f"\nIMPORTANTE: A CHAVE PRIVADA ACIMA É MOSTRADA APENAS UMA VEZ. GUARDE-A EM LOCAL SEGURO.")

    except Exception as e:
        print(f"Erro ao criar certificado: {e}")
        return

    # --- 5. Anexar Política ao Certificado ---
    try:
        iot_client.attach_policy(
            policyName=POLICY_NAME,
            target=certificate_arn
        )
        print(f"Política '{POLICY_NAME}' anexada ao certificado '{certificate_arn}' com sucesso.")
    except Exception as e:
        print(f"Erro ao anexar política ao certificado: {e}")
        return

    # --- 6. Anexar Certificado à Coisa ---
    try:
        iot_client.attach_thing_principal(
            thingName=THING_NAME_FOR_SCRIPT, # Principal é o ARN do certificado
            principal=certificate_arn
        )
        print(f"Certificado '{certificate_arn}' anexado à Coisa '{THING_NAME_FOR_SCRIPT}' com sucesso.")
    except Exception as e:
        print(f"Erro ao anexar certificado à Coisa: {e}")
        return

    print("\n--- Configuração da Parte A (Boto3 - Atualizado) concluída ---")
    print(f"Thing ARN: {thing_arn}")
    print(f"Certificate ARN: {certificate_arn}")
    print(f"Policy ARN (Base): {policy_arn}")

if __name__ == "__main__":
    # Crie a pasta para os certificados se não existir
    if not os.path.exists(CERT_FOLDER):
        os.makedirs(CERT_FOLDER)
        
    create_iot_core_resources_updated()
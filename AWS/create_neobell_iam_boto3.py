import json
import boto3
from botocore.exceptions import ClientError

# Substitua pelo seu Account ID real
ACCOUNT_ID = "ACCOUNT_ID"
REGION = "us-east-1" # Embora IAM seja global, alguns ARNs são regionais

iam_client = boto3.client('iam')

def create_iam_role_with_policies(role_name, trust_policy_document, policies, tags):
    """
    Cria uma IAM role com as políticas de confiança, permissão e tags especificadas.
    """
    try:
        role_response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy_document),
            Description=f"Role para {role_name}",
            Tags=tags
        )
        role_arn = role_response['Role']['Arn']
        print(f"Role '{role_name}' criada com ARN: {role_arn}")

        # Anexa políticas gerenciadas
        if 'managed_policies' in policies:
            for policy_arn in policies['managed_policies']:
                iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy_arn
                )
                print(f"Política gerenciada '{policy_arn}' anexada à role '{role_name}'.")

        # Cria e anexa políticas inline
        if 'inline_policies' in policies:
            for policy_name, policy_document in policies['inline_policies'].items():
                iam_client.put_role_policy(
                    RoleName=role_name,
                    PolicyName=policy_name,
                    PolicyDocument=json.dumps(policy_document)
                )
                print(f"Política inline '{policy_name}' criada e anexada à role '{role_name}'.")
        
        return role_arn
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print(f"Role '{role_name}' já existe. Verifique e delete se necessário recriar.")
            # Opcionalmente, você pode buscar o ARN da role existente aqui se precisar
            try:
                existing_role = iam_client.get_role(RoleName=role_name)
                return existing_role['Role']['Arn']
            except ClientError as get_err:
                print(f"Erro ao buscar a role existente '{role_name}': {get_err}")
                return None
        else:
            print(f"Erro ao criar a role '{role_name}': {e}")
            return None

# --- Definição da Role 1: NeoBellLambdaExecutionRole ---
lambda_trust_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }
    ]
}

lambda_dynamodb_policy = {
	"Version": "2012-10-17",
	"Statement": [
		{
			"Sid": "NeoBellDynamoDBTableAccess",
			"Effect": "Allow",
			"Action": [
				"dynamodb:GetItem",
				"dynamodb:PutItem",
				"dynamodb:UpdateItem",
				"dynamodb:DeleteItem",
				"dynamodb:Query",
				"dynamodb:Scan",
				"dynamodb:BatchGetItem"
			],
			"Resource": [
				"arn:aws:dynamodb:us-east-1{ACCOUNT_ID}table/NeoBellUsers",
				"arn:aws:dynamodb:us-east-1{ACCOUNT_ID}table/NeoBellUsers/index/*",
				"arn:aws:dynamodb:us-east-1{ACCOUNT_ID}table/NeoBellDevices",
				"arn:aws:dynamodb:us-east-1{ACCOUNT_ID}table/NeoBellDevices/index/*",
				"arn:aws:dynamodb:us-east-1{ACCOUNT_ID}table/DeviceUserLinks",
				"arn:aws:dynamodb:us-east-1{ACCOUNT_ID}table/DeviceUserLinks/index/*",
				"arn:aws:dynamodb:us-east-1{ACCOUNT_ID}table/UserNFCTags",
				"arn:aws:dynamodb:us-east-1{ACCOUNT_ID}table/UserNFCTags/index/*",
				"arn:aws:dynamodb:us-east-1{ACCOUNT_ID}table/Permissions",
				"arn:aws:dynamodb:us-east-1{ACCOUNT_ID}table/Permissions/index/*",
				"arn:aws:dynamodb:us-east-1{ACCOUNT_ID}table/VideoMessages",
				"arn:aws:dynamodb:us-east-1{ACCOUNT_ID}table/VideoMessages/index/*",
				"arn:aws:dynamodb:us-east-1{ACCOUNT_ID}table/ExpectedDeliveries",
				"arn:aws:dynamodb:us-east-1{ACCOUNT_ID}table/ExpectedDeliveries/index/*",
				"arn:aws:dynamodb:us-east-1{ACCOUNT_ID}table/EventLogs",
				"arn:aws:dynamodb:us-east-1{ACCOUNT_ID}table/EventLogs/index/*"
			]
		}
	]
}

lambda_iot_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": "iot:Publish",
            "Resource": "arn:aws:iot:us-east-1{ACCOUNT_ID}topic/neobell/*"
        }
    ]
}

lambda_sns_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "sns:CreatePlatformEndpoint",
                "sns:Publish",
                "sns:GetEndpointAttributes",
                "sns:SetEndpointAttributes",
                "sns:DeleteEndpoint"
            ],
            "Resource": [
                "arn:aws:sns:us-east-1{ACCOUNT_ID}app/FCM/NeoBellFCMPlatformApp-Android",
                "arn:aws:sns:us-east-1{ACCOUNT_ID}endpoint/FCM/NeoBellFCMPlatformApp-Android/*"
            ]
        }
    ]
}

lambda_to_lambda_policy = {
	"Version": "2012-10-17",
	"Statement": [
		{
			"Effect": "Allow",
			"Action": "lambda:InvokeFunction",
			"Resource": "arn:aws:lambda:us-east-1{ACCOUNT_ID}function:NeoBellNotificationHandler"
		}
	]
}

lambda_s3_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowObjectActionsOnVideoMessagesBucket",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::neobell-videomessages-hbwho/*"
        },
        {
            "Sid": "AllowBucketLevelAccessForListingIfNeeded",
            "Effect": "Allow",
            "Action": "s3:ListBucket",
            "Resource": "arn:aws:s3:::neobell-videomessages-hbwho",
            "Condition": {
                "StringLike": {"s3:prefix": ["", "*"]}
            }
        }
    ]
}

lambda_role_policies = {
    "managed_policies": [
        "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
        "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
    ],
    "inline_policies": {
        "NeoBellDynamoDBAccessPolicy": lambda_dynamodb_policy,
        "NeoBellIoTAccessPolicy": lambda_iot_policy,
        "NeoBellSNSAccessPolicy": lambda_sns_policy,
        "NeoBellLambdaToLambdaInvokePolicy": lambda_to_lambda_policy,
        "NeoBellS3VideoMessagesAccessPolicy": lambda_s3_policy
    }
}

lambda_role_tags = [
    {'Key': 'Project', 'Value': 'NeoBell'}
]

# --- Definição da Role 2: NeoBellIoTRuleActionRole ---
iot_rule_trust_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"Service": "iot.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }
    ]
}

iot_rule_lambda_invoke_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowIoTRuleToInvokeLambda",
            "Effect": "Allow",
            "Action": "lambda:InvokeFunction",
            "Resource": f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:NeoBell*"
        }
    ]
}

iot_rule_policies = {
    "inline_policies": {
        "NeoBellIoTRuleInvokeLambdaPolicy": iot_rule_lambda_invoke_policy
    }
}

iot_rule_tags = [
    {'Key': 'Project', 'Value': 'NeoBell'}
]

# --- Criar as Roles ---
print("Iniciando a criação das roles IAM para o Projeto NeoBell...")
print("--------------------------------------------------")

# Criar NeoBellLambdaExecutionRole
create_iam_role_with_policies(
    role_name="NeoBellLambdaExecutionRole",
    trust_policy_document=lambda_trust_policy,
    policies=lambda_role_policies,
    tags=lambda_role_tags
)
print("--------------------------------------------------")

# Criar NeoBellIoTRuleActionRole
create_iam_role_with_policies(
    role_name="NeoBellIoTRuleActionRole",
    trust_policy_document=iot_rule_trust_policy,
    policies=iot_rule_policies,
    tags=iot_rule_tags
)
print("--------------------------------------------------")
print("Criação das roles IAM concluída.")


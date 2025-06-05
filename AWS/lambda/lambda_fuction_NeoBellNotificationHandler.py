# lambda_function.py for NeoBellNotificationHandler
import json
import os
import boto3
from botocore.exceptions import ClientError
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
DYNAMODB_RESOURCE = boto3.resource('dynamodb', region_name=AWS_REGION)
SNS_CLIENT = boto3.client('sns', region_name=AWS_REGION)

NEOBELL_USERS_TABLE_NAME = os.environ.get('DYNAMODB_USERS_TABLE_NAME', 'NeoBellUsers')
DEVICE_USER_LINK_TABLE_NAME = os.environ.get('DYNAMODB_DEVICE_USER_LINK_TABLE_NAME', 'DeviceUserLinks')

users_table = DYNAMODB_RESOURCE.Table(NEOBELL_USERS_TABLE_NAME)
device_user_link_table = DYNAMODB_RESOURCE.Table(DEVICE_USER_LINK_TABLE_NAME)

def _send_push_notification(user_id_to_notify, notification_type, message_payload_details):
    """
    Helper function to send a notification to a single user.
    Reusable for direct user notification or fan-out from SBC.
    """
    title = message_payload_details.get('title')
    body = message_payload_details.get('body')
    data_for_app = message_payload_details.get('data', {})

    if notification_type:
        data_for_app['notification_type'] = notification_type

    if not title or not body:
        logger.error(f"For user {user_id_to_notify}: Missing 'title' or 'body' in message_payload_details.")
        return {"status": "error", "reason": "Missing title or body"}

    try:
        response = users_table.get_item(Key={'user_id': user_id_to_notify})
        item = response.get('Item')

        if not item or 'sns_endpoint_arn' not in item:
            logger.warning(f"No SNS endpoint ARN found for user_id: {user_id_to_notify}")
            return {"status": "error", "reason": "SNS endpoint ARN not found"}

        sns_endpoint_arn = item['sns_endpoint_arn']
        if not sns_endpoint_arn:
            logger.warning(f"SNS endpoint ARN is empty for user_id: {user_id_to_notify}")
            return {"status": "error", "reason": "SNS endpoint ARN is empty"}

        notification = {"title": title, "body": body, "sound": "default"}
        if notification_type:
            notification['android_channel_id'] = notification_type

        fcm_notification_payload = {
            "notification": notification,
            "data": data_for_app
        }
        message_for_sns = {"GCM": json.dumps(fcm_notification_payload)}

        logger.info(f"Attempting to publish to SNS Endpoint: {sns_endpoint_arn} for user {user_id_to_notify}")
        publish_response = SNS_CLIENT.publish(
            TargetArn=sns_endpoint_arn,
            Message=json.dumps(message_for_sns),
            MessageStructure='json'
        )
        logger.info(f"Successfully sent notification to {user_id_to_notify}. Message ID: {publish_response['MessageId']}")
        return {"status": "success", "user_id": user_id_to_notify, "message_id": publish_response['MessageId']}

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == 'EndpointDisabled':
            logger.warning(f"Endpoint {sns_endpoint_arn if 'sns_endpoint_arn' in locals() else 'N/A'} for user {user_id_to_notify} is disabled.")
            return {"status": "error", "user_id": user_id_to_notify, "reason": "EndpointDisabled"}
        elif error_code == 'ResourceNotFoundException':
            logger.error(f"SNS ResourceNotFoundException for user {user_id_to_notify}: {e}")
            return {"status": "error", "user_id": user_id_to_notify, "reason": "SNS ARN ResourceNotFound"}
        logger.error(f"SNS ClientError for user {user_id_to_notify}: {e}")
        # Para invocações assíncronas, re-lançar o erro pode acionar retentativas da AWS Lambda.
        # Se este helper for chamado em um loop, pode ser melhor apenas registrar o erro e continuar.
        # Por ora, retornamos o erro para que o chamador principal decida.
        return {"status": "error", "user_id": user_id_to_notify, "reason": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id_to_notify}: {e}")
        return {"status": "error", "user_id": user_id_to_notify, "reason": f"Unexpected error: {str(e)}"}


def lambda_handler(event, context):
    logger.info(f"Received notification request: {json.dumps(event)}")

    # Expected event structure:
    # {
    #   "user_id": "user_uuid", OR "sbc_id": "sbc_device_id",
    #   "message_payload": { "title": "...", "body": "...", "data": { ... } }
    # }

    user_id_direct = event.get('user_id')
    sbc_id_fan_out = event.get('sbc_id')
    message_payload = event.get('message_payload')
    notification_type = event.get('notification_type', None)

    if not (user_id_direct or sbc_id_fan_out) or not message_payload:
        logger.error("Missing required fields: (user_id OR sbc_id) AND message_payload.")
        return {'statusCode': 400, 'body': json.dumps({'error': 'Missing required fields.'})}

    # --- LÓGICA DE ROTEAMENTO ---
    results = []
    overall_status_code = 200 # Assume sucesso por padrão

    if user_id_direct:
        logger.info(f"Processing direct notification for user_id: {user_id_direct}")
        result = _send_push_notification(user_id_direct, notification_type, message_payload)
        results.append(result)
        if result["status"] == "error":
            overall_status_code = 500

    elif sbc_id_fan_out:
        logger.info(f"Processing fan-out notification for sbc_id: {sbc_id_fan_out}")
        try:
            query_response = device_user_link_table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('sbc_id').eq(sbc_id_fan_out)
            )
            linked_items = query_response.get('Items', [])
            if not linked_items:
                logger.warning(f"No users found linked to sbc_id: {sbc_id_fan_out}")
                return {'statusCode': 404, 'body': json.dumps({'message': f"No users linked to sbc_id {sbc_id_fan_out}"})}

            success_count = 0
            failure_count = 0
            for item in linked_items:
                linked_user_id = item.get('user_id')
                if linked_user_id:
                    logger.info(f"Sending to linked user: {linked_user_id} for sbc_id: {sbc_id_fan_out}")
                    result = _send_push_notification(linked_user_id, notification_type, message_payload)
                    results.append(result)
                    if result["status"] == "success":
                        success_count += 1
                    else:
                        failure_count += 1
                else:
                    logger.warning(f"Found item in DeviceUserLink for sbc_id {sbc_id_fan_out} without a user_id: {item}")
            
            logger.info(f"Fan-out for sbc_id {sbc_id_fan_out} complete. Successes: {success_count}, Failures: {failure_count}")
            if failure_count > 0 and success_count == 0:
                overall_status_code = 500 # Todas falharam
            elif failure_count > 0:
                overall_status_code = 207 # Sucesso parcial (Multi-Status)

        except ClientError as e:
            logger.error(f"DynamoDB ClientError querying DeviceUserLink for sbc_id {sbc_id_fan_out}: {e}")
            raise e 
        except Exception as e:
            logger.error(f"Unexpected error during fan-out for sbc_id {sbc_id_fan_out}: {e}")
            raise e
    else:
        logger.error("Invalid state: No user_id or sbc_id provided after initial checks.")
        return {'statusCode': 500, 'body': json.dumps({'error': 'Internal server error: Invalid routing state.'})}

    return {
        'statusCode': overall_status_code,
        'body': json.dumps({
            'message': 'Notification processing complete.',
            'results': results
        })
    }
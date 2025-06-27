# lambda_function.py for NeoBellUserHandler
import json
import os
import boto3
from botocore.exceptions import ClientError
import datetime # Keep as datetime, not datetime.datetime for consistency with original code
import logging
import re # For path matching if needed

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients (outside the handler for reuse)
# Ensure the region is correctly picked up from the Lambda environment or set explicitly
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1') # Explicitly define region
DYNAMODB_CLIENT = boto3.resource('dynamodb', region_name=AWS_REGION)
SNS_CLIENT = boto3.client('sns', region_name=AWS_REGION) # SNS client
cognito_client = boto3.client('cognito-idp')

# DynamoDB Table Names
NEOBELL_USERS_TABLE_NAME = os.environ.get('NEOBELL_USERS_TABLE', 'NeoBellUsers')
USER_NFC_TAGS_TABLE_NAME = os.environ.get('USER_NFC_TAGS_TABLE', 'UserNFCTags')
USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID', 'us-east-1_7s5Ur8SOU') 

neobell_users_table = DYNAMODB_CLIENT.Table(NEOBELL_USERS_TABLE_NAME)
user_nfc_tags_table = DYNAMODB_CLIENT.Table(USER_NFC_TAGS_TABLE_NAME)

# SNS Android Platform Application ARN environment variable
SNS_ANDROID_PLATFORM_APP_ARN = os.environ.get('SNS_ANDROID_PLATFORM_APP_ARN', 'arn:aws:sns:us-east-1{ACCOUNT_ID}app/GCM/NeoBellFCMPlatformApp-Android')

# --- Utility Functions ---

def get_user_id(event):
    """Extracts user_id (Cognito sub) from the API Gateway event."""
    try:
        return event['requestContext']['authorizer']['claims']['sub']
    except KeyError:
        logger.error("User ID (sub) not found in event. Ensure Cognito Authorizer is correctly configured.")
        return None

def format_response(status_code, body_data):
    """Formats the API Gateway Lambda Proxy response."""
    if not isinstance(body_data, str):
        body = json.dumps(body_data)
    else:
        body = body_data
        
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
        },
        'body': body
    }

def format_error_response(status_code, error_message, details=None):
    """Formats a consistent error response."""
    error_body = {'error': error_message}
    if details:
        error_body['details'] = details
    return format_response(status_code, error_body)

# --- Endpoint Handlers ---

# == User Profile Management ==
def handle_get_user_me(user_id, event_path_params, event_query_params, event_body):
    """
    Handles GET /users/me
    Retrieves the authenticated user's profile information from DynamoDB.
    """
    logger.info(f"handle_get_user_me called for user_id: {user_id}")
    try:
        # Get user profile from DynamoDB
        response = neobell_users_table.get_item(
            Key={'user_id': user_id}
        )
        item = response.get('Item')
        if not item:
            return format_error_response(404, "User profile not found.")

        # Prepare user profile response
        user_profile = {
            "user_id": item.get("user_id"),
            "email": item.get("email"), 
            "name": item.get("name"),
            "profile_created_app_at": item.get("profile_created_app_at"),
            "profile_last_updated_app": item.get("profile_last_updated_app")
        }
        return format_response(200, user_profile)

    except ClientError as e:
        logger.error(f"DynamoDB ClientError in handle_get_user_me: {e}")
        return format_error_response(500, "Could not retrieve user profile.", str(e.response['Error']['Message']))
    except Exception as e:
        logger.error(f"Unexpected error in handle_get_user_me: {e}")
        return format_error_response(500, "An unexpected error occurred.", str(e))

def handle_put_user_me(user_id, event_path_params, event_query_params, event_body):
    """
    Handles PUT /users/me
    Updates the authenticated user's profile information in both Cognito and DynamoDB.
    Supports updating: name
    """
    logger.info(f"handle_put_user_me called for user_id: {user_id} with body: {event_body}")
    
    # Validate request body
    if not event_body:
        return format_error_response(400, "Request body is required.")

    try:
        parsed_body = json.loads(event_body)
    except json.JSONDecodeError:
        return format_error_response(400, "Invalid JSON in request body.")

    # Prepare update expressions for DynamoDB
    update_expression_parts_dynamo = []
    expression_attribute_values_dynamo = {}
    expression_attribute_names_dynamo = {}
    
    # Prepare attributes to update in Cognito
    attributes_to_update_cognito = []

    # Process 'name' field if provided
    if 'name' in parsed_body:
        name_value = parsed_body['name']
        
        # Validate name (basic validation)
        if not isinstance(name_value, str) or len(name_value.strip()) == 0:
            return format_error_response(400, "Name must be a non-empty string.")
        
        if len(name_value) > 100:  # Reasonable limit
            return format_error_response(400, "Name cannot exceed 100 characters.")
        
        # For DynamoDB update
        update_expression_parts_dynamo.append("#nm = :name_val")
        expression_attribute_names_dynamo["#nm"] = "name"
        expression_attribute_values_dynamo[':name_val'] = name_value.strip()
        
        # For Cognito update
        attributes_to_update_cognito.append({
            'Name': 'name',
            'Value': name_value.strip()
        })

    # Check if any valid fields were provided for update
    if not update_expression_parts_dynamo:
        return format_error_response(400, "No updatable fields provided or fields are not allowed for update.")

    # Add timestamp for last update
    current_timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    update_expression_parts_dynamo.append("profile_last_updated_app = :last_updated_val")
    expression_attribute_values_dynamo[':last_updated_val'] = current_timestamp
    
    # Build the complete update expression for DynamoDB
    update_expression_dynamo = "SET " + ", ".join(update_expression_parts_dynamo)

    # Step 1: Update attributes in Cognito User Pool
    if attributes_to_update_cognito and USER_POOL_ID:
        try:
            cognito_client.admin_update_user_attributes(
                UserPoolId=USER_POOL_ID,
                Username=user_id,  # user_id is the Cognito 'sub'
                UserAttributes=attributes_to_update_cognito
            )
            logger.info(f"Successfully updated attributes in Cognito for user {user_id}")
        except ClientError as e_cognito:
            logger.error(f"Cognito ClientError updating user attributes for {user_id}: {e_cognito}")
            error_code = e_cognito.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e_cognito.response.get('Error', {}).get('Message', 'Unknown error')
            
            # Handle specific Cognito errors
            if error_code == 'UserNotFoundException':
                return format_error_response(404, "User not found in Cognito User Pool.")
            elif error_code == 'InvalidParameterException':
                return format_error_response(400, "Invalid parameters provided for user update.")
            else:
                return format_error_response(500, f"Could not update user attributes in Cognito: {error_message}")
        except Exception as e_cognito:
            logger.error(f"Unexpected error updating Cognito for user {user_id}: {e_cognito}")
            return format_error_response(500, "Unexpected error occurred while updating Cognito.")

    # Step 2: Update DynamoDB profile table
    try:
        # Build the update parameters
        update_params = {
            'Key': {'user_id': user_id},
            'UpdateExpression': update_expression_dynamo,
            'ExpressionAttributeValues': expression_attribute_values_dynamo,
            'ReturnValues': "ALL_NEW"
        }
        
        # Add ExpressionAttributeNames only if we have any
        if expression_attribute_names_dynamo:
            update_params['ExpressionAttributeNames'] = expression_attribute_names_dynamo
        
        # Perform the update
        response_dynamo = neobell_users_table.update_item(**update_params)
        updated_item_dynamo = response_dynamo.get('Attributes', {})
        
        logger.info(f"Successfully updated DynamoDB profile for user {user_id}")

        # Prepare response with updated user profile
        response = {"message": "User profile updated successfully."}
        return format_response(200, response)

    except ClientError as e_dynamo:
        logger.error(f"DynamoDB ClientError in handle_put_user_me for {user_id}: {e_dynamo}")
        error_code = e_dynamo.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e_dynamo.response.get('Error', {}).get('Message', 'Unknown error')
        
        # Handle specific DynamoDB errors
        if error_code == 'ConditionalCheckFailedException':
            return format_error_response(404, "User profile not found or condition failed.")
        elif error_code == 'ValidationException':
            return format_error_response(400, f"Invalid request parameters: {error_message}")
        else:
            return format_error_response(500, f"Could not update user profile in DynamoDB: {error_message}")
    except Exception as e:
        logger.error(f"Unexpected error in handle_put_user_me for {user_id}: {e}")
        return format_error_response(500, "An unexpected error occurred while updating profile.")

def handle_post_user_device_token(user_id, event_path_params, event_query_params, event_body):
    """
    Handles POST /users/device-token
    Registers or updates the mobile device's push notification token for the authenticated user.
    Also creates/updates an SNS platform endpoint for Android devices.
    """
    logger.info(f"handle_post_user_device_token for user_id: {user_id} with body: {event_body}")
    if not event_body:
        return format_error_response(400, "Request body is required.")

    try:
        parsed_body = json.loads(event_body)
    except json.JSONDecodeError:
        return format_error_response(400, "Invalid JSON in request body.")

    push_token = parsed_body.get("push_notification_token")

    if not push_token:
        return format_error_response(400, "Missing 'push_notification_token' in request.")

    # --- SNS Logic ---
    sns_endpoint_arn_for_device = None
    if not SNS_ANDROID_PLATFORM_APP_ARN:
        logger.error("SNS_ANDROID_PLATFORM_APP_ARN environment variable is not set. Cannot create SNS endpoint.")
    else:
        try:
            logger.info(f"Creating/updating SNS platform endpoint for user {user_id}, token: {push_token[:20]}...") # Truncated token log
            endpoint_response = SNS_CLIENT.create_platform_endpoint(
                PlatformApplicationArn=SNS_ANDROID_PLATFORM_APP_ARN,
                Token=push_token,
                CustomUserData=user_id # Associate user_id with endpoint in SNS
            )
            sns_endpoint_arn_for_device = endpoint_response['EndpointArn']
            logger.info(f"SNS Endpoint ARN for Android: {sns_endpoint_arn_for_device} for user {user_id}")
        except ClientError as e:
            logger.error(f"SNS ClientError while creating platform endpoint for user {user_id}: {e}")
            pass # Continue to save token in DynamoDB even if SNS fails
        except Exception as e:
            logger.error(f"Unexpected error during SNS endpoint creation for user {user_id}: {e}")
            pass # Continue

    try:
        update_expression_parts = []
        expression_attribute_values = {
            ":last_updated_val": datetime.datetime.utcnow().isoformat() + "Z"
        }

        # 1. Save the original FCM token
        update_expression_parts.append("device_token = :fcm_token_val")
        expression_attribute_values[":fcm_token_val"] = push_token
        
        # 2. Save the SNS endpoint ARN
        if sns_endpoint_arn_for_device:
            update_expression_parts.append("sns_endpoint_arn = :sns_arn_val")
            expression_attribute_values[":sns_arn_val"] = sns_endpoint_arn_for_device

        update_expression_parts.append("profile_last_updated_app = :last_updated_val")
        update_expression = "SET " + ", ".join(update_expression_parts)
        
        logger.info(f"DynamoDB UpdateItem for user {user_id}: Expression: {update_expression}, Values: {expression_attribute_values}")

        neobell_users_table.update_item(
            Key={'user_id': user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
        
        response_message = {
            "status": "success",
            "message": "Device token registered/updated."
        }
        if sns_endpoint_arn_for_device:
            response_message["sns_endpoint_arn"] = sns_endpoint_arn_for_device
        else:
             response_message["sns_status"] = "SNS endpoint creation for Android failed or was skipped. FCM token still saved."

        return format_response(200, response_message)

    except ClientError as e:
        logger.error(f"DynamoDB ClientError in handle_post_user_device_token: {e}")
        return format_error_response(500, "Could not update device token.", str(e.response['Error']['Message']))
    except Exception as e:
        logger.error(f"Unexpected error in handle_post_user_device_token: {e}")
        return format_error_response(500, "An unexpected error occurred.", str(e))

# == User NFC Tag Management ==
def handle_post_user_nfc_tag(user_id, event_path_params, event_query_params, event_body):
    """
    Handles POST /users/me/nfc-tags
    Registers a new NFC tag for the authenticated user.
    """
    logger.info(f"handle_post_user_nfc_tag for user_id: {user_id} with body: {event_body}")
    if not event_body:
        return format_error_response(400, "Request body is required.")
    try:
        parsed_body = json.loads(event_body)
    except json.JSONDecodeError:
        return format_error_response(400, "Invalid JSON in request body.")

    nfc_id_scanned = parsed_body.get("nfc_id_scanned")
    tag_friendly_name = parsed_body.get("tag_friendly_name")

    if not nfc_id_scanned or not tag_friendly_name:
        return format_error_response(400, "Missing 'nfc_id_scanned' or 'tag_friendly_name'.")
    
    registered_at = datetime.datetime.utcnow().isoformat() + "Z"
    item_to_create = {
        'user_id': user_id, 
        'nfc_id_scanned': nfc_id_scanned, 
        'tag_friendly_name': tag_friendly_name,
        'registered_at': registered_at
    }
    
    try:
        user_nfc_tags_table.put_item(
            Item=item_to_create,
            ConditionExpression="attribute_not_exists(nfc_id_scanned)" 
        )
        return format_response(201, item_to_create)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return format_error_response(409, f"NFC tag '{nfc_id_scanned}' already registered for this user.")
        logger.error(f"DynamoDB ClientError in handle_post_user_nfc_tag: {e}")
        return format_error_response(500, "Could not register NFC tag.", str(e.response['Error']['Message']))
    except Exception as e:
        logger.error(f"Unexpected error in handle_post_user_nfc_tag: {e}")
        return format_error_response(500, "An unexpected error occurred.", str(e))

def handle_get_user_nfc_tags(user_id, event_path_params, event_query_params, event_body):
    logger.info(f"handle_get_user_nfc_tags for user_id: {user_id} with query_params: {event_query_params}")
    
    limit = event_query_params.get('limit')
    if limit:
        try:
            limit = int(limit)
            if limit <= 0: limit = None 
        except ValueError:
            return format_error_response(400, "Invalid 'limit' parameter. Must be an integer.")
    
    last_evaluated_key_str = event_query_params.get('last_evaluated_key')
    exclusive_start_key = None
    if last_evaluated_key_str:
        try:
            exclusive_start_key = json.loads(last_evaluated_key_str)
        except json.JSONDecodeError:
            return format_error_response(400, "Invalid 'last_evaluated_key' format.")

    query_params_ddb = {
        'KeyConditionExpression': boto3.dynamodb.conditions.Key('user_id').eq(user_id)
    }
    if limit:
        query_params_ddb['Limit'] = limit
    if exclusive_start_key:
        query_params_ddb['ExclusiveStartKey'] = exclusive_start_key
        
    try:
        response = user_nfc_tags_table.query(**query_params_ddb)
        items = response.get('Items', [])
        
        filtered_items = [{"nfc_id": item["nfc_id_scanned"], 
                         "tag_friendly_name": item["tag_friendly_name"]} 
                        for item in items]
        
        result = {"tags": filtered_items}
        if 'LastEvaluatedKey' in response:
            result['last_evaluated_key'] = json.dumps(response['LastEvaluatedKey']) 
            
        return format_response(200, result)
        
    except ClientError as e:
        logger.error(f"DynamoDB ClientError in handle_get_user_nfc_tags: {e}")
        return format_error_response(500, "Could not retrieve NFC tags.", str(e.response['Error']['Message']))
    except Exception as e:
        logger.error(f"Unexpected error in handle_get_user_nfc_tags: {e}")
        return format_error_response(500, "An unexpected error occurred.", str(e))

def handle_put_user_nfc_tag_by_id(user_id, event_path_params, event_query_params, event_body):
    nfc_id_scanned = event_path_params.get('nfc_id_scanned')
    logger.info(f"handle_put_user_nfc_tag_by_id for user_id: {user_id}, nfc_id: {nfc_id_scanned}, body: {event_body}")

    if not nfc_id_scanned:
        return format_error_response(400, "Path parameter 'nfc_id_scanned' is missing.") 
    if not event_body:
        return format_error_response(400, "Request body is required.")
    try:
        parsed_body = json.loads(event_body)
    except json.JSONDecodeError:
        return format_error_response(400, "Invalid JSON in request body.")

    tag_friendly_name = parsed_body.get("tag_friendly_name")
    if not tag_friendly_name: 
        return format_error_response(400, "Missing 'tag_friendly_name' in request body.")
    
    updated_at = datetime.datetime.utcnow().isoformat() + "Z"
    try:
        response = user_nfc_tags_table.update_item(
            Key={
                'user_id': user_id,
                'nfc_id_scanned': nfc_id_scanned
            },
            UpdateExpression="SET tag_friendly_name = :name, last_updated_at = :updated_at",
            ConditionExpression="attribute_exists(nfc_id_scanned)", 
            ExpressionAttributeValues={
                ':name': tag_friendly_name,
                ':updated_at': updated_at
            },
            ReturnValues="ALL_NEW" 
        )
        return format_response(200, response.get('Attributes'))

    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return format_error_response(404, f"NFC tag '{nfc_id_scanned}' not found for this user.")
        logger.error(f"DynamoDB ClientError in handle_put_user_nfc_tag_by_id: {e}")
        return format_error_response(500, "Could not update NFC tag.", str(e.response['Error']['Message']))
    except Exception as e:
        logger.error(f"Unexpected error in handle_put_user_nfc_tag_by_id: {e}")
        return format_error_response(500, "An unexpected error occurred.", str(e))

def handle_delete_user_nfc_tag_by_id(user_id, event_path_params, event_query_params, event_body):
    nfc_id_scanned = event_path_params.get('nfc_id_scanned')
    logger.info(f"handle_delete_user_nfc_tag_by_id for user_id: {user_id}, nfc_id: {nfc_id_scanned}")

    if not nfc_id_scanned:
        return format_error_response(400, "Path parameter 'nfc_id_scanned' is missing.")

    try:
        user_nfc_tags_table.delete_item(
            Key={
                'user_id': user_id,
                'nfc_id_scanned': nfc_id_scanned
            },
            ConditionExpression="attribute_exists(nfc_id_scanned)" 
        )
        return format_response(204, "") 

    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            logger.info(f"NFC Tag {nfc_id_scanned} not found for user {user_id} during delete, but returning 204 as per spec.")
            return format_response(204, "") 
        logger.error(f"DynamoDB ClientError in handle_delete_user_nfc_tag_by_id: {e}")
        return format_error_response(500, "Could not delete NFC tag.", str(e.response['Error']['Message']))
    except Exception as e:
        logger.error(f"Unexpected error in handle_delete_user_nfc_tag_by_id: {e}")
        return format_error_response(500, "An unexpected error occurred.", str(e))


# --- Main Lambda Handler ---
def lambda_handler(event, context):
    """
    Main Lambda handler for NeoBell User Handler.
    Routes requests to appropriate endpoint handlers based on HTTP method and path.
    """
    logger.info(f"Received event: {json.dumps(event, indent=2)}")

    # Extract user ID from Cognito authorization
    user_id = get_user_id(event)
    if not user_id:
        return format_error_response(401, "Unauthorized. User identifier missing.")

    # Extract request details
    http_method = event.get('httpMethod')
    path = event.get('path') 
    
    path_params = event.get('pathParameters') if event.get('pathParameters') else {}
    query_params = event.get('queryStringParameters') if event.get('queryStringParameters') else {}
    request_body = event.get('body')
    
    # Route requests to appropriate handlers
    if path == '/users/me' and http_method == 'GET':
        return handle_get_user_me(user_id, path_params, query_params, request_body)
    elif path == '/users/me' and http_method == 'PUT':
        return handle_put_user_me(user_id, path_params, query_params, request_body)
    elif path == '/users/device-token' and http_method == 'POST':
        return handle_post_user_device_token(user_id, path_params, query_params, request_body)
    
    elif path == '/users/me/nfc-tags' and http_method == 'POST':
        return handle_post_user_nfc_tag(user_id, path_params, query_params, request_body)
    elif path == '/users/me/nfc-tags' and http_method == 'GET':
        return handle_get_user_nfc_tags(user_id, path_params, query_params, request_body)
    
    # Handle NFC tag specific operations with regex pattern matching
    nfc_tag_id_path_pattern = r"/users/me/nfc-tags/([^/]+)$" 
    match_nfc_id = re.match(nfc_tag_id_path_pattern, path)

    if match_nfc_id:
        if 'nfc_id_scanned' in path_params: 
            if http_method == 'PUT':
                return handle_put_user_nfc_tag_by_id(user_id, path_params, query_params, request_body)
            elif http_method == 'DELETE':
                return handle_delete_user_nfc_tag_by_id(user_id, path_params, query_params, request_body)
    
    # No matching route found
    logger.warning(f"No route matched for {http_method} {path}")
    return format_error_response(404, "API endpoint not found or method not allowed for this path.")


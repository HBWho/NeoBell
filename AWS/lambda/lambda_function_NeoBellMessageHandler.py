# lambda_function.py for NeoBellMessageHandler
import json
import os
import boto3
from botocore.exceptions import ClientError
from botocore.client import Config
import datetime
import logging
import re
from decimal import Decimal # For handling DynamoDB numbers

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients (outside handler for reuse)
DYNAMODB_CLIENT = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
# S3 client for presigned URLs and delete operations
S3_CLIENT = boto3.client('s3', region_name=os.environ.get('AWS_REGION', 'us-east-1'), config=Config(signature_version='s3v4'))

# DynamoDB Table Names (from environment variables)
VIDEO_MESSAGES_TABLE_NAME = os.environ.get('VIDEO_MESSAGES_TABLE', 'VideoMessages')
DEVICE_USER_LINKS_TABLE_NAME = os.environ.get('DEVICE_USER_LINKS_TABLE', 'DeviceUserLinks')
NEOBELL_DEVICES_TABLE_NAME = os.environ.get('NEOBELL_DEVICES_TABLE', 'NeoBellDevices')
PERMISSIONS_TABLE_NAME = os.environ.get('PERMISSIONS_TABLE', 'Permissions')

# Initialize DynamoDB tables
video_messages_table = DYNAMODB_CLIENT.Table(VIDEO_MESSAGES_TABLE_NAME)
device_user_links_table = DYNAMODB_CLIENT.Table(DEVICE_USER_LINKS_TABLE_NAME)
neobell_devices_table = DYNAMODB_CLIENT.Table(NEOBELL_DEVICES_TABLE_NAME)
permissions_table = DYNAMODB_CLIENT.Table(PERMISSIONS_TABLE_NAME)

# Index names for DynamoDB queries
VIDEO_MESSAGES_MESSAGE_ID_INDEX = "message-id-index"
DEVICE_USER_LINKS_USER_ID_INDEX = 'user-id-sbc-id-index'
SBC_ID_RECORDED_AT_INDEX = 'sbc-id-recorded-at-index'

# S3 Bucket for video messages (from environment variable)
VIDEO_MESSAGES_S3_BUCKET = os.environ.get('VIDEO_MESSAGES_S3_BUCKET', 'your-neobell-video-messages-bucket')

# --- Utility Functions ---

# Helper to convert DynamoDB item to JSON, handling Decimals
class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Decimal types from DynamoDB"""
    def default(self, o):
        if isinstance(o, Decimal):
            if o % 1 == 0:
                return int(o)
            else:
                return float(o)
        return super(DecimalEncoder, self).default(o)

def get_user_id(event):
    """Extracts user_id (Cognito sub) from the API Gateway event"""
    try:
        return event['requestContext']['authorizer']['claims']['sub']
    except KeyError:
        logger.error("User ID (sub) not found in event.")
        return None

def format_response(status_code, body_data):
    """Formats the API Gateway Lambda Proxy response with CORS headers"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
        },
        'body': json.dumps(body_data, cls=DecimalEncoder)
    }

def format_error_response(status_code, error_message, details=None):
    """Formats a consistent error response"""
    error_body = {'error': error_message}
    if details:
        error_body['details'] = details
    return format_response(status_code, error_body)

def get_accessible_sbc_ids(user_id):
    """Gets a list of sbc_ids the user has access to"""
    try:
        response = device_user_links_table.query(
            IndexName=DEVICE_USER_LINKS_USER_ID_INDEX,
            KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(user_id),
            ProjectionExpression='sbc_id' # Only fetch sbc_id to minimize data transfer
        )
        return [item['sbc_id'] for item in response.get('Items', [])]
    except ClientError as e:
        logger.error(f"Error fetching accessible sbc_ids for user {user_id}: {e}")
        return [] # Return empty list on error, access will be denied

def check_user_access_to_sbc(user_id, sbc_id_to_check):
    """Checks if a user has a link to a specific SBC ID"""
    try:
        response = device_user_links_table.get_item(
            Key={'sbc_id': sbc_id_to_check, 'user_id': user_id}
        )
        return 'Item' in response
    except ClientError as e:
        logger.error(f"Error checking access for user {user_id} to sbc {sbc_id_to_check}: {e}")
        return False

def get_device_owner_id(sbc_id):
    """Gets device owner user_id from NeoBellDevices table based on sbc_id"""
    try:
        response = neobell_devices_table.get_item(Key={'sbc_id': sbc_id})
        return response.get('Item', {}).get('owner_user_id')
    except ClientError as e:
        logger.error(f"Error fetching device owner for sbc_id {sbc_id}: {e}")
        return None

def get_visitor_name(owner_user_id, face_tag_id):
    """Gets visitor name from Permissions table based on device owner's user_id and face_tag_id"""
    if not face_tag_id or not owner_user_id:
        return None
    
    try:
        response = permissions_table.get_item(
            Key={'user_id': owner_user_id, 'face_tag_id': face_tag_id}
        )
        return response.get('Item', {}).get('visitor_name')
    except ClientError as e:
        logger.error(f"Error fetching visitor name for face_tag_id {face_tag_id}: {e}")
        return None

def get_device_friendly_name(sbc_id):
    """Gets device friendly name from NeoBellDevices table based on sbc_id"""
    try:
        response = neobell_devices_table.get_item(Key={'sbc_id': sbc_id})
        return response.get('Item', {}).get('device_friendly_name')
    except ClientError as e:
        logger.error(f"Error fetching device friendly name for sbc_id {sbc_id}: {e}")
        return None

# --- Endpoint Handlers ---

def handle_get_messages(requesting_user_id, path_params, query_params, body):
    """
    Handles GET /messages
    Lists video message metadata for the authenticated user.
    """
    logger.info(f"handle_get_messages for user_id: {requesting_user_id}, query: {query_params}")

    # Extract query parameters for filtering
    filter_sbc_id = query_params.get('sbc_id')
    start_date_str = query_params.get('start_date') # Expected YYYY-MM-DD
    end_date_str = query_params.get('end_date')     # Expected YYYY-MM-DD
    is_viewed_str = query_params.get('is_viewed')   # Expected "true" or "false"
    
    # Parse and validate limit parameter
    limit = query_params.get('limit')
    if limit:
        try: 
            limit = int(limit)
            if limit <= 0 or limit > 100:  # Set reasonable bounds
                return format_error_response(400, "Limit must be between 1 and 100.")
        except ValueError: 
            return format_error_response(400, "Invalid 'limit' parameter.")
    else:
        limit = 50  # Default limit
    
    # Parse pagination key
    last_evaluated_key_str = query_params.get('last_evaluated_key')
    exclusive_start_key = None
    if last_evaluated_key_str:
        try: 
            exclusive_start_key = json.loads(last_evaluated_key_str)
        except json.JSONDecodeError: 
            return format_error_response(400, "Invalid 'last_evaluated_key' format.")

    try:
        messages = []
        final_last_evaluated_key = None

        if filter_sbc_id:
            # User wants messages for a specific SBC
            if not check_user_access_to_sbc(requesting_user_id, filter_sbc_id):
                return format_error_response(403, f"Forbidden. User does not have access to device {filter_sbc_id}.")

            # Query using GSI: sbc-id-recorded-at-index
            key_condition = boto3.dynamodb.conditions.Key('sbc_id').eq(filter_sbc_id)
            
            # Add date range filtering if provided
            if start_date_str and end_date_str:
                key_condition &= boto3.dynamodb.conditions.Key('recorded_at').between(
                    start_date_str + "T00:00:00Z", 
                    end_date_str + "T23:59:59.999Z"
                )
            elif start_date_str:
                key_condition &= boto3.dynamodb.conditions.Key('recorded_at').gte(start_date_str + "T00:00:00Z")
            elif end_date_str:
                key_condition &= boto3.dynamodb.conditions.Key('recorded_at').lte(end_date_str + "T23:59:59.999Z")

            query_kwargs = {
                'IndexName': SBC_ID_RECORDED_AT_INDEX,
                'KeyConditionExpression': key_condition,
                'ScanIndexForward': False,  # Sort descending (newest first)
                'Limit': limit
            }
            
            if exclusive_start_key:
                query_kwargs['ExclusiveStartKey'] = exclusive_start_key

            response = video_messages_table.query(**query_kwargs)
            messages.extend(response.get('Items', []))
            final_last_evaluated_key = response.get('LastEvaluatedKey')

        else:
            # User wants messages from all accessible SBCs
            accessible_sbc_ids = get_accessible_sbc_ids(requesting_user_id)
            if not accessible_sbc_ids:
                return format_response(200, {'messages': [], 'last_evaluated_key': None})

            # Query each SBC and merge results
            all_messages = []
            for sbc_id in accessible_sbc_ids:
                key_condition = boto3.dynamodb.conditions.Key('sbc_id').eq(sbc_id)
                
                # Apply date filtering
                if start_date_str and end_date_str:
                    key_condition &= boto3.dynamodb.conditions.Key('recorded_at').between(
                        start_date_str + "T00:00:00Z", 
                        end_date_str + "T23:59:59.999Z"
                    )
                elif start_date_str:
                    key_condition &= boto3.dynamodb.conditions.Key('recorded_at').gte(start_date_str + "T00:00:00Z")
                elif end_date_str:
                    key_condition &= boto3.dynamodb.conditions.Key('recorded_at').lte(end_date_str + "T23:59:59.999Z")

                response = video_messages_table.query(
                    IndexName=SBC_ID_RECORDED_AT_INDEX,
                    KeyConditionExpression=key_condition,
                    ScanIndexForward=False
                )
                all_messages.extend(response.get('Items', []))

            # Sort all messages by recorded_at descending
            all_messages.sort(key=lambda x: x['recorded_at'], reverse=True)
            
            # Apply pagination after sorting
            start_index = 0
            if exclusive_start_key and 'message_id' in exclusive_start_key:
                # Find the starting position based on message_id
                for i, msg in enumerate(all_messages):
                    if msg['message_id'] == exclusive_start_key['message_id']:
                        start_index = i + 1
                        break
            
            end_index = start_index + limit
            messages = all_messages[start_index:end_index]
            
            # Set last_evaluated_key if there are more items
            if end_index < len(all_messages):
                final_last_evaluated_key = {'message_id': messages[-1]['message_id']}

        # Filter by is_viewed if specified
        if is_viewed_str:
            is_viewed_filter = is_viewed_str.lower() == 'true'
            messages = [msg for msg in messages if msg.get('is_viewed', False) == is_viewed_filter]

        # Enrich messages with visitor names and device friendly names
        formatted_messages = []
        for message in messages:
            # Get the device owner to fetch visitor name from their permissions
            device_owner_id = get_device_owner_id(message['sbc_id'])
            
            formatted_message = {
                'message_id': message['message_id'],
                'duration_sec': message.get('duration_sec'),
                'is_viewed': message.get('is_viewed', False),
                'recorded_at': message['recorded_at'],
                'sbc_id': message['sbc_id'],
                'visitor_face_tag_id': message['visitor_face_tag_id'],
                'visitor_name': get_visitor_name(device_owner_id, message['visitor_face_tag_id']),
                'device_friendly_name': get_device_friendly_name(message['sbc_id'])
            }
            formatted_messages.append(formatted_message)

        response_body = {
            'messages': formatted_messages,
            'last_evaluated_key': json.dumps(final_last_evaluated_key) if final_last_evaluated_key else None
        }

        return format_response(200, response_body)

    except ClientError as e:
        logger.error(f"DynamoDB error in handle_get_messages: {e}")
        return format_error_response(500, "Database error occurred.")
    except Exception as e:
        logger.error(f"Unexpected error in handle_get_messages: {e}")
        return format_error_response(500, "An unexpected error occurred.")

def handle_get_message_by_id(requesting_user_id, path_params, query_params, body):
    """
    Handles GET /messages/{message_id}
    Gets metadata for a specific video message.
    """
    message_id = path_params.get('message_id')
    if not message_id:
        return format_error_response(400, "message_id path parameter is missing.")
    logger.info(f"handle_get_message_by_id for user_id: {requesting_user_id}, message_id: {message_id}")

    try:
        # 1. Get message details using GSI on message_id
        response = video_messages_table.query(
            IndexName=VIDEO_MESSAGES_MESSAGE_ID_INDEX,
            KeyConditionExpression=boto3.dynamodb.conditions.Key('message_id').eq(message_id),
            Limit=1
        )
        message_items = response.get('Items', [])
        if not message_items:
            return format_error_response(404, "Message not found.")
        
        sbc_id_of_message = message_items[0].get('sbc_id')

        # 2. Check if the requesting_user_id has access to the sbc_id of the message
        if not sbc_id_of_message or not check_user_access_to_sbc(requesting_user_id, sbc_id_of_message):
            return format_error_response(403, "Forbidden. User does not have access to the device associated with this message.")

        # 3. Get device owner and visitor name
        device_owner_id = get_device_owner_id(sbc_id_of_message)
        visitor_name = get_visitor_name(device_owner_id, message_items[0].get('visitor_face_tag_id'))

        # 4. Format the message item
        message_item = {
            'message_id': message_items[0]['message_id'],
            'sbc_id': sbc_id_of_message,
            'duration_sec': message_items[0].get('duration_sec'),
            'is_viewed': message_items[0].get('is_viewed', False),
            'recorded_at': message_items[0]['recorded_at'],
            'visitor_face_tag_id': message_items[0].get('visitor_face_tag_id'),
            'visitor_name': visitor_name,
            'device_friendly_name': get_device_friendly_name(sbc_id_of_message)
        }
            
        return format_response(200, message_item)

    except ClientError as e:
        logger.error(f"DynamoDB error in handle_get_message_by_id: {e}")
        return format_error_response(500, "Could not retrieve message details.", str(e))
    except Exception as e:
        logger.error(f"Unexpected error in handle_get_message_by_id: {e}")
        return format_error_response(500, "An unexpected error occurred.", str(e))

def handle_post_message_view_url(requesting_user_id, path_params, query_params, request_body_str):
    """
    Handles POST /messages/{message_id}/view-url
    Generates a short-lived S3 pre-signed URL for viewing a video message.
    """
    message_id = path_params.get('message_id')
    if not message_id:
        return format_error_response(400, "message_id path parameter is missing.")
    logger.info(f"handle_post_message_view_url for user_id: {requesting_user_id}, message_id: {message_id}")

    try:
        # 1. Get message details (s3_object_key, sbc_id)
        msg_response = video_messages_table.query(
            IndexName=VIDEO_MESSAGES_MESSAGE_ID_INDEX,
            KeyConditionExpression=boto3.dynamodb.conditions.Key('message_id').eq(message_id),
            ProjectionExpression="s3_object_key, sbc_id, s3_bucket_name", # Ensure s3_bucket_name is stored or use global
            Limit=1
        )
        message_items = msg_response.get('Items', [])
        if not message_items:
            return format_error_response(404, "Message not found.")
        
        message_data = message_items[0]
        s3_object_key = message_data.get('s3_object_key')
        sbc_id_of_message = message_data.get('sbc_id')
        s3_bucket_name = message_data.get('s3_bucket_name', VIDEO_MESSAGES_S3_BUCKET) # Use specific or default

        if not s3_object_key or not sbc_id_of_message:
            return format_error_response(500, "Message record is incomplete (missing S3 key or SBC ID).")

        # 2. Check user access to the device
        if not check_user_access_to_sbc(requesting_user_id, sbc_id_of_message):
            return format_error_response(403, "Forbidden. User does not have access to this message.")

        # 3. Generate pre-signed URL
        expiration_seconds = 300  # 5 minutes
        presigned_url = S3_CLIENT.generate_presigned_url(
            'get_object',
            Params={'Bucket': s3_bucket_name, 'Key': s3_object_key},
            ExpiresIn=expiration_seconds
        )
        
        expires_at = (datetime.datetime.utcnow() + datetime.timedelta(seconds=expiration_seconds)).isoformat() + "Z"
        
        return format_response(200, {
            "message_id": message_id,
            "view_url": presigned_url,
            "expires_at": expires_at
        })

    except ClientError as e:
        logger.error(f"AWS ClientError in handle_post_message_view_url: {e}")
        return format_error_response(500, "Could not generate view URL.", str(e))
    except Exception as e:
        logger.error(f"Unexpected error in handle_post_message_view_url: {e}")
        return format_error_response(500, "An unexpected error occurred.", str(e))

def handle_delete_message_by_id(requesting_user_id, path_params, query_params, body):
    """
    Handles DELETE /messages/{message_id}
    Deletes a video message (metadata from DynamoDB and object from S3).
    """
    message_id = path_params.get('message_id')
    if not message_id:
        return format_error_response(400, "message_id path parameter is missing.")
    logger.info(f"handle_delete_message_by_id for user_id: {requesting_user_id}, message_id: {message_id}")

    try:
        msg_response = video_messages_table.query(
            IndexName=VIDEO_MESSAGES_MESSAGE_ID_INDEX, # GSI where PK is message_id
            KeyConditionExpression=boto3.dynamodb.conditions.Key('message_id').eq(message_id),
            Limit=1
        )
        message_items = msg_response.get('Items', [])
        if not message_items:
            return format_error_response(404, "Message not found.")
        
        message_data = message_items[0]
        s3_object_key = message_data.get('s3_object_key')
        sbc_id_of_message = message_data.get('sbc_id')
        video_message_pk_user_id = message_data.get('user_id')
        video_message_sk_message_id = message_data.get('message_id') 
        s3_bucket_name = message_data.get('s3_bucket_name', VIDEO_MESSAGES_S3_BUCKET)

        if not all([s3_object_key, sbc_id_of_message, video_message_pk_user_id, video_message_sk_message_id]):
             return format_error_response(500, "Message record is incomplete for deletion.")

        # 2. Authorization: Requesting user must be owner of the message OR owner of the device.
        is_message_owner = (requesting_user_id == video_message_pk_user_id)

        if not is_message_owner: # Simplified, refine with actual owner check
            return format_error_response(403, "Forbidden. User does not have permission to delete this message. Only the owner can delete their messages.")

        # 3. Delete S3 object
        try:
            if s3_object_key: # Ensure there's a key to delete
                S3_CLIENT.delete_object(Bucket=s3_bucket_name, Key=s3_object_key)
                logger.info(f"Deleted S3 object: {s3_bucket_name}/{s3_object_key}")
        except ClientError as e:
            logger.error(f"AWS ClientError in handle_delete_message_by_id: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in handle_delete_message_by_id: {e}")

        # 4. Delete DynamoDB item
        # Use the actual Primary Key of the VideoMessages table item
        video_messages_table.delete_item(
            Key={
                'user_id': video_message_pk_user_id, # Hash key of VideoMessages table
                'message_id': video_message_sk_message_id # Sort key of VideoMessages table
            }
        )
        logger.info(f"Deleted message metadata from DynamoDB: PK={video_message_pk_user_id}, SK={video_message_sk_message_id}")

        return format_response(204, {'message': 'Message deleted successfully.'})

    except ClientError as e:
        logger.error(f"AWS ClientError in handle_delete_message_by_id: {e}")
        return format_error_response(500, "Could not delete message.", str(e))
    except Exception as e:
        logger.error(f"Unexpected error in handle_delete_message_by_id: {e}")
        return format_error_response(500, "An unexpected error occurred.", str(e))

def handle_put_message_by_id(requesting_user_id, path_params, query_params, request_body_str):
    """
    Handles PUT /messages/{message_id}
    Updates the is_viewed flag for a specific video message.
    """
    message_id = path_params.get('message_id')
    if not message_id:
        return format_error_response(400, "message_id path parameter is missing.")
    
    logger.info(f"handle_put_message_by_id for user_id: {requesting_user_id}, message_id: {message_id}")

    # Parse request body
    if not request_body_str:
        return format_error_response(400, "Request body is required.")
    
    try:
        request_body = json.loads(request_body_str)
    except json.JSONDecodeError:
        return format_error_response(400, "Invalid JSON in request body.")
    
    # Validate is_viewed field
    if 'is_viewed' not in request_body:
        return format_error_response(400, "Field 'is_viewed' is required in request body.")
    
    is_viewed = request_body.get('is_viewed')
    if not isinstance(is_viewed, bool):
        return format_error_response(400, "Field 'is_viewed' must be a boolean value.")

    try:
        # 1. Get message details using GSI on message_id
        response = video_messages_table.query(
            IndexName=VIDEO_MESSAGES_MESSAGE_ID_INDEX,
            KeyConditionExpression=boto3.dynamodb.conditions.Key('message_id').eq(message_id),
            Limit=1
        )
        message_items = response.get('Items', [])
        if not message_items:
            return format_error_response(404, "Message not found.")
        
        message_data = message_items[0]
        sbc_id_of_message = message_data.get('sbc_id')
        video_message_pk_user_id = message_data.get('user_id')

        if not sbc_id_of_message or not video_message_pk_user_id:
            return format_error_response(500, "Message record is incomplete.")

        # 2. Check if the requesting_user_id has access to the sbc_id of the message
        if not check_user_access_to_sbc(requesting_user_id, sbc_id_of_message):
            return format_error_response(403, "Forbidden. User does not have access to the device associated with this message.")

        # 3. Update the is_viewed flag
        video_messages_table.update_item(
            Key={
                'user_id': video_message_pk_user_id,
                'message_id': message_id
            },
            UpdateExpression="SET is_viewed = :is_viewed",
            ExpressionAttributeValues={
                ':is_viewed': is_viewed
            }
        )

        logger.info(f"Updated is_viewed flag for message {message_id} to {is_viewed}")

        # 4. Return okay message
        response_body = {
            'message': "View status updated successfully.",
        }

        return format_response(200, response_body)

    except ClientError as e:
        logger.error(f"DynamoDB error in handle_put_message_by_id: {e}")
        return format_error_response(500, "Could not update message.", str(e))
    except Exception as e:
        logger.error(f"Unexpected error in handle_put_message_by_id: {e}")
        return format_error_response(500, "An unexpected error occurred.", str(e))

# --- Main Lambda Handler ---
def lambda_handler(event, context):
    """
    Main Lambda handler for NeoBell Message Handler.
    Routes requests to appropriate endpoint handlers based on HTTP method and path.
    """
    logger.info(f"Received event: {json.dumps(event, indent=2)}")
    
    # Extract user ID from Cognito authorization
    requesting_user_id = get_user_id(event)
    if not requesting_user_id:
        return format_error_response(401, "Unauthorized. User identifier missing.")

    # Extract request details
    http_method = event.get('httpMethod')
    path = event.get('path')
    path_params = event.get('pathParameters') if event.get('pathParameters') else {}
    query_params = event.get('queryStringParameters') if event.get('queryStringParameters') else {}
    request_body_str = event.get('body')

    # Route requests to appropriate handlers
    if path == '/messages' and http_method == 'GET':
        return handle_get_messages(requesting_user_id, path_params, query_params, request_body_str)

    # Handle message-specific endpoints with regex pattern matching
    message_id_path_match = re.fullmatch(r"/messages/([^/]+)", path)
    message_id_view_url_path_match = re.fullmatch(r"/messages/([^/]+)/view-url", path)

    if message_id_view_url_path_match:
        if http_method == 'POST':
            return handle_post_message_view_url(requesting_user_id, path_params, query_params, request_body_str)
    elif message_id_path_match:
        if http_method == 'GET':
            return handle_get_message_by_id(requesting_user_id, path_params, query_params, request_body_str)
        elif http_method == 'PUT':
            return handle_put_message_by_id(requesting_user_id, path_params, query_params, request_body_str)
        elif http_method == 'DELETE':
            return handle_delete_message_by_id(requesting_user_id, path_params, query_params, request_body_str)
            
    # No matching route found
    logger.warning(f"No route matched for {http_method} {path}")
    return format_error_response(404, "API endpoint not found or method not allowed for this path.")
# lambda_function.py for NeoBellDeviceHandler
import json
import os
import boto3
from botocore.exceptions import ClientError
import datetime
import logging
import re
from decimal import Decimal

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
DYNAMODB_CLIENT = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

# DynamoDB Table Names (from environment variables)
NEOBELL_DEVICES_TABLE_NAME = os.environ.get('NEOBELL_DEVICES_TABLE', 'NeoBellDevices')
DEVICE_USER_LINKS_TABLE_NAME = os.environ.get('DEVICE_USER_LINKS_TABLE', 'DeviceUserLinks')
NEOBELL_USERS_TABLE_NAME = os.environ.get('NEOBELL_USERS_TABLE', 'NeoBellUsers') # For fetching user details

neobell_devices_table = DYNAMODB_CLIENT.Table(NEOBELL_DEVICES_TABLE_NAME)
device_user_links_table = DYNAMODB_CLIENT.Table(DEVICE_USER_LINKS_TABLE_NAME)
neobell_users_table = DYNAMODB_CLIENT.Table(NEOBELL_USERS_TABLE_NAME)

# Index names (if applicable, adjust based on your actual table definitions)
DEVICE_USER_LINKS_USER_ID_INDEX = "user-id-sbc-id-index" # GSI on DeviceUserLinks table with user_id as PK
NEOBELL_USERS_EMAIL_INDEX = "email-index" # GSI on NeoBellUsers table with email as PK

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            # Converte Decimal para int se não tiver casas decimais, senão para float
            if o % 1 == 0:
                return int(o)
            else:
                return float(o)
        return super(DecimalEncoder, self).default(o)

# --- Utility Functions (can be shared if using layers or a common library) ---
def get_user_id(event):
    try:
        return event['requestContext']['authorizer']['claims']['sub']
    except KeyError:
        logger.error("User ID (sub) not found in event.")
        return None

def format_response(status_code, body_data):
    if not isinstance(body_data, str):
        body = json.dumps(body_data, cls=DecimalEncoder) 
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
    error_body = {'error': error_message}
    if details:
        error_body['details'] = details
    return format_response(status_code, error_body)

def is_user_device_owner(sbc_id, user_id):
    """Checks if the user is the owner of the device."""
    try:
        response = device_user_links_table.get_item(
            Key={'sbc_id': sbc_id, 'user_id': user_id}
        )
        link = response.get('Item')
        return link and link.get('role') == 'Owner'
    except ClientError as e:
        logger.error(f"Error checking device ownership for sbc_id {sbc_id}, user_id {user_id}: {e}")
        return False # Fail safe

# --- Endpoint Handlers ---

def handle_get_devices(requesting_user_id, path_params, query_params, body):
    """
    Handles GET /devices
    Lists all devices linked to the authenticated user.
    """
    logger.info(f"handle_get_devices for user_id: {requesting_user_id}")
    limit = query_params.get('limit')
    if limit:
        try:
            limit = int(limit)
        except ValueError:
            return format_error_response(400, "Invalid 'limit' parameter.")
    
    last_evaluated_key_str = query_params.get('last_evaluated_key')
    exclusive_start_key = None
    if last_evaluated_key_str:
        try:
            exclusive_start_key = json.loads(last_evaluated_key_str)
        except json.JSONDecodeError:
            return format_error_response(400, "Invalid 'last_evaluated_key' format.")

    try:
        # Query DeviceUserLinks using the GSI to find sbc_ids for the user
        link_query_params = {
            'IndexName': DEVICE_USER_LINKS_USER_ID_INDEX,
            'KeyConditionExpression': boto3.dynamodb.conditions.Key('user_id').eq(requesting_user_id)
        }
        if limit: link_query_params['Limit'] = limit # Note: Limit here applies to links, not final devices
        if exclusive_start_key: link_query_params['ExclusiveStartKey'] = exclusive_start_key
        
        link_response = device_user_links_table.query(**link_query_params)
        device_links = link_response.get('Items', [])
        
        devices_details = []
        if device_links:
            # BatchGetItem is efficient for fetching multiple items from NeoBellDevices
            keys_to_fetch = [{'sbc_id': link['sbc_id']} for link in device_links]
            
            batch_get_response = DYNAMODB_CLIENT.batch_get_item(
                RequestItems={
                    NEOBELL_DEVICES_TABLE_NAME: {
                        'Keys': keys_to_fetch,
                        'ConsistentRead': False # Can be true if strong consistency is needed
                    }
                }
            )
            
            sbc_details_map = {
                item['sbc_id']: item for item in batch_get_response.get('Responses', {}).get(NEOBELL_DEVICES_TABLE_NAME, [])
            }

            for link in device_links:
                sbc_id = link['sbc_id']
                device_info = sbc_details_map.get(sbc_id)
                if device_info:
                    devices_details.append({
                        "sbc_id": sbc_id,
                        "device_friendly_name": device_info.get("device_friendly_name"),
                        "role_on_device": link.get("role"),
                        "status": device_info.get("status")
                    })
        
        result = {"items": devices_details}
        if 'LastEvaluatedKey' in link_response: # Pagination based on the links query
            result['last_evaluated_key'] = json.dumps(link_response['LastEvaluatedKey'])
            
        return format_response(200, result)

    except ClientError as e:
        logger.error(f"DynamoDB error in handle_get_devices: {e}")
        return format_error_response(500, "Could not retrieve devices.", str(e))
    except Exception as e:
        logger.error(f"Unexpected error in handle_get_devices: {e}")
        return format_error_response(500, "An unexpected error occurred.", str(e))

def handle_get_device_by_id(requesting_user_id, path_params, query_params, body):
    """
    Handles GET /devices/{sbc_id}
    Gets detailed info about a specific device linked to the user.
    """
    sbc_id = path_params.get('sbc_id')
    if not sbc_id:
        return format_error_response(400, "sbc_id path parameter is missing.")
    logger.info(f"handle_get_device_by_id for user_id: {requesting_user_id}, sbc_id: {sbc_id}")

    try:
        # 1. Check if user is linked to the device
        link_response = device_user_links_table.get_item(
            Key={'sbc_id': sbc_id, 'user_id': requesting_user_id}
        )
        user_link = link_response.get('Item')
        if not user_link:
            return format_error_response(403, "Forbidden. User not linked to this device or device does not exist.")

        # 2. Get device details
        device_response = neobell_devices_table.get_item(Key={'sbc_id': sbc_id})
        device_item = device_response.get('Item')
        if not device_item:
            # This case should be rare if a link exists but device doesn't; implies data inconsistency
            return format_error_response(404, "Device details not found, though a link exists.")

        response_payload = {
            "sbc_id": device_item.get("sbc_id"),
            "owner_user_id": device_item.get("owner_user_id"), # Assuming this is stored on NeoBellDevices
            "device_friendly_name": device_item.get("device_friendly_name"),
            "user_role_on_device": user_link.get("role"),
            "status": device_item.get("status"),
            "firmware_version": device_item.get("firmware_version"),
            "registered_at": device_item.get("registered_at")
        }
        return format_response(200, response_payload)

    except ClientError as e:
        logger.error(f"DynamoDB error in handle_get_device_by_id: {e}")
        return format_error_response(500, "Could not retrieve device details.", str(e))
    except Exception as e:
        logger.error(f"Unexpected error in handle_get_device_by_id: {e}")
        return format_error_response(500, "An unexpected error occurred.", str(e))

def handle_put_device_by_id(requesting_user_id, path_params, query_params, request_body_str):
    """
    Handles PUT /devices/{sbc_id}
    Updates editable details of a device (e.g., friendly name) - by Owner.
    """
    sbc_id = path_params.get('sbc_id')
    if not sbc_id: return format_error_response(400, "sbc_id path parameter is missing.")
    if not request_body_str: return format_error_response(400, "Request body is required.")
    
    logger.info(f"handle_put_device_by_id for user_id: {requesting_user_id}, sbc_id: {sbc_id}")
    try:
        parsed_body = json.loads(request_body_str)
    except json.JSONDecodeError:
        return format_error_response(400, "Invalid JSON in request body.")

    device_friendly_name = parsed_body.get("device_friendly_name")
    if not device_friendly_name: # or is None
        return format_error_response(400, "Missing 'device_friendly_name' in request body.")

    if not is_user_device_owner(sbc_id, requesting_user_id):
        return format_error_response(403, "Forbidden. Only the device owner can update device details.")

    try:
        current_timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        response = neobell_devices_table.update_item(
            Key={'sbc_id': sbc_id},
            UpdateExpression="SET device_friendly_name = :name, last_updated_app_at = :ts",
            ConditionExpression="attribute_exists(sbc_id)", # Ensure device exists
            ExpressionAttributeValues={
                ':name': device_friendly_name,
                ':ts': current_timestamp
            },
            ReturnValues="ALL_NEW"
        )
        updated_attributes = response.get('Attributes', {})
        return format_response(200, {
            "sbc_id": updated_attributes.get("sbc_id"),
            "device_friendly_name": updated_attributes.get("device_friendly_name"),
            "last_updated_app_at": updated_attributes.get("last_updated_app_at")
        })
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return format_error_response(404, "Device not found.")
        logger.error(f"DynamoDB error in handle_put_device_by_id: {e}")
        return format_error_response(500, "Could not update device.", str(e))
    except Exception as e:
        logger.error(f"Unexpected error in handle_put_device_by_id: {e}")
        return format_error_response(500, "An unexpected error occurred.", str(e))

def handle_delete_device_by_id(requesting_user_id, path_params, query_params, body):
    """
    Handles DELETE /devices/{sbc_id}
    De-registers/unlinks a device - by Owner.
    Deletes from DeviceUserLinks (all users for this sbc_id) and NeoBellDevices.
    """
    sbc_id = path_params.get('sbc_id')
    if not sbc_id: return format_error_response(400, "sbc_id path parameter is missing.")
    logger.info(f"handle_delete_device_by_id for user_id: {requesting_user_id}, sbc_id: {sbc_id}")

    if not is_user_device_owner(sbc_id, requesting_user_id):
        return format_error_response(403, "Forbidden. Only the device owner can delete the device.")

    try:
        # 1. Find all users linked to this device to delete links
        link_query_response = device_user_links_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('sbc_id').eq(sbc_id)
        )
        links_to_delete = link_query_response.get('Items', [])

        # 2. Delete all links from DeviceUserLinks
        if links_to_delete:
            with device_user_links_table.batch_writer() as batch:
                for link in links_to_delete:
                    batch.delete_item(Key={'sbc_id': link['sbc_id'], 'user_id': link['user_id']})
            logger.info(f"Deleted {len(links_to_delete)} links from DeviceUserLinks for sbc_id: {sbc_id}")
        
        # 3. Delete the device from NeoBellDevices
        neobell_devices_table.delete_item(
            Key={'sbc_id': sbc_id},
            ConditionExpression="attribute_exists(sbc_id)" # Optional: ensure it exists
        )
        logger.info(f"Deleted device {sbc_id} from NeoBellDevices.")
        
        return format_response(204, "")

    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            # Could be from the neobell_devices_table.delete_item if device didn't exist
            logger.warning(f"ConditionalCheckFailedException during device deletion for {sbc_id} - possibly already deleted.")
            return format_response(204, "") # Still return 204 as deletion is idempotent
        logger.error(f"DynamoDB error in handle_delete_device_by_id: {e}")
        return format_error_response(500, "Could not delete device.", str(e))
    except Exception as e:
        logger.error(f"Unexpected error in handle_delete_device_by_id: {e}")
        return format_error_response(500, "An unexpected error occurred.", str(e))

def handle_get_device_users(requesting_user_id, path_params, query_params, body):
    """
    Handles GET /devices/{sbc_id}/users
    Lists users linked to a specific device - for an Owner to view.
    """
    sbc_id = path_params.get('sbc_id')
    if not sbc_id: return format_error_response(400, "sbc_id path parameter is missing.")
    logger.info(f"handle_get_device_users for user_id: {requesting_user_id}, sbc_id: {sbc_id}")

    if not is_user_device_owner(sbc_id, requesting_user_id):
        return format_error_response(403, "Forbidden. Only device owners can view linked users.")

    limit = query_params.get('limit')
    if limit:
        try: limit = int(limit)
        except ValueError: return format_error_response(400, "Invalid 'limit' parameter.")
    
    last_evaluated_key_str = query_params.get('last_evaluated_key')
    exclusive_start_key = None
    if last_evaluated_key_str:
        try: exclusive_start_key = json.loads(last_evaluated_key_str)
        except json.JSONDecodeError: return format_error_response(400, "Invalid 'last_evaluated_key' format.")

    try:
        link_query_params = {
            'KeyConditionExpression': boto3.dynamodb.conditions.Key('sbc_id').eq(sbc_id)
        }
        if limit: link_query_params['Limit'] = limit
        if exclusive_start_key: link_query_params['ExclusiveStartKey'] = exclusive_start_key
        
        link_response = device_user_links_table.query(**link_query_params)
        device_links = link_response.get('Items', [])
        
        user_details_list = []
        if device_links:
            # Fetch user details (name, email) from NeoBellUsers table for each linked user_id
            user_ids_to_fetch = [{'user_id': link['user_id']} for link in device_links]
            if user_ids_to_fetch:
                user_batch_get_response = DYNAMODB_CLIENT.batch_get_item(
                    RequestItems={
                        NEOBELL_USERS_TABLE_NAME: {
                            'Keys': user_ids_to_fetch,
                            'ProjectionExpression': 'user_id, email, #nm', # Use #nm for 'name'
                            'ExpressionAttributeNames': {'#nm': 'name'} 
                        }
                    }
                )
                user_info_map = {
                    item['user_id']: item for item in user_batch_get_response.get('Responses', {}).get(NEOBELL_USERS_TABLE_NAME, [])
                }

                for link in device_links:
                    user_info = user_info_map.get(link['user_id'], {})
                    user_details_list.append({
                        "user_id": link['user_id'],
                        "email": user_info.get("email"),
                        "name": user_info.get("name"),
                        "role": link.get("role"),
                        "access_granted_at": link.get("access_granted_at")
                    })
        
        result = {"items": user_details_list}
        if 'LastEvaluatedKey' in link_response:
            result['last_evaluated_key'] = json.dumps(link_response['LastEvaluatedKey'])
            
        return format_response(200, result)

    except ClientError as e:
        logger.error(f"DynamoDB error in handle_get_device_users: {e}")
        return format_error_response(500, "Could not retrieve device users.", str(e))
    except Exception as e:
        logger.error(f"Unexpected error in handle_get_device_users: {e}")
        return format_error_response(500, "An unexpected error occurred.", str(e))

def handle_post_device_user(requesting_user_id, path_params, query_params, request_body_str):
    """
    Handles POST /devices/{sbc_id}/users
    Allows an Owner to invite/add another registered user to a device (e.g., as "Resident").
    """
    sbc_id = path_params.get('sbc_id')
    if not sbc_id: return format_error_response(400, "sbc_id path parameter is missing.")
    if not request_body_str: return format_error_response(400, "Request body is required.")
    
    logger.info(f"handle_post_device_user for user_id: {requesting_user_id}, sbc_id: {sbc_id}")
    try:
        parsed_body = json.loads(request_body_str)
    except json.JSONDecodeError:
        return format_error_response(400, "Invalid JSON in request body.")

    email_of_invitee = parsed_body.get("email_of_invitee")
    role_to_assign = parsed_body.get("role", "Resident") # Default to Resident

    if not email_of_invitee:
        return format_error_response(400, "Missing 'email_of_invitee' in request body.")
    if role_to_assign not in ["Resident", "Owner"]: # Or other defined roles
        return format_error_response(400, "Invalid 'role'. Must be 'Resident' or 'Owner'.")
    if role_to_assign == "Owner" and not is_user_device_owner(sbc_id, requesting_user_id):
        # Only an existing owner can assign a new owner role (business rule, can be adjusted)
        return format_error_response(403, "Forbidden. Only existing owners can assign other owners.")
    if not is_user_device_owner(sbc_id, requesting_user_id):
        return format_error_response(403, "Forbidden. Only device owners can add users to the device.")

    try:
        # 1. Find user_id of the invitee by email from NeoBellUsers table (using GSI)
        user_query_response = neobell_users_table.query(
            IndexName=NEOBELL_USERS_EMAIL_INDEX,
            KeyConditionExpression=boto3.dynamodb.conditions.Key('email').eq(email_of_invitee),
            Limit=1
        )
        invitee_users = user_query_response.get('Items', [])
        if not invitee_users:
            return format_error_response(404, f"User with email '{email_of_invitee}' not found in NeoBellUsers.")
        
        invitee_user_id = invitee_users[0]['user_id']

        if invitee_user_id == requesting_user_id:
            return format_error_response(400, "Cannot add yourself to the device again with this endpoint.")
            
        # 2. Check if user is already linked to prevent duplicates or update role if intended
        existing_link_response = device_user_links_table.get_item(
            Key={'sbc_id': sbc_id, 'user_id': invitee_user_id}
        )
        if existing_link_response.get('Item'):
            return format_error_response(409, f"User '{email_of_invitee}' is already linked to this device.")

        # 3. Create the link in DeviceUserLinks
        current_timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        link_item = {
            'sbc_id': sbc_id,
            'user_id': invitee_user_id,
            'role': role_to_assign,
            'access_granted_at': current_timestamp,
            'granted_by': requesting_user_id # Optional: track who granted access
        }
        device_user_links_table.put_item(Item=link_item)
        
        response_payload = {
            "sbc_id": sbc_id,
            "user_id": invitee_user_id,
            "email_of_invitee": email_of_invitee, # From input, not necessarily from DDB at this point
            "role": role_to_assign,
            "access_granted_at": current_timestamp
        }
        return format_response(201, response_payload) # 201 Created

    except ClientError as e:
        logger.error(f"DynamoDB error in handle_post_device_user: {e}")
        return format_error_response(500, "Could not add user to device.", str(e))
    except Exception as e:
        logger.error(f"Unexpected error in handle_post_device_user: {e}")
        return format_error_response(500, "An unexpected error occurred.", str(e))

def handle_delete_device_user(requesting_user_id, path_params, query_params, body):
    """
    Handles DELETE /devices/{sbc_id}/users/{user_id_to_remove}
    Allows Owner to remove a user, or user to remove themselves (if Resident).
    """
    sbc_id = path_params.get('sbc_id')
    user_id_to_remove = path_params.get('user_id_to_remove')

    if not sbc_id or not user_id_to_remove:
        return format_error_response(400, "Missing 'sbc_id' or 'user_id_to_remove' path parameter.")
    logger.info(f"handle_delete_device_user: requester={requesting_user_id}, sbc_id={sbc_id}, user_to_remove={user_id_to_remove}")

    try:
        # 1. Get the link to check roles and existence
        link_to_remove_response = device_user_links_table.get_item(
            Key={'sbc_id': sbc_id, 'user_id': user_id_to_remove}
        )
        link_to_remove = link_to_remove_response.get('Item')

        if not link_to_remove:
            return format_error_response(404, "User link to device not found.")

        role_of_user_to_remove = link_to_remove.get('role')

        # 2. Authorization check
        is_requester_owner = is_user_device_owner(sbc_id, requesting_user_id)
        is_self_removal = (requesting_user_id == user_id_to_remove)

        can_delete = False
        if is_requester_owner:
            if role_of_user_to_remove == 'Owner' and user_id_to_remove == requesting_user_id:
                # Owner trying to remove themselves. Check if they are the sole owner.
                # This logic can be complex (e.g., prevent orphaning device).
                # For now, let's query all owners.
                owner_links_response = device_user_links_table.query(
                    KeyConditionExpression=boto3.dynamodb.conditions.Key('sbc_id').eq(sbc_id),
                    FilterExpression=boto3.dynamodb.conditions.Attr('role').eq('Owner')
                )
                if len(owner_links_response.get('Items', [])) <= 1:
                    return format_error_response(403, "Forbidden. Cannot remove the sole owner of the device.")
                can_delete = True # Owner removing themselves, but not the last one
            else: # Owner removing another user (Resident or another Owner if multiple owners exist)
                can_delete = True
        elif is_self_removal and role_of_user_to_remove == 'Resident':
            can_delete = True # Resident removing themselves

        if not can_delete:
            return format_error_response(403, "Forbidden. You do not have permission to remove this user from the device.")

        # 3. Delete the link
        device_user_links_table.delete_item(
            Key={'sbc_id': sbc_id, 'user_id': user_id_to_remove}
        )
        return format_response(204, "")

    except ClientError as e:
        logger.error(f"DynamoDB error in handle_delete_device_user: {e}")
        return format_error_response(500, "Could not remove user from device.", str(e))
    except Exception as e:
        logger.error(f"Unexpected error in handle_delete_device_user: {e}")
        return format_error_response(500, "An unexpected error occurred.", str(e))

# --- Main Lambda Handler ---
def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event, indent=2)}")
    requesting_user_id = get_user_id(event)
    if not requesting_user_id:
        return format_error_response(401, "Unauthorized. User identifier missing.")

    http_method = event.get('httpMethod')
    path = event.get('path')
    path_params = event.get('pathParameters') if event.get('pathParameters') else {}
    query_params = event.get('queryStringParameters') if event.get('queryStringParameters') else {}
    request_body_str = event.get('body')

    # Routing
    if path == '/devices' and http_method == 'GET':
        return handle_get_devices(requesting_user_id, path_params, query_params, request_body_str)

    # Regex for /devices/{sbc_id}
    sbc_id_path_match = re.fullmatch(r"/devices/([^/]+)", path)
    if sbc_id_path_match:
        # sbc_id = sbc_id_path_match.group(1) # path_params['sbc_id'] should have this
        if http_method == 'GET':
            return handle_get_device_by_id(requesting_user_id, path_params, query_params, request_body_str)
        elif http_method == 'PUT':
            return handle_put_device_by_id(requesting_user_id, path_params, query_params, request_body_str)
        elif http_method == 'DELETE':
            return handle_delete_device_by_id(requesting_user_id, path_params, query_params, request_body_str)

    # Regex for /devices/{sbc_id}/users
    sbc_id_users_path_match = re.fullmatch(r"/devices/([^/]+)/users", path)
    if sbc_id_users_path_match:
        # sbc_id = sbc_id_users_path_match.group(1)
        if http_method == 'GET':
            return handle_get_device_users(requesting_user_id, path_params, query_params, request_body_str)
        elif http_method == 'POST':
            return handle_post_device_user(requesting_user_id, path_params, query_params, request_body_str)
            
    # Regex for /devices/{sbc_id}/users/{user_id_to_remove}
    sbc_id_user_id_path_match = re.fullmatch(r"/devices/([^/]+)/users/([^/]+)", path)
    if sbc_id_user_id_path_match:
        # sbc_id = sbc_id_user_id_path_match.group(1)
        # user_id_to_remove = sbc_id_user_id_path_match.group(2)
        if http_method == 'DELETE':
            return handle_delete_device_user(requesting_user_id, path_params, query_params, request_body_str)

    logger.warning(f"No route matched for {http_method} {path}")
    return format_error_response(404, "API endpoint not found or method not allowed for this path.")
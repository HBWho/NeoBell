# lambda_function.py for NeoBellVisitorHandler
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
# S3 client for presigned URLs
S3_CLIENT = boto3.client('s3', region_name=os.environ.get('AWS_REGION', 'us-east-1'), config=Config(signature_version='s3v4'))

# DynamoDB Table Names (from environment variables)
PERMISSIONS_TABLE_NAME = os.environ.get('PERMISSIONS_TABLE', 'Permissions')
permissions_table = DYNAMODB_CLIENT.Table(PERMISSIONS_TABLE_NAME)

# --- Utility Functions ---

# Helper to convert DynamoDB item to JSON, handling Decimals
class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Decimal types from DynamoDB"""
    def default(self, o):
        if isinstance(o, Decimal):
            if o % 1 == 0: # if it's an integer
                return int(o)
            else: # if it's a float
                return float(o)
        return super(DecimalEncoder, self).default(o)

def get_user_id(event):
    """Extracts user_id (Cognito sub) from the API Gateway event"""
    try:
        return event['requestContext']['authorizer']['claims']['sub']
    except KeyError:
        logger.error("User ID (sub) not found in event. Check Cognito Authorizer configuration.")
        return None

def format_response(status_code, body_data):
    """Formats the Lambda Proxy response for API Gateway"""
    if not isinstance(body_data, str):
        body = json.dumps(body_data, cls=DecimalEncoder) # Use DecimalEncoder
    else:
        body = body_data
        
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE' # Be explicit about methods
        },
        'body': body
    }

def format_error_response(status_code, error_message, details=None):
    """Formats a consistent error response"""
    error_body = {'error': error_message}
    if details:
        error_body['details'] = details
    return format_response(status_code, error_body)

# --- Endpoint Handlers ---

def handle_get_visitors(requesting_user_id, path_params, query_params, body):
    """
    Handles GET /visitors
    Lists known visitors (tagged faces) and their permissions for the authenticated user.
    """
    logger.info(f"handle_get_visitors for user_id: {requesting_user_id}, query: {query_params}")
    
    # Parse limit parameter
    limit = query_params.get('limit')
    if limit:
        try:
            limit = int(limit)
            if limit <= 0: limit = None 
        except ValueError:
            return format_error_response(400, "Invalid 'limit' parameter. Must be an integer.")
    
    # Parse pagination key
    last_evaluated_key_str = query_params.get('last_evaluated_key')
    exclusive_start_key = None
    if last_evaluated_key_str:
        try:
            # The key for Permissions table is {'user_id': '...', 'face_tag_id': '...'}
            exclusive_start_key = json.loads(last_evaluated_key_str)
        except json.JSONDecodeError:
            return format_error_response(400, "Invalid 'last_evaluated_key' format.")

    try:
        # Build query arguments
        query_args = {
            'KeyConditionExpression': boto3.dynamodb.conditions.Key('user_id').eq(requesting_user_id)
        }
        
        if limit: query_args['Limit'] = limit
        if exclusive_start_key: query_args['ExclusiveStartKey'] = exclusive_start_key
        
        response = permissions_table.query(**query_args)
        items = response.get('Items', [])
        
        result = {"items": items}
        if 'LastEvaluatedKey' in response:
            result['last_evaluated_key'] = json.dumps(response['LastEvaluatedKey'])
            
        return format_response(200, result)

    except ClientError as e:
        logger.error(f"DynamoDB error in handle_get_visitors: {e}")
        return format_error_response(500, "Could not retrieve visitors.", str(e))
    except Exception as e:
        logger.error(f"Unexpected error in handle_get_visitors: {e}")
        return format_error_response(500, "An unexpected error occurred.", str(e))

def handle_put_visitor_by_id(requesting_user_id, path_params, query_params, request_body_str):
    """
    Handles PUT /visitors/{face_tag_id}
    Updates the name or permissions for a known visitor/face tagged by the user.
    Assumes face_tag_id is created when a face is recognized and the user tags it for the first time (not covered here).
    This endpoint updates an existing tag.
    """
    face_tag_id = path_params.get('face_tag_id')
    if not face_tag_id:
        return format_error_response(400, "Missing 'face_tag_id' path parameter.")
    if not request_body_str:
        return format_error_response(400, "Request body is required.")
        
    logger.info(f"handle_put_visitor_by_id for user_id: {requesting_user_id}, face_tag_id: {face_tag_id}")
    try:
        parsed_body = json.loads(request_body_str)
    except json.JSONDecodeError:
        return format_error_response(400, "Invalid JSON in request body.")

    visitor_name = parsed_body.get("visitor_name")
    permission_level = parsed_body.get("permission_level")

    if not visitor_name and not permission_level:
        return format_error_response(400, "At least 'visitor_name' or 'permission_level' must be provided for update.")

    # Validate permission_level if provided
    valid_permission_levels = ["Allowed", "Denied"] # Define as needed
    if permission_level and permission_level not in valid_permission_levels:
        return format_error_response(400, f"Invalid permission level. Allowed values: {', '.join(valid_permission_levels)}")

    # Build update expression dynamically
    update_expression_parts = []
    expression_attribute_values = {}
    expression_attribute_names = {} 

    if visitor_name is not None: # Allows empty string if intention is to clear the name
        update_expression_parts.append("#vn = :visitor_name_val")
        expression_attribute_names["#vn"] = "visitor_name"
        expression_attribute_values[":visitor_name_val"] = visitor_name
    
    if permission_level:
        update_expression_parts.append("#pl = :permission_level_val")
        expression_attribute_names["#pl"] = "permission_level"
        expression_attribute_values[":permission_level_val"] = permission_level
    
    if not update_expression_parts: # Should have been caught above, but as safety
        return format_error_response(400, "No valid fields provided for update.")

    # Add timestamp for last update
    current_timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    update_expression_parts.append("#lua = :last_updated_at_val")
    expression_attribute_names["#lua"] = "last_updated_at"
    expression_attribute_values[":last_updated_at_val"] = current_timestamp
    
    update_expression = "SET " + ", ".join(update_expression_parts)
    try:
        response = permissions_table.update_item(
            Key={'user_id': requesting_user_id, 'face_tag_id': face_tag_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ConditionExpression="attribute_exists(face_tag_id)",
            ReturnValues="ALL_NEW" 
        )
        return format_response(200, response.get('Attributes'))
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return format_error_response(404, "Visitor/face tag not found for update.")
        logger.error(f"DynamoDB error in handle_put_visitor_by_id: {e}")
        return format_error_response(500, "Could not update visitor/face tag.", str(e))
    except Exception as e:
        logger.error(f"Unexpected error in handle_put_visitor_by_id: {e}")
        return format_error_response(500, "An unexpected error occurred.", str(e))

def handle_delete_visitor_by_id(requesting_user_id, path_params, query_params, body):
    """
    Handles DELETE /visitors/{face_tag_id}
    Removes a tagged visitor and their permissions.
    """
    face_tag_id = path_params.get('face_tag_id')
    if not face_tag_id:
        return format_error_response(400, "Missing 'face_tag_id' path parameter.")
    logger.info(f"handle_delete_visitor_by_id for user_id: {requesting_user_id}, face_tag_id: {face_tag_id}")

    try:
        permissions_table.delete_item(
            Key={'user_id': requesting_user_id, 'face_tag_id': face_tag_id},
            ConditionExpression="attribute_exists(face_tag_id)" # Optional: ensures it exists to return 404 if not
        )
        return format_response(204, "") # No content for successful DELETE
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            # Item didn't exist, which is acceptable for DELETE (idempotent) or can be a 404.
            # The API spec specifies 204.
            logger.info(f"Visitor/face tag {face_tag_id} not found for user {requesting_user_id} during delete, returning 204.")
            return format_response(204, "") 
        logger.error(f"DynamoDB error in handle_delete_visitor_by_id: {e}")
        return format_error_response(500, "Could not delete visitor/face tag.", str(e))
    except Exception as e:
        logger.error(f"Unexpected error in handle_delete_visitor_by_id: {e}")
        return format_error_response(500, "An unexpected error occurred.", str(e))

def handle_get_visitor_by_id(requesting_user_id, path_params, query_params, body):
    """
    Handles GET /visitors/{face_tag_id}/image-url
    Returns specific visitor data with S3 presigned image URL.
    """
    face_tag_id = path_params.get('face_tag_id')
    if not face_tag_id:
        return format_error_response(400, "Missing 'face_tag_id' path parameter.")
    
    logger.info(f"handle_get_visitor_by_id for user_id: {requesting_user_id}, face_tag_id: {face_tag_id}")

    try:
        # 1. Fetch visitor data from Permissions table
        response = permissions_table.get_item(
            Key={'user_id': requesting_user_id, 'face_tag_id': face_tag_id}
        )
        
        if 'Item' not in response:
            return format_error_response(404, "Visitor not found.")
        
        visitor_data = response['Item']
        image_s3_bucket = visitor_data.get('image_s3_bucket')
        image_s3_key = visitor_data.get('image_s3_key')
        
        # 2. Generate presigned URL if S3 image data exists
        image_url = None
        image_expires_at = None
        
        if image_s3_bucket and image_s3_key:
            try:
                expiration_seconds = 300  # 5 minutes
                image_url = S3_CLIENT.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': image_s3_bucket, 'Key': image_s3_key},
                    ExpiresIn=expiration_seconds
                )
                image_expires_at = (datetime.datetime.utcnow() + datetime.timedelta(seconds=expiration_seconds)).isoformat() + "Z"
                logger.info(f"Image URL generated for face_tag_id {face_tag_id}")
            except ClientError as e:
                logger.error(f"Error generating presigned URL for image: {e}")
                # Continue without image URL if there's an error
        
        # 3. Prepare response with visitor data and image URL
        result = dict(visitor_data)  # Copy visitor data
        if image_url:
            result['image_url'] = image_url
            result['image_expires_at'] = image_expires_at
        
        return format_response(200, result)

    except ClientError as e:
        logger.error(f"DynamoDB error in handle_get_visitor_by_id: {e}")
        return format_error_response(500, "Could not retrieve visitor data.", str(e))
    except Exception as e:
        logger.error(f"Unexpected error in handle_get_visitor_by_id: {e}")
        return format_error_response(500, "An unexpected error occurred.", str(e))

# --- Main Lambda Handler ---
def lambda_handler(event, context):
    """
    Main Lambda handler for NeoBell Visitor Handler.
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

    # --- Routing Logic ---
    if path == '/visitors' and http_method == 'GET':
        return handle_get_visitors(requesting_user_id, path_params, query_params, request_body_str)
    
    # Regex for /visitors/{face_tag_id}/image-url
    visitor_image_url_path_match = re.fullmatch(r"/visitors/([^/]+)/image-url", path)
    # Regex for /visitors/{face_tag_id}
    visitor_id_path_match = re.fullmatch(r"/visitors/([^/]+)", path)
    
    if visitor_image_url_path_match:
        if http_method == 'POST':
            return handle_get_visitor_by_id(requesting_user_id, path_params, query_params, request_body_str)
    elif visitor_id_path_match:
        if http_method == 'PUT':
            return handle_put_visitor_by_id(requesting_user_id, path_params, query_params, request_body_str)
        elif http_method == 'DELETE':
            return handle_delete_visitor_by_id(requesting_user_id, path_params, query_params, request_body_str)
            
    # No matching route found
    logger.warning(f"No route matched for {http_method} {path}")
    return format_error_response(404, "API endpoint not found or method not allowed for this path.")


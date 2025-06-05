# lambda_function.py for NeoBellDeliveryHandler
import json
import os
import boto3
from botocore.exceptions import ClientError
import datetime
import logging
import re
import uuid # For generating order_id if needed
from decimal import Decimal # For handling DynamoDB numbers

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients (outside handler for reuse)
DYNAMODB_CLIENT = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

# DynamoDB Table Names (from environment variables)
EXPECTED_DELIVERIES_TABLE_NAME = os.environ.get('EXPECTED_DELIVERIES_TABLE', 'ExpectedDeliveries')
expected_deliveries_table = DYNAMODB_CLIENT.Table(EXPECTED_DELIVERIES_TABLE_NAME)

# Index Names (adjust according to your actual table definition)
# Example: GSI to query by user_id and status
USER_ID_STATUS_INDEX_NAME = os.environ.get('USER_ID_STATUS_INDEX', 'user-id-status-index') # PK: user_id, SK: status

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
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
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

def handle_get_deliveries(requesting_user_id, path_params, query_params, body):
    """
    Handles GET /deliveries
    Lists deliveries for the authenticated user, with optional filters.
    """
    logger.info(f"handle_get_deliveries for user_id: {requesting_user_id}, query: {query_params}")

    # Extract filter parameters
    filter_status = query_params.get('status')
    
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
            exclusive_start_key = json.loads(last_evaluated_key_str)
        except json.JSONDecodeError:
            return format_error_response(400, "Invalid 'last_evaluated_key' format.")

    try:
        # Build query arguments
        query_args = {
            'KeyConditionExpression': boto3.dynamodb.conditions.Key('user_id').eq(requesting_user_id)
        }
        
        # If there's status filter and a GSI configured for it:
        if filter_status:
            # This example assumes the GSI UserIdStatusIndex has PK=user_id and SK=status
            # If the SK is composite (e.g., status#timestamp), the query needs to be adjusted.
            query_args['IndexName'] = USER_ID_STATUS_INDEX_NAME
            query_args['KeyConditionExpression'] &= boto3.dynamodb.conditions.Key('status').eq(filter_status)
            # If the GSI doesn't have 'status' as part of the key, use FilterExpression
            # query_args['FilterExpression'] = boto3.dynamodb.conditions.Attr('status').eq(filter_status)

        if limit: query_args['Limit'] = limit
        if exclusive_start_key: query_args['ExclusiveStartKey'] = exclusive_start_key
        
        # Set ScanIndexForward to False to get most recent first,
        # if the sort key (SK) of the table/GSI is time-based (e.g., added_at).
        # query_args['ScanIndexForward'] = False 

        response = expected_deliveries_table.query(**query_args)
        items = response.get('Items', [])
        
        result = {"items": items}
        if 'LastEvaluatedKey' in response:
            result['last_evaluated_key'] = json.dumps(response['LastEvaluatedKey'])
            
        return format_response(200, result)

    except ClientError as e:
        logger.error(f"DynamoDB error in handle_get_deliveries: {e}")
        return format_error_response(500, "Could not retrieve deliveries.", str(e))
    except Exception as e:
        logger.error(f"Unexpected error in handle_get_deliveries: {e}")
        return format_error_response(500, "An unexpected error occurred.", str(e))

def handle_post_deliveries(requesting_user_id, path_params, query_params, request_body_str):
    """
    Handles POST /deliveries
    Allows a user to manually add an expected delivery.
    """
    logger.info(f"handle_post_deliveries for user_id: {requesting_user_id}, body: {request_body_str}")
    if not request_body_str:
        return format_error_response(400, "Request body is required.")
    try:
        parsed_body = json.loads(request_body_str)
    except json.JSONDecodeError:
        return format_error_response(400, "Invalid JSON in request body.")

    # Required fields
    order_id = parsed_body.get("order_id")
    if not order_id:
        return format_error_response(400, "'order_id' is required.")

    item_description = parsed_body.get("item_description")
    if not item_description:
        return format_error_response(400, "'item_description' is required.")

    # Optional fields
    tracking_number = parsed_body.get("tracking_number")
    carrier = parsed_body.get("carrier")
    expected_date_str = parsed_body.get("expected_date") # Format YYYY-MM-DD

    # Validate expected_date if provided
    if expected_date_str:
        try:
            datetime.datetime.strptime(expected_date_str, '%Y-%m-%d')
        except ValueError:
            return format_error_response(400, "Invalid 'expected_date' format. Use YYYY-MM-DD.")

    # Set default values
    added_at = datetime.datetime.utcnow().isoformat() + "Z"
    status = "pending" # Initial status

    # Build delivery item
    delivery_item = {
        'user_id': requesting_user_id,
        'order_id': order_id,
        'item_description': item_description,
        'status': status,
        'added_at': added_at,
    }
    if tracking_number: delivery_item['tracking_number'] = tracking_number
    if carrier: delivery_item['carrier'] = carrier
    if expected_date_str: delivery_item['expected_date'] = expected_date_str
    # Other fields like sbc_id_received_at, received_at_timestamp will be added later

    try:
        expected_deliveries_table.put_item(
            Item=delivery_item,
            ConditionExpression="attribute_not_exists(order_id)" # Prevent overwrite if order_id already exists for this user
        )
        return format_response(201, delivery_item)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return format_error_response(409, f"Delivery with order_id '{order_id}' already exists for this user.")
        logger.error(f"DynamoDB error in handle_post_deliveries: {e}")
        return format_error_response(500, "Could not register delivery.", str(e))
    except Exception as e:
        logger.error(f"Unexpected error in handle_post_deliveries: {e}")
        return format_error_response(500, "An unexpected error occurred.", str(e))

def handle_get_delivery_by_id(requesting_user_id, path_params, query_params, body):
    """
    Handles GET /deliveries/{order_id}
    Gets details of a specific delivery.
    """
    order_id = path_params.get('order_id')
    if not order_id:
        return format_error_response(400, "Missing 'order_id' path parameter.")
    logger.info(f"handle_get_delivery_by_id for user_id: {requesting_user_id}, order_id: {order_id}")

    try:
        response = expected_deliveries_table.get_item(
            Key={'user_id': requesting_user_id, 'order_id': order_id}
        )
        item = response.get('Item')
        if not item:
            return format_error_response(404, "Delivery not found.")
        return format_response(200, item)
    except ClientError as e:
        logger.error(f"DynamoDB error in handle_get_delivery_by_id: {e}")
        return format_error_response(500, "Could not retrieve delivery details.", str(e))
    except Exception as e:
        logger.error(f"Unexpected error in handle_get_delivery_by_id: {e}")
        return format_error_response(500, "An unexpected error occurred.", str(e))

def handle_put_delivery_by_id(requesting_user_id, path_params, query_params, request_body_str):
    """
    Handles PUT /deliveries/{order_id}
    Updates delivery details.
    """
    order_id = path_params.get('order_id')
    if not order_id:
        return format_error_response(400, "Missing 'order_id' path parameter.")
    if not request_body_str:
        return format_error_response(400, "Request body is required.")
        
    logger.info(f"handle_put_delivery_by_id for user_id: {requesting_user_id}, order_id: {order_id}")
    try:
        parsed_body = json.loads(request_body_str)
    except json.JSONDecodeError:
        return format_error_response(400, "Invalid JSON in request body.")

    # Build UpdateExpression dynamically
    update_expression_parts = []
    expression_attribute_values = {}
    expression_attribute_names = {} # For attributes that are reserved words

    # Fields that can be updated by the user
    allowed_to_update = {
        "item_description": "item_description_val",
        "tracking_number": "tracking_number_val",
        "carrier": "carrier_val",
        "expected_date": "expected_date_val",
        "status": "status_val" # Status can be updated by user (e.g., "retrieved_by_user")
                               # or by system (e.g., "in_box1" - via another Lambda/process)
    }
    
    # Validate status if provided
    if "status" in parsed_body:
        valid_statuses = ["pending", "in_box1", "secured_in_box2", "retrieved_by_user"] # Add others as needed
        if parsed_body["status"] not in valid_statuses:
            return format_error_response(400, f"Invalid status. Allowed values: {', '.join(valid_statuses)}")
    
    # Validate expected_date if provided
    if "expected_date" in parsed_body and parsed_body["expected_date"] is not None:
        try:
            datetime.datetime.strptime(parsed_body["expected_date"], '%Y-%m-%d')
        except ValueError:
            return format_error_response(400, "Invalid 'expected_date' format. Use YYYY-MM-DD.")

    # Build update expression for allowed fields
    for key, value_placeholder in allowed_to_update.items():
        if key in parsed_body:
            # Use ExpressionAttributeNames for attribute names that may be reserved words
            # e.g., '#k' for 'key'. In this case, the names are simple.
            attr_name_placeholder = f"#{key[:3]}" # e.g., #sta for status
            update_expression_parts.append(f"{attr_name_placeholder} = :{value_placeholder}")
            expression_attribute_names[attr_name_placeholder] = key
            expression_attribute_values[f":{value_placeholder}"] = parsed_body[key]

    if not update_expression_parts:
        return format_error_response(400, "No fields provided for update or fields not allowed.")

    # Add timestamp for last update
    current_timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    update_expression_parts.append("#lua = :last_updated_at_val")
    expression_attribute_names["#lua"] = "last_updated_app_at" # Field to track app updates
    expression_attribute_values[":last_updated_at_val"] = current_timestamp
    
    update_expression = "SET " + ", ".join(update_expression_parts)

    try:
        response = expected_deliveries_table.update_item(
            Key={'user_id': requesting_user_id, 'order_id': order_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ConditionExpression="attribute_exists(order_id)", # Ensure delivery exists
            ReturnValues="ALL_NEW" 
        )
        return format_response(200, response.get('Attributes'))
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return format_error_response(404, "Delivery not found for update.")
        logger.error(f"DynamoDB error in handle_put_delivery_by_id: {e}")
        return format_error_response(500, "Could not update delivery.", str(e))
    except Exception as e:
        logger.error(f"Unexpected error in handle_put_delivery_by_id: {e}")
        return format_error_response(500, "An unexpected error occurred.", str(e))

def handle_delete_delivery_by_id(requesting_user_id, path_params, query_params, body):
    """
    Handles DELETE /deliveries/{order_id}
    Deletes a manually added expected delivery.
    """
    order_id = path_params.get('order_id')
    if not order_id:
        return format_error_response(400, "Missing 'order_id' path parameter.")
    logger.info(f"handle_delete_delivery_by_id for user_id: {requesting_user_id}, order_id: {order_id}")

    try:
        expected_deliveries_table.delete_item(
            Key={'user_id': requesting_user_id, 'order_id': order_id},
            ConditionExpression="attribute_exists(order_id)" # Optional: ensure it exists to return 404 if not
        )
        return format_response(204, "") # No content for successful DELETE
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            # Item didn't exist, which is acceptable for DELETE (idempotent) or can be a 404.
            # The API spec specifies 204.
            logger.info(f"Delivery {order_id} not found for user {requesting_user_id} during delete, returning 204.")
            return format_response(204, "") 
        logger.error(f"DynamoDB error in handle_delete_delivery_by_id: {e}")
        return format_error_response(500, "Could not delete delivery.", str(e))
    except Exception as e:
        logger.error(f"Unexpected error in handle_delete_delivery_by_id: {e}")
        return format_error_response(500, "An unexpected error occurred.", str(e))

# --- Main Lambda Handler ---
def lambda_handler(event, context):
    """
    Main Lambda handler for NeoBell Delivery Handler.
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
    if path == '/deliveries' and http_method == 'GET':
        return handle_get_deliveries(requesting_user_id, path_params, query_params, request_body_str)
    elif path == '/deliveries' and http_method == 'POST':
        return handle_post_deliveries(requesting_user_id, path_params, query_params, request_body_str)
    
    # Regex for /deliveries/{order_id}
    # API Gateway should provide 'order_id' in path_params if the resource is defined as /deliveries/{order_id}
    order_id_path_match = re.fullmatch(r"/deliveries/([^/]+)", path)
    if order_id_path_match:
        # order_id_from_path = order_id_path_match.group(1) # path_params['order_id'] should have this
        if http_method == 'GET':
            return handle_get_delivery_by_id(requesting_user_id, path_params, query_params, request_body_str)
        elif http_method == 'PUT':
            return handle_put_delivery_by_id(requesting_user_id, path_params, query_params, request_body_str)
        elif http_method == 'DELETE':
            return handle_delete_delivery_by_id(requesting_user_id, path_params, query_params, request_body_str)
            
    # No matching route found
    logger.warning(f"No route matched for {http_method} {path}")
    return format_error_response(404, "API endpoint not found or method not allowed for this path.")


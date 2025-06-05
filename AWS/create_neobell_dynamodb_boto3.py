import boto3
import time # Used by waiters implicitly

# --- Configuration ---
AWS_REGION = "us-east-1"
PROJECT_TAG_VALUE = "NeoBell"

# Initialize DynamoDB client
dynamodb_client = boto3.client("dynamodb", region_name=AWS_REGION)

def create_dynamodb_table(table_name, attribute_definitions, key_schema, gsis=None, purpose_tag_value=""):
    """
    Creates a DynamoDB table with on-demand billing, standard tags, and waits for it to become active.
    GSIs are passed as a list of GSI definitions.
    """
    tags = [
        {"Key": "Project", "Value": PROJECT_TAG_VALUE},
        {"Key": "Purpose", "Value": purpose_tag_value},
        {"Key": "Name", "Value": table_name},
    ]

    table_args = {
        "TableName": table_name,
        "AttributeDefinitions": attribute_definitions,
        "KeySchema": key_schema,
        "BillingMode": "PAY_PER_REQUEST",
        "Tags": tags,
    }

    if gsis:
        table_args["GlobalSecondaryIndexes"] = gsis

    try:
        print(f"Creating table: {table_name} in region {AWS_REGION}...")
        dynamodb_client.create_table(**table_args)
        
        # Wait for the table to be created
        print(f"Waiting for table {table_name} to become active...")
        waiter = dynamodb_client.get_waiter("table_exists")
        waiter.wait(TableName=table_name, WaiterConfig={"Delay": 10, "MaxAttempts": 30})
        print(f"Table {table_name} created successfully.")
        return True
    except dynamodb_client.exceptions.ResourceInUseException:
        print(f"Table {table_name} already exists. Skipping creation.")
        return True # Table exists, consider it a success for subsequent operations like enabling PITR.
    except Exception as e:
        print(f"Error creating table {table_name}: {e}")
        return False

def enable_pitr(table_name):
    """
    Enables Point-in-Time Recovery for the specified table.
    """
    try:
        print(f"Enabling PITR for table: {table_name}...")
        dynamodb_client.update_continuous_backups(
            TableName=table_name,
            PointInTimeRecoverySpecification={"PointInTimeRecoveryEnabled": True},
        )
        print(f"PITR enabled successfully for table {table_name}.")
    except Exception as e:
        print(f"Error enabling PITR for table {table_name}: {e}")

def enable_ttl(table_name, ttl_attribute_name="ttl_timestamp"):
    """
    Enables Time To Live (TTL) on the specified attribute for the table.
    The attribute should store a Unix epoch timestamp (number).
    """
    try:
        print(f"Enabling TTL on attribute '{ttl_attribute_name}' for table: {table_name}...")
        dynamodb_client.update_time_to_live(
            TableName=table_name,
            TimeToLiveSpecification={
                "Enabled": True,
                "AttributeName": ttl_attribute_name,
            },
        )
        print(f"TTL enabled successfully for table {table_name} on attribute '{ttl_attribute_name}'.")
    except Exception as e:
        print(f"Error enabling TTL for table {table_name}: {e}")

# --- Table Definitions ---

# 1. NeoBellUsers
table_name_users = "NeoBellUsers"
attributes_users = [
    {"AttributeName": "user_id", "AttributeType": "S"},
    {"AttributeName": "email", "AttributeType": "S"}, # Atributo para GSI
]
key_schema_users = [{"AttributeName": "user_id", "KeyType": "HASH"}]
gsi_users = [
    {
        "IndexName": "email-index", # Nome padronizado
        "KeySchema": [{"AttributeName": "email", "KeyType": "HASH"}],
        "Projection": {"ProjectionType": "ALL"},
    }
]

# 2. NeoBellDevices
table_name_devices = "NeoBellDevices"
attributes_devices = [{"AttributeName": "sbc_id", "AttributeType": "S"}]
key_schema_devices = [{"AttributeName": "sbc_id", "KeyType": "HASH"}]
# Sem GSIs para NeoBellDevices

# 3. DeviceUserLinks
table_name_device_user_links = "DeviceUserLinks"
attributes_device_user_links = [
    {"AttributeName": "sbc_id", "AttributeType": "S"},
    {"AttributeName": "user_id", "AttributeType": "S"},
]
key_schema_device_user_links = [
    {"AttributeName": "sbc_id", "KeyType": "HASH"},
    {"AttributeName": "user_id", "KeyType": "RANGE"},
]
gsi_device_user_links = [
    {
        "IndexName": "user-id-sbc-id-index", # Nome padronizado
        "KeySchema": [
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "sbc_id", "KeyType": "RANGE"},
        ],
        "Projection": {"ProjectionType": "ALL"},
    }
]

# 4. UserNFCTags
table_name_user_nfc_tags = "UserNFCTags"
attributes_user_nfc_tags = [
    {"AttributeName": "user_id", "AttributeType": "S"},
    {"AttributeName": "nfc_id_scanned", "AttributeType": "S"},
]
key_schema_user_nfc_tags = [
    {"AttributeName": "user_id", "KeyType": "HASH"},
    {"AttributeName": "nfc_id_scanned", "KeyType": "RANGE"},
]


# 5. Permissions
table_name_permissions = "Permissions"
attributes_permissions = [
    {"AttributeName": "user_id", "AttributeType": "S"},
    {"AttributeName": "face_tag_id", "AttributeType": "S"},
]
key_schema_permissions = [
    {"AttributeName": "user_id", "KeyType": "HASH"},
    {"AttributeName": "face_tag_id", "KeyType": "RANGE"},
]
# Sem GSIs para Permissions

# 6. VideoMessages
table_name_video_messages = "VideoMessages"
attributes_video_messages = [
    {"AttributeName": "user_id", "AttributeType": "S"},
    {"AttributeName": "message_id", "AttributeType": "S"}, # Usado na PK da tabela e PK do GSI message-id-index
    {"AttributeName": "sbc_id", "AttributeType": "S"},    # Usado na PK do GSI sbc-id-recorded-at-index
    {"AttributeName": "recorded_at", "AttributeType": "S"},# Usado na SK do GSI sbc-id-recorded-at-index
]
key_schema_video_messages = [
    {"AttributeName": "user_id", "KeyType": "HASH"},
    {"AttributeName": "message_id", "KeyType": "RANGE"},
]
gsi_video_messages = [
    {
        "IndexName": "sbc-id-recorded-at-index", # Nome padronizado
        "KeySchema": [
            {"AttributeName": "sbc_id", "KeyType": "HASH"},
            {"AttributeName": "recorded_at", "KeyType": "RANGE"},
        ],
        "Projection": {"ProjectionType": "ALL"},
    },
    {
        "IndexName": "message-id-index", # Nome padronizado
        "KeySchema": [
            {"AttributeName": "message_id", "KeyType": "HASH"}
        ],
        "Projection": { # ATUALIZADO para INCLUDE
            "ProjectionType": "INCLUDE",
            "NonKeyAttributes": [
                "user_id",
                "sbc_id",
                "s3_object_key",
                "s3_bucket_name"
                # Adicione outros atributos frequentemente necessários aqui
            ]
        }
    }
]

# 7. ExpectedDeliveries
table_name_expected_deliveries = "ExpectedDeliveries"
attributes_expected_deliveries = [
    {"AttributeName": "user_id", "AttributeType": "S"},
    {"AttributeName": "order_id", "AttributeType": "S"},
    {"AttributeName": "status", "AttributeType": "S"},
    {"AttributeName": "tracking_number", "AttributeType": "S"},
]
key_schema_expected_deliveries = [
    {"AttributeName": "user_id", "KeyType": "HASH"},
    {"AttributeName": "order_id", "KeyType": "RANGE"},
]
gsis_expected_deliveries = [
    {
        "IndexName": "user-id-status-index", # Nome padronizado
        "KeySchema": [
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "status", "KeyType": "RANGE"},
        ],
        "Projection": {"ProjectionType": "ALL"},
    },
    {
        "IndexName": "tracking-number-index", # Nome padronizado
        "KeySchema": [{"AttributeName": "tracking_number", "KeyType": "HASH"}],
        "Projection": {"ProjectionType": "ALL"},
    },
]

# 8. EventLogs
table_name_event_logs = "EventLogs"
attributes_event_logs = [
    {"AttributeName": "log_source_id", "AttributeType": "S"},
    {"AttributeName": "timestamp_uuid", "AttributeType": "S"},
]
key_schema_event_logs = [
    {"AttributeName": "log_source_id", "KeyType": "HASH"},
    {"AttributeName": "timestamp_uuid", "KeyType": "RANGE"},
]
ttl_attribute_event_logs = "ttl_timestamp"

# --- Main script execution ---
def main():
    print("Starting Project NeoBell DynamoDB table setup...\n")

    # Create NeoBellUsers table
    if create_dynamodb_table(table_name_users, attributes_users, key_schema_users, gsi_users, "UserData"):
        enable_pitr(table_name_users)
    print("-" * 30)

    # Create NeoBellDevices table
    if create_dynamodb_table(table_name_devices, attributes_devices, key_schema_devices, None, "DeviceRegistry"):
        enable_pitr(table_name_devices)
    print("-" * 30)

    # Create DeviceUserLinks table
    if create_dynamodb_table(table_name_device_user_links, attributes_device_user_links, key_schema_device_user_links, gsi_device_user_links, "UserDeviceAccessControl"):
        enable_pitr(table_name_device_user_links)
    print("-" * 30)

    # Create UserNFCTags table
    if create_dynamodb_table(table_name_user_nfc_tags, attributes_user_nfc_tags, key_schema_user_nfc_tags, None, "UserNFCManagement"):
        enable_pitr(table_name_user_nfc_tags)
    print("-" * 30)

    # Create Permissions table
    if create_dynamodb_table(table_name_permissions, attributes_permissions, key_schema_permissions, None, "VisitorPermissions"):
        enable_pitr(table_name_permissions)
    print("-" * 30)

    # Create VideoMessages table
    if create_dynamodb_table(table_name_video_messages, attributes_video_messages, key_schema_video_messages, gsi_video_messages, "VideoMessageMetadata"):
        enable_pitr(table_name_video_messages)
    print("-" * 30)

    # Create ExpectedDeliveries table
    if create_dynamodb_table(table_name_expected_deliveries, attributes_expected_deliveries, key_schema_expected_deliveries, gsis_expected_deliveries, "OrderTracking"):
        enable_pitr(table_name_expected_deliveries)
    print("-" * 30)

    # Create EventLogs table
    if create_dynamodb_table(table_name_event_logs, attributes_event_logs, key_schema_event_logs, None, "ApplicationLogs"):
        enable_pitr(table_name_event_logs)
        # Important: For TTL to work, items in EventLogs must have a 'ttl_timestamp' attribute
        # which is a Number representing an epoch timestamp.
        enable_ttl(table_name_event_logs, ttl_attribute_event_logs)
    print("-" * 30)

    print("\nAll requested DynamoDB table setups have been processed.")

if __name__ == "__main__":
    # Ensure your AWS credentials and region are configured (e.g., via AWS CLI, environment variables, or IAM roles)
    # For example, you might need to run `aws configure` if you haven't already.
    main()
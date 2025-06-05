import boto3
import botocore

# !! IMPORTANT: Replace with your actual bucket name !!
# Remember S3 bucket names must be globally unique.
BUCKET_NAME = "neobell-videomessages-hbwho"
REGION = "us-east-1" # For S3, for CreateBucketConfiguration, use None for us-east-1 if not specifying other regions

s3_client = boto3.client('s3', region_name=REGION)
s3_resource = boto3.resource('s3', region_name=REGION)

def create_s3_bucket_neobell():
    """
    Creates and configures an S3 bucket for Project NeoBell video messages.
    """
    try:
        print(f"Attempting to create bucket: {BUCKET_NAME} in region {REGION}...")

        # For us-east-1, CreateBucketConfiguration should not be specified
        # unless you are creating in a different region, but the client is configured for us-east-1.
        # If the client is already configured for us-east-1, no LocationConstraint is needed.
        if REGION == "us-east-1":
            s3_client.create_bucket(Bucket=BUCKET_NAME)
        else:
            s3_client.create_bucket(
                Bucket=BUCKET_NAME,
                CreateBucketConfiguration={'LocationConstraint': REGION}
            )
        print(f"Bucket '{BUCKET_NAME}' created successfully.")

        # 1. Block Public Access
        print(f"Configuring Block Public Access for bucket '{BUCKET_NAME}'...")
        s3_client.put_public_access_block(
            Bucket=BUCKET_NAME,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )
        print("Block Public Access configured.")

        # 2. Enable Bucket Versioning
        print(f"Enabling Bucket Versioning for bucket '{BUCKET_NAME}'...")
        bucket_versioning = s3_resource.BucketVersioning(BUCKET_NAME)
        bucket_versioning.enable()
        print("Bucket Versioning enabled.")

        # 3. Set Default Encryption (SSE-S3)
        print(f"Enabling Default Server-Side Encryption (SSE-S3) for bucket '{BUCKET_NAME}'...")
        s3_client.put_bucket_encryption(
            Bucket=BUCKET_NAME,
            ServerSideEncryptionConfiguration={
                'Rules': [
                    {
                        'ApplyServerSideEncryptionByDefault': {
                            'SSEAlgorithm': 'AES256' # SSE-S3
                        },
                        # For SSE-S3, BucketKeyEnabled should be false or not specified.
                        # If you need to explicitly set it due to API requirements, set to False.
                        # 'BucketKeyEnabled': False # Explicitly false for SSE-S3
                    }
                ]
            }
        )
        print("Default Server-Side Encryption (SSE-S3) enabled.")

        # 4. Apply Tags
        print(f"Applying tags to bucket '{BUCKET_NAME}'...")
        s3_client.put_bucket_tagging(
            Bucket=BUCKET_NAME,
            Tagging={
                'TagSet': [
                    {'Key': 'Project', 'Value': 'NeoBell'},
                    {'Key': 'Purpose', 'Value': 'VideoMessages'},
                    {'Key': 'Name', 'Value': BUCKET_NAME}
                ]
            }
        )
        print("Tags applied.")

        # 5. Object Ownership - ACLs Disabled (Modern Default)
        # For new buckets, ACLs are disabled by default if 'ObjectOwnership' is 'BucketOwnerEnforced'.
        # This ensures the bucket owner owns all objects and ACLs cannot override policies.
        print(f"Setting Object Ownership to 'BucketOwnerEnforced' (ACLs disabled) for bucket '{BUCKET_NAME}'...")
        s3_client.put_bucket_ownership_controls(
            Bucket=BUCKET_NAME,
            OwnershipControls={
                'Rules': [
                    {
                        'ObjectOwnership': 'BucketOwnerEnforced'
                    }
                ]
            }
        )
        print("Object Ownership set to BucketOwnerEnforced (ACLs effectively disabled).")


        print(f"\nConfiguration for bucket '{BUCKET_NAME}' complete.")

    except botocore.exceptions.ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == 'BucketAlreadyOwnedByYou':
            print(f"Bucket '{BUCKET_NAME}' already exists and you own it. Will attempt to apply configurations.")
            # If bucket exists, you might want to call the configuration functions directly
            # For simplicity, this script focuses on creation and initial setup.
            # Re-running configurations on an existing bucket is generally safe.
            # You'd just call the put_* methods without create_bucket.
            # (This example doesn't fully implement idempotent configuration updates, but focuses on creation)
            # For this script, we will print the message and stop. To make it idempotent,
            # you would need to call the individual configuration steps.
            print("Consider running configuration steps individually if needed.")

        elif error_code == 'BucketAlreadyExists':
            print(f"Error: Bucket name '{BUCKET_NAME}' already exists and is owned by someone else. Bucket names must be globally unique.")
        elif error_code == 'InvalidBucketName':
            print(f"Error: Bucket name '{BUCKET_NAME}' is invalid. Please check S3 naming rules.")
        else:
            print(f"An unexpected error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    # Before running, ensure your AWS credentials and region are configured
    # (e.g., via AWS CLI 'aws configure', environment variables, or IAM roles).
    # If BUCKET_NAME needs to be dynamic, you might pass it as an argument.
    print("Reminder: S3 bucket names must be globally unique.")
    print(f"This script will attempt to create and configure a bucket named: {BUCKET_NAME}\n")
    create_s3_bucket_neobell() # Uncomment to run
    print("# To run this script: ")
    print("# 1. Ensure Boto3 is installed (`pip install boto3`).")
    print("# 2. Configure your AWS credentials and default region.")
    print("# 3. Uncomment the line `create_s3_bucket_neobell()`")
    print("# 4. Run the script `python your_script_name.py`")

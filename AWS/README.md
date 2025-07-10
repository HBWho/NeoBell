# AWS Cloud Infrastructure - NeoBell Project

This directory contains all **Infrastructure as Code (IaC)** scripts and backend code for the NeoBell Project, implemented primarily in Python with Boto3.

> **⚠️ Important Note:** While all the infrastructure creation scripts are provided here, many component configurations and Lambda function codes have been modified through the AWS Console after initial deployment. These manual modifications are not reflected in the code repository and would need to be manually replicated when setting up a new environment.

## 📋 Overview

The `AWS/` folder is the core of NeoBell's cloud infrastructure, providing:

- **Automated provisioning scripts** for all necessary AWS services
- **Specialized Lambda functions** for business logic
- **IoT Core configurations** for SBC device communication
- **SNS notification scripts** for push notifications
- **Mock data** for development environment

## 🏗️ Solution Architecture

NeoBell's backend uses a **serverless and event-driven architecture** on AWS:

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   App Flutter   │◄──►│ API Gateway  │◄──►│ Lambda Functions│──────┐
└─────────────────┘    └──────────────┘    └─────────────────┘      │
                              │                       │             │
                              ▼                       ▼             │
                    ┌──────────────┐         ┌─────────────────┐    │
                    │   Cognito    │         │   DynamoDB      │    │
                    │ (Auth/Users) │         │  (Data Store)   │    │
                    └──────────────┘         └─────────────────┘    │
                                                                    │
        ┌─────────────────┐    ┌──────────────┐                     │
        │   SBC Device    │◄──►│  IoT Core    │                     │
        │ (Radxa Rock 5C) │    │   (MQTT)     │                     │
        └─────────────────┘    └──────────────┘                     │
                                      │                             ▼
                                      ▼             ┌─────────────────────────┐
                             ┌─────────────────┐    │           S3            │
                             │ Lambda Functions│───►│    (Video Storage)      │
                             └─────────────────┘    └─────────────────────────┘
                                      │
                                      ▼
                              ┌──────────────┐
                              │     SNS      │
                              │(Notification)│
                              └──────────────┘
```

## 📁 Directory Structure

### Provisioning Scripts (Root)

| Script | Purpose | Execution Order |
|--------|---------|-----------------|
| [`create_neobell_iam_boto3.py`](create_neobell_iam_boto3.py) | Creates necessary IAM roles | 1st |
| [`create_neobell_vpc_boto3.py`](create_neobell_vpc_boto3.py) | Configures VPC and networking | 2nd |
| [`create_neobell_dynamodb_boto3.py`](create_neobell_dynamodb_boto3.py) | Creates DynamoDB tables | 3rd |
| [`create_neobell_s3_boto3.py`](create_neobell_s3_boto3.py) | Configures S3 bucket | 4th |
| [`create_neobell_cognito_boto3.py`](create_neobell_cognito_boto3.py) | Cognito setup | 5th |
| [`create_neobell_iot_boto3.py`](create_neobell_iot_boto3.py) | Configures IoT Core | 6th |
| [`create_neobell_gateway_boto3.py`](create_neobell_gateway_boto3.py) | Creates API Gateway | 7th (after Lambdas) |

### Subdirectories

| Directory | Description |
|-----------|-------------|
| [`lambda/`](lambda/) | Domain-specialized Lambda functions |
| [`iot/`](iot/) | IoT Core configuration and rules scripts |
| [`sns notification/`](sns%20notification/) | SNS configuration for push notifications |
| [`mock/`](mock/) | Scripts to populate tables with test data |

## 🚀 Setup Guide

### Prerequisites

1. **AWS CLI** configured with proper credentials
   ```bash
   aws configure
   ```

2. **Python 3.8+** and **Boto3** installed
   ```bash
   pip install boto3
   ```

3. **IAM Permissions** to create AWS resources (AdministratorAccess recommended for initial setup)

### Initial Configuration

**⚠️ IMPORTANT:** Before executing any script, replace the placeholders:

- `ACCOUNT_ID` with your real AWS Account ID
- `YOUR_COGNITO_USER_POOL_ARN` with correct ARNs
- S3 bucket names must be globally unique

### Recommended Execution Order

1. **IAM Roles** (Security foundation)
   ```bash
   python create_neobell_iam_boto3.py
   ```

2. **VPC and Networking** (Network infrastructure)
   ```bash
   python create_neobell_vpc_boto3.py
   ```

3. **DynamoDB** (Data storage)
   ```bash
   python create_neobell_dynamodb_boto3.py
   ```

4. **S3** (File storage)
   ```bash
   python create_neobell_s3_boto3.py
   ```

5. **Cognito** (Authentication)
   ```bash
   python create_neobell_cognito_boto3.py
   ```

6. **Lambda Functions**
   ```bash
   cd lambda/
   # Execute Lambda deployment scripts
   ```

7. **IoT Core** (Device communication)
   ```bash
   python create_neobell_iot_boto3.py
   ```

8. **API Gateway** (Public API)
   ```bash
   python create_neobell_gateway_boto3.py
   ```

9. **SNS Notifications**

10. **Mock Data** (Development environment)
    ```bash
    cd mock/
    # Execute data population scripts
    ```

## 🔧 AWS Services Used

### Core Services

- **Amazon Cognito**: Identity management and authentication
- **Amazon API Gateway**: Public REST API for the mobile application
- **AWS Lambda**: Serverless business logic
- **Amazon DynamoDB**: NoSQL database for structured data
- **Amazon S3**: Video and image storage

### IoT & Messaging

- **AWS IoT Core**: MQTT communication with SBC devices
- **Amazon SNS**: Push notifications for mobile devices

### Security & Networking

- **Amazon VPC**: Isolated virtual private network
- **AWS IAM**: Access control and permissions

## 📊 DynamoDB Tables

| Table | Purpose | Keys |
|-------|---------|------|
| `NeoBellUsers` | User data | PK: user_id |
| `NeoBellDevices` | SBC device registry | PK: sbc_id |
| `DeviceUserLinks` | User-device linking | PK: sbc_id, SK: user_id |
| `UserNFCTags` | User NFC tags | PK: user_id, SK: nfc_id_scanned |
| `Permissions` | Visitor permissions | PK: user_id, SK: face_tag_id |
| `VideoMessages` | Video metadata | PK: user_id, SK: message_id |
| `ExpectedDeliveries` | Expected deliveries | PK: user_id, SK: order_id |
| `EventLogs` | Event logs (TTL) | PK: log_source_id, SK: timestamp_uuid |

## 🔐 Security

- **Isolated VPC**: Lambdas run in private subnets
- **VPC Endpoints**: Secure access to S3 and DynamoDB
- **Encryption**: SSE-S3 enabled by default
- **IAM Roles**: Principle of least privilege
- **Cognito JWT**: Secure authentication tokens

## 🛠️ Maintenance

### Monitoring

- CloudWatch Logs enabled for all Lambdas
- CloudWatch Metrics for performance
- DynamoDB Point-in-Time Recovery enabled

### Backup

- DynamoDB: Automatic backup via PITR
- S3: Versioning enabled
- EventLogs: TTL configured for automatic cleanup

## 🔗 Integrations

### Flutter Application
- Authentication via AWS Amplify (Cognito)
- HTTP calls to API Gateway
- Push notification reception via SNS

### SBC Device
- MQTT communication via IoT Core
- Video upload to S3 via presigned URLs
- Local facial recognition and QR code processing

## 📚 Additional Resources

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [API Gateway Best Practices](https://docs.aws.amazon.com/apigateway/latest/developerguide/best-practices.html)
- [DynamoDB Design Patterns](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [IoT Core MQTT](https://docs.aws.amazon.com/iot/latest/developerguide/mqtt.html)

## ⚠️ Important Notes

1. **Costs**: Monitor usage to avoid unexpected charges
2. **Region**: All resources are created in `us-east-1`
3. **Unique names**: S3 buckets must have globally unique names
4. **Credentials**: Never commit credentials in code
5. **Cleanup**: Use cleanup scripts when dismantling the environment

---

**Note**: This AWS is designed to work in conjunction with the NeoBell hardware device and NeoBell App. Ensure all components are properly configured for full functionality.

**NeoBell** - Securely connected. Simply Home
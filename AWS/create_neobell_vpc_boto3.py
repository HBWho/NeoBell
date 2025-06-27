import boto3
import time

# Initialize boto3 client for EC2 (VPC services are under EC2)
# Specify the region directly or ensure it's configured in your AWS profile/environment
REGION_NAME = 'us-east-1' # <<<<< Your selected region
ec2_client = boto3.client('ec2', region_name=REGION_NAME)
ec2_resource = boto3.resource('ec2', region_name=REGION_NAME)

# --- Configuration Variables ---
VPC_NAME = 'neobell-vpc'
VPC_CIDR = '10.0.0.0/16'
PROJECT_TAG = {'Key': 'Project', 'Value': 'NeoBell'}

# Subnet configurations
# We'll use the actual AZ names you used.
# For us-east-1, these are often us-east-1a, us-east-1b, etc.
# Please ensure these are correct for your region if different from the script.
AZ_A = f'{REGION_NAME}a' # e.g., us-east-1a
AZ_B = f'{REGION_NAME}b' # e.g., us-east-1b

PUBLIC_SUBNET_A_NAME = 'neobell-subnet-public1-us-east-1a'
PUBLIC_SUBNET_A_CIDR = '10.0.1.0/24'
PRIVATE_SUBNET_A_NAME = 'neobell-subnet-private1-us-east-1a'
PRIVATE_SUBNET_A_CIDR = '10.0.101.0/24'

PUBLIC_SUBNET_B_NAME = 'neobell-subnet-public2-us-east-1b'
PUBLIC_SUBNET_B_CIDR = '10.0.2.0/24'
PRIVATE_SUBNET_B_NAME = 'neobell-subnet-private2-us-east-1b'
PRIVATE_SUBNET_B_CIDR = '10.0.102.0/24'

IGW_NAME = 'neobell-igw'
PUBLIC_RTB_NAME = 'neobell-rtb-public'
PRIVATE_RTB_A_NAME = 'neobell-rtb-private1-us-east-1a'
PRIVATE_RTB_B_NAME = 'neobell-rtb-private2-us-east-1b'

# Single NAT Gateway in AZ A
NAT_GW_EIP_NAME_AZ_A = 'neobell-nat-eip-az-a' # Conceptual name for the EIP
NAT_GW_NAME_AZ_A = 'neobell-nat-public1-us-east-1a'

S3_ENDPOINT_NAME_TAG = 'neobell-vpce-s3' # Name tag for S3 endpoint
DYNAMODB_ENDPOINT_NAME_TAG = 'neobell-dynamodb-gateway-endpoint' # Name tag for DynamoDB endpoint

# Lambda Security Group Configuration
LAMBDA_SG_NAME = 'neobell-lambda-sg'
LAMBDA_SG_DESCRIPTION = 'Security group for NeoBell Lambda functions running in VPC'

def create_vpc():
    print(f"Creating VPC: {VPC_NAME} with CIDR {VPC_CIDR}")
    vpc = ec2_resource.create_vpc(
        CidrBlock=VPC_CIDR,
        TagSpecifications=[
            {'ResourceType': 'vpc', 'Tags': [PROJECT_TAG, {'Key': 'Name', 'Value': VPC_NAME}]}
        ]
    )
    vpc.wait_until_available()
    # Enable DNS hostnames and DNS support
    ec2_client.modify_vpc_attribute(VpcId=vpc.id, EnableDnsSupport={'Value': True})
    ec2_client.modify_vpc_attribute(VpcId=vpc.id, EnableDnsHostnames={'Value': True})
    print(f"VPC {VPC_NAME} ({vpc.id}) created and configured.")
    return vpc

def create_subnet(vpc, availability_zone, cidr_block, name_tag_value, is_public=False):
    print(f"Creating subnet: {name_tag_value} in AZ {availability_zone} with CIDR {cidr_block}")
    subnet = vpc.create_subnet(
        CidrBlock=cidr_block,
        AvailabilityZone=availability_zone,
        TagSpecifications=[
            {'ResourceType': 'subnet', 'Tags': [PROJECT_TAG, {'Key': 'Name', 'Value': name_tag_value}]}
        ]
    )
    if is_public:
        ec2_client.modify_subnet_attribute(
            SubnetId=subnet.id,
            MapPublicIpOnLaunch={'Value': True} # Enable auto-assign public IP
        )
        print(f"Enabled auto-assign public IP for {name_tag_value}")
    print(f"Subnet {name_tag_value} ({subnet.id}) created.")
    return subnet

def create_internet_gateway(vpc):
    print(f"Creating Internet Gateway: {IGW_NAME}")
    igw = ec2_resource.create_internet_gateway(
        TagSpecifications=[
            {'ResourceType': 'internet-gateway', 'Tags': [PROJECT_TAG, {'Key': 'Name', 'Value': IGW_NAME}]}
        ]
    )
    vpc.attach_internet_gateway(InternetGatewayId=igw.id)
    print(f"Internet Gateway {IGW_NAME} ({igw.id}) created and attached to VPC {vpc.id}.")
    return igw

def create_route_table(vpc, name_tag_value):
    print(f"Creating Route Table: {name_tag_value}")
    rtb = vpc.create_route_table(
        TagSpecifications=[
            {'ResourceType': 'route-table', 'Tags': [PROJECT_TAG, {'Key': 'Name', 'Value': name_tag_value}]}
        ]
    )
    print(f"Route Table {name_tag_value} ({rtb.id}) created.")
    return rtb

def associate_route_table_with_subnet(route_table, subnet):
    print(f"Associating Route Table {route_table.id} with Subnet {subnet.id}")
    route_table.associate_with_subnet(SubnetId=subnet.id)
    print(f"Association complete.")

def create_route_to_igw(route_table, internet_gateway):
    print(f"Adding route 0.0.0.0/0 -> IGW {internet_gateway.id} to Route Table {route_table.id}")
    route_table.create_route(
        DestinationCidrBlock='0.0.0.0/0',
        GatewayId=internet_gateway.id
    )
    print(f"Route to IGW added.")

def allocate_elastic_ip(name_tag_value):
    print(f"Allocating Elastic IP: {name_tag_value}")
    eip = ec2_client.allocate_address(
        Domain='vpc',
        TagSpecifications=[
            {'ResourceType': 'elastic-ip', 'Tags': [PROJECT_TAG, {'Key': 'Name', 'Value': name_tag_value}]}
        ]
    )
    print(f"Elastic IP {eip['AllocationId']} allocated.")
    return eip['AllocationId'] # Return AllocationId

def create_nat_gateway(subnet, eip_allocation_id, name_tag_value):
    print(f"Creating NAT Gateway: {name_tag_value} in Subnet {subnet.id}")
    response = ec2_client.create_nat_gateway(
        SubnetId=subnet.id,
        AllocationId=eip_allocation_id,
        TagSpecifications=[
            {'ResourceType': 'natgateway', 'Tags': [PROJECT_TAG, {'Key': 'Name', 'Value': name_tag_value}]}
        ]
    )
    nat_gw_id = response['NatGateway']['NatGatewayId']
    print(f"NAT Gateway {name_tag_value} ({nat_gw_id}) creation initiated. Waiting for it to become available...")
    
    # Wait for NAT Gateway to become available
    waiter = ec2_client.get_waiter('nat_gateway_available')
    waiter.wait(NatGatewayIds=[nat_gw_id])
    print(f"NAT Gateway {nat_gw_id} is now available.")
    return nat_gw_id

def create_route_to_nat_gw(route_table, nat_gateway_id):
    print(f"Adding route 0.0.0.0/0 -> NAT GW {nat_gateway_id} to Route Table {route_table.id}")
    route_table.create_route(
        DestinationCidrBlock='0.0.0.0/0',
        NatGatewayId=nat_gateway_id
    )
    print(f"Route to NAT GW added.")

def create_gateway_endpoint(vpc_id, service_name_type, route_table_ids, name_tag_value):
    service_full_name = f"com.amazonaws.{REGION_NAME}.{service_name_type}"
    print(f"Creating Gateway Endpoint for {service_full_name} ({name_tag_value})")
    endpoint = ec2_client.create_vpc_endpoint(
        VpcId=vpc_id,
        ServiceName=service_full_name,
        VpcEndpointType='Gateway',
        RouteTableIds=route_table_ids,
        TagSpecifications=[
            {'ResourceType': 'vpc-endpoint', 'Tags': [PROJECT_TAG, {'Key': 'Name', 'Value': name_tag_value}]}
        ]
    )
    print(f"Gateway Endpoint {name_tag_value} ({endpoint['VpcEndpoint']['VpcEndpointId']}) created.")
    return endpoint['VpcEndpoint']['VpcEndpointId']

def create_lambda_security_group(vpc_id, sg_name, sg_description):
    """
    Creates a security group for Lambda functions.
    - No inbound rules.
    - Allows all outbound traffic.
    """
    print(f"Creating Lambda Security Group: {sg_name}")
    try:
        response = ec2_client.create_security_group(
            GroupName=sg_name,
            Description=sg_description,
            VpcId=vpc_id,
            TagSpecifications=[
                {'ResourceType': 'security-group', 'Tags': [PROJECT_TAG, {'Key': 'Name', 'Value': sg_name}]}
            ]
        )
        sg_id = response['GroupId']
        print(f"Security Group {sg_name} ({sg_id}) created.")

        # Add outbound rule: Allow all traffic
        ec2_client.authorize_security_group_egress(
            GroupId=sg_id,
            IpPermissions=[
                {
                    'IpProtocol': '-1', # -1 signifies all protocols
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}],
                    'Ipv6Ranges': [],
                    'PrefixListIds': [],
                    'UserIdGroupPairs': []
                }
            ]
        )
        print(f"Added outbound rule (all traffic to 0.0.0.0/0) to Security Group {sg_id}.")
        return sg_id
    except Exception as e:
        print(f"Error creating security group {sg_name}: {e}")
        # Check if it already exists by description and VPC ID if name conflict occurs
        if "InvalidGroup.Duplicate" in str(e):
            sgs = ec2_client.describe_security_groups(
                Filters=[
                    {'Name': 'vpc-id', 'Values': [vpc_id]},
                    {'Name': 'group-name', 'Values': [sg_name]}
                ]
            )['SecurityGroups']
            if sgs:
                print(f"Security Group {sg_name} already exists with ID {sgs[0]['GroupId']}. Using existing.")
                return sgs[0]['GroupId']
        return None

def main():
    print(f"Starting Project NeoBell VPC setup in region {REGION_NAME}...")

    # 1. Create VPC
    vpc = create_vpc()

    # 1.1 Create Lambda Security Group
    # This is created early as other resources might not depend on it directly,
    # but it's good to have it available.
    lambda_sg_id = create_lambda_security_group(vpc.id, LAMBDA_SG_NAME, LAMBDA_SG_DESCRIPTION)
    if not lambda_sg_id:
        print("Failed to create or retrieve Lambda Security Group. Aborting.")
        return

    # 2. Create Subnets
    public_subnet_a = create_subnet(vpc, AZ_A, PUBLIC_SUBNET_A_CIDR, PUBLIC_SUBNET_A_NAME, is_public=True)
    private_subnet_a = create_subnet(vpc, AZ_A, PRIVATE_SUBNET_A_CIDR, PRIVATE_SUBNET_A_NAME)
    public_subnet_b = create_subnet(vpc, AZ_B, PUBLIC_SUBNET_B_CIDR, PUBLIC_SUBNET_B_NAME, is_public=True)
    private_subnet_b = create_subnet(vpc, AZ_B, PRIVATE_SUBNET_B_CIDR, PRIVATE_SUBNET_B_NAME)

    # 3. Create Internet Gateway and attach
    igw = create_internet_gateway(vpc)

    # 4. Create Public Route Table, add IGW route, and associate with public subnets
    public_rtb = create_route_table(vpc, PUBLIC_RTB_NAME)
    create_route_to_igw(public_rtb, igw)
    associate_route_table_with_subnet(public_rtb, public_subnet_a)
    associate_route_table_with_subnet(public_rtb, public_subnet_b)

    # 5. Allocate EIP for NAT Gateway (only one NAT GW in AZ A)
    nat_gw_eip_allocation_id_a = allocate_elastic_ip(NAT_GW_EIP_NAME_AZ_A)
    
    # 6. Create NAT Gateway in Public Subnet A
    # NAT Gateway needs a few moments for EIP to be fully ready for association after allocation
    print("Waiting for 30 seconds for EIP to be fully ready before NAT GW creation...")
    time.sleep(30) 
    nat_gw_a_id = create_nat_gateway(public_subnet_a, nat_gw_eip_allocation_id_a, NAT_GW_NAME_AZ_A)

    # 7. Create Private Route Tables
    private_rtb_a = create_route_table(vpc, PRIVATE_RTB_A_NAME)
    private_rtb_b = create_route_table(vpc, PRIVATE_RTB_B_NAME)

    # 8. Add NAT Gateway route to Private Route Tables
    # Both private subnets will route through the single NAT Gateway in AZ A
    create_route_to_nat_gw(private_rtb_a, nat_gw_a_id)
    create_route_to_nat_gw(private_rtb_b, nat_gw_a_id)

    # 9. Associate Private Route Tables with Private Subnets
    associate_route_table_with_subnet(private_rtb_a, private_subnet_a)
    associate_route_table_with_subnet(private_rtb_b, private_subnet_b)
    
    # 10. Create Gateway Endpoints (S3 and DynamoDB)
    # Ensure route tables are fully associated before adding endpoints to them.
    # The S3/DynamoDB routes are added by AWS to the specified route tables.
    private_route_table_ids = [private_rtb_a.id, private_rtb_b.id]
    
    s3_endpoint_id = create_gateway_endpoint(vpc.id, "s3", private_route_table_ids, S3_ENDPOINT_NAME_TAG)
    # Brief pause can sometimes help before creating the next endpoint if there are many route table updates
    time.sleep(10) 
    dynamodb_endpoint_id = create_gateway_endpoint(vpc.id, "dynamodb", private_route_table_ids, DYNAMODB_ENDPOINT_NAME_TAG)

    print("\n--- Project NeoBell Foundational VPC Setup Complete ---")
    print(f"VPC ID: {vpc.id}")
    print(f"Lambda Security Group ID: {lambda_sg_id}")
    print(f"Public Subnet A ID: {public_subnet_a.id}")
    print(f"Private Subnet A ID: {private_subnet_a.id}")
    print(f"Public Subnet B ID: {public_subnet_b.id}")
    print(f"Private Subnet B ID: {private_subnet_b.id}")
    print(f"Internet Gateway ID: {igw.id}")
    print(f"Public Route Table ID: {public_rtb.id}")
    print(f"Private Route Table A ID: {private_rtb_a.id}")
    print(f"Private Route Table B ID: {private_rtb_b.id}")
    print(f"Elastic IP (for NAT GW A) Allocation ID: {nat_gw_eip_allocation_id_a}")
    print(f"NAT Gateway A ID: {nat_gw_a_id}")
    print(f"S3 Gateway Endpoint ID: {s3_endpoint_id}")
    print(f"DynamoDB Gateway Endpoint ID: {dynamodb_endpoint_id}")
    print("----------------------------------------------------")

if __name__ == '__main__':
    main()

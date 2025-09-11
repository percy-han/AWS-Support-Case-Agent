"""AWS Cognito and AgentCore setup utilities for MCP server deployment."""

import boto3
import json
import time
from boto3.session import Session

from config import (
    CLIENT_NAME,
    COGNITO_DISCOVERY_URL_TEMPLATE,
    DEBUG_MODE,
    MAX_POLICIES_TO_LIST,
    MAX_POOLS_TO_LIST,
    PASSWORD,
    POOL_NAME,
    ROLE_CREATION_WAIT_SECONDS,
    ROLE_NAME_TEMPLATE, POLICY_NAME,
    USERNAME,
    AWS_SUPPORT_ACCESS_MANAGED_POLICY_ARN,
)


def _get_aws_session():
    """Get AWS session and region.

    Returns:
        tuple: (Session object, region name)
    """
    session = Session()
    return session, session.region_name


def _authenticate_user(cognito_client, client_id):
    """Authenticate user and return bearer token.

    Args:
        cognito_client: Boto3 Cognito client
        client_id (str): Cognito client ID

    Returns:
        str: Bearer token for authentication
    """
    auth_response = cognito_client.initiate_auth(
        ClientId=client_id,
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={'USERNAME': USERNAME, 'PASSWORD': PASSWORD}
    )
    return auth_response['AuthenticationResult']['AccessToken']


def _find_existing_pool(cognito_client):
    """Find existing user pool and client.

    Args:
        cognito_client: Boto3 Cognito client

    Returns:
        tuple: (pool_id, client_id) or (None, None) if not found
    """
    pools = cognito_client.list_user_pools(MaxResults=MAX_POOLS_TO_LIST)
    for pool in pools['UserPools']:
        if pool['Name'] == POOL_NAME:
            clients = cognito_client.list_user_pool_clients(
                UserPoolId=pool['Id']
            )
            for client in clients['UserPoolClients']:
                if client['ClientName'] == CLIENT_NAME:
                    return pool['Id'], client['ClientId']
    return None, None


def _create_user_pool(cognito_client):
    """Create new user pool and client.

    Args:
        cognito_client: Boto3 Cognito client

    Returns:
        tuple: (pool_id, client_id)
    """
    # Create User Pool
    user_pool_response = cognito_client.create_user_pool(
        PoolName=POOL_NAME,
        Policies={'PasswordPolicy': {'MinimumLength': 8}}
    )
    pool_id = user_pool_response['UserPool']['Id']

    # Create App Client
    app_client_response = cognito_client.create_user_pool_client(
        UserPoolId=pool_id,
        ClientName=CLIENT_NAME,
        GenerateSecret=False,
        ExplicitAuthFlows=[
            'ALLOW_USER_PASSWORD_AUTH',
            'ALLOW_REFRESH_TOKEN_AUTH'
        ]
    )
    client_id = app_client_response['UserPoolClient']['ClientId']

    # Create and configure user
    cognito_client.admin_create_user(
        UserPoolId=pool_id,
        Username=USERNAME,
        TemporaryPassword='Temp123!',
        MessageAction='SUPPRESS'
    )
    cognito_client.admin_set_user_password(
        UserPoolId=pool_id,
        Username=USERNAME,
        Password=PASSWORD,
        Permanent=True
    )

    return pool_id, client_id


def setup_cognito_user_pool():
    """Setup Cognito user pool with duplicate prevention.

    Returns:
        dict: Configuration dictionary with pool details, or None on error
    """
    _, region = _get_aws_session()
    cognito_client = boto3.client('cognito-idp', region_name=region)

    try:
        # Check for existing pool first
        pool_id, client_id = _find_existing_pool(cognito_client)

        if pool_id and client_id:
            print(f"✅ Found existing user pool: {pool_id}")
        else:
            # Create new pool if none exists
            pool_id, client_id = _create_user_pool(cognito_client)

        # Authenticate and get token
        bearer_token = _authenticate_user(cognito_client, client_id)

        discovery_url = COGNITO_DISCOVERY_URL_TEMPLATE.format(
            region=region,
            pool_id=pool_id
        )

        config = {
            'pool_id': pool_id,
            'client_id': client_id,
            'bearer_token': bearer_token,
            'discovery_url': discovery_url,
            'AuthParameters': {'USERNAME': USERNAME, 'PASSWORD': PASSWORD}
        }

        if DEBUG_MODE:
            print(f"✅ Pool id: {pool_id}")
            print(f"✅ Discovery URL: {config['discovery_url']}")
            print(f"✅ Client ID: {client_id}")
            print(f"✅ Bearer Token: {bearer_token}")
            print(f"✅ UserName: {USERNAME}")
            print(f"✅ Password: {PASSWORD}")

        return config

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def reauthenticate_user(client_id):
    """Re-authenticate user with existing client.

    Args:
        client_id (str): Cognito client ID

    Returns:
        str: New bearer token
    """
    _, region = _get_aws_session()
    cognito_client = boto3.client('cognito-idp', region_name=region)
    return _authenticate_user(cognito_client, client_id)


def _get_role_policy(region, account_id, agent_name):
    """Get IAM role policy document.

    Args:
        region (str): AWS region
        account_id (str): AWS account ID
        agent_name (str): Agent name for resource naming

    Returns:
        dict: IAM policy document
    """
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "BedrockPermissions",
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                "Resource": "*"
            },
            {
                "Sid": "ECRImageAccess",
                "Effect": "Allow",
                "Action": [
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:GetAuthorizationToken"
                ],
                "Resource": [f"arn:aws:ecr:{region}:{account_id}:repository/*"]
            },
            {
                "Effect": "Allow",
                "Action": ["logs:DescribeLogStreams", "logs:CreateLogGroup"],
                "Resource": [
                    f"arn:aws:logs:{region}:{account_id}:"
                    f"log-group:/aws/bedrock-agentcore/runtimes/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": ["logs:DescribeLogGroups"],
                "Resource": [
                    f"arn:aws:logs:{region}:{account_id}:log-group:*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
                "Resource": [
                    f"arn:aws:logs:{region}:{account_id}:"
                    f"log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*"
                ]
            },
            {
                "Sid": "ECRTokenAccess",
                "Effect": "Allow",
                "Action": ["ecr:GetAuthorizationToken"],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords",
                    "xray:GetSamplingRules",
                    "xray:GetSamplingTargets"
                ],
                "Resource": ["*"]
            },
            {
                "Effect": "Allow",
                "Resource": "*",
                "Action": "cloudwatch:PutMetricData",
                "Condition": {
                    "StringEquals": {
                        "cloudwatch:namespace": "bedrock-agentcore"
                    }
                }
            },
            {
                "Sid": "GetAgentAccessToken",
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:GetWorkloadAccessToken",
                    "bedrock-agentcore:GetWorkloadAccessTokenForJWT",
                    "bedrock-agentcore:GetWorkloadAccessTokenForUserId"
                ],
                "Resource": [
                    f"arn:aws:bedrock-agentcore:{region}:{account_id}:"
                    f"workload-identity-directory/default",
                    f"arn:aws:bedrock-agentcore:{region}:{account_id}:"
                    f"workload-identity-directory/default/"
                    f"workload-identity/{agent_name}-*"
                ]
            }
        ]
    }


def _get_assume_role_policy(region, account_id):
    """Get assume role policy document.

    Args:
        region (str): AWS region
        account_id (str): AWS account ID

    Returns:
        dict: Assume role policy document
    """
    return {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "AssumeRolePolicy",
            "Effect": "Allow",
            "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {"aws:SourceAccount": account_id},
                "ArnLike": {
                    "aws:SourceArn": (
                        f"arn:aws:bedrock-agentcore:{region}:{account_id}:*"
                    )
                }
            }
        }]
    }


def _cleanup_existing_role(iam_client, role_name):
    """Clean up existing IAM role and its policies.

    Args:
        iam_client: Boto3 IAM client
        role_name (str): Name of the role to clean up
    """
    print("⚠️ Role already exists -- recreating")
    # Clean up existing policies
    policies = iam_client.list_role_policies(
        RoleName=role_name,
        MaxItems=MAX_POLICIES_TO_LIST
    )
    for policy_name in policies['PolicyNames']:
        iam_client.delete_role_policy(
            RoleName=role_name,
            PolicyName=policy_name
        )

    # Delete role
    iam_client.delete_role(RoleName=role_name)


def _add_managed_policy_to_role(role_name, policy_arn):
    """Add a managed policy to an existing IAM role.

    Args:
        role_name (str): Name of the IAM role
        policy_arn (str): ARN of the managed policy to add

    Returns:
        dict: Response from AWS
    """
    iam_client = boto3.client('iam')

    try:
        # Check if policy is already attached
        attached_policies = iam_client.list_attached_role_policies(
            RoleName=role_name)
        for policy in attached_policies['AttachedPolicies']:
            if policy['PolicyArn'] == policy_arn:
                print(
                    f"✅ Managed policy {policy_arn} already attached to {role_name}")
                return None

        # Attach policy if not already attached
        response = iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn=policy_arn
        )
        print(f"✅ Managed policy {policy_arn} attached to {role_name}")
        return response
    except Exception as e:
        print(f"❌ Error attaching managed policy: {e}")
        raise


def create_agentcore_role(agent_name):
    """Create IAM role for AgentCore with proper permissions.

    Args:
        agent_name (str): Name of the agent for resource naming

    Returns:
        dict: Created IAM role response
    """
    iam_client = boto3.client('iam')
    role_name = ROLE_NAME_TEMPLATE.format(agent_name=agent_name)
    _, region = _get_aws_session()
    account_id = boto3.client("sts").get_caller_identity()["Account"]

    # Get policy documents
    role_policy = _get_role_policy(region, account_id, agent_name)
    assume_role_policy = _get_assume_role_policy(region, account_id)

    try:
        # Create role
        role = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy)
        )
        time.sleep(ROLE_CREATION_WAIT_SECONDS)  # Wait for role creation

    except iam_client.exceptions.EntityAlreadyExistsException:
        _cleanup_existing_role(iam_client, role_name)
        role = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy)
        )

    # Attach policy
    try:
        iam_client.put_role_policy(
            PolicyDocument=json.dumps(role_policy),
            PolicyName=POLICY_NAME,
            RoleName=role_name
        )
    except Exception as e:
        print(f"❌ Error attaching policy: {e}")
        raise

    print("📝 Attaching AWSSupportAccess policy...")
    _add_managed_policy_to_role(
        role_name, AWS_SUPPORT_ACCESS_MANAGED_POLICY_ARN)

    return role


def get_existing_role_arn(agent_name):
    """Check if role already exists and return its ARN.

    Args:
        agent_name (str): Agent name for role lookup

    Returns:
        str or None: Role ARN if exists, None otherwise
    """
    iam_client = boto3.client('iam')
    role_name = ROLE_NAME_TEMPLATE.format(agent_name=agent_name)

    try:
        response = iam_client.get_role(RoleName=role_name)
        return response['Role']['Arn']
    except iam_client.exceptions.NoSuchEntityException:
        return None


def get_or_create_role(agent_name):
    """Get existing role ARN or create new one if needed.

    Args:
        agent_name (str): Agent name for role management

    Returns:
        str: Role ARN
    """
    # Check if role already exists
    existing_arn = get_existing_role_arn(agent_name)
    if existing_arn:
        print(f"✅ Using existing role: {existing_arn}")
        return existing_arn

    # Create new role if none exists
    print("Creating new IAM role...")
    role_response = create_agentcore_role(agent_name)

    return role_response['Role']['Arn']

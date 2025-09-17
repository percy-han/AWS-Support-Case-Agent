"""AWS IAM setup utilities for Agent deployment."""

import boto3
import json
import time
from boto3.session import Session
from botocore.exceptions import ClientError

from config import AGENT_NAME

# Role naming template
ROLE_NAME_TEMPLATE = 'agentcore-{agent_name}-role'
POLICY_NAME = 'AgentExecutionPolicy'


def _get_aws_session():
    """Get AWS session and region.

    Returns:
        tuple: (Session object, region name)
    """
    session = Session()
    return session, session.region_name


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
                "Sid": "ECRImageAccess",
                "Effect": "Allow",
                "Action": [
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:GetAuthorizationToken"
                ],
                "Resource": "*"
            },
            {
                "Sid": "SecretsManagerAccess",
                "Effect": "Allow",
                "Action": [
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret",
                    "secretsmanager:UpdateSecret",
                    "secretsmanager:CreateSecret"
                ],
                "Resource": "*"
            },
            {
                "Sid": "SSMParameterAccess",
                "Effect": "Allow",
                "Action": [
                    "ssm:GetParameter",
                    "ssm:GetParameters",
                    "ssm:PutParameter"
                ],
                "Resource": "*"
            },
            {
                "Sid": "SupportAPIAccess",
                "Effect": "Allow",
                "Action": [
                    "support:*"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "logs:DescribeLogStreams",
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "logs:DescribeLogGroups"
                ],
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
                "Resource": "*"
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
                "Sid": "BedrockAgentCoreRuntime",
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:InvokeAgentRuntime"
                ],
                "Resource": "*"
            },
            {
                "Sid": "BedrockAgentCoreMemoryCreateMemory",
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:CreateMemory"
                ],
                "Resource": "*"
            },
            {
                "Sid": "BedrockAgentCoreMemory",
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:CreateEvent",
                    "bedrock-agentcore:GetEvent",
                    "bedrock-agentcore:GetMemory",
                    "bedrock-agentcore:GetMemoryRecord",
                    "bedrock-agentcore:ListActors",
                    "bedrock-agentcore:ListEvents",
                    "bedrock-agentcore:ListMemoryRecords",
                    "bedrock-agentcore:ListSessions",
                    "bedrock-agentcore:DeleteEvent",
                    "bedrock-agentcore:DeleteMemoryRecord",
                    "bedrock-agentcore:RetrieveMemoryRecords"
                ],
                "Resource": "*"
            },
            {
                "Sid": "BedrockAgentCoreIdentityGetResourceApiKey",
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:GetResourceApiKey"
                ],
                "Resource": "*"
            },
            {
                "Sid": "BedrockAgentCoreIdentityGetResourceOauth2Token",
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:GetResourceOauth2Token"
                ],
                "Resource": "*"
            },
            {
                "Sid": "BedrockAgentCoreIdentityGetWorkloadAccessToken",
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:GetWorkloadAccessToken",
                    "bedrock-agentcore:GetWorkloadAccessTokenForJWT",
                    "bedrock-agentcore:GetWorkloadAccessTokenForUserId"
                ],
                "Resource": "*"
            },
            {
                "Sid": "BedrockModelInvocation",
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                    "bedrock:ApplyGuardrail"
                ],
                "Resource": "*"
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
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            return None
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
            AssumeRolePolicyDocument=json.dumps(assume_role_policy),
            Description=f'Execution role for Bedrock AgentCore agent: {agent_name}'
        )
        time.sleep(10)  # Wait for role creation

        # Attach policy
        policy_name = f"{POLICY_NAME}-{agent_name}"
        iam_client.put_role_policy(
            PolicyDocument=json.dumps(role_policy),
            PolicyName=policy_name,
            RoleName=role_name
        )

        print(f"✅ Created role: {role['Role']['Arn']}")
        return role

    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print("⚠️ Role already exists -- using existing role")
            response = iam_client.get_role(RoleName=role_name)
            return response
        raise


def ensure_role_policy_updated(role_name, agent_name):
    """Ensure role has the latest policy definition"""
    iam_client = boto3.client('iam')
    _, region = _get_aws_session()
    account_id = boto3.client("sts").get_caller_identity()["Account"]

    # Get the expected policy
    expected_policy = _get_role_policy(region, account_id, agent_name)
    policy_name = f"{POLICY_NAME}-{agent_name}"

    try:
        # Update the policy to match current definition
        iam_client.put_role_policy(
            PolicyDocument=json.dumps(expected_policy),
            PolicyName=policy_name,
            RoleName=role_name
        )
        print(f"✅ Updated role policy to match code definition")
    except ClientError as e:
        print(f"❌ Error updating role policy: {e}")
        raise

def get_or_create_role(agent_name):
    """Get existing role ARN or create new one if needed. Ensures existing role matches code definition.

    Args:
        agent_name (str): Agent name for role management

    Returns:
        str: Role ARN
    """
    role_name = ROLE_NAME_TEMPLATE.format(agent_name=agent_name)

    # Check if role already exists
    existing_arn = get_existing_role_arn(agent_name)
    if existing_arn:
        print(f"✅ Found existing role: {existing_arn}")
        # Ensure the existing role has the correct policy
        ensure_role_policy_updated(role_name, agent_name)
        return existing_arn

    # Create new role if none exists
    print("Creating new IAM role...")
    role_response = create_agentcore_role(agent_name)

    return role_response['Role']['Arn']

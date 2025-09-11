"""MCP client test module for validating server connection and tools."""

import asyncio
import json
import sys
from datetime import timedelta

import boto3
from boto3.session import Session
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from config import (
    SECRETS_NAME, PARAMETER_NAME, MCP_TIMEOUT_SECONDS,
    AGENTCORE_URL_TEMPLATE
)


def _get_credentials_from_aws(region):
    """Retrieve credentials from AWS services.

    Args:
        region (str): AWS region name

    Returns:
        tuple: (agent_arn, bearer_token)

    Raises:
        SystemExit: If credentials cannot be retrieved
    """
    try:
        # Get Agent ARN from Parameter Store
        ssm_client = boto3.client('ssm', region_name=region)
        agent_arn_response = ssm_client.get_parameter(Name=PARAMETER_NAME)
        agent_arn = agent_arn_response['Parameter']['Value']
        print(f"✅ Retrieved Agent ARN: {agent_arn}")

        # Get bearer token from Secrets Manager
        secrets_client = boto3.client('secretsmanager', region_name=region)
        response = secrets_client.get_secret_value(SecretId=SECRETS_NAME)
        secret_value = response['SecretString']
        parsed_secret = json.loads(secret_value)
        bearer_token = parsed_secret['bearer_token']
        print("✅ Retrieved bearer token from Secrets Manager")

        return agent_arn, bearer_token

    except Exception as e:
        print(f"❌ Error retrieving credentials: {e}")
        sys.exit(1)


def _validate_credentials(agent_arn, bearer_token):
    """Validate that credentials are properly retrieved.

    Args:
        agent_arn (str): Agent ARN
        bearer_token (str): Bearer token

    Raises:
        SystemExit: If credentials are invalid
    """
    if not agent_arn or not bearer_token:
        print("❌ Error: AGENT_ARN or BEARER_TOKEN not retrieved properly")
        sys.exit(1)


def _build_mcp_url(agent_arn, region):
    """Build MCP server URL from agent ARN.

    Args:
        agent_arn (str): Agent ARN
        region (str): AWS region

    Returns:
        str: MCP server URL
    """
    encoded_arn = agent_arn.replace(':', '%3A').replace('/', '%2F')
    return AGENTCORE_URL_TEMPLATE.format(
        region=region,
        encoded_arn=encoded_arn
    )


def _get_request_headers(bearer_token):
    """Get HTTP headers for MCP requests.

    Args:
        bearer_token (str): Bearer token for authentication

    Returns:
        dict: HTTP headers
    """
    return {
        "authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }


def _print_tool_info(tool_result):
    """Print information about available MCP tools.

    Args:
        tool_result: MCP tools list result
    """
    print("\n📋 Available MCP Tools:")
    print("=" * 50)
    for tool in tool_result.tools:
        print(f"🔧 {tool.name}")
        print(f"   Description: {tool.description}")
        if hasattr(tool, 'inputSchema') and tool.inputSchema:
            properties = tool.inputSchema.get('properties', {})
            if properties:
                print(f"   Parameters: {list(properties.keys())}")
        print()

    print("✅ Successfully connected to MCP server!")
    print(f"Found {len(tool_result.tools)} tools available.")


async def test_mcp_connection():
    """Test MCP server connection and list available tools.

    Raises:
        SystemExit: If connection fails or credentials are invalid
    """
    boto_session = Session()
    region = boto_session.region_name

    print(f"✅ Using AWS region: {region}")

    # Get credentials from AWS
    agent_arn, bearer_token = _get_credentials_from_aws(region)
    _validate_credentials(agent_arn, bearer_token)

    # Prepare MCP connection
    mcp_url = _build_mcp_url(agent_arn, region)
    headers = _get_request_headers(bearer_token)

    print(f"\n🔗 Connecting to: {mcp_url}")
    print("✅ Headers configured")

    try:
        async with streamablehttp_client(
            mcp_url,
            headers,
            timeout=timedelta(seconds=MCP_TIMEOUT_SECONDS),
            terminate_on_close=False
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                print("\n🔄 Initializing MCP session...")
                await session.initialize()
                print("✅ MCP session initialized")

                print("\n🔄 Listing available tools...")
                tool_result = await session.list_tools()

                _print_tool_info(tool_result)

    except Exception as e:
        print(f"❌ Error connecting to MCP server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_mcp_connection())

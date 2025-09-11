"""Configuration constants for MCP server deployment."""

# Cognito Configuration
POOL_NAME = 'AWS-Support-MCPServerPool'
CLIENT_NAME = 'AWS-Support-MCP-Server-PoolClient'
USERNAME = 'testuser'
PASSWORD = 'MyPassword123!'

# AWS Resource Names
SECRETS_NAME = 'support_mcp_server/cognito/credentials'
PARAMETER_NAME = '/support_mcp_server/runtime/agent_arn'

# AgentCore Configuration
AGENT_NAME = 'awssupportmcpserver'
ROLE_NAME_TEMPLATE = 'agentcore-{agent_name}-role'
POLICY_NAME = 'AgentCorePolicy'

# MCP Configuration
MCP_ENTRYPOINT = 'awslabs/aws_support_mcp_server/server.py'
REQUIREMENTS_FILE = 'requirements.txt'
MCP_PROTOCOL = 'MCP'

# Timeouts and Limits
MCP_TIMEOUT_SECONDS = 120
ROLE_CREATION_WAIT_SECONDS = 10
MAX_POOLS_TO_LIST = 60
MAX_POLICIES_TO_LIST = 100

# Debug Settings
DEBUG_MODE = False

# URL Templates
COGNITO_DISCOVERY_URL_TEMPLATE = (
    "https://cognito-idp.{region}.amazonaws.com/"
    "{pool_id}/.well-known/openid-configuration"
)

AGENTCORE_URL_TEMPLATE = (
    "https://bedrock-agentcore.{region}.amazonaws.com/"
    "runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
)

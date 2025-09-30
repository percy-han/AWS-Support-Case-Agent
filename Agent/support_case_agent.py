
import asyncio
import boto3
import json
from strands import Agent
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from boto3.session import Session
from datetime import timedelta
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from datetime import datetime, timedelta, timezone
import logging


# 配置日志
logging.basicConfig(
    filename='application.log',  # 日志文件名
    level=logging.INFO,          # 日志级别
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # 日志格式
    datefmt='%Y-%m-%d %H:%M:%S'  # 日期格式
)

# ============ 全局配置 ============

# AWS 区域（从 boto session 里获取一次即可）
boto_session = Session()
REGION = boto_session.region_name
# Secret 和 Parameter 名称
SECRET_ID = "support_mcp_server/cognito/credentials"
SSM_AGENT_ARN_PARAM = "/support_mcp_server/runtime/agent_arn"

app = BedrockAgentCoreApp()


# 配置system prompt
def get_system_prompt() -> str:
    """
    Return the full system prompt for the AWS Support Case Management Agent,
    including dynamic current Beijing Time (UTC+8).
    """
    # 获取当前北京时间
    beijing_tz = timezone(timedelta(hours=8))
    now_bj = datetime.now(beijing_tz)
    current_time_str = now_bj.strftime("%Y-%m-%d %H:%M:%S %Z")

    # 定义 system prompt
    system_prompt = f"""
# AWS Support Case Management Agent - Cross-border E-commerce IT Support

## Current Reference Time
The current Beijing Time (UTC+8) is: **{current_time_str}**.
- When the user mentions relative time ranges (e.g., "last month", "yesterday", "过去一周"), always calculate them based on this reference time.
- Always assume the user's timezone is Beijing Time (UTC+8) unless explicitly stated otherwise.

## Identity & Role
You are an AWS Support Case Management Agent specialized in serving cross-border e-commerce IT teams. You have deep expertise in AWS services commonly used in e-commerce operations and understand the critical nature of e-commerce business continuity.

## Language Preference
- When interacting with the customer, always **prefer Chinese** for explanations and responses, unless the customer explicitly requests English.
- When creating new support cases, the **default language must be Chinese**, unless the customer explicitly specifies otherwise.

## Case ID Handling
- Customers usually refer to cases by **displayId** (the case number shown in the AWS Support console).
- The AWS Support API maybe requires the internal **caseId**.
- If only a displayId is provided, first use `describe_support_cases()` to retrieve the corresponding **caseId** before making further API calls.

## Core Capabilities
You can create, query, analyze, and provide strategic insights on AWS Support cases using the AWS Support MCP server. Your analysis focuses on business impact, operational efficiency, and proactive problem prevention for large-scale e-commerce operations.

## Target User Profile
- **Primary Users**: IT personnel at large-scale cross-border e-commerce companies
- **Business Context**: High-volume, time-sensitive e-commerce operations with global reach
- **Critical Requirements**: 24/7 availability, data security, compliance, and minimal downtime tolerance

## Key Responsibilities
1. **Case Creation & Management**: Create well-structured support cases with appropriate severity and business impact.
2. **Intelligent Case Analysis**: Summarize, classify, and analyze cases by severity, service, and category.
3. **Strategic Insights**: Provide best practices, preventive actions, and business impact assessments.
4. **Escalation Guidance**: Identify critical cases that require urgent action or executive visibility.

## E-commerce Specific Considerations
- Prioritize cases affecting **payment systems, website performance, databases, and security**.
- Pay special attention during **peak shopping seasons** and **flash sale events**.
- Map case severity to business impact (Critical = revenue-stopping, High = degraded CX, etc.).

## Output Guidelines
- Always provide summaries with **executive overviews** + **detailed breakdowns**.
- Highlight **critical cases** and **patterns**.
- Provide **clear, actionable recommendations**.
- Keep responses **concise, structured, and business-focused**.
- Always connect technical issues to **business impact**.

## Security & Compliance
- Always consider PCI DSS, GDPR, and cross-border data compliance in analysis.
- Treat payment and security-related cases as **highest priority**.

Remember: Your primary goal is to help e-commerce IT teams maintain robust, secure, and high-performing AWS infrastructure that supports their business objectives while minimizing operational risks and maximizing customer satisfaction.
"""
    return system_prompt



# =============== 核心封装 ===============
async def _run_once(user_input: str, system_prompt: str):
    """封装一次完整的 MCP 调用逻辑"""
    logging.info(f"建立 MCP 连接")
    streamable_http_mcp_client = MCPClient(create_streamable_http_transport)

    with streamable_http_mcp_client:
        logging.info(f"获取 MCP 工具列表")
        logging.info(f"Current Time9: {datetime.now()}")
        tools = streamable_http_mcp_client.list_tools_sync()
        logging.info(f"✓ 找到 {len(tools)} 个工具")

        logging.info(f"创建 Agent..")
        agent = Agent(
            model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            tools=tools,
            system_prompt=system_prompt
        )

        print(f"💭 开始流式执行查询: {user_input}")
        # 流式执行
        async for event in agent.stream_async(user_input):
            if "data" in event:
                yield event["data"]
        print("✅ 流式查询执行完成")


async def run_with_retry(user_input: str, system_prompt: str):
    """带 token 自动刷新的一次重试封装"""
    try:
        # 第一次尝试
        async for data in _run_once(user_input, system_prompt):
            yield data
    except Exception as e:
        err_msg = str(e)
        logging.warning(f"第一次失败: {err_msg}")

        # ✅ 判断是否 token 过期错误
        if "client initialization failed" in err_msg.lower():
            logging.info("检测到 token 失效，尝试 refresh_token 后重试...")
            try:
                refresh_token()  # 刷新 token
                async for data in _run_once(user_input, system_prompt):
                    yield data
            except Exception as e2:
                logging.error(f"刷新 token 后仍然失败: {e2}")
                yield {"error": str(e2), "type": "stream_error"}
        else:
            # 非 token 错误，直接返回
            yield {"error": err_msg, "type": "stream_error"}



def refresh_token():
    try:
        secrets_client = boto3.client('secretsmanager', region_name=REGION)
        secrets_response = secrets_client.get_secret_value(SecretId=SECRET_ID)
        secret_data = json.loads(secrets_response['SecretString'])
        client_id = secret_data['client_id']
        AuthParameters_username = secret_data['AuthParameters']['USERNAME']
        AuthParameters_password = secret_data['AuthParameters']['PASSWORD']
        logging.info(f"old secret data: {secret_data}")
        ##refresh access token
        cognito_client = boto3.client('cognito-idp', region_name=REGION)
        auth_response = cognito_client.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': AuthParameters_username,
                'PASSWORD': AuthParameters_password
            }
        )
        refreshed_bearer_token = auth_response['AuthenticationResult']['AccessToken']
        secret_data['bearer_token'] = refreshed_bearer_token
        logging.info(f"new data: {secret_data}")
        update_response = secrets_client.update_secret(SecretId=SECRET_ID,SecretString=json.dumps(secret_data))
        logging.info("refresh success")
    except Exception as e:
        print(f"Refresh cognito access token failed: {e}")
        raise e

def create_streamable_http_transport():
    try:
        # 你的现有配置代码（保持不变）
        ssm_client = boto3.client('ssm', region_name=REGION)
        agent_arn_response = ssm_client.get_parameter(Name=SSM_AGENT_ARN_PARAM)
        agent_arn = agent_arn_response['Parameter']['Value']
        logging.info(f"Retrieved Agent ARN: {agent_arn}")

        secrets_client = boto3.client('secretsmanager', region_name=REGION)
        response = secrets_client.get_secret_value(SecretId=SECRET_ID)
        secret_value = response['SecretString']
        parsed_secret = json.loads(secret_value)
        bearer_token = parsed_secret['bearer_token']
        logging.info(f"Retrieved bearer token: {bearer_token}")

        encoded_arn = agent_arn.replace(':', '%3A').replace('/', '%2F')
        mcp_url = f"https://bedrock-agentcore.{REGION}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
        headers = {
            "authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }
        logging.info(f"MCP URL configured: {mcp_url}")
        logging.info(f"创建 MCP 传输层")
        logging.info(f"headers: {headers}")
        return streamablehttp_client(mcp_url, headers, timeout=timedelta(seconds=120), terminate_on_close=False)
    except Exception as e:
        print(f"Error Message: {e}")
        raise e




# 🔥 关键修改：将函数改为异步并支持流式输出
@app.entrypoint
async def strands_agent_bedrock(payload):
    """
    流式入口点 - 修改你的现有函数
    """
    try:
        user_input = payload.get("prompt", "show me the case in the past four weeks?")
        logging.info(f"User input: {user_input}")

        system_prompt = get_system_prompt()
        logging.info(f"System Prompt: {system_prompt}")

        # 执行 agent 查询（带自动重试）
        async for result in run_with_retry(user_input, system_prompt):
            yield result

    except Exception as e:
        # Handle errors gracefully in streaming context
        error_response = {"error": str(e), "type": "entrypoint_error"}
        logging.info(f"entrypoint_error: {error_response}")
        yield error_response


if __name__ == "__main__":
    logging.info(f"process main function")
    app.run()

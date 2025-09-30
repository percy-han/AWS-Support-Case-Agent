import boto3
import json
import pickle
import os
from boto3.session import Session


def test_support_case_agent():
    """Test the deployed support case agent by invoking it with a sample prompt"""

    prompt_text = "请分析我过去半年的case并给出最佳实践建议和洞察"

    def invoke_agent(prompt_text):
        boto_session = Session()
        REGION = boto_session.region_name

        # Get agent ARN from launch_result.pkl
        try:
            with open('launch_result.pkl', 'rb') as f:
                launch_result = pickle.load(f)
            agent_arn = launch_result.agent_arn
        except FileNotFoundError:
            agent_arn = 'arn:aws:bedrock-agentcore:XXXXXX:XXXX:runtime/XXXXXXX-XXXXXX'

        print(f"Using agent ARN: {agent_arn}")

        agentcore_client = boto3.client("bedrock-agentcore", region_name=REGION)

        try:
            boto3_response = agentcore_client.invoke_agent_runtime(
                agentRuntimeArn=agent_arn,
                qualifier="DEFAULT",
                payload=json.dumps({"prompt": prompt_text})
            )

            print(f"Response status: {boto3_response['statusCode']}")
            print(f"Content type: {boto3_response.get('contentType', 'N/A')}")

            # Handle streaming response
            if "text/event-stream" in boto3_response.get("contentType", ""):
                print("Agent response:")
                try:
                    response_body = boto3_response["response"].read()
                    # Parse and clean the streaming data
                    lines = response_body.decode('utf-8').split('\n')
                    content = []
                    for line in lines:
                        if line.startswith('data: '):
                            data = line[6:].strip('"')
                            if data and data != '\\n':
                                content.append(data)

                    full_response = ''.join(content).replace('\\n', '\n')
                    print(full_response)
                except Exception as e:
                    print(f"Error reading response: {e}")
            else:
                print("Non-streaming response")

        except Exception as e:
            print(f"Error invoking agent: {e}")
            return False

        return True

    print(f"Testing with prompt: {prompt_text}")
    success = invoke_agent(prompt_text)

    if success:
        print("✅ Test completed successfully")
    else:
        print("❌ Test failed")

    return success


if __name__ == "__main__":
    test_support_case_agent()

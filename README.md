# Intelligent AWS Support Case Management with MCP & Bedrock AgentCore
## 智能化管理 AWS Support Case | 托管 MCP Server | 基于strands SDK创建Agent并托管到AgentCore实现MCP的调用

Amazon Bedrock AgentCore 可帮助您安全、大规模地部署和运行功能强大的人工智能代理。
它提供专为动态代理工作负载构建的基础设施、可增强代理功能的强大工具，以及适用于现实部署场景的基础控件。

### AgentCore 具有以下特性：

✅ 兼容性强：支持 CrewAI、LangGraph、LlamaIndex、Strands Agents 等框架

✅ 模型灵活：可调用 Amazon Bedrock 内外的基础模型

✅ 降低成本：免去企业自行构建专用代理基础设施的重复工作


### 本项目在此基础上，聚焦以下应用场景：

🛠 托管现有 MCP Server —— 将企业现有的 MCP Server 源代码直接托管到 AgentCore Runtime，最大程度减少改造成本

🤖 创建可调用 MCP 的 Agent —— 构建 Agent，从而实现 AgentCore Runtime（Agent） --> AgentCore Runtime（MCP） 的调用

📂 智能化管理 AWS Support Case —— 通过 Agent 自动完成 Support Case 的查询、创建和管理，支持 流式处理、认证授权、提示词优化 等高级功能


## 🚀 功能特性

- **智能支持案例管理**: 自动化AWS支持案例创建、跟踪和解决
- **智能支持案例总结和洞察**: 支持只能对AWS Case进行总结分析并给出最佳实践和洞察
- **MCP集成**: 利用模型上下文协议增强工具能力
- **跨境电商专用**: 专为国际业务IT支持场景优化
- **Bedrock Agent Core**: 基于AWS Bedrock Agent Core构建，支持可扩展的AI交互
- **可将现有MCP Server做无缝移植到AgentCore Runtime上**: 支持北京时间(UTC+8)的实时支持案例处理
- **构建Agent调用MCP Server**: 在AgentCore Runtime上额外构建Agent，从而实现智能调用MCP Tools

## 📁 项目结构

```
support-agent/
├── MCP/                                      # MCP实现
│   ├── aws_setup.py                          # 底层环境配置
│   ├── mcp_agentcore_deployment.ipynb        # MCP部署的Jupyter notebook
│   ├── config.py                             # 配置文件
│   ├── requirements.txt                      # MCP依赖
│   ├── mcp_client_test.py                    # MCP测试脚本
│   └── awslabs/                              # AWS Labs MCP服务器
│       └── aws_support_mcp_server/           # 支持专用MCP服务器
│
├── Agent/                                    # Agent实现
│   ├── aws_setup.py                          # 底层环境配置
│   ├── support_case_agent_deployment.ipynb   # Agent部署的Jupyter notebook
│   ├── config.py                             # 配置文件
│   ├── requirements.txt                      # Agent依赖
│   ├── support_case_agent.py                 # Agent核心代码
│   ├── support_case_agent_test.py            # Agent调用脚本
└── README.md                                 # 本文件
```

## 🏗️ 系统架构

<img width="813" height="422" alt="iShot_2025-08-29_01 08 37" src="https://github.com/user-attachments/assets/1ea5b964-68fb-40de-ba22-4c72befec92b" />
AgentCore Runtime 上的 Agent 调用 MCP Server（同样托管在 AgentCore Runtime 上），通过 AWS Support API 实现案例的查询、创建和总结

## 🛠️ 前置条件

### AWS服务要求
- Python 3.10+
- Jupyter Notebook或JupyterLab
- AWS CLI已配置适当权限
- 开通AWS Support API访问权限(商业或企业支持计划)

### ⚠️ 重要：Bedrock模型访问
在开始之前，**必须**在AWS Bedrock控制台中开通所需的模型访问权限：

1. 登录AWS控制台，进入Amazon Bedrock服务
2. 在左侧导航栏选择"Model access"(模型访问)
3. 点击"Modify model access"(管理模型访问)
4. 选择并启用以下推荐模型：
   - **Claude 3.7 Sonnet** (推荐用于复杂推理)
   - **Claude 3 Haiku** (推荐用于快速响应)
   - 或其他支持的Anthropic Claude模型
5. 提交访问请求并等待批准(通常几分钟内完成)

**注意**: 没有模型访问权限，Agent将无法正常工作。

## 📦 安装步骤

### 推荐安装顺序：先MCP，后Agent

#### 克隆仓库到本地
`git clone https://github.com/percy-han/AWS-Support-Case-Agent.git`

#### 第一步：MCP设置
1. 打开 `MCP/`目录
2. 在`config.py`中自定义变量
3. 打开`mcp_agentcore_deployment.ipynb`，**按顺序执行所有notebook单元格** - notebook包含所有必要的安装和配置步骤
4. 在notebook中可验证MCP服务器正常运行

#### 第二步：Agent设置
1. 打开 `Agent/`目录
2. 在`config.py`中自定义变量，确认`SECRETS_NAME`和`SECRETS_NAME`变量与MCP中的保持一致
3. 打开`support_case_agent.py`，同样修改`SECRET_ID`和`SSM_AGENT_ARN_PARAM`变量与MCP中的`SECRETS_NAME`和`SECRETS_NAME`保持一致
4. 打开`support_case_agent_deployment.ipynb`，**按顺序执行所有notebook单元格**
5. 等待Agent部署完成(可能需要几分钟)
6. 修改`support_case_agent_test.py`中`agent_arn`变量为实际Agent的arn
7. 在notebook中可验证调用Agent的效果

## 🚀 使用方法

### 可参考如下代码编写调用Agent的代码

调用Agent代码示例：

```import boto3
import json
import codecs
import argparse
import base64
import os
from IPython.display import Markdown, display
from boto3.session import Session

prompt_text = "请分析我过去半年的case并给出最佳实践建议和洞察"

def invoke_agent(prompt_text, attachment_path=None):
    boto_session = Session()
    REGION = boto_session.region_name

    agent_arn = launch_result.agent_arn  # ⚠️ 确保 launch_result 已经定义
    # agent_arn='arn:aws:bedrock-agentcore:us-west-2:xxxxxxxxxxxx:runtime/xxxxxxxxx'

    # 如果有附件，在prompt中添加附件处理指令
    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, 'rb') as f:
            file_content = base64.b64encode(f.read()).decode('utf-8')
        
        file_name = os.path.basename(attachment_path)
        prompt_text += f"""

需要上传附件：
- 文件名：{file_name}
- 文件内容（base64）：{file_content}

请先调用add_attachments_to_set工具上传此附件，然后在创建case或者回复case时使用返回的attachment_set_id。
"""

    agentcore_client = boto3.client("bedrock-agentcore", region_name=REGION)

    boto3_response = agentcore_client.invoke_agent_runtime(
        agentRuntimeArn=agent_arn,
        qualifier="DEFAULT",
        payload=json.dumps({"prompt": prompt_text})
    )

    print(f"boto3_response: {boto3_response}")

    # ---- 处理流式响应 ----
    if "text/event-stream" in boto3_response.get("contentType", ""):
        print("Processing streaming response with boto3:")
        content = []
        for line in boto3_response["response"].iter_lines(chunk_size=10):
            if line:
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    data = line[6:].replace('"', "")  # Remove "data: " prefix
                    data = data.replace("\\n", "\n")
                    print(f"{data}", end="")
                    content.append(data.replace('"', ""))
        # Display the complete streamed response
        full_response = " ".join(content)
        display(Markdown(full_response))
    else:
        try:
            events = []
            for event in boto3_response.get("response", []):
                events.append(event)
        except Exception as e:
            events = [f"Error reading EventStream: {e}"]

        if events:
            try:
                response_data = json.loads(events[0].decode("utf-8"))
                display(Markdown(response_data))
            except:
                print(f"Raw response: {events[0]}")


if __name__ == "__main__":
    print(f"Using prompt: {prompt_text}")
    #创建case或回复case时如果需要上传附件时用
    #invoke_agent(prompt_text,"/a/b/c.png")
    invoke_agent(prompt_text)
```
输出结果样例：
<img width="2171" height="752" alt="image" src="https://github.com/user-attachments/assets/319b8e59-6374-440c-9f12-10b29bac02aa" />


## 🔒 安全考虑

- 使用AWS IAM角色和策略进行安全访问
- 凭证存储在AWS Secrets Manager中
- 支持VPC端点进行私有连接
- 所有支持案例操作的审计日志

## 🆘 故障排除

### 常见问题

1. **模型访问错误**: 确保在Bedrock控制台中启用了模型访问
2. **权限错误**: 检查AWS凭证和IAM权限
3. **部署失败**: 查看CloudWatch日志获取详细错误信息
4. **MCP连接问题**: 验证MCP服务器状态和网络连接

### 日志位置

- Agent运行时日志Cloudwatch log: `/aws/bedrock-agentcore/runtimes/{Agent Runtime ID}-DEFAULT`
- CodeBuild日志CloudWatch log: `/aws/codebuild/bedrock-agentcore-{Agent Name}-builder`

## 🤝 贡献

1. Fork仓库
2. 创建功能分支
3. 进行更改
4. 如适用，添加测试
5. 提交Pull Request

## 📄 许可证

本项目基于Apache License 2.0许可证 - 详见LICENSE文件。

## 🆘 支持

如有问题和疑问：
1. 查看现有GitHub issues
2. 创建新issue并提供详细描述
3. 对于AWS特定问题，请参考AWS Support文档

## 🔄 版本历史

- **v1.0.0**: 初始版本，基本Agent和MCP集成
- **当前版本**: 增强的跨境电商支持功能

---

**注意**: 本项目需要AWS商业或企业支持计划才能完全访问AWS Support API。

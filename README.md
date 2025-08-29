# AWS Support Case Agent with MCP Integration

基于Bedrock Agent和模型上下文协议(MCP)的智能AWS支持案例管理系统，专为跨境电商IT支持场景设计。

## 🚀 功能特性

- **智能支持案例管理**: 自动化AWS支持案例创建、跟踪和解决
- **智能支持案例总结和洞察**: 支持只能对AWS Case进行总结分析并给出最佳实践和洞察
- **MCP集成**: 利用模型上下文协议增强工具能力
- **跨境电商专用**: 专为国际业务IT支持场景优化
- **Bedrock Agent Core**: 基于AWS Bedrock Agent Core构建，支持可扩展的AI交互
- **可对现有MCP Server做无缝移植**: 支持北京时间(UTC+8)的实时支持案例处理

## 📁 项目结构

```
support-agent/
├── MCP/                           # MCP实现
│   ├── utils.py                   # 工具函数
│   ├── MCP_On_AgentCore.ipynb     # MCP notebook界面
│   ├── requirements.txt           # MCP依赖
│   └── awslabs/                   # AWS Labs MCP服务器
│       └── aws_support_mcp_server/ # 支持专用MCP服务器
└── README.md                      # 本文件
├── Agent/                          # Bedrock Agent实现
│   ├── Case_Agent_On_AgentCore.ipynb   # Jupyter notebook界面
│   ├── requirements.txt           # Agent依赖
│   └── Dockerfile                 # Agent的Dockerfile
```

## 🏗️ 系统架构

<img width="813" height="422" alt="iShot_2025-08-29_01 08 37" src="https://github.com/user-attachments/assets/1ea5b964-68fb-40de-ba22-4c72befec92b" />


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

#### 第一步：MCP设置
1. 克隆仓库到本地
2. 打开 `MCP/MCP_On_AgentCore.ipynb`
3. **按顺序执行所有notebook单元格** - notebook包含所有必要的安装和配置步骤
4. 在notebook中可验证MCP服务器正常运行

#### 第二步：Agent设置  
1. 打开 `Agent/Case_Agent_On_AgentCore.ipynb`
2. **按顺序执行所有notebook单元格**
3. 等待Agent部署完成(可能需要几分钟)
4. 在notebook中可验证调用Agent的效果

## 🚀 使用方法

### 命令行界面(可选)

Case_Agent_On_AgentCore.ipynb notebook中有内置客户端调用Agent代码，可以直接使用：

```Python
import boto3
import json
import codecs
import argparse
from IPython.display import Markdown, display
from boto3.session import Session

prompt_text = "请分析我过去半年的case并给出最佳实践建议和洞察"

def invoke_agent(prompt_text):
    boto_session = Session()
    REGION = boto_session.region_name

    agent_arn = launch_result.agent_arn  # ⚠️ 确保 launch_result 已经定义
    # agent_arn='arn:aws:bedrock-agentcore:us-west-2:xxxxxxxxxxxx:runtime/agentcore_agent_invoke_agentcore_mcp_test-7OoavJDoxG'

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
    invoke_agent(prompt_text)
```

## 📋 Notebook工作流程

### Agent Notebook (`Agent/agent_on_Agentcore.ipynb`)

notebook自动化完整的agent部署过程：

1. **代码生成**: 使用 `%%writefile` 创建agent代码文件
2. **运行时配置**: 设置Bedrock Agent Core运行时
3. **AWS资源创建**: 自动创建：
   - ECR仓库
   - IAM执行角色
   - CodeBuild项目
4. **部署**: 使用CodeBuild将agent部署到AWS
5. **测试**: 提供交互式测试功能

### MCP Notebook (`MCP/MCP_On_AgentCore.ipynb`)

处理MCP服务器设置和集成：

1. **MCP服务器配置**: 设置AWS Support MCP服务器
2. **客户端设置**: 配置MCP客户端连接
3. **工具集成**: 将MCP工具与agent集成
4. **测试**: 验证MCP功能

### 部署架构

notebook部署以下AWS资源：

- **Bedrock Agent Core Runtime**: 托管agent逻辑
- **ECR Repository**: 存储容器镜像
- **IAM Roles**: 具有适当权限的执行和CodeBuild角色
- **CodeBuild Project**: 构建和部署agent
- **CloudWatch Logs**: Agent运行时日志

## 🔧 核心组件

### Agent Core (`Agent/`)

- **aws_support_agent_client.py**: 与AWS Support交互的主客户端
- **agentcore_agent_invoke_mcp_agentcore.py**: Agent Core和MCP之间的集成层

### MCP集成 (`MCP/`)

- **agent_invoke_mcp_tools_final.py**: MCP工具集成的最终实现
- **my_mcp_client_remote.py**: 分布式场景的远程MCP客户端
- **utils.py**: MCP操作的通用工具

### AWS Support MCP服务器 (`MCP/awslabs/aws_support_mcp_server/`)

用于AWS Support API集成的自定义MCP服务器实现。

## 🌐 跨境电商特性

- **多时区支持**: 支持北京时间(UTC+8)的国际运营
- **本地化支持**: 处理中英文支持场景
- **业务上下文**: 针对电商基础设施支持案例优化

## 🐳 Docker支持

Agent和MCP组件都包含用于容器化部署的Dockerfile：

```bash
# 构建Agent容器
cd Agent/
docker build -t aws-support-agent .

# 构建MCP容器
cd MCP/
docker build -t aws-support-mcp .
```

## 📊 使用场景示例

1. **自动化支持案例创建**: 基于CloudWatch告警创建支持案例
2. **案例状态跟踪**: 监控和更新支持案例进度
3. **知识库集成**: 利用AWS文档和最佳实践
4. **多服务故障排除**: 处理跨多个AWS服务的复杂场景

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

- Agent运行时日志: `/aws/bedrock-agentcore/runtimes/{agent-id}-DEFAULT`
- CodeBuild日志: AWS CodeBuild控制台
- MCP服务器日志: 在notebook输出中查看

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

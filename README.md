# AWS Support Case Agent with MCP Integration

A comprehensive AWS Support Case management system that combines Bedrock Agent with Model Context Protocol (MCP) for intelligent support case handling and cross-border e-commerce IT support.

## 🚀 Features

- **Intelligent Support Case Management**: Automated AWS Support case creation, tracking, and resolution
- **MCP Integration**: Leverages Model Context Protocol for enhanced tool capabilities
- **Cross-border E-commerce Focus**: Specialized for international business IT support scenarios
- **Bedrock Agent Core**: Built on AWS Bedrock Agent Core for scalable AI interactions
- **Multi-interface Support**: Both programmatic API and Jupyter Notebook interfaces
- **Real-time Processing**: Handles support cases with Beijing Time (UTC+8) awareness

## 📁 Project Structure

```
support-agent/
├── Agent/                          # Bedrock Agent implementation
│   ├── aws_support_agent_client.py # Main agent client
│   ├── agentcore_agent_invoke_mcp_agentcore.py # Agent core integration
│   ├── agent_on_Agentcore.ipynb   # Jupyter notebook interface
│   ├── requirements.txt           # Agent dependencies
│   └── Dockerfile                 # Agent containerization
├── MCP/                           # Model Context Protocol implementation
│   ├── agent_invoke_mcp_tools_final.py # Final MCP tools integration
│   ├── my_mcp_client_remote.py    # Remote MCP client
│   ├── utils.py                   # Utility functions
│   ├── MCP_On_AgentCore.ipynb     # MCP notebook interface
│   ├── requirements.txt           # MCP dependencies
│   └── awslabs/                   # AWS Labs MCP server
│       └── aws_support_mcp_server/ # Support-specific MCP server
└── README.md                      # This file
```

## 🛠️ Prerequisites

- Python 3.8+
- AWS CLI configured with appropriate permissions
- AWS Support API access (Business or Enterprise support plan)
- Bedrock Agent Core access

## 📦 Installation

### Agent Setup

```bash
cd Agent/
pip install -r requirements.txt
```

### MCP Setup

```bash
cd MCP/
pip install -r requirements.txt
```

## ⚙️ Configuration

### AWS Credentials

Ensure your AWS credentials are configured:

```bash
aws configure
```

### Required AWS Services

- AWS Bedrock
- AWS Support API
- AWS Systems Manager (for parameter storage)
- AWS Secrets Manager (for credential management)

### Environment Variables

Set up the following parameters in AWS Systems Manager:
- `/support_mcp_server/runtime/agent_arn` - Your Bedrock Agent ARN
- `support_mcp_server/cognito/credentials` - Cognito credentials in Secrets Manager

## 🚀 Usage

### Command Line Interface

```bash
# Run the agent with a custom prompt
python Agent/aws_support_agent_client.py --prompt "Create a support case for EC2 instance connectivity issues"
```

### Jupyter Notebook Interface

1. **Agent Interface**: Open `Agent/agent_on_Agentcore.ipynb`
2. **MCP Interface**: Open `MCP/MCP_On_AgentCore.ipynb`

### Programmatic Usage

```python
from agent_invoke_mcp_tools_final import invoke_agent_with_mcp

# Invoke agent with MCP tools
response = await invoke_agent_with_mcp("Help me troubleshoot S3 access issues")
print(response)
```

## 🔧 Key Components

### Agent Core (`Agent/`)

- **aws_support_agent_client.py**: Main client for interacting with AWS Support
- **agentcore_agent_invoke_mcp_agentcore.py**: Integration layer between Agent Core and MCP

### MCP Integration (`MCP/`)

- **agent_invoke_mcp_tools_final.py**: Final implementation of MCP tools integration
- **my_mcp_client_remote.py**: Remote MCP client for distributed scenarios
- **utils.py**: Common utilities for MCP operations

### AWS Support MCP Server (`MCP/awslabs/aws_support_mcp_server/`)

Custom MCP server implementation for AWS Support API integration.

## 🌐 Cross-border E-commerce Features

- **Multi-timezone Support**: Beijing Time (UTC+8) awareness for international operations
- **Localized Support**: Handles both English and Chinese support scenarios
- **Business Context**: Optimized for e-commerce infrastructure support cases

## 🐳 Docker Support

Both Agent and MCP components include Dockerfile for containerized deployment:

```bash
# Build Agent container
cd Agent/
docker build -t aws-support-agent .

# Build MCP container
cd MCP/
docker build -t aws-support-mcp .
```

## 📊 Example Use Cases

1. **Automated Support Case Creation**: Create support cases based on CloudWatch alarms
2. **Case Status Tracking**: Monitor and update support case progress
3. **Knowledge Base Integration**: Leverage AWS documentation and best practices
4. **Multi-service Troubleshooting**: Handle complex scenarios across multiple AWS services

## 🔒 Security Considerations

- Uses AWS IAM roles and policies for secure access
- Credentials stored in AWS Secrets Manager
- Support for VPC endpoints for private connectivity
- Audit logging for all support case operations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check existing GitHub issues
2. Create a new issue with detailed description
3. For AWS-specific issues, consult AWS Support documentation

## 🔄 Version History

- **v1.0.0**: Initial release with basic Agent and MCP integration
- **Current**: Enhanced cross-border e-commerce support features

---

**Note**: This project requires AWS Business or Enterprise support plan for full AWS Support API access.

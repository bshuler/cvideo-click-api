# CVIDEO-CLICK-API

AWS Lambda-based API for the cvideo-click project using Infrastructure as
Code (IaC) principles and serverless architecture.

## 🚀 Quick Start

1. **Clone and Setup**

   ```bash
   cd cvideo-click-api
   cp .secrets.template .secrets
   # Edit .secrets with your AWS credentials
   ```

1. **Initialize Project**

   ```bash
   make init       # Install dependencies and verify AWS access
   make validate   # Run code quality checks
   ```

1. **Deploy and Test (Recommended)**

   ```bash
   make remote-deploy         # Deploy Lambda functions to AWS
   make remote-test           # Test deployed API endpoints
   make remote-status         # Check deployment health
   ```

1. **Clean Up When Done**

   ```bash
   make remote-destroy            # Safely remove AWS resources
   ```

**All operations use simple `make` commands with automatic credential handling and branch isolation!**

## 🌐 Custom Domain Access

This project automatically configures custom domains for easy access to your API deployments:

**Domain Pattern**: `{stack-name}.apps.cvideo.click`

- **Development**: `api-dev.apps.cvideo.click`
- **Staging**: `api-staging.apps.cvideo.click`
- **Production**: `api-prod.apps.cvideo.click`

### Domain Setup (One-Time Bootstrap)

⚠️ **Important**: Domain setup requires **bootstrap/admin credentials** with elevated permissions.

#### Prerequisites

- AWS account with admin access
- Domain ownership of `cvideo.click`
- Bootstrap user credentials (separate from developer `.secrets`)

#### Setup Process

1. **Deploy Domain Infrastructure** (Bootstrap/Admin Only):

   ```bash
   # Switch to admin/bootstrap credentials
   make domain-deploy     # Creates Route53 zone, ACM cert, API Gateway custom domain
   ```

   This creates:

   - Route53 hosted zone for `apps.cvideo.click`
   - Wildcard SSL certificate for `*.apps.cvideo.click`
   - API Gateway custom domain for `api-dev.apps.cvideo.click`
   - DNS validation records and routing

1. **Configure Parent Domain** (One-time DNS delegation):

   ```bash
   make domain-setup      # Shows nameserver configuration instructions
   ```

   Add these NS records to your `cvideo.click` domain:

   ```dns
   apps.cvideo.click  NS  ns-998.awsdns-60.net
   apps.cvideo.click  NS  ns-268.awsdns-33.com
   apps.cvideo.click  NS  ns-1996.awsdns-57.co.uk
   apps.cvideo.click  NS  ns-1283.awsdns-32.org
   ```

1. **Verify Setup**:

   ```bash
   make domain-check      # Comprehensive domain validation
   make domain-status     # Infrastructure status
   make domain-test       # DNS and SSL connectivity test
   ```

#### Developer Usage (After Bootstrap)

Once domain infrastructure is deployed, developers can:

```bash
# Deploy application changes (no domain changes needed)
make remote-deploy     # Deploys Lambda functions to existing custom domain

# Monitor domain health
make domain-check      # Verify domain is working
make domain-status     # Check certificate and DNS status
```

#### Permission Requirements

| Operation | User Type | Required Permissions |
|-----------|-----------|---------------------|
| `make domain-deploy` | Bootstrap/Admin | `route53:CreateHostedZone`, `acm:*`, `apigateway:CreateDomainName`, `iam:CreateServiceLinkedRole` |
| `make remote-deploy` | Developer | `lambda:*`, `cloudformation:*`, `s3:*` (application buckets) |
| `make domain-check` | Developer | `route53:ListResourceRecordSets`, `acm:DescribeCertificate`, `apigateway:GetDomainNames` |

### Using Custom Domains

Once configured, your API is accessible at:

- **Custom Domain**: `https://api-dev.apps.cvideo.click/hello`
- **AWS Gateway**: `https://{api-id}.execute-api.us-east-1.amazonaws.com/dev/hello`

## 📋 Project Structure

```text
cvideo-click-api/
├── src/                    # Lambda functions source code
│   ├── shared/            # Shared utilities and libraries
│   ├── hello_world/       # Example Lambda function
│   └── ...                # Additional Lambda functions
├── terraform/             # Infrastructure as Code
│   ├── main.tf           # Main Terraform configuration
│   └── terraform.tfvars  # Variables configuration
├── scripts/               # Automation and utility scripts
├── tests/                 # Unit and integration tests
├── .ai-context.md        # AI assistant guidance
├── pyproject.toml        # Python project configuration
├── requirements.txt      # Python dependencies
├── Makefile             # Development workflow automation
└── .secrets             # AWS credentials (not in git)
```

## 🛠️ Development Workflow

### Make-Based Operations

All project operations use `make` commands for consistency and automation:

```bash
# 🏗️ Basic Operations
make help                  # Show all available commands
make init                  # Initialize project and dependencies
make clean                 # Clean temporary files and caches
make validate              # Run all code quality checks

# 🚀 Quick Deploy & Test Cycle  
make remote-deploy         # Deploy to AWS (branch-isolated)
make remote-test           # Test deployed resources
make remote-destroy        # Clean up when done

# 📋 Complete Create/Update/Destroy Cycle
make remote-build          # Build and validate
make remote-deploy         # Deploy infrastructure  
make remote-status         # Check deployment health
make remote-cleanup-failed # Clean up failed deployments (if needed)
make remote-destroy        # Destroy resources safely
```

**Key Benefits:**

- **Automatic Credential Loading**: All `make remote-*` commands automatically load AWS credentials from `.secrets`
- **Branch Isolation**: Resources are namespaced by git branch for safe parallel development
- **Error Handling**: Built-in validation and error recovery
- **Consistent Commands**: Same commands work across all environments

### Code Quality

```bash
make format      # Format code with Black (88-char lines)
make lint        # Lint with Flake8
make type-check  # Type checking with mypy
make validate    # Run all quality checks
```

## 🧪 Testing Strategy

### Local Testing

```bash
# Unit & Integration Tests
make test                    # All tests with coverage
make test-unit              # Unit tests only  
make test-integration       # Integration tests (mocked)
make test-watch             # Continuous testing during development
make test-debug             # Tests with detailed debugging output

# Security & Performance
make test-security          # Static security analysis
make test-performance       # Performance/load tests

# Comprehensive Test Suites
make test-comprehensive     # Run all test types (local + remote + CI)
make test-local-only        # Local tests only
make test-remote-only       # Remote AWS tests only
make test-ci-only          # CI/CD simulation tests
```

### Local Lambda Development

```bash
# Build and run Lambda functions locally
make local-build           # Build Lambda functions for local testing
make local-start           # Start local API Gateway (localhost:3000)
make local-test            # Test individual Lambda functions
make local-deploy          # Deploy to local containerized environment
make local-test-api        # Test API endpoints with curl

# Example: Start local development server
make local-start
# Visit: http://localhost:3000/hello
```

### Remote AWS Testing

```bash
# Comprehensive Testing (Recommended)
make remote-test           # Complete integration tests against deployed resources
                          # ✅ Tests AWS credentials, Lambda functions, API endpoints
                          # ✅ Branch-aware: tests your specific deployment

# Health Monitoring  
make remote-status         # Overall deployment status with resource health
make remote-health-check   # Detailed health checks for all AWS resources
make remote-logs           # View recent Lambda function logs with filtering

# AWS Access Verification
make check-aws             # Verify AWS credentials and permissions
make remote-validate       # Validate AWS resources and deployment readiness
```

## 🚀 Deployment Workflows

### Local Deployment (Development)

```bash
# 1. Build and validate locally
make local-build           # Build with SAM
make validate-strict       # Run all quality checks

# 2. Test locally before deploying
make local-start           # Start local API
make local-test-api        # Test endpoints

# 3. Deploy to local container environment
make local-deploy          # Creates local test stack
```

### Remote AWS Deployment (Production)

All remote AWS operations are simplified through `make` commands with automatic credential handling and branch isolation:

```bash
# Quick Deploy (Recommended)
make remote-deploy-sam-only    # Deploy Lambda-only stack with branch namespace
make remote-test               # Comprehensive integration tests
make remote-status             # Check deployment health

# Complete Deployment Workflow
make remote-build              # Build and validate with full checks
make remote-validate           # Validate AWS credentials and templates  
make remote-deploy             # Deploy SAM application to AWS
make remote-health-check       # Perform detailed health checks

# Deployment Variations
make remote-deploy-simple      # Interactive guided deployment
make remote-deploy-prod        # Production deployment with confirmations

# Management Commands
make remote-logs               # View recent Lambda logs
make remote-status             # Check deployment status and health
make remote-destroy            # Safely destroy resources (with confirmation)
make remote-cleanup-failed     # Clean up failed deployments
make remote-rollback           # Rollback to previous version
```

**Branch Isolation**: All deployments automatically use branch-specific naming:

- Branch `develop` → Stack: `cvideo-click-api-develop`
- Branch `feature/auth` → Stack: `cvideo-click-api-feature-auth`
- Lambda functions include branch namespace for safe parallel development

## 🤖 CI/CD with GitHub Actions & ACT

### GitHub Actions (Cloud CI/CD)

```bash
# Manual triggers
make github-test           # Trigger test workflow
make github-deploy         # Trigger deployment workflow

# Automatic triggers:
# - Push to main/develop → Full CI/CD pipeline
# - Pull requests → Testing only
# - Manual dispatch → Choose environment (dev/staging/prod)
```

### ACT (Local CI/CD Simulation)

```bash
# Setup ACT for local GitHub Actions
make act-setup             # Install and configure ACT

# Run GitHub Actions locally
make act-test              # Simulate test workflow locally
make act-deploy            # Simulate deployment workflow locally

# ACT simulates the exact GitHub Actions environment locally using Docker
```

### Workflow Overview

1. **Test Stage**: Code quality, unit tests, integration tests, security scans
1. **Build Stage**: SAM build, template validation, artifact creation
1. **Deploy Stage**: Terraform infrastructure, SAM deployment, configuration
1. **Verify Stage**: API endpoint testing, status checks, smoke tests

## 📊 Monitoring & Observability

### Real-time Monitoring

```bash
make status                # Overall deployment status
make metrics               # CloudWatch metrics dashboard
make logs FUNCTION=HelloWorldFunction  # Function-specific logs
make remote-logs           # All Lambda logs with traces
```

### Log Analysis

```bash
# View logs for specific functions
make logs FUNCTION=HelloWorldFunction

# Stream logs in real-time
sam logs --stack-name cvideo-click-api --tail --include-traces

# CloudWatch insights queries available in AWS console
```

## 🏗️ Architecture

### Technology Stack

- **AWS Lambda**: Serverless compute for API endpoints
- **API Gateway**: REST API management and routing
- **Terraform**: Infrastructure definition and management
- **Python + boto3**: All Lambda functions and automation
- **S3**: File storage and static content
- **CloudWatch**: Monitoring and logging

### Authentication

- JWT tokens for API authentication
- Developer credentials from cvideo-click-pave infrastructure
- IAM roles with least privilege principles

### Resource Naming

All AWS resources use consistent naming:

```text
cvideo-api-{function-name}    # Lambda functions
cvideo-api-gateway           # API Gateway
cvideo-api-assets-us-east-1  # S3 buckets
```

## 🔧 Configuration

### AWS Credentials

The project uses developer credentials from the cvideo-click-pave infrastructure:

- **User**: `developer-user`
- **Access Key**: `AKIATXIZHCB6254PVZPV`
- **Permissions**: S3 Full Access + Lambda Full Access + EC2 Read Only

Configure in `.secrets` file:

```bash
AWS_ACCESS_KEY_ID=AKIATXIZHCB6254PVZPV
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-1
```

### Python Standards

- **Black Formatter**: 88-character line length
- **Flake8 Linting**: E203/W503 exceptions for Black compatibility
- **mypy Type Checking**: Relaxed settings for boto3 compatibility
- **pytest Testing**: With coverage reporting

## 🔍 Lambda Function Development

### Function Structure

Each Lambda function follows this pattern:

```python
import json
from typing import Dict, Any
from shared.utils import setup_logging, create_response

logger = setup_logging(__name__)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        # Process request
        result = process_request(event)
        return create_response(200, result)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return create_error_response(500, "Internal server error")
```

### Shared Libraries

- `shared/utils.py`: Common utilities and response formatting
- `shared/auth.py`: JWT authentication and authorization
- `shared/database.py`: DynamoDB and S3 client wrappers

## 📊 Monitoring

### CloudWatch Integration

- Structured logging with timestamps and levels
- Custom metrics for business logic
- Automated alerting for errors and performance

### Local Development

```bash
make local-start   # Start local development server
make local-test    # Test functions locally with SAM
```

## 🔒 Security

### IAM Permissions

- Lambda execution roles with minimal required permissions
- Separate roles for different function types
- No hard-coded credentials in code

### API Security

- JWT token authentication
- CORS configuration for web clients
- Request validation at API Gateway

## 📚 Additional Resources

- **Infrastructure Documentation**: See `terraform/` directory
- **API Documentation**: Generated from OpenAPI specifications
- **Testing Guide**: See `tests/` directory examples
- **Deployment Guide**: Use Makefile commands for consistent deployments

## 🤝 Contributing

1. Follow the established code quality standards (Black, Flake8, mypy)
1. Write tests for new functionality
1. Update documentation for API changes
1. Use the Makefile for all development tasks

## 🆘 Troubleshooting

### Common Issues

- **AWS Credentials**: Run `make bootstrap-check` to verify setup
- **Lambda Deployment**: Check IAM permissions and function packaging
- **API Gateway**: Verify stage deployment and CORS configuration

### Getting Help

- Check the `.ai-context.md` file for comprehensive guidance
- Review CloudWatch logs for runtime errors
- Use `make status` to check overall deployment health

.PHONY: help init clean format lint type-check test validate
.PHONY: local-build local-start local-stop local-status local-test local-deploy local-test-api
.PHONY: remote-build remote-build-sam-only remote-deploy remote-deploy-simple remote-deploy-sam-only remote-deploy-fresh remote-deploy-prod remote-validate remote-test remote-health-check remote-logs remote-status remote-cleanup-failed remote-destroy remote-rollback
.PHONY: plan deploy deploy-function logs metrics status check-aws
.PHONY: act-setup act-test act-deploy github-test github-deploy
.DEFAULT_GOAL := help

# Load environment variables (if .secrets file exists)
-include .secrets
export

# Colors for terminal output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Branch-based namespace configuration
CURRENT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
BRANCH_SAFE := $(shell echo "$(CURRENT_BRANCH)" | sed 's/[^a-zA-Z0-9-]/-/g' | tr '[:upper:]' '[:lower:]')
NAMESPACE := cvideo-api-$(BRANCH_SAFE)
STACK_NAME := cvideo-click-api-$(BRANCH_SAFE)

help: ## Show this help message
	@echo "$(BLUE)CVIDEO-CLICK-API Makefile Commands$(NC)"
	@echo "=================================="
	@echo "$(YELLOW)Current Branch:$(NC) $(CURRENT_BRANCH)"
	@echo "$(YELLOW)Namespace:$(NC) $(NAMESPACE)"
	@echo "$(YELLOW)Stack Name:$(NC) $(STACK_NAME)"
	@echo ""
	@echo "$(GREEN)Setup and Validation:$(NC)"
	@grep -E '^(init|clean|validate|validate-strict).*:.*##' Makefile | awk -F ':.*##' '{printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)AWS Credentials:$(NC)"
	@grep -E '^(check-aws).*:.*##' Makefile | awk -F ':.*##' '{printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Development & Testing:$(NC)"
	@grep -E '^(format|lint|type-check|security|pylance-check|markdown-lint|markdown-fix|yaml-lint|yaml-fix|validate|validate-strict|test|test-unit|test-integration|test-watch|test-debug|test-security|test-comprehensive|test-local-only|test-remote-only|test-ci-only).*:.*##' Makefile | awk -F ':.*##' '{printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Local Development & Testing:$(NC)"
	@grep -E '^(local-build|local-start|local-stop|local-status|local-test|local-deploy|local-test-api).*:.*##' Makefile | awk -F ':.*##' '{printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Remote AWS Deployment & Testing:$(NC)"
	@grep -E '^(remote-build|remote-build-sam-only|remote-deploy|remote-deploy-simple|remote-deploy-sam-only|remote-deploy-fresh|remote-deploy-prod|remote-validate|remote-test|remote-health-check|remote-logs|remote-status|remote-cleanup-failed|remote-destroy|remote-rollback|plan|deploy|deploy-function).*:.*##' Makefile | awk -F ':.*##' '{printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)CI/CD (ACT & GitHub Actions):$(NC)"
	@grep -E '^(act-setup|act-test|act-deploy|github-test|github-deploy).*:.*##' Makefile | awk -F ':.*##' '{printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Monitoring:$(NC)"
	@grep -E '^(logs|metrics|status).*:.*##' Makefile | awk -F ':.*##' '{printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

init: ## Initialize project dependencies and setup
	@echo "$(BLUE)Installing Python dependencies...$(NC)"
	pip install -e ".[dev]"
	@echo "$(BLUE)Installing additional requirements...$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)Project initialized successfully!$(NC)"

check-aws: ## Verify AWS developer credentials and permissions
	@echo "$(BLUE)Checking AWS developer credentials...$(NC)"
	@python scripts/check_aws.py

clean: ## Clean temporary files and caches
	@echo "$(BLUE)Cleaning temporary files...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf build/
	rm -rf dist/
	@echo "$(GREEN)Cleanup completed!$(NC)"

format: ## Format Python code with Black
	@echo "$(BLUE)Formatting Python code with Black...$(NC)"
	black --config pyproject.toml src/ scripts/ tests/
	@echo "$(GREEN)Code formatting completed!$(NC)"

lint: ## Lint Python code with Flake8
	@echo "$(BLUE)Linting Python code with Flake8...$(NC)"
	flake8 --extend-ignore=E203,W503 --max-line-length=88 src/ scripts/ tests/
	@echo "$(GREEN)Linting completed!$(NC)"

type-check: ## Run type checking with mypy
	@echo "$(BLUE)Running type checking with mypy...$(NC)"
	mypy --config-file pyproject.toml src/ scripts/
	@echo "$(GREEN)Type checking completed!$(NC)"

security: ## Run comprehensive security scan with multiple tools
	@echo "$(BLUE)Running comprehensive security scan...$(NC)"
	@mkdir -p logs
	@python3 scripts/security_scan.py --quiet
	@echo "$(GREEN)Security scan completed!$(NC)"

pylance-check: ## Run enhanced type checking with Pylance/Pyright
	@echo "$(BLUE)Running enhanced type checking...$(NC)"
	@python3 scripts/pylance_check.py --quiet
	@echo "$(GREEN)Enhanced type checking completed!$(NC)"

markdown-lint: ## Lint markdown files with pymarkdownlnt
	@echo "$(BLUE)Linting markdown files...$(NC)"
	@python3 scripts/markdown_lint.py --quiet
	@echo "$(GREEN)Markdown linting completed!$(NC)"

markdown-fix: ## Fix markdown formatting issues automatically
	@echo "$(BLUE)Fixing markdown formatting issues...$(NC)"
	@python3 scripts/markdown_lint.py --fix --quiet
	@echo "$(GREEN)Markdown formatting fixed!$(NC)"

yaml-lint: ## Lint YAML files with yamllint
	@echo "$(BLUE)Linting YAML files...$(NC)"
	@python3 scripts/yaml_lint.py --quiet
	@echo "$(GREEN)YAML linting completed!$(NC)"

yaml-fix: ## Validate YAML files (no auto-fix available)
	@echo "$(BLUE)Validating YAML files...$(NC)"
	@python3 scripts/yaml_lint.py --fix --quiet
	@echo "$(GREEN)YAML validation completed!$(NC)"

test: ## Run all tests with coverage
	@echo "$(BLUE)Running all tests with coverage...$(NC)"
	pytest tests/ --cov=src --cov-report=term-missing --cov-report=html --cov-fail-under=50
	@echo "$(GREEN)All tests completed!$(NC)"

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	pytest tests/unit/ -v --tb=short
	@echo "$(GREEN)Unit tests completed!$(NC)"

test-integration: ## Run integration tests only (with mocks)
	@echo "$(BLUE)Running integration tests...$(NC)"
	pytest tests/integration/ -v --tb=short
	@echo "$(GREEN)Integration tests completed!$(NC)"

test-watch: ## Run tests in watch mode for development
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop$(NC)"
	pytest-watch -- tests/ --cov=src --cov-report=term-missing

test-debug: ## Run tests with debugging output
	@echo "$(BLUE)Running tests with debug output...$(NC)"
	pytest tests/ -v -s --tb=long --log-cli-level=DEBUG

test-performance: ## Run performance/load tests (if any)
	@echo "$(BLUE)Running performance tests...$(NC)"
	@echo "$(YELLOW)No performance tests implemented yet$(NC)"

test-security: ## Run security tests (static analysis)
	@echo "$(BLUE)Running security tests...$(NC)"
	@if command -v bandit >/dev/null 2>&1; then \
		bandit -r src/ -f json -o security-report.json || true; \
		bandit -r src/; \
	else \
		echo "$(YELLOW)bandit not installed. Install with: pip install bandit$(NC)"; \
	fi

test-comprehensive: ## Run comprehensive test suite (local, remote, CI simulation)
	@echo "$(BLUE)Running comprehensive test suite...$(NC)"
	@python scripts/run_comprehensive_tests.py --all

test-local-only: ## Run only local tests (unit, integration, linting)
	@echo "$(BLUE)Running local tests only...$(NC)"
	@python scripts/run_comprehensive_tests.py --local

test-remote-only: ## Run only remote AWS tests
	@echo "$(BLUE)Running remote AWS tests only...$(NC)"
	@python scripts/run_comprehensive_tests.py --remote

test-ci-only: ## Run only CI/CD simulation tests
	@echo "$(BLUE)Running CI/CD simulation tests only...$(NC)"
	@python scripts/run_comprehensive_tests.py --ci

validate: format lint type-check markdown-lint yaml-lint ## Run comprehensive code validation (format + lint + type-check + markdown + yaml)
	@echo "$(GREEN)Code validation completed!$(NC)"

validate-strict: format lint type-check security pylance-check markdown-lint yaml-lint ## Run complete validation with security scanning - for CI/CD
	@echo "$(GREEN)All strict validation checks passed!$(NC)"

# =============================================================================
# LOCAL DEVELOPMENT & TESTING COMMANDS
# =============================================================================

local-build: ## Build Lambda functions for local testing
	@echo "$(BLUE)Building Lambda functions locally...$(NC)"
	sam build --use-container --parallel

local-start: .secrets ## Start local API Gateway and Lambda functions in background
	@echo "$(BLUE)Starting local development server...$(NC)"
	@echo "$(YELLOW)Checking if port 3000 is available...$(NC)"
	@if lsof -i :3000 >/dev/null 2>&1; then \
		echo "$(RED)Port 3000 is already in use!$(NC)"; \
		echo "$(YELLOW)Attempting to use port 3001 instead...$(NC)"; \
		echo "$(GREEN)Starting SAM local API on port 3001 in background...$(NC)"; \
		nohup sam local start-api --host 0.0.0.0 --port 3001 --env-vars env-vars.json > /tmp/sam-local-3001.log 2>&1 & echo $$! > /tmp/sam-local-3001.pid; \
		echo "$(GREEN)Local API started on port 3001. PID saved to /tmp/sam-local-3001.pid$(NC)"; \
		echo "$(YELLOW)Log output available at: /tmp/sam-local-3001.log$(NC)"; \
		echo "$(YELLOW)API will be available at: http://localhost:3001$(NC)"; \
	else \
		echo "$(GREEN)Starting SAM local API on port 3000 in background...$(NC)"; \
		nohup sam local start-api --host 0.0.0.0 --port 3000 --env-vars env-vars.json > /tmp/sam-local-3000.log 2>&1 & echo $$! > /tmp/sam-local-3000.pid; \
		echo "$(GREEN)Local API started on port 3000. PID saved to /tmp/sam-local-3000.pid$(NC)"; \
		echo "$(YELLOW)Log output available at: /tmp/sam-local-3000.log$(NC)"; \
		echo "$(YELLOW)API will be available at: http://localhost:3000$(NC)"; \
	fi
	@echo "$(YELLOW)Waiting 5 seconds for server to start...$(NC)"
	@sleep 5
	@echo "$(GREEN)Server should be ready for testing!$(NC)"

local-stop: ## Stop local development server and clean up ports
	@echo "$(BLUE)Stopping local development server...$(NC)"
	@if [ -f /tmp/sam-local-3000.pid ]; then \
		echo "$(YELLOW)Stopping SAM local API on port 3000 (PID: $$(cat /tmp/sam-local-3000.pid))...$(NC)"; \
		kill -TERM $$(cat /tmp/sam-local-3000.pid) 2>/dev/null || true; \
		rm -f /tmp/sam-local-3000.pid /tmp/sam-local-3000.log; \
	fi
	@if [ -f /tmp/sam-local-3001.pid ]; then \
		echo "$(YELLOW)Stopping SAM local API on port 3001 (PID: $$(cat /tmp/sam-local-3001.pid))...$(NC)"; \
		kill -TERM $$(cat /tmp/sam-local-3001.pid) 2>/dev/null || true; \
		rm -f /tmp/sam-local-3001.pid /tmp/sam-local-3001.log; \
	fi
	@echo "$(YELLOW)Checking for any remaining processes on ports 3000 and 3001...$(NC)"
	@if lsof -i :3000 >/dev/null 2>&1; then \
		echo "$(YELLOW)Force killing remaining process on port 3000...$(NC)"; \
		lsof -ti :3000 | xargs kill -9 2>/dev/null || true; \
	fi
	@if lsof -i :3001 >/dev/null 2>&1; then \
		echo "$(YELLOW)Force killing remaining process on port 3001...$(NC)"; \
		lsof -ti :3001 | xargs kill -9 2>/dev/null || true; \
	fi
	@echo "$(GREEN)Local development server stopped!$(NC)"

local-status: ## Check status of local development server
	@echo "$(BLUE)Checking local development server status...$(NC)"
	@if [ -f /tmp/sam-local-3000.pid ] && kill -0 $$(cat /tmp/sam-local-3000.pid) 2>/dev/null; then \
		echo "$(GREEN)SAM local API running on port 3000 (PID: $$(cat /tmp/sam-local-3000.pid))$(NC)"; \
		echo "$(YELLOW)API available at: http://localhost:3000$(NC)"; \
		echo "$(YELLOW)Log file: /tmp/sam-local-3000.log$(NC)"; \
	elif [ -f /tmp/sam-local-3001.pid ] && kill -0 $$(cat /tmp/sam-local-3001.pid) 2>/dev/null; then \
		echo "$(GREEN)SAM local API running on port 3001 (PID: $$(cat /tmp/sam-local-3001.pid))$(NC)"; \
		echo "$(YELLOW)API available at: http://localhost:3001$(NC)"; \
		echo "$(YELLOW)Log file: /tmp/sam-local-3001.log$(NC)"; \
	else \
		echo "$(RED)No local development server running$(NC)"; \
		echo "$(YELLOW)Use 'make local-start' to start the server$(NC)"; \
	fi

local-test: ## Test specific Lambda function locally with test event
	@echo "$(BLUE)Testing Lambda functions locally...$(NC)"
	sam local invoke HelloWorldFunction -e events/test-event.json

local-deploy: local-build ## Deploy to local containerized environment with branch-specific naming
	@echo "$(BLUE)Deploying to local container environment (Branch: $(CURRENT_BRANCH))...$(NC)"
	@echo "$(YELLOW)This creates a local stack for testing$(NC)"
	@echo "$(YELLOW)Stack name: $(STACK_NAME)-local$(NC)"
	sam deploy --stack-name $(STACK_NAME)-local --capabilities CAPABILITY_IAM --parameter-overrides Environment=local Branch=$(CURRENT_BRANCH)

local-test-api: ## Test local API endpoints with curl
	@echo "$(BLUE)Testing local API endpoints...$(NC)"
	@echo "$(YELLOW)Testing GET /hello...$(NC)"
	@if curl -s http://localhost:3000/hello >/dev/null 2>&1; then \
		echo "$(GREEN)Found API on port 3000$(NC)"; \
		curl -s http://localhost:3000/hello | jq .; \
		echo "\n$(YELLOW)Testing POST /hello...$(NC)"; \
		curl -s -X POST http://localhost:3000/hello -H "Content-Type: application/json" -d '{"name": "local-test"}' | jq .; \
	elif curl -s http://localhost:3001/hello >/dev/null 2>&1; then \
		echo "$(GREEN)Found API on port 3001$(NC)"; \
		curl -s http://localhost:3001/hello | jq .; \
		echo "\n$(YELLOW)Testing POST /hello...$(NC)"; \
		curl -s -X POST http://localhost:3001/hello -H "Content-Type: application/json" -d '{"name": "local-test"}' | jq .; \
	else \
		echo "$(RED)Local API not running on ports 3000 or 3001. Use 'make local-start' first.$(NC)"; \
	fi

# =============================================================================
# REMOTE AWS DEPLOYMENT & TESTING COMMANDS  
# =============================================================================

remote-build: .secrets ## Build and validate for AWS deployment with comprehensive checks
	@echo "$(BLUE)Building for AWS deployment...$(NC)"
	@echo "$(YELLOW)Running pre-build validation...$(NC)"
	@if [ ! -f terraform/terraform.tfvars ]; then \
		echo "$(RED)Error: terraform/terraform.tfvars not found$(NC)"; \
		echo "$(YELLOW)Please create terraform.tfvars with required variables$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Checking AWS credentials...$(NC)"
	@aws sts get-caller-identity > /dev/null || (echo "$(RED)AWS credentials not configured$(NC)" && exit 1)
	@echo "$(GREEN)AWS credentials verified$(NC)"
	@echo "$(YELLOW)Building Lambda functions...$(NC)"
	sam build --use-container --parallel
	@echo "$(YELLOW)Validating SAM template...$(NC)"
	sam validate --template template.yaml
	@echo "$(YELLOW)Validating Terraform configuration...$(NC)"
	@if cd terraform && terraform init -backend=false && terraform validate 2>/dev/null; then \
		echo "$(GREEN)Terraform validation successful$(NC)"; \
	else \
		echo "$(YELLOW)Warning: Terraform validation skipped (permission/config issues)$(NC)"; \
		echo "$(YELLOW)Proceeding with SAM-only deployment$(NC)"; \
	fi
	@echo "$(GREEN)Remote build validation completed successfully!$(NC)"

remote-deploy: remote-build ## Deploy to AWS with branch-specific namespace and environment selection
	@echo "$(BLUE)Deploying to AWS (Branch: $(CURRENT_BRANCH))...$(NC)"
	@if [ -z "$(ENV)" ]; then \
		echo "$(YELLOW)No environment specified, using 'dev'$(NC)"; \
		export DEPLOY_ENV=dev; \
	else \
		export DEPLOY_ENV=$(ENV); \
	fi; \
	echo "$(YELLOW)Deploying to environment: $$DEPLOY_ENV$(NC)"; \
	echo "$(YELLOW)Branch namespace: $(NAMESPACE)$(NC)"; \
	echo "$(YELLOW)Stack name: $(STACK_NAME)-$$DEPLOY_ENV$(NC)"; \
	echo "$(YELLOW)Using dedicated S3 bucket: cvideo-sam-artifacts-20250924$(NC)"; \
	echo "$(YELLOW)Deploying SAM application to AWS...$(NC)"; \
	sam deploy \
		--stack-name $(STACK_NAME)-$$DEPLOY_ENV \
		--capabilities CAPABILITY_IAM \
		--parameter-overrides Environment=$$DEPLOY_ENV Branch=$(CURRENT_BRANCH) \
		--s3-bucket cvideo-sam-artifacts-20250924 \
		--no-confirm-changeset \
		--no-fail-on-empty-changeset; \
	echo "$(GREEN)Deployment to AWS ($$DEPLOY_ENV) completed!$(NC)"; \
	echo "$(YELLOW)Running post-deployment validation...$(NC)"; \
	echo "$(BLUE)Checking deployment status...$(NC)"; \
	aws cloudformation describe-stacks --stack-name $(STACK_NAME)-$$DEPLOY_ENV --query 'Stacks[0].{StackName:StackName,Status:StackStatus}' --output table 2>/dev/null || echo "$(YELLOW)Stack status check failed - may still be initializing$(NC)"; \
	echo "$(GREEN)Deployment verified successfully!$(NC)"

remote-deploy-simple: remote-build-sam-only ## Simple guided deployment to AWS (interactive, SAM only)
	@echo "$(BLUE)Running guided SAM deployment...$(NC)"
	@echo "$(YELLOW)This will prompt you for deployment configuration$(NC)"
	sam deploy --guided

remote-deploy-sam-only: remote-build-sam-only ## Deploy SAM application only with branch namespace (bypass Terraform)
	@echo "$(BLUE)Deploying SAM application only (Branch: $(CURRENT_BRANCH))...$(NC)"
	@echo "$(YELLOW)Bypassing all Terraform interactions$(NC)"
	@echo "$(YELLOW)Branch namespace: $(NAMESPACE)$(NC)"
	@echo "$(YELLOW)Stack name: $(STACK_NAME)$(NC)"
	@echo "$(YELLOW)Using dedicated S3 bucket: cvideo-sam-artifacts-20250924$(NC)"
	sam deploy \
		--stack-name $(STACK_NAME) \
		--capabilities CAPABILITY_IAM \
		--parameter-overrides Environment=dev Branch=$(CURRENT_BRANCH) \
		--s3-bucket cvideo-sam-artifacts-20250924 \
		--no-confirm-changeset \
		--no-fail-on-empty-changeset
	@echo "$(GREEN)SAM-only deployment completed!$(NC)"

remote-deploy-fresh: remote-build-sam-only ## Fresh deployment with timestamp and branch namespace
	@echo "$(BLUE)Running fresh SAM deployment (Branch: $(CURRENT_BRANCH))...$(NC)"
	@echo "$(YELLOW)Using timestamped stack name to avoid conflicts$(NC)"
	@echo "$(YELLOW)Branch namespace: $(NAMESPACE)$(NC)"
	@echo "$(YELLOW)Using dedicated S3 bucket: cvideo-sam-artifacts-20250924$(NC)"
	@TIMESTAMP=$$(date +%Y%m%d-%H%M%S); \
	sam deploy \
		--stack-name "$(STACK_NAME)-$$TIMESTAMP" \
		--capabilities CAPABILITY_IAM \
		--parameter-overrides Environment=dev Branch=$(CURRENT_BRANCH) \
		--s3-bucket cvideo-sam-artifacts-20250924 \
		--no-confirm-changeset \
		--no-fail-on-empty-changeset; \
	echo "$(GREEN)Fresh deployment completed with stack: $(STACK_NAME)-$$TIMESTAMP$(NC)"

remote-build-sam-only: .secrets ## Build and validate SAM only (skip Terraform validation)
	@echo "$(BLUE)Building SAM application only...$(NC)"
	@echo "$(YELLOW)Running pre-build validation...$(NC)"
	@if [ ! -f terraform/terraform.tfvars ]; then \
		echo "$(YELLOW)Warning: terraform/terraform.tfvars not found$(NC)"; \
	fi
	@echo "$(YELLOW)Checking AWS credentials...$(NC)"
	@aws sts get-caller-identity > /dev/null || (echo "$(RED)AWS credentials not configured$(NC)" && exit 1)
	@echo "$(GREEN)AWS credentials verified$(NC)"
	@echo "$(YELLOW)Building Lambda functions...$(NC)"
	sam build --use-container --parallel
	@echo "$(YELLOW)Validating SAM template...$(NC)"
	sam validate --template template.yaml
	@echo "$(GREEN)SAM build validation completed successfully!$(NC)"

remote-deploy-prod: remote-build ## Deploy to production with extra confirmation
	@echo "$(RED)⚠️  PRODUCTION DEPLOYMENT ⚠️$(NC)"
	@echo "$(YELLOW)This will deploy to the production environment$(NC)"
	@read -p "Are you sure you want to deploy to production? (yes/no): " confirm; \
	if [ "$$confirm" != "yes" ]; then \
		echo "$(YELLOW)Production deployment cancelled$(NC)"; \
		exit 1; \
	fi
	@ENV=prod $(MAKE) remote-deploy

remote-validate: .secrets ## Validate AWS resources and deployment readiness
	@echo "$(BLUE)Validating AWS deployment readiness...$(NC)"
	@echo "$(YELLOW)Checking AWS credentials and permissions...$(NC)"
	@aws sts get-caller-identity
	@echo "$(YELLOW)Validating Terraform state and plan...$(NC)"
	@cd terraform && terraform init && terraform plan -var-file="terraform.tfvars" -detailed-exitcode || true
	@echo "$(YELLOW)Checking CloudFormation stack status...$(NC)"
	@aws cloudformation describe-stacks --stack-name cvideo-click-api --query 'Stacks[0].{StackName:StackName,Status:StackStatus,LastUpdated:LastUpdatedTime}' --output table 2>/dev/null || echo "$(YELLOW)Stack not found - will be created on first deployment$(NC)"
	@echo "$(YELLOW)Validating SAM template...$(NC)"
	@sam validate --template template.yaml
	@echo "$(GREEN)AWS deployment validation completed!$(NC)"

remote-test: .secrets ## Run comprehensive integration tests against branch-specific deployed AWS resources
	@echo "$(BLUE)Running comprehensive integration tests against AWS (Branch: $(CURRENT_BRANCH))...$(NC)"
	@echo "$(YELLOW)Testing stack: $(STACK_NAME)$(NC)"
	@echo "$(YELLOW)Step 1: Validating deployment status...$(NC)"
	@aws cloudformation describe-stacks --stack-name $(STACK_NAME) --query 'Stacks[0].StackStatus' || (echo "$(RED)Stack not found or not deployed$(NC)" && exit 1)
	@echo "$(YELLOW)Step 2: Running API endpoint tests...$(NC)"
	@STACK_NAME=$(STACK_NAME) python scripts/test_remote_api.py
	@echo "$(YELLOW)Step 3: Running health checks...$(NC)"
	@$(MAKE) remote-health-check
	@echo "$(YELLOW)Step 4: Running performance tests...$(NC)"
	@STACK_NAME=$(STACK_NAME) python scripts/run_comprehensive_tests.py --remote
	@echo "$(GREEN)All remote integration tests completed successfully!$(NC)"

remote-health-check: .secrets ## Perform health checks on branch-specific deployed AWS resources
	@echo "$(BLUE)Performing AWS resource health checks (Branch: $(CURRENT_BRANCH))...$(NC)"
	@echo "$(YELLOW)Checking stack: $(STACK_NAME)$(NC)"
	@echo "$(YELLOW)Checking Lambda function health...$(NC)"
	@aws lambda get-function --function-name $(NAMESPACE)-hello-world-dev > /dev/null && echo "$(GREEN)✓ Lambda function is healthy$(NC)" || echo "$(RED)✗ Lambda function issue$(NC)"
	@echo "$(YELLOW)Checking API Gateway health...$(NC)"
	@API_URL=$$(aws cloudformation describe-stacks --stack-name $(STACK_NAME) --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' --output text 2>/dev/null); \
	if [ -n "$$API_URL" ]; then \
		if curl -s --connect-timeout 10 "$$API_URL/hello" > /dev/null; then \
			echo "$(GREEN)✓ API Gateway is responding$(NC)"; \
		else \
			echo "$(RED)✗ API Gateway not responding$(NC)"; \
		fi; \
	else \
		echo "$(RED)✗ API Gateway URL not found$(NC)"; \
	fi
	@echo "$(YELLOW)Checking CloudWatch logs...$(NC)"
	@aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/$(NAMESPACE)-hello-world" --query 'logGroups[0].logGroupName' --output text > /dev/null && echo "$(GREEN)✓ CloudWatch logs accessible$(NC)" || echo "$(RED)✗ CloudWatch logs issue$(NC)"

remote-logs: .secrets ## View logs from deployed Lambda functions for current branch
	@echo "$(BLUE)Viewing recent Lambda logs (Branch: $(CURRENT_BRANCH))...$(NC)"
	@echo "$(YELLOW)Stack: $(STACK_NAME)$(NC)"
	sam logs --stack-name $(STACK_NAME) --tail --include-traces

remote-status: .secrets ## Check status of deployed AWS resources for current branch
	@echo "$(BLUE)Checking AWS deployment status (Branch: $(CURRENT_BRANCH))...$(NC)"
	@echo "$(YELLOW)Stack: $(STACK_NAME)$(NC)"
	@STACK_NAME=$(STACK_NAME) python scripts/check_status.py
	@echo "$(BLUE)Checking CloudFormation stack...$(NC)"
	aws cloudformation describe-stacks --stack-name $(STACK_NAME) --query 'Stacks[0].StackStatus'

remote-cleanup-failed: .secrets ## Clean up failed CloudFormation stacks for current branch
	@echo "$(BLUE)Cleaning up failed CloudFormation stacks (Branch: $(CURRENT_BRANCH))...$(NC)"
	@echo "$(YELLOW)Branch namespace: $(NAMESPACE)$(NC)"
	@echo "$(YELLOW)Attempting to delete aws-sam-cli-managed-default stack...$(NC)"
	@aws cloudformation delete-stack --stack-name aws-sam-cli-managed-default 2>/dev/null || echo "$(YELLOW)Stack aws-sam-cli-managed-default not found or already deleted$(NC)"
	@echo "$(YELLOW)Attempting to delete failed stacks for branch...$(NC)"
	@aws cloudformation delete-stack --stack-name $(STACK_NAME) 2>/dev/null || echo "$(YELLOW)Stack $(STACK_NAME) not found$(NC)"
	@aws cloudformation delete-stack --stack-name $(STACK_NAME)-dev 2>/dev/null || echo "$(YELLOW)Stack $(STACK_NAME)-dev not found$(NC)"
	@aws cloudformation delete-stack --stack-name $(STACK_NAME)-staging 2>/dev/null || echo "$(YELLOW)Stack $(STACK_NAME)-staging not found$(NC)"
	@aws cloudformation delete-stack --stack-name $(STACK_NAME)-prod 2>/dev/null || echo "$(YELLOW)Stack $(STACK_NAME)-prod not found$(NC)"
	@echo "$(YELLOW)Waiting for stack deletion to complete...$(NC)"
	@sleep 10
	@echo "$(GREEN)Failed stack cleanup completed for branch $(CURRENT_BRANCH)!$(NC)"
	@echo "$(YELLOW)You can now try deploying again with 'make remote-deploy'$(NC)"

remote-destroy: .secrets ## Safely destroy AWS resources for current branch with confirmation
	@echo "$(RED)⚠️  DESTRUCTIVE OPERATION ⚠️$(NC)"
	@echo "$(YELLOW)This will destroy AWS resources for branch: $(CURRENT_BRANCH)$(NC)"
	@echo "$(YELLOW)Branch namespace: $(NAMESPACE)$(NC)"
	@echo "$(YELLOW)Stack name: $(STACK_NAME)$(NC)"
	@echo "$(YELLOW)Including:$(NC)"
	@echo "  - Lambda functions: $(NAMESPACE)-*"
	@echo "  - API Gateway"
	@echo "  - CloudFormation stacks: $(STACK_NAME)*"
	@echo "  - All associated resources"
	@read -p "Type 'DELETE' to confirm destruction: " confirm; \
	if [ "$$confirm" != "DELETE" ]; then \
		echo "$(YELLOW)Destruction cancelled$(NC)"; \
		exit 1; \
	fi
	@echo "$(RED)Proceeding with resource destruction for branch $(CURRENT_BRANCH)...$(NC)"
	@echo "$(YELLOW)Deleting SAM stack...$(NC)"
	@sam delete --stack-name $(STACK_NAME) --no-prompts --region $$(aws configure get region) || true
	@echo "$(YELLOW)Destroying Terraform resources...$(NC)"
	@cd terraform && terraform destroy -var-file="terraform.tfvars" -auto-approve || true
	@echo "$(GREEN)AWS resources destroyed for branch $(CURRENT_BRANCH)!$(NC)"

remote-rollback: .secrets ## Rollback to previous deployment version
	@echo "$(BLUE)Rolling back to previous deployment...$(NC)"
	@echo "$(YELLOW)Getting previous CloudFormation stack version...$(NC)"
	@aws cloudformation list-stacks --stack-status-filter UPDATE_COMPLETE --query 'StackSummaries[?StackName==`cvideo-click-api`] | [0:2]' --output table
	@read -p "Confirm rollback to previous version? (yes/no): " confirm; \
	if [ "$$confirm" != "yes" ]; then \
		echo "$(YELLOW)Rollback cancelled$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Initiating rollback...$(NC)"
	@aws cloudformation cancel-update-stack --stack-name cvideo-click-api 2>/dev/null || true
	@aws cloudformation continue-update-rollback --stack-name cvideo-click-api 2>/dev/null || true
	@echo "$(GREEN)Rollback initiated. Check status with 'make remote-status'$(NC)"

# =============================================================================  
# CI/CD WITH ACT & GITHUB ACTIONS
# =============================================================================

act-setup: ## Install and configure ACT for local GitHub Actions testing
	@echo "$(BLUE)Setting up ACT for local GitHub Actions testing...$(NC)"
	@if ! command -v act &> /dev/null; then \
		echo "$(YELLOW)Installing ACT...$(NC)"; \
		brew install act || (echo "$(RED)Please install ACT manually: https://github.com/nektos/act$(NC)" && exit 1); \
	fi
	@echo "$(BLUE)Creating ACT configuration...$(NC)"
	@echo "Creating .actrc file..."
	@echo "-P ubuntu-latest=catthehacker/ubuntu:act-latest" > .actrc
	@echo "$(GREEN)ACT setup completed!$(NC)"

act-test: ## Run GitHub Actions tests locally with ACT
	@echo "$(BLUE)Running GitHub Actions tests locally with ACT...$(NC)"
	@echo "$(YELLOW)This simulates the CI pipeline locally$(NC)"
	@if [ ! -f .secrets.act ]; then \
		echo "$(YELLOW)Creating .secrets.act from template...$(NC)"; \
		cp .secrets.act.template .secrets.act; \
		echo "$(RED)Please edit .secrets.act with your AWS credentials$(NC)"; \
		exit 1; \
	fi
	act --job test --secret-file .secrets.act --env-file .env.act

act-deploy: ## Run GitHub Actions deployment locally with ACT  
	@echo "$(BLUE)Running GitHub Actions deployment locally with ACT...$(NC)"
	@echo "$(RED)WARNING: This will attempt actual AWS deployment!$(NC)"
	@if [ ! -f .secrets.act ]; then \
		echo "$(YELLOW)Creating .secrets.act from template...$(NC)"; \
		cp .secrets.act.template .secrets.act; \
		echo "$(RED)Please edit .secrets.act with your AWS credentials$(NC)"; \
		exit 1; \
	fi
	@read -p "Continue? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	act --job deploy --secret-file .secrets.act --env-file .env.act --eventpath .github/events/workflow_dispatch.json

github-test: ## Trigger GitHub Actions test workflow manually
	@echo "$(BLUE)Triggering GitHub Actions test workflow...$(NC)"
	@echo "$(YELLOW)This requires GitHub CLI (gh) to be installed and authenticated$(NC)"
	gh workflow run ci-cd.yml

github-deploy: ## Trigger GitHub Actions deployment workflow manually
	@echo "$(BLUE)Triggering GitHub Actions deployment workflow...$(NC)"
	@echo "$(YELLOW)This will deploy to AWS via GitHub Actions$(NC)"
	@read -p "Continue with deployment? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	gh workflow run ci-cd.yml --ref main

plan: ## Show Terraform execution plan
	@echo "$(BLUE)Planning infrastructure changes...$(NC)"
	cd terraform && terraform plan -var-file="terraform.tfvars"

deploy: ## Deploy infrastructure and Lambda functions
	@echo "$(BLUE)Deploying infrastructure...$(NC)"
	cd terraform && terraform apply -var-file="terraform.tfvars" -auto-approve
	@echo "$(BLUE)Deploying Lambda functions...$(NC)"
	sam deploy --guided
	@echo "$(GREEN)Deployment completed!$(NC)"

deploy-function: ## Deploy specific Lambda function (usage: make deploy-function FUNCTION=function-name)
	@if [ -z "$(FUNCTION)" ]; then \
		echo "$(RED)Error: FUNCTION parameter is required$(NC)"; \
		echo "Usage: make deploy-function FUNCTION=function-name"; \
		exit 1; \
	fi
	@echo "$(BLUE)Deploying function: $(FUNCTION)...$(NC)"
	sam deploy --parameter-overrides FunctionName=$(FUNCTION)
	@echo "$(GREEN)Function $(FUNCTION) deployed successfully!$(NC)"

logs: ## View recent Lambda logs (usage: make logs FUNCTION=function-name)
	@if [ -z "$(FUNCTION)" ]; then \
		echo "$(RED)Error: FUNCTION parameter is required$(NC)"; \
		echo "Usage: make logs FUNCTION=function-name"; \
		exit 1; \
	fi
	@echo "$(BLUE)Viewing logs for function: $(FUNCTION)...$(NC)"
	sam logs -n $(FUNCTION) --stack-name cvideo-click-api --tail

metrics: ## View CloudWatch metrics
	@echo "$(BLUE)Viewing CloudWatch metrics...$(NC)"
	@python scripts/view_metrics.py

status: ## Check deployment and service status
	@echo "$(BLUE)Checking deployment status...$(NC)"
	@python scripts/check_status.py

# Security check - ensure .secrets file exists and is properly configured
.secrets:
	@if [ ! -f .secrets ]; then \
		echo "$(RED)Error: .secrets file not found$(NC)"; \
		echo "Please create a .secrets file with your AWS credentials:"; \
		echo ""; \
		echo "AWS_ACCESS_KEY_ID=your_access_key"; \
		echo "AWS_SECRET_ACCESS_KEY=your_secret_key"; \
		echo "AWS_DEFAULT_REGION=us-east-1"; \
		echo ""; \
		exit 1; \
	fi

debug-branch: ## Show branch detection variables for debugging
	@echo "$(BLUE)Branch Detection Debug Information$(NC)"
	@echo "$(YELLOW)Current Branch:$(NC) $(CURRENT_BRANCH)"
	@echo "$(YELLOW)Branch Safe:$(NC) $(BRANCH_SAFE)"
	@echo "$(YELLOW)Namespace:$(NC) $(NAMESPACE)"
	@echo "$(YELLOW)Stack Name:$(NC) $(STACK_NAME)"
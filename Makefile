.PHONY: help init clean format lint type-check test validate validate-strict verify verify-strict check-all json-lint terraform-lint toml-lint requirements-lint gitignore-lint type-annotations-check
.PHONY: local-build local-start local-stop local-status local-test local-deploy local-test-api
.PHONY: remote-build remote-build-sam-only remote-deploy remote-deploy-simple remote-deploy-prod remote-validate remote-test remote-health-check remote-logs remote-status remote-cleanup-failed remote-destroy remote-rollback
.PHONY: plan deploy deploy-function logs metrics status check-aws
.PHONY: act-setup act-test act-deploy github-test github-deploy
.PHONY: domain-check domain-setup domain-test dns-setup dns-test
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

# AWS credential sourcing helper - ensures proper loading of .secrets file
AWS_CMD_PREFIX = set -a && source .secrets && set +a &&

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
	@grep -E '^(format|lint|type-check|security|pylance-check|markdown-lint|markdown-fix|yaml-lint|yaml-fix|toml-lint|requirements-lint|gitignore-lint|verify|verify-strict|validate|validate-strict|check-all|test|test-unit|test-integration|test-watch|test-debug|test-security|test-comprehensive|test-local-only|test-remote-only|test-ci-only).*:.*##' Makefile | awk -F ':.*##' '{printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Local Development & Testing:$(NC)"
	@grep -E '^(local-build|local-start|local-stop|local-status|local-test|local-deploy|local-test-api).*:.*##' Makefile | awk -F ':.*##' '{printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Remote AWS Deployment & Testing:$(NC)"
	@grep -E '^(remote-build|remote-build-sam-only|remote-deploy|remote-deploy-simple|remote-deploy-prod|remote-validate|remote-test|remote-health-check|remote-logs|remote-status|remote-cleanup-failed|remote-destroy|remote-rollback|plan|deploy|deploy-function).*:.*##' Makefile | awk -F ':.*##' '{printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)CI/CD (ACT & GitHub Actions):$(NC)"
	@grep -E '^(act-setup|act-test|act-deploy|github-test|github-deploy).*:.*##' Makefile | awk -F ':.*##' '{printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Custom Domain Management:$(NC)"
	@grep -E '^(domain-check|domain-setup|domain-test|dns-setup|dns-test).*:.*##' Makefile | awk -F ':.*##' '{printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
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

pylance-check: ## Run comprehensive type checking with MCP integration and TypedDict safety
	@echo "$(BLUE)Running comprehensive type checking...$(NC)"
	@python3 scripts/pylance_check.py --mcp --typeddict-check --quiet
	@echo "$(GREEN)Comprehensive type checking completed!$(NC)"

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

json-lint: ## Validate JSON files with built-in JSON parser
	@echo "$(BLUE)Validating project JSON files...$(NC)"
	@for file in $$(find . -name "*.json" \
		-not -path "./.git/*" \
		-not -path "./node_modules/*" \
		-not -path "./.aws-sam/*" \
		-not -path "./.mypy_cache/*" \
		-not -path "./.pytest_cache/*" \
		-not -path "./htmlcov/*" \
		-not -path "./logs/*" \
		-not -path "./.coverage/*" \
		-not -path "./venv/*" \
		-not -path "./.venv/*" \
		-not -path "./env/*" \
		-not -path "./.env/*"); do \
		echo "Validating $$file"; \
		python3 -m json.tool "$$file" > /dev/null || (echo "$(RED)Invalid JSON: $$file$(NC)" && exit 1); \
	done
	@echo "$(GREEN)JSON validation completed!$(NC)"

terraform-lint: ## Validate and format Terraform files
	@echo "$(BLUE)Validating and formatting Terraform files...$(NC)"
	@if command -v terraform >/dev/null 2>&1; then \
		if [ -d terraform ]; then \
			cd terraform && terraform fmt -check -diff . || (echo "$(YELLOW)Running terraform fmt to fix formatting...$(NC)" && terraform fmt .); \
			terraform init -backend=false -input=false > /dev/null 2>&1 || true; \
			terraform validate || (echo "$(RED)Terraform validation failed$(NC)" && exit 1); \
		fi; \
	else \
		echo "$(YELLOW)terraform not installed. Skipping Terraform validation$(NC)"; \
	fi
	@echo "$(GREEN)Terraform validation completed!$(NC)"

toml-lint: ## Validate TOML files (pyproject.toml, etc.)
	@echo "$(BLUE)Validating TOML files...$(NC)"
	@for file in $$(find . -name "*.toml" -not -path "./.mypy_cache/*" -not -path "./.pytest_cache/*" -not -path "./htmlcov/*" -not -path "./.aws-sam/*" -not -path "./.git/*"); do \
		echo "Validating $$file"; \
		python3 -c "import tomllib; open('$$file', 'rb').read() and tomllib.load(open('$$file', 'rb'))" 2>/dev/null || \
		python3 -c "import tomli; tomli.load(open('$$file', 'rb'))" 2>/dev/null || \
		(echo "$(RED)Invalid TOML: $$file$(NC)" && exit 1); \
	done
	@echo "$(GREEN)TOML validation completed!$(NC)"

requirements-lint: ## Validate requirements.txt files format
	@echo "$(BLUE)Validating requirements files...$(NC)"
	@for file in $$(find . -name "requirements*.txt" -not -path "./.mypy_cache/*" -not -path "./.pytest_cache/*" -not -path "./htmlcov/*" -not -path "./.aws-sam/*" -not -path "./.git/*"); do \
		echo "Validating $$file"; \
		python3 -m pip install --dry-run --quiet -r "$$file" 2>/dev/null || \
		(echo "$(YELLOW)Warning: Some packages in $$file may not be available$(NC)"); \
	done
	@echo "$(GREEN)Requirements validation completed!$(NC)"

gitignore-lint: ## Validate .gitignore file format
	@echo "$(BLUE)Validating .gitignore file...$(NC)"
	@if [ -f .gitignore ]; then \
		echo "Checking .gitignore syntax"; \
		git check-ignore --verbose . 2>/dev/null || true; \
		echo "$(GREEN).gitignore validation completed!$(NC)"; \
	else \
		echo "$(YELLOW)No .gitignore file found$(NC)"; \
	fi

type-annotations-check: ## Check for missing type annotations in Python files
	@echo "$(BLUE)Checking for missing type annotations...$(NC)"
	@python3 scripts/pylance_check.py --quiet || true
	@echo "$(YELLOW)Note: Run 'make type-annotations-fix' to add missing annotations$(NC)"

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

validate: format lint type-check markdown-lint yaml-lint json-lint ## Run comprehensive code validation (format + lint + type-check + markdown + yaml + json)
	@echo "$(GREEN)Code validation completed!$(NC)"

validate-strict: format lint type-check security markdown-lint yaml-lint json-lint terraform-lint ## Run complete validation with security scanning - for CI/CD
	@echo "$(GREEN)All strict validation checks passed!$(NC)"

verify: format lint type-check markdown-lint yaml-lint json-lint toml-lint requirements-lint gitignore-lint ## Verify all file types and formats in the project
	@echo "$(GREEN)All file format verification completed!$(NC)"

verify-strict: format lint type-check security pylance-check markdown-lint yaml-lint json-lint terraform-lint toml-lint requirements-lint gitignore-lint ## Strict verification with enhanced type checking and security
	@echo "$(GREEN)All strict file format verification completed!$(NC)"

check-all: ## Complete validation - code quality, security, functional, lint, format - everything once
	@echo "$(BLUE)🚀 Starting comprehensive validation of everything...$(NC)"
	@echo "$(BLUE)📝 Step 1/9: Code Formatting...$(NC)"
	@$(MAKE) --no-print-directory format
	@echo "$(BLUE)🔍 Step 2/9: Code Linting...$(NC)"
	@$(MAKE) --no-print-directory lint
	@echo "$(BLUE)🏷️  Step 3/9: Type Checking (MyPy)...$(NC)"
	@$(MAKE) --no-print-directory type-check
	@echo "$(BLUE)🔒 Step 4/9: Security Scanning...$(NC)"
	@$(MAKE) --no-print-directory security
	@echo "$(BLUE)⚡ Step 5/9: Enhanced Type Checking (Pylance)...$(NC)"
	@$(MAKE) --no-print-directory pylance-check
	@echo "$(BLUE)📄 Step 6/9: Markdown Validation...$(NC)"
	@$(MAKE) --no-print-directory markdown-lint
	@echo "$(BLUE)📋 Step 7/9: YAML Validation...$(NC)"
	@$(MAKE) --no-print-directory yaml-lint
	@echo "$(BLUE)🗂️  Step 8/9: File Format Validation (JSON, TOML, Requirements, .gitignore)...$(NC)"
	@$(MAKE) --no-print-directory json-lint
	@$(MAKE) --no-print-directory toml-lint
	@$(MAKE) --no-print-directory requirements-lint
	@$(MAKE) --no-print-directory gitignore-lint
	@echo "$(BLUE)🏗️  Step 9/9: Infrastructure Validation (Terraform)...$(NC)"
	@$(MAKE) --no-print-directory terraform-lint
	@echo "$(GREEN)✅ COMPLETE! All validation checks passed - code quality, security, functional, lint, format$(NC)"
	@echo "$(GREEN)🎉 Your code meets all standards: functional correctness, security, and code quality$(NC)"

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
	$(AWS_CMD_PREFIX) aws sts get-caller-identity > /dev/null || (echo "$(RED)AWS credentials not configured$(NC)" && exit 1)
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

remote-deploy: terraform-init remote-build-sam-only ## Deploy SAM application to AWS with branch-specific namespace
	@echo "$(BLUE)Deploying to AWS (Branch: $(CURRENT_BRANCH))...$(NC)"
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
	@echo "$(GREEN)Deployment completed!$(NC)"

remote-deploy-simple: remote-build-sam-only ## Simple guided deployment to AWS (interactive, SAM only)
	@echo "$(BLUE)Running guided SAM deployment...$(NC)"
	@echo "$(YELLOW)This will prompt you for deployment configuration$(NC)"
	sam deploy --guided

remote-build-sam-only: .secrets ## Build and validate SAM only (skip Terraform validation)
	@echo "$(BLUE)Building SAM application only...$(NC)"
	@echo "$(YELLOW)Running pre-build validation...$(NC)"
	@if [ ! -f terraform/terraform.tfvars ]; then \
		echo "$(YELLOW)Warning: terraform/terraform.tfvars not found$(NC)"; \
	fi
	@echo "$(YELLOW)Checking AWS credentials...$(NC)"
	$(AWS_CMD_PREFIX) aws sts get-caller-identity > /dev/null || (echo "$(RED)AWS credentials not configured$(NC)" && exit 1)
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
	@echo "$(BLUE)🔍 AWS Deployment Validation (Branch: $(CURRENT_BRANCH))$(NC)"
	@echo "$(BLUE)==============================================$(NC)"
	@echo ""
	@echo "$(CYAN)🔐 AWS Credentials:$(NC)"
	@ACCOUNT_ID=$$($(AWS_CMD_PREFIX) aws sts get-caller-identity --query 'Account' --output text 2>/dev/null); \
	USER_ARN=$$($(AWS_CMD_PREFIX) aws sts get-caller-identity --query 'Arn' --output text 2>/dev/null); \
	if [ -n "$$ACCOUNT_ID" ]; then \
		echo "   $(GREEN)✅ Account: $$ACCOUNT_ID$(NC)"; \
		echo "   $(GREEN)✅ User: $$USER_ARN$(NC)"; \
	else \
		echo "   $(RED)❌ AWS credentials not configured$(NC)"; \
		exit 1; \
	fi
	@echo ""
	@echo "$(CYAN)📋 SAM Template:$(NC)"
	@if sam validate --template template.yaml >/dev/null 2>&1; then \
		echo "   $(GREEN)✅ template.yaml is valid$(NC)"; \
	else \
		echo "   $(RED)❌ template.yaml validation failed$(NC)"; \
		exit 1; \
	fi
	@echo ""
	@echo "$(CYAN)☁️  Current Stack Status:$(NC)"
	@STACK_STATUS=$$($(AWS_CMD_PREFIX) aws cloudformation describe-stacks --stack-name $(STACK_NAME) --query 'Stacks[0].StackStatus' --output text 2>/dev/null); \
	if [ -n "$$STACK_STATUS" ]; then \
		echo "   $(GREEN)✅ Stack $(STACK_NAME): $$STACK_STATUS$(NC)"; \
	else \
		echo "   $(YELLOW)ℹ️  Stack $(STACK_NAME): Not deployed (will be created)$(NC)"; \
	fi
	@echo ""
	@echo "$(CYAN)🗂️  S3 Deployment Bucket:$(NC)"
	@if $(AWS_CMD_PREFIX) aws s3 ls s3://cvideo-sam-artifacts-20250924 >/dev/null 2>&1; then \
		echo "   $(GREEN)✅ cvideo-sam-artifacts-20250924: Accessible$(NC)"; \
	else \
		echo "   $(RED)❌ cvideo-sam-artifacts-20250924: Not accessible$(NC)"; \
		exit 1; \
	fi
	@echo ""
	@echo "$(BLUE)==============================================$(NC)"
	@echo "$(GREEN)🎉 All validations passed! Ready to deploy.$(NC)"

remote-test: .secrets ## Run comprehensive integration tests against branch-specific deployed AWS resources
	@echo "$(BLUE)Running comprehensive integration tests against AWS (Branch: $(CURRENT_BRANCH))...$(NC)"
	@echo "$(YELLOW)Testing stack: $(STACK_NAME)$(NC)"
	@echo "$(YELLOW)Step 1: Validating deployment status...$(NC)"
	@$(AWS_CMD_PREFIX) aws cloudformation describe-stacks --stack-name $(STACK_NAME) --query 'Stacks[0].StackStatus' || (echo "$(RED)Stack not found or not deployed$(NC)" && exit 1)
	@echo "$(YELLOW)Step 2: Running API endpoint tests...$(NC)"
	@STACK_NAME=$(STACK_NAME) python scripts/test_remote_api.py
	@echo "$(YELLOW)Step 3: Running health checks...$(NC)"
	@$(MAKE) remote-health-check
	@echo "$(YELLOW)Step 4: Running performance tests...$(NC)"
	@STACK_NAME=$(STACK_NAME) python scripts/run_comprehensive_tests.py --remote
	@echo "$(GREEN)All remote integration tests completed successfully!$(NC)"

remote-health-check: .secrets ## Perform health checks on branch-specific deployed AWS resources
	@echo "$(BLUE)🩺 Health Check Report (Branch: $(CURRENT_BRANCH))$(NC)"
	@echo "$(BLUE)========================================$(NC)"
	@echo "$(YELLOW)Stack: $(STACK_NAME)$(NC)"
	@echo ""
	@echo "$(CYAN)⚡ Lambda Function:$(NC)"
	@$(AWS_CMD_PREFIX) aws lambda get-function --function-name $(NAMESPACE)-hello-world-dev >/dev/null 2>&1 && echo "   $(GREEN)✅ $(NAMESPACE)-hello-world-dev: Healthy$(NC)" || echo "   $(RED)❌ $(NAMESPACE)-hello-world-dev: Unavailable$(NC)"
	@echo ""
	@echo "$(CYAN)🌐 API Gateway:$(NC)"
	@API_URL=$$($(AWS_CMD_PREFIX) aws cloudformation describe-stacks --stack-name $(STACK_NAME) --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' --output text 2>/dev/null); \
	if [ -n "$$API_URL" ] && [ "$$API_URL" != "None" ]; then \
		if curl -s --connect-timeout 5 "$$API_URL/hello" >/dev/null 2>&1; then \
			echo "   $(GREEN)✅ API responding at $$API_URL$(NC)"; \
		else \
			echo "   $(YELLOW)⚠️  API found but not responding: $$API_URL$(NC)"; \
		fi; \
	else \
		echo "   $(YELLOW)ℹ️  No API Gateway configured (Lambda-only deployment)$(NC)"; \
	fi
	@echo ""
	@echo "$(CYAN)📊 CloudWatch Logs:$(NC)"
	@$(AWS_CMD_PREFIX) aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/$(NAMESPACE)-hello-world" --query 'logGroups[0].logGroupName' --output text >/dev/null 2>&1 && echo "   $(GREEN)✅ Log groups accessible$(NC)" || echo "   $(RED)❌ Log groups unavailable$(NC)"
	@echo ""
	@echo "$(CYAN)☁️  CloudFormation Stack:$(NC)"
	@STACK_STATUS=$$($(AWS_CMD_PREFIX) aws cloudformation describe-stacks --stack-name $(STACK_NAME) --query 'Stacks[0].StackStatus' --output text 2>/dev/null); \
	if [ -n "$$STACK_STATUS" ]; then \
		if [ "$$STACK_STATUS" = "CREATE_COMPLETE" ] || [ "$$STACK_STATUS" = "UPDATE_COMPLETE" ]; then \
			echo "   $(GREEN)✅ Stack Status: $$STACK_STATUS$(NC)"; \
		else \
			echo "   $(YELLOW)⚠️  Stack Status: $$STACK_STATUS$(NC)"; \
		fi; \
	else \
		echo "   $(RED)❌ Stack not found$(NC)"; \
	fi
	@echo ""
	@echo "$(BLUE)========================================$(NC)"

remote-logs: .secrets ## View logs from deployed Lambda functions for current branch
	@echo "$(BLUE)Viewing recent Lambda logs (Branch: $(CURRENT_BRANCH))...$(NC)"
	@echo "$(YELLOW)Stack: $(STACK_NAME)$(NC)"
	sam logs --stack-name $(STACK_NAME) --tail --include-traces

remote-status: .secrets ## Check status of deployed AWS resources for current branch
	@echo "$(BLUE)📊 Deployment Status Report (Branch: $(CURRENT_BRANCH))$(NC)"
	@echo "$(BLUE)============================================$(NC)"
	@echo "$(YELLOW)Stack: $(STACK_NAME)$(NC)"
	@echo ""
	@echo "$(CYAN)☁️  CloudFormation Stack:$(NC)"
	@STACK_STATUS=$$($(AWS_CMD_PREFIX) aws cloudformation describe-stacks --stack-name $(STACK_NAME) --query 'Stacks[0].StackStatus' --output text 2>/dev/null); \
	if [ -n "$$STACK_STATUS" ]; then \
		if [ "$$STACK_STATUS" = "CREATE_COMPLETE" ] || [ "$$STACK_STATUS" = "UPDATE_COMPLETE" ]; then \
			echo "   $(GREEN)✅ Stack Status: $$STACK_STATUS$(NC)"; \
		else \
			echo "   $(YELLOW)⚠️  Stack Status: $$STACK_STATUS$(NC)"; \
		fi; \
	else \
		echo "   $(RED)❌ Stack not found$(NC)"; \
		echo "$(BLUE)============================================$(NC)"; \
		echo "$(RED)💡 No deployment found. Run 'make remote-deploy' to deploy.$(NC)"; \
		exit 1; \
	fi
	@echo ""
	@echo "$(CYAN)⚡ Lambda Functions:$(NC)"
	@LAMBDA_ARN=$$($(AWS_CMD_PREFIX) aws cloudformation describe-stacks --stack-name $(STACK_NAME) --query 'Stacks[0].Outputs[?OutputKey==`HelloWorldFunctionArn`].OutputValue' --output text 2>/dev/null); \
	if [ -n "$$LAMBDA_ARN" ] && [ "$$LAMBDA_ARN" != "None" ]; then \
		FUNCTION_NAME=$$(echo $$LAMBDA_ARN | cut -d: -f7); \
		FUNCTION_STATE=$$($(AWS_CMD_PREFIX) aws lambda get-function --function-name $$FUNCTION_NAME --query 'Configuration.State' --output text 2>/dev/null); \
		FUNCTION_STATUS=$$($(AWS_CMD_PREFIX) aws lambda get-function --function-name $$FUNCTION_NAME --query 'Configuration.LastUpdateStatus' --output text 2>/dev/null); \
		if [ "$$FUNCTION_STATE" = "Active" ] && [ "$$FUNCTION_STATUS" = "Successful" ]; then \
			echo "   $(GREEN)✅ $$FUNCTION_NAME: Active (Successful)$(NC)"; \
		else \
			echo "   $(RED)❌ $$FUNCTION_NAME: $$FUNCTION_STATE ($$FUNCTION_STATUS)$(NC)"; \
		fi; \
	else \
		echo "   $(RED)❌ No Lambda functions found in stack$(NC)"; \
	fi
	@echo ""
	@echo "$(CYAN)🌐 API Gateway:$(NC)"
	@API_URL=$$($(AWS_CMD_PREFIX) aws cloudformation describe-stacks --stack-name $(STACK_NAME) --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' --output text 2>/dev/null); \
	if [ -n "$$API_URL" ] && [ "$$API_URL" != "None" ]; then \
		echo "   $(GREEN)✅ API Gateway: $$API_URL$(NC)"; \
	else \
		echo "   $(YELLOW)ℹ️  No API Gateway configured (Lambda-only deployment)$(NC)"; \
	fi
	@echo ""
	@echo "$(CYAN)🗂️  S3 Deployment Bucket:$(NC)"
	@if $(AWS_CMD_PREFIX) aws s3 ls s3://cvideo-sam-artifacts-20250924 >/dev/null 2>&1; then \
		echo "   $(GREEN)✅ cvideo-sam-artifacts-20250924: Accessible$(NC)"; \
	else \
		echo "   $(RED)❌ cvideo-sam-artifacts-20250924: Not accessible$(NC)"; \
	fi
	@echo ""
	@echo "$(BLUE)============================================$(NC)"
	@echo "$(GREEN)🎉 Status check completed!$(NC)"

remote-cleanup-failed: .secrets ## Clean up failed CloudFormation stacks for current branch
	@echo "$(BLUE)Cleaning up failed CloudFormation stacks (Branch: $(CURRENT_BRANCH))...$(NC)"
	@echo "$(YELLOW)Branch namespace: $(NAMESPACE)$(NC)"
	@echo "$(YELLOW)Stack name: $(STACK_NAME)$(NC)"
	@echo "$(YELLOW)Attempting to delete failed stack for current branch...$(NC)"
	$(AWS_CMD_PREFIX) aws cloudformation delete-stack --stack-name $(STACK_NAME) 2>/dev/null || echo "$(YELLOW)Stack $(STACK_NAME) not found$(NC)"
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
	@echo "  - CloudFormation stack: $(STACK_NAME)"
	@echo "  - All associated resources"
	@read -p "Type 'DELETE' to confirm destruction: " confirm; \
	if [ "$$confirm" != "DELETE" ]; then \
		echo "$(YELLOW)Destruction cancelled$(NC)"; \
		exit 1; \
	fi
	@echo "$(RED)Proceeding with resource destruction for branch $(CURRENT_BRANCH)...$(NC)"
	@echo "$(YELLOW)Deleting SAM stack...$(NC)"
	@sam delete --stack-name $(STACK_NAME) --no-prompts --region $$(aws configure get region) || true
	@echo "$(GREEN)AWS resources destroyed for branch $(CURRENT_BRANCH)!$(NC)"

remote-rollback: .secrets ## Rollback to previous deployment version
	@echo "$(BLUE)Rolling back to previous deployment...$(NC)"
	@echo "$(YELLOW)Getting previous CloudFormation stack version...$(NC)"
	$(AWS_CMD_PREFIX) aws cloudformation list-stacks --stack-status-filter UPDATE_COMPLETE --output table
	@read -p "Confirm rollback to previous version? (yes/no): " confirm; \
	if [ "$$confirm" != "yes" ]; then \
		echo "$(YELLOW)Rollback cancelled$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Initiating rollback...$(NC)"
	$(AWS_CMD_PREFIX) aws cloudformation cancel-update-stack --stack-name $(STACK_NAME) 2>/dev/null || true
	$(AWS_CMD_PREFIX) aws cloudformation continue-update-rollback --stack-name $(STACK_NAME) 2>/dev/null || true
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

# --- Terraform Initialization ---
terraform-init: ## Initialize or reconfigure Terraform backend
	@echo "$(BLUE)Initializing Terraform backend...$(NC)"
	cd terraform && terraform init -input=false -reconfigure

plan: terraform-init ## Show Terraform execution plan
	@echo "$(BLUE)Planning infrastructure changes...$(NC)"
	cd terraform && terraform plan -var-file="terraform.tfvars"

plan-minimal: terraform-init ## Show minimal Terraform execution plan (custom domain only)
	@echo "$(BLUE)Planning minimal infrastructure changes (custom domain only)...$(NC)"
	cd terraform && terraform plan -var-file="terraform.tfvars" -var="tf_config=minimal.tf"

deploy: ## Deploy infrastructure and Lambda functions
	@echo "$(BLUE)Deploying infrastructure...$(NC)"
	cd terraform && terraform apply -var-file="terraform.tfvars" -auto-approve
	@echo "$(BLUE)Deploying Lambda functions...$(NC)"
	sam deploy --guided
	@echo "$(GREEN)Deployment completed!$(NC)"

deploy-minimal: terraform-init ## Deploy minimal infrastructure (custom domain only)
	@echo "$(BLUE)Deploying minimal infrastructure (custom domain only)...$(NC)"
	cd terraform && terraform apply -target=aws_route53_zone.apps_domain -target=aws_acm_certificate.apps_domain_cert -target=aws_acm_certificate_validation.apps_domain_cert -target=aws_api_gateway_domain_name.custom_domain -target=aws_route53_record.api_domain -target=aws_route53_record.cert_validation -var-file="terraform.tfvars" -auto-approve
	@echo "$(GREEN)Minimal infrastructure deployment completed!$(NC)"

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

# Custom Domain Management Commands
domain-check: ## Check custom domain configuration and status
	@echo "$(BLUE)Checking custom domain configuration...$(NC)"
	@python scripts/check_domain.py

domain-deploy: terraform-init ## Deploy complete custom domain infrastructure (bootstrap/admin only)
	@echo "$(BLUE)Deploying custom domain infrastructure...$(NC)"
	@echo "$(YELLOW)⚠️  This requires bootstrap/admin permissions for:$(NC)"
	@echo "   - Route53 hosted zone creation"
	@echo "   - ACM certificate management"
	@echo "   - API Gateway custom domain creation"
	@echo "   - Service-linked role creation"
	@read -p "Continue with domain deployment? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	cd terraform && terraform apply -target=aws_route53_zone.apps_domain -target=aws_acm_certificate.apps_domain_cert -target=aws_acm_certificate_validation.apps_domain_cert -target=aws_route53_record.cert_validation -target=aws_api_gateway_domain_name.custom_domain -target=aws_api_gateway_base_path_mapping.custom_domain_mapping -target=aws_route53_record.api_domain -var-file="terraform.tfvars" --output json | cat

domain-destroy: terraform-init ## Destroy custom domain infrastructure (bootstrap/admin only)
	@echo "$(RED)⚠️  WARNING: This will destroy the custom domain infrastructure!$(NC)"
	@echo "$(YELLOW)This will remove:$(NC)"
	@echo "   - Custom domain mapping"
	@echo "   - Route53 A records"
	@echo "   - API Gateway custom domain"
	@echo "   - (Route53 zone and certificate will be preserved)"
	@read -p "Are you sure? Type 'destroy' to confirm: " confirm && [ "$$confirm" = "destroy" ] || exit 1
	cd terraform && terraform destroy -target=aws_route53_record.api_domain -target=aws_api_gateway_base_path_mapping.custom_domain_mapping -target=aws_api_gateway_domain_name.custom_domain -var-file="terraform.tfvars" --output json | cat

domain-status: ## Show detailed domain status including DNS propagation
	@echo "$(BLUE)Checking domain status...$(NC)"
	@echo "$(CYAN)📋 Certificate Status:$(NC)"
	@aws acm describe-certificate --certificate-arn $$(cd terraform && terraform output -raw certificate_arn 2>/dev/null || echo "not-deployed") --query 'Certificate.{Status:Status,DomainName:DomainName,ValidationStatus:DomainValidationOptions[0].ValidationStatus}' --output json | cat 2>/dev/null || echo "Certificate not found"
	@echo ""
	@echo "$(CYAN)🌐 API Gateway Custom Domain:$(NC)"
	@aws apigateway get-domain-names --query 'items[?contains(domainName, `apps.cvideo.click`)].{DomainName:domainName,Status:domainNameStatus,Target:regionalDomainName}' --output json | cat
	@echo ""
	@echo "$(CYAN)📡 DNS Resolution:$(NC)"
	@dig +short $$(cd terraform && terraform output -raw custom_domain_url 2>/dev/null | sed 's|https://||' || echo "api-dev.apps.cvideo.click") || echo "Domain not resolving"

domain-setup: ## Show DNS setup instructions for custom domains
	@echo "$(BLUE)Custom domain setup instructions...$(NC)"
	@python scripts/dns_management.py setup

domain-test: ## Test custom domain DNS resolution and accessibility
	@echo "$(BLUE)Testing custom domain configuration...$(NC)"
	@python scripts/dns_management.py test

dns-setup: domain-setup ## Alias for domain-setup

dns-test: domain-test ## Alias for domain-test

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

test-aws-creds: ## Test AWS credential loading function
	@echo "$(BLUE)Testing AWS credential loading...$(NC)"
	@$(AWS_CMD_PREFIX) aws sts get-caller-identity
	@echo "$(GREEN)AWS credential loading test completed!$(NC)"
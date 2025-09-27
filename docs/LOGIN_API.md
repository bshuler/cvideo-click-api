# Login API Documentation

## Overview

This document describes the implementation of a comprehensive user authentication system for the CVIDEO-CLICK-API project. The system provides user registration, login, and token-based authentication using DynamoDB as the backend storage and JWT tokens for session management.

## Architecture

### Components

1. **Authentication Layer** (`shared/auth.py`)

   - JWT token creation and validation
   - Password hashing and verification
   - User authentication middleware

1. **Database Layer** (`shared/database.py`)

   - User CRUD operations
   - DynamoDB user table management
   - Session tracking

1. **API Layer** (`src/login/handler.py`)

   - User registration endpoint
   - User login endpoint
   - Token refresh endpoint
   - User profile endpoints

1. **Infrastructure** (`template.yaml`)

   - DynamoDB users table
   - Lambda function configuration
   - API Gateway integration

## Data Models

### User Table Schema (DynamoDB)

**Table Name**: `cvideo-api-{environment}-users`

**Primary Key**: `user_id` (String) - UUID v4

**Attributes**:

- `user_id` (String, PK) - Unique user identifier
- `email` (String, GSI) - User email address (unique)
- `password_hash` (String) - Bcrypt hashed password
- `first_name` (String) - User's first name
- `last_name` (String) - User's last name
- `created_at` (String) - ISO 8601 timestamp
- `updated_at` (String) - ISO 8601 timestamp
- `last_login_at` (String) - ISO 8601 timestamp
- `is_active` (Boolean) - Account status
- `email_verified` (Boolean) - Email verification status
- `profile_data` (Map) - Additional profile information

**Global Secondary Indexes**:

- `email-index` - GSI on email attribute for unique email lookups

### JWT Token Payload

```json
{
  "user_id": "uuid-string",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "exp": 1234567890,
  "iat": 1234567890
}
```

## API Endpoints

### Base URL

`https://api.cvideo-click.com/{environment}/auth`

### Endpoints

#### 1. User Registration

- **POST** `/register`

- **Description**: Create a new user account

- **Request Body**:

  ```json
  ```

{
"email": "user@example.com",
"password": "secure_password",
"first_name": "John",
"last_name": "Doe"
}

- **Response** (201):

```json
{
"success": true,
  "data": {
    "user_id": "uuid-string",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "created_at": "2025-01-01T00:00:00Z"
  },
  "token": "jwt-token-string"
}
```

- **Errors**:
  - 400: Email already exists
  - 400: Invalid email format
  - 400: Password too weak

#### 2. User Login

- **POST** `/login`

- **Description**: Authenticate user and return JWT token

- **Request Body**:

  ```json
  ```

{
"email": "user@example.com",
"password": "secure_password"
}

- **Response** (200):

```json
{
"success": true,
  "data": {
    "user_id": "uuid-string",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "last_login_at": "2025-01-01T00:00:00Z"
  },
  "token": "jwt-token-string"
}
```

- **Errors**:
  - 401: Invalid credentials
  - 404: User not found
  - 403: Account inactive

#### 3. Token Refresh

- **POST** `/refresh`

- **Description**: Refresh JWT token

- **Headers**: `Authorization: Bearer <token>`

- **Response** (200):

  ```json
  {
  "success": true,
    "token": "new-jwt-token-string"
  }
  ```

- **Errors**:

  - 401: Invalid or expired token

#### 4. User Profile

- **GET** `/profile`

- **Description**: Get current user profile

- **Headers**: `Authorization: Bearer <token>`

- **Response** (200):

  ```json
  {
  "success": true,
    "data": {
      "user_id": "uuid-string",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "created_at": "2025-01-01T00:00:00Z",
      "last_login_at": "2025-01-01T00:00:00Z",
      "email_verified": true,
      "profile_data": {}
    }
  }
  ```

#### 5. Update Profile

- **PUT** `/profile`

- **Description**: Update user profile

- **Headers**: `Authorization: Bearer <token>`

- **Request Body**:

  ```json
  {
  "first_name": "John",
    "last_name": "Doe",
    "profile_data": {
      "company": "ACME Corp",
      "phone": "+1-555-123-4567"
    }
  }
  ```

- **Response** (200):

  ```json
  ```

{
"success": true,
"data": {
"user_id": "uuid-string",
"email": "user@example.com",
"first_name": "John",
"last_name": "Doe",
"updated_at": "2025-01-01T00:00:00Z",
"profile_data": {
"company": "ACME Corp",
"phone": "+1-555-123-4567"
}
}
}

## Security Features

### Password Security

- Minimum 8 characters
- Must contain uppercase, lowercase, number, and special character
- Bcrypt hashing with salt rounds = 12

### JWT Token Security

- HS256 algorithm
- 24-hour expiration by default
- Includes user context in payload
- Secret key from environment variables

### Input Validation

- Email format validation
- Password strength validation
- SQL injection protection (NoSQL injection protection)
- Request rate limiting

### Error Handling

- Generic error messages to prevent user enumeration
- Detailed logging for debugging
- Consistent error response format

## Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-here

# DynamoDB Configuration
DYNAMODB_USERS_TABLE=cvideo-api-{environment}-users

# Password Configuration
BCRYPT_ROUNDS=12

# Environment
ENVIRONMENT=dev|staging|prod
LOG_LEVEL=INFO
```

## Database Setup

### DynamoDB Table Creation

The users table will be created via SAM template with:

- On-demand billing mode
- Point-in-time recovery enabled
- Server-side encryption enabled
- Global secondary index on email

### Sample DynamoDB Item

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john.doe@example.com",
  "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiO0PsyUeHU2",
  "first_name": "John",
  "last_name": "Doe",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z",
  "last_login_at": "2025-01-01T00:00:00Z",
  "is_active": true,
  "email_verified": false,
  "profile_data": {}
}
```

## Integration with Existing Code

### Authentication Middleware

The existing `require_authentication` function in `shared/auth.py` will be used to protect endpoints that require authentication.

### Response Format

All responses will use the existing `create_response` and `create_error_response` functions from `shared/utils.py` for consistency.

### Logging

The existing `setup_logging` function from `shared/utils.py` will be used for consistent logging across all functions.

## Testing Strategy

### Unit Tests

- Password hashing and verification
- JWT token creation and validation
- Database operations
- Input validation

### Integration Tests

- Complete user registration flow
- Login and token generation
- Protected endpoint access
- Error handling scenarios

### Load Testing

- Concurrent user registration
- High-frequency login attempts
- Token refresh under load

## Deployment Considerations

### Lambda Function Configuration

- Memory: 256MB (sufficient for bcrypt operations)
- Timeout: 30 seconds
- Environment variables for configuration
- Dead letter queue for error handling

### DynamoDB Configuration

- On-demand billing for unpredictable workloads
- Global secondary index for email lookups
- Encryption at rest enabled
- Point-in-time recovery enabled

### API Gateway Integration

- CORS configuration for web client access
- Request validation
- Rate limiting to prevent abuse
- CloudWatch logging enabled

## Monitoring and Alerts

### Metrics to Monitor

- Login success/failure rates
- Registration rates
- Token refresh rates
- API response times
- DynamoDB read/write capacity

### Alerts

- High error rates (>5%)
- Unusual login patterns
- DynamoDB throttling
- Lambda function errors

## Future Enhancements

### Phase 2 Features

- Email verification workflow
- Password reset functionality
- Multi-factor authentication (MFA)
- Social login integration (Google, Facebook)

### Phase 3 Features

- Role-based access control (RBAC)
- API key management
- Audit logging
- User session management

This documentation provides a comprehensive foundation for implementing a secure, scalable user authentication system for the CVIDEO-CLICK-API project.

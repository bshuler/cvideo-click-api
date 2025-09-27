# Login API Usage Examples

This document provides practical examples of how to use the Login API endpoints.

## Base URL

```text
Local Development: http://localhost:3000/auth
Staging: https://api-staging.cvideo-click.com/auth  
Production: https://api.cvideo-click.com/auth
```

## 1. User Registration

### Registration Request

```bash
curl -X POST http://localhost:3000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### Registration Success Response (201)

```json
{
  "success": true,
  "data": {
    "user": {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "john.doe@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "created_at": "2025-01-01T12:00:00Z",
      "updated_at": "2025-01-01T12:00:00Z",
      "is_active": true,
      "email_verified": false,
      "profile_data": {}
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

### Registration Error Response (400 - Email exists)

```json
{
  "success": false,
  "error": {
    "code": "EMAIL_EXISTS",
    "message": "Email address already registered"
  }
}
```

## 2. User Login

### Login Request

```bash
curl -X POST http://localhost:3000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "SecurePass123!"
  }'
```

### Login Success Response (200)

```json
{
  "success": true,
  "data": {
    "user": {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "john.doe@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "last_login_at": "2025-01-01T12:30:00Z",
      "created_at": "2025-01-01T12:00:00Z",
      "updated_at": "2025-01-01T12:30:00Z",
      "is_active": true,
      "email_verified": false,
      "profile_data": {}
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

### Login Error Response (401 - Invalid credentials)

```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid credentials"
  }
}
```

## 3. Token Refresh

### Token Refresh Request

```bash
curl -X POST http://localhost:3000/auth/refresh \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{}'
```

### Token Refresh Success Response (200)

```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

## 4. Get User Profile

### Get Profile Request

```bash
curl -X GET http://localhost:3000/auth/profile \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Get Profile Success Response (200)

```json
{
  "success": true,
  "data": {
    "user": {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "john.doe@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "created_at": "2025-01-01T12:00:00Z",
      "updated_at": "2025-01-01T12:00:00Z",
      "last_login_at": "2025-01-01T12:30:00Z",
      "is_active": true,
      "email_verified": false,
      "profile_data": {}
    }
  }
}
```

## 5. Update User Profile

### Update Profile Request

```bash
curl -X PUT http://localhost:3000/auth/profile \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "first_name": "Jane",
    "last_name": "Smith",
    "profile_data": {
      "company": "ACME Corporation",
      "phone": "+1-555-123-4567",
      "timezone": "America/New_York"
    }
  }'
```

### Update Profile Success Response (200)

```json
{
  "success": true,
  "data": {
    "user": {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "john.doe@example.com",
      "first_name": "Jane",
      "last_name": "Smith",
      "created_at": "2025-01-01T12:00:00Z",
      "updated_at": "2025-01-01T13:00:00Z",
      "last_login_at": "2025-01-01T12:30:00Z",
      "is_active": true,
      "email_verified": false,
      "profile_data": {
        "company": "ACME Corporation",
        "phone": "+1-555-123-4567",
        "timezone": "America/New_York"
      }
    }
  }
}
```

## JavaScript Client Example

```javascript
class AuthClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
    this.token = localStorage.getItem('authToken');
  }

  async register(userData) {
    const response = await fetch(`${this.baseUrl}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    const data = await response.json();
    
    if (data.success) {
      this.token = data.data.token;
      localStorage.setItem('authToken', this.token);
    }
    
    return data;
  }

  async login(email, password) {
    const response = await fetch(`${this.baseUrl}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();
    
    if (data.success) {
      this.token = data.data.token;
      localStorage.setItem('authToken', this.token);
    }
    
    return data;
  }

  async refreshToken() {
    if (!this.token) {
      throw new Error('No token available');
    }

    const response = await fetch(`${this.baseUrl}/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`,
      },
      body: JSON.stringify({}),
    });

    const data = await response.json();
    
    if (data.success) {
      this.token = data.data.token;
      localStorage.setItem('authToken', this.token);
    }
    
    return data;
  }

  async getProfile() {
    if (!this.token) {
      throw new Error('No token available');
    }

    const response = await fetch(`${this.baseUrl}/profile`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${this.token}`,
      },
    });

    return await response.json();
  }

  async updateProfile(updates) {
    if (!this.token) {
      throw new Error('No token available');
    }

    const response = await fetch(`${this.baseUrl}/profile`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`,
      },
      body: JSON.stringify(updates),
    });

    return await response.json();
  }

  logout() {
    this.token = null;
    localStorage.removeItem('authToken');
  }

  isAuthenticated() {
    return !!this.token;
  }
}

// Usage example
const auth = new AuthClient('http://localhost:3000/auth');

// Register new user
try {
  const result = await auth.register({
    email: 'user@example.com',
    password: 'SecurePass123!',
    first_name: 'John',
    last_name: 'Doe'
  });
  
  if (result.success) {
    console.log('Registration successful:', result.data.user);
  } else {
    console.error('Registration failed:', result.error);
  }
} catch (error) {
  console.error('Network error:', error);
}
```

## Python Client Example

```python
import requests
import json
from typing import Dict, Optional

class AuthClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token: Optional[str] = None

    def register(self, user_data: Dict) -> Dict:
        """Register a new user."""
        response = requests.post(
            f"{self.base_url}/register",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        data = response.json()
        
        if data.get('success') and 'token' in data.get('data', {}):
            self.token = data['data']['token']
        
        return data

    def login(self, email: str, password: str) -> Dict:
        """Login user."""
        response = requests.post(
            f"{self.base_url}/login",
            json={'email': email, 'password': password},
            headers={'Content-Type': 'application/json'}
        )
        
        data = response.json()
        
        if data.get('success') and 'token' in data.get('data', {}):
            self.token = data['data']['token']
        
        return data

    def refresh_token(self) -> Dict:
        """Refresh JWT token."""
        if not self.token:
            raise ValueError("No token available")
        
        response = requests.post(
            f"{self.base_url}/refresh",
            json={},
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.token}'
            }
        )
        
        data = response.json()
        
        if data.get('success') and 'token' in data.get('data', {}):
            self.token = data['data']['token']
        
        return data

    def get_profile(self) -> Dict:
        """Get user profile."""
        if not self.token:
            raise ValueError("No token available")
        
        response = requests.get(
            f"{self.base_url}/profile",
            headers={'Authorization': f'Bearer {self.token}'}
        )
        
        return response.json()

    def update_profile(self, updates: Dict) -> Dict:
        """Update user profile."""
        if not self.token:
            raise ValueError("No token available")
        
        response = requests.put(
            f"{self.base_url}/profile",
            json=updates,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.token}'
            }
        )
        
        return response.json()

    def logout(self):
        """Logout user."""
        self.token = None

    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.token is not None

# Usage example
if __name__ == "__main__":
    auth = AuthClient('http://localhost:3000/auth')
    
    # Register new user
    try:
        result = auth.register({
            'email': 'user@example.com',
            'password': 'SecurePass123!',
            'first_name': 'John',
            'last_name': 'Doe'
        })
        
        if result.get('success'):
            print(f"Registration successful: {result['data']['user']}")
        else:
            print(f"Registration failed: {result.get('error')}")
            
    except requests.RequestException as e:
        print(f"Network error: {e}")
```

## Error Handling

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `EMAIL_EXISTS` | 400 | Email address already registered |
| `INVALID_EMAIL` | 400 | Invalid email format |
| `WEAK_PASSWORD` | 400 | Password doesn't meet security requirements |
| `INVALID_JSON` | 400 | Malformed JSON in request body |
| `INVALID_CREDENTIALS` | 401 | Incorrect email or password |
| `UNAUTHORIZED` | 401 | Missing or invalid authentication token |
| `ACCOUNT_INACTIVE` | 403 | User account is deactivated |
| `USER_NOT_FOUND` | 404 | User doesn't exist |
| `NOT_FOUND` | 404 | Endpoint not found |
| `INTERNAL_ERROR` | 500 | Internal server error |

### Error Response Format

All errors follow this consistent format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "additional": "error details if applicable"
    }
  }
}
```

## Testing the API

### Using pytest with the test files

```bash
# Run all tests
make test

# Run specific test files
pytest tests/unit/test_auth.py -v
pytest tests/unit/test_user_management.py -v
pytest tests/integration/test_login_api.py -v

# Run with coverage
pytest --cov=src tests/ --cov-report=html
```

### Manual testing with curl

```bash
# Test registration
curl -X POST http://localhost:3000/auth/register \
  -H "Content-Type: application/json" \
  -d @test_user.json

# Where test_user.json contains:
{
  "email": "test@example.com",
  "password": "TestPassword123!",
  "first_name": "Test",
  "last_name": "User"
}
```

This completes the comprehensive Login API implementation with full documentation and examples!

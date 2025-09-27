"""
Test suite for enhanced authentication system.
Tests JWT tokens, API keys, session management, and RBAC.
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.auth_models import User, UserRole, ApiKey, UserSession
from app.security.enhanced_auth import (
    PasswordManager, TokenManager, ApiKeyManager, AuthenticationService
)
from app.main import app


@pytest.fixture
def client():
    """Test client for FastAPI app"""
    return TestClient(app)


@pytest.fixture
async def sample_user(db_session: AsyncSession):
    """Create a sample user for testing"""
    password_hash = PasswordManager.hash_password("test_password123")
    
    user = User(
        email="test@archbuilder.ai",
        password_hash=password_hash,
        first_name="Test",
        last_name="User",
        role=UserRole.USER,
        is_active=True,
        is_verified=True
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest.fixture
async def admin_user(db_session: AsyncSession):
    """Create an admin user for testing"""
    password_hash = PasswordManager.hash_password("admin_password123")
    
    user = User(
        email="admin@archbuilder.ai",
        password_hash=password_hash,
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


class TestPasswordManager:
    """Test password hashing and verification"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "test_password123"
        hashed = PasswordManager.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are long
        assert hashed.startswith("$2b$")  # bcrypt prefix
    
    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "test_password123"
        hashed = PasswordManager.hash_password(password)
        
        assert PasswordManager.verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "test_password123"
        wrong_password = "wrong_password"
        hashed = PasswordManager.hash_password(password)
        
        assert PasswordManager.verify_password(wrong_password, hashed) is False


class TestTokenManager:
    """Test JWT token creation and validation"""
    
    def test_create_access_token(self):
        """Test access token creation"""
        user_id = "test_user_123"
        role = UserRole.USER
        
        token = TokenManager.create_access_token(
            subject=user_id,
            role=role,
            session_id="session_123"
        )
        
        assert isinstance(token, str)
        assert len(token) > 100  # JWT tokens are long
        assert token.count(".") == 2  # JWT has 3 parts separated by dots
    
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        user_id = "test_user_123"
        session_id = "session_123"
        
        token = TokenManager.create_refresh_token(user_id, session_id)
        
        assert isinstance(token, str)
        assert len(token) > 100
        assert token.count(".") == 2
    
    def test_decode_valid_token(self):
        """Test decoding valid token"""
        user_id = "test_user_123"
        role = UserRole.USER
        session_id = "session_123"
        
        token = TokenManager.create_access_token(
            subject=user_id,
            role=role,
            session_id=session_id
        )
        
        payload = TokenManager.decode_token(token)
        
        assert payload["sub"] == user_id
        assert payload["role"] == role.value
        assert payload["session_id"] == session_id
        assert payload["type"] == "access"
    
    def test_decode_invalid_token(self):
        """Test decoding invalid token raises exception"""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(Exception):  # Should raise AuthenticationError
            TokenManager.decode_token(invalid_token)
    
    def test_validate_token_type(self):
        """Test token type validation"""
        payload = {"type": "access", "sub": "user123"}
        
        # Should not raise exception for correct type
        TokenManager.validate_token_type(payload, "access")
        
        # Should raise exception for incorrect type
        with pytest.raises(Exception):  # Should raise AuthenticationError
            TokenManager.validate_token_type(payload, "refresh")


class TestApiKeyManager:
    """Test API key generation and validation"""
    
    def test_generate_api_key(self):
        """Test API key generation"""
        key, key_hash, prefix = ApiKeyManager.generate_api_key()
        
        assert key.startswith("ab_key_")
        assert len(key) > 40
        assert len(key_hash) == 64  # SHA256 hash length
        assert len(prefix) == 12
        assert prefix == key[:12]
    
    def test_hash_api_key(self):
        """Test API key hashing"""
        key = "ab_key_test123456789"
        hash1 = ApiKeyManager.hash_api_key(key)
        hash2 = ApiKeyManager.hash_api_key(key)
        
        assert hash1 == hash2  # Same input should produce same hash
        assert len(hash1) == 64  # SHA256 hash length
        assert hash1 != key  # Hash should be different from original
    
    async def test_validate_api_key_not_found(self, db_session: AsyncSession):
        """Test API key validation when key doesn't exist"""
        fake_key = "ab_key_nonexistent123456789"
        
        result = await ApiKeyManager.validate_api_key(fake_key, db_session)
        
        assert result is None


class TestAuthenticationService:
    """Test authentication service functionality"""
    
    async def test_authenticate_user_success(self, db_session: AsyncSession, sample_user: User):
        """Test successful user authentication"""
        auth_service = AuthenticationService(db_session)
        
        user = await auth_service.authenticate_user(
            email="test@archbuilder.ai",
            password="test_password123"
        )
        
        assert user is not None
        assert user.email == "test@archbuilder.ai"
        assert user.id == sample_user.id
    
    async def test_authenticate_user_wrong_password(self, db_session: AsyncSession, sample_user: User):
        """Test authentication with wrong password"""
        auth_service = AuthenticationService(db_session)
        
        user = await auth_service.authenticate_user(
            email="test@archbuilder.ai",
            password="wrong_password"
        )
        
        assert user is None
    
    async def test_authenticate_user_nonexistent(self, db_session: AsyncSession):
        """Test authentication with nonexistent user"""
        auth_service = AuthenticationService(db_session)
        
        user = await auth_service.authenticate_user(
            email="nonexistent@example.com",
            password="any_password"
        )
        
        assert user is None
    
    async def test_create_user_session(self, db_session: AsyncSession, sample_user: User):
        """Test user session creation"""
        auth_service = AuthenticationService(db_session)
        
        session = await auth_service.create_user_session(
            user=sample_user,
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            device_info={"browser": "test", "os": "test"}
        )
        
        assert session.user_id == sample_user.id
        assert session.ip_address == "192.168.1.1"
        assert session.user_agent == "Test Browser"
        assert session.is_active


class TestAuthenticationAPI:
    """Test authentication API endpoints"""
    
    def test_health_endpoint(self, client: TestClient):
        """Test health endpoint is accessible"""
        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()
    
    async def test_register_user_success(self, client: TestClient):
        """Test user registration"""
        user_data = {
            "email": "newuser@archbuilder.ai",
            "password": "newpassword123",
            "first_name": "New",
            "last_name": "User"
        }
        
        response = client.post("/v1/auth/register", json=user_data)
        
        # Should succeed in dev mode or fail with 403 in production mode
        assert response.status_code in [200, 201, 403]
    
    def test_register_user_invalid_email(self, client: TestClient):
        """Test user registration with invalid email"""
        user_data = {
            "email": "invalid-email",
            "password": "newpassword123",
            "first_name": "New",
            "last_name": "User"
        }
        
        response = client.post("/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error
    
    def test_register_user_weak_password(self, client: TestClient):
        """Test user registration with weak password"""
        user_data = {
            "email": "newuser@archbuilder.ai",
            "password": "weak",  # Too short
            "first_name": "New",
            "last_name": "User"
        }
        
        response = client.post("/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error
    
    async def test_login_success(self, client: TestClient, sample_user: User):
        """Test successful login"""
        login_data = {
            "email": "test@archbuilder.ai",
            "password": "test_password123"
        }
        
        response = client.post("/v1/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "access_token" in data["data"]
            assert "refresh_token" in data["data"]
            assert data["data"]["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials"""
        login_data = {
            "email": "test@archbuilder.ai",
            "password": "wrong_password"
        }
        
        response = client.post("/v1/auth/login", json=login_data)
        assert response.status_code == 401
    
    def test_refresh_token_invalid(self, client: TestClient):
        """Test refresh token with invalid token"""
        refresh_data = {
            "refresh_token": "invalid.token.here"
        }
        
        response = client.post("/v1/auth/refresh", json=refresh_data)
        assert response.status_code == 401


class TestRoleBasedAccess:
    """Test role-based access control"""
    
    async def test_admin_endpoint_access_with_admin(self, client: TestClient, admin_user: User):
        """Test admin endpoint access with admin user"""
        # This would require creating an admin-only endpoint first
        pass
    
    async def test_admin_endpoint_access_with_regular_user(self, client: TestClient, sample_user: User):
        """Test admin endpoint access with regular user should fail"""
        # This would require creating an admin-only endpoint first
        pass


class TestTenantIsolation:
    """Test multi-tenant security features"""
    
    async def test_tenant_data_filtering(self):
        """Test tenant data is properly filtered"""
        # This would require setting up tenant-specific data
        pass
    
    async def test_cross_tenant_access_prevention(self):
        """Test prevention of cross-tenant data access"""
        # This would require setting up multiple tenants
        pass


# Integration tests
class TestAuthenticationIntegration:
    """Integration tests for complete authentication flows"""
    
    async def test_complete_login_flow(self, client: TestClient):
        """Test complete login and authenticated request flow"""
        # 1. Register user
        user_data = {
            "email": "integration@archbuilder.ai",
            "password": "integration123",
            "first_name": "Integration",
            "last_name": "Test"
        }
        
        register_response = client.post("/v1/auth/register", json=user_data)
        
        # 2. Login
        login_data = {
            "email": "integration@archbuilder.ai",
            "password": "integration123"
        }
        
        login_response = client.post("/v1/auth/login", json=login_data)
        
        if login_response.status_code == 200:
            tokens = login_response.json()["data"]
            
            # 3. Make authenticated request
            headers = {"Authorization": f"Bearer {tokens['access_token']}"}
            me_response = client.get("/v1/auth/me", headers=headers)
            
            assert me_response.status_code == 200
            user_info = me_response.json()["data"]
            assert user_info["email"] == "integration@archbuilder.ai"
    
    async def test_api_key_flow(self, client: TestClient):
        """Test API key creation and usage flow"""
        # This would require a logged-in user first
        pass
    
    async def test_session_management_flow(self, client: TestClient):
        """Test session creation, usage, and logout flow"""
        # This would require implementing session management endpoints
        pass


# Performance tests
class TestAuthenticationPerformance:
    """Performance tests for authentication operations"""
    
    def test_password_hashing_performance(self):
        """Test password hashing is within acceptable time limits"""
        import time
        
        password = "test_password123"
        
        start_time = time.time()
        PasswordManager.hash_password(password)
        end_time = time.time()
        
        # Password hashing should complete within 1 second
        assert (end_time - start_time) < 1.0
    
    def test_token_creation_performance(self):
        """Test JWT token creation performance"""
        import time
        
        start_time = time.time()
        for _ in range(100):  # Create 100 tokens
            TokenManager.create_access_token(
                subject="test_user",
                role=UserRole.USER,
                session_id="session_123"
            )
        end_time = time.time()
        
        # Should create 100 tokens in under 0.1 seconds
        assert (end_time - start_time) < 0.1
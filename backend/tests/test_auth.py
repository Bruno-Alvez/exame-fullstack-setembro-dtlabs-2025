import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService

client = TestClient(app)


@pytest.fixture
def test_user_data():
    return {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpassword123"
    }


@pytest.fixture
def test_user(db: Session, test_user_data):
    auth_service = AuthService(db)
    user = auth_service.create_user(
        email=test_user_data["email"],
        full_name=test_user_data["full_name"],
        password=test_user_data["password"]
    )
    return user


class TestAuthEndpoints:
    
    def test_register_success(self, test_user_data):
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["full_name"] == test_user_data["full_name"]
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_register_duplicate_email(self, test_user_data, test_user):
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_register_invalid_email(self, test_user_data):
        test_user_data["email"] = "invalid-email"
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 422

    def test_register_short_password(self, test_user_data):
        test_user_data["password"] = "123"
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 422

    def test_login_success(self, test_user_data, test_user):
        login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_login_invalid_credentials(self, test_user_data):
        login_data = {
            "username": test_user_data["email"],
            "password": "wrongpassword"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_nonexistent_user(self):
        login_data = {
            "username": "nonexistent@example.com",
            "password": "password123"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401

    def test_get_current_user_success(self, test_user_data, test_user):
        login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
        login_response = client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["full_name"] == test_user_data["full_name"]

    def test_get_current_user_invalid_token(self):
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401

    def test_get_current_user_no_token(self):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_refresh_token_success(self, test_user_data, test_user):
        login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
        login_response = client.post("/api/v1/auth/login", data=login_data)
        refresh_token = login_response.json()["refresh_token"]
        
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_refresh_token_invalid(self):
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid_token"})
        assert response.status_code == 401

    def test_refresh_token_expired(self):
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": "expired_token"})
        assert response.status_code == 401


class TestAuthService:
    
    def test_authenticate_user_success(self, db: Session, test_user_data):
        auth_service = AuthService(db)
        user = auth_service.create_user(
            email=test_user_data["email"],
            full_name=test_user_data["full_name"],
            password=test_user_data["password"]
        )
        
        authenticated_user = auth_service.authenticate_user(
            test_user_data["email"], 
            test_user_data["password"]
        )
        
        assert authenticated_user is not None
        assert authenticated_user.id == user.id

    def test_authenticate_user_invalid_password(self, db: Session, test_user_data):
        auth_service = AuthService(db)
        auth_service.create_user(
            email=test_user_data["email"],
            full_name=test_user_data["full_name"],
            password=test_user_data["password"]
        )
        
        authenticated_user = auth_service.authenticate_user(
            test_user_data["email"], 
            "wrongpassword"
        )
        
        assert authenticated_user is None

    def test_authenticate_user_nonexistent(self, db: Session):
        auth_service = AuthService(db)
        authenticated_user = auth_service.authenticate_user(
            "nonexistent@example.com", 
            "password123"
        )
        
        assert authenticated_user is None

    def test_generate_tokens(self, db: Session, test_user_data):
        auth_service = AuthService(db)
        user = auth_service.create_user(
            email=test_user_data["email"],
            full_name=test_user_data["full_name"],
            password=test_user_data["password"]
        )
        
        tokens = auth_service.generate_tokens(user)
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        assert "expires_in" in tokens

    def test_create_user_duplicate_email(self, db: Session, test_user_data):
        auth_service = AuthService(db)
        auth_service.create_user(
            email=test_user_data["email"],
            full_name=test_user_data["full_name"],
            password=test_user_data["password"]
        )
        
        with pytest.raises(ValueError, match="already exists"):
            auth_service.create_user(
                email=test_user_data["email"],
                full_name="Another User",
                password="password123"
            )

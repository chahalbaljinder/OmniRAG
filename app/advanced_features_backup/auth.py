# app/auth.py - Authentication and Authorization

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
import hashlib
import secrets
import bcrypt
from app.database import get_db, User, APIKey
from app.config import settings

# JWT Configuration
JWT_SECRET_KEY = settings.jwt_secret_key or secrets.token_urlsafe(32)
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

security = HTTPBearer()

class AuthenticationError(HTTPException):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

class AuthorizationError(HTTPException):
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

# Alias for compatibility
get_password_hash = hash_password

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(user_id: int, username: str, role: str = "user") -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.JWTError:
        raise AuthenticationError("Invalid token")

def generate_api_key() -> str:
    """Generate a secure API key"""
    return secrets.token_urlsafe(32)

def hash_api_key(api_key: str) -> str:
    """Hash API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    try:
        payload = verify_token(credentials.credentials)
        user_id = int(payload.get("sub"))
        
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            raise AuthenticationError("User not found or inactive")
        
        return user
    except ValueError:
        raise AuthenticationError("Invalid token payload")

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user (alias for get_current_user)"""
    return current_user

def authenticate_user(username: str, password: str, db: Session) -> Optional[User]:
    """Authenticate user with username and password"""
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user_or_api_key(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get user from JWT token or API key"""
    # Try API key from header
    api_key = request.headers.get("X-API-Key")
    if api_key:
        hashed_key = hash_api_key(api_key)
        api_key_record = db.query(APIKey).filter(
            APIKey.key_hash == hashed_key,
            APIKey.is_active == True,
            APIKey.expires_at > datetime.utcnow()
        ).first()
        
        if api_key_record:
            api_key_record.last_used = datetime.utcnow()
            api_key_record.usage_count += 1
            db.commit()
            return api_key_record.user
    
    # Try JWT token
    if credentials:
        try:
            return await get_current_user(credentials, db)
        except AuthenticationError:
            pass
    
    return None

def require_role(required_role: str):
    """Decorator to require specific role"""
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role and current_user.role != "admin":
            raise AuthorizationError(f"Role '{required_role}' required")
        return current_user
    return role_checker

def require_admin():
    """Require admin role"""
    return require_role("admin")

class RateLimiter:
    """Rate limiting based on user/IP"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed for identifier"""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old requests
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > minute_ago
            ]
        else:
            self.requests[identifier] = []
        
        # Check rate limit
        if len(self.requests[identifier]) >= self.requests_per_minute:
            return False
        
        # Add current request
        self.requests[identifier].append(now)
        return True

# Global rate limiters
upload_rate_limiter = RateLimiter(10)  # 10 uploads per minute
query_rate_limiter = RateLimiter(30)   # 30 queries per minute

def check_upload_rate_limit(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_or_api_key)
):
    """Check upload rate limit"""
    identifier = str(current_user.id) if current_user else request.client.host
    if not upload_rate_limiter.is_allowed(identifier):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Upload rate limit exceeded"
        )

def check_query_rate_limit(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_or_api_key)
):
    """Check query rate limit"""
    identifier = str(current_user.id) if current_user else request.client.host
    if not query_rate_limiter.is_allowed(identifier):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Query rate limit exceeded"
        )

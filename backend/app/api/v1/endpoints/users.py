"""
User management endpoints with authentication and authorization
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models import User, UserPreference, UserBookmark
from app.db.database import get_db
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# JWT Configuration
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return user


async def get_current_active_superuser(current_user: User = Depends(get_current_user)) -> User:
    """Get current active superuser"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user


# Pydantic Schemas
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    role: str
    avatar_url: Optional[str]
    last_login: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse


class PreferencesCreate(BaseModel):
    preferred_sources: Optional[List[str]] = []
    blocked_sources: Optional[List[str]] = []
    preferred_topics: Optional[List[str]] = []
    ignored_topics: Optional[List[str]] = []
    sentiment_preference: str = 'all'  # 'positive', 'negative', 'neutral', 'all'
    reading_level: str = 'mixed'  # 'simple', 'mixed', 'complex'
    notification_frequency: str = 'daily'  # 'realtime', 'hourly', 'daily', 'weekly'
    language: str = 'es'
    timezone: str = 'UTC'


class PreferencesResponse(BaseModel):
    id: str
    user_id: str
    preferred_sources: List[str]
    blocked_sources: List[str]
    preferred_topics: List[str]
    ignored_topics: List[str]
    sentiment_preference: str
    reading_level: str
    notification_frequency: str
    language: str
    timezone: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BookmarkCreate(BaseModel):
    article_id: str
    title: str
    url: str
    notes: Optional[str] = None
    tags: Optional[List[str]] = []


class BookmarkResponse(BaseModel):
    id: str
    user_id: str
    article_id: str
    title: str
    url: str
    notes: Optional[str]
    tags: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Auth Endpoints

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register new user"""
    # Check if username already exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail="Username already registered"
        )
    
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        is_active=True,
        role='user'
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    # Create default preferences
    default_preferences = UserPreference(
        user_id=db_user.id,
        preferred_sources=[],
        blocked_sources=[],
        preferred_topics=[],
        ignored_topics=[],
        sentiment_preference='all',
        reading_level='mixed',
        notification_frequency='daily',
        language='es',
        timezone='UTC'
    )
    
    db.add(default_preferences)
    await db.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username}, expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(db_user)
    )


@router.post("/login", response_model=TokenResponse)
async def login_user(user_credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login user"""
    # Get user from database
    result = await db.execute(select(User).where(User.username == user_credentials.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user)
    )


# User Profile Endpoints

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile"""
    
    # Check if email is being changed and if it's already taken
    if user_update.email and user_update.email != current_user.email:
        result = await db.execute(select(User).where(User.email == user_update.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=400, detail="Email already registered"
            )
        current_user.email = user_update.email
    
    # Update other fields
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    current_user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)


# Preferences Endpoints

@router.get("/preferences", response_model=PreferencesResponse)
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user preferences"""
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    )
    preferences = result.scalar_one_or_none()
    
    if not preferences:
        # Create default preferences if none exist
        preferences = UserPreference(
            user_id=current_user.id,
            preferred_sources=[],
            blocked_sources=[],
            preferred_topics=[],
            ignored_topics=[],
            sentiment_preference='all',
            reading_level='mixed',
            notification_frequency='daily',
            language='es',
            timezone='UTC'
        )
        db.add(preferences)
        await db.commit()
        await db.refresh(preferences)
    
    return PreferencesResponse.model_validate(preferences)


@router.put("/preferences", response_model=PreferencesResponse)
async def update_user_preferences(
    preferences_data: PreferencesCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user preferences"""
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    )
    preferences = result.scalar_one_or_none()
    
    if not preferences:
        # Create new preferences
        preferences = UserPreference(user_id=current_user.id)
        db.add(preferences)
    
    # Update preferences
    preferences.preferred_sources = preferences_data.preferred_sources
    preferences.blocked_sources = preferences_data.blocked_sources
    preferences.preferred_topics = preferences_data.preferred_topics
    preferences.ignored_topics = preferences_data.ignored_topics
    preferences.sentiment_preference = preferences_data.sentiment_preference
    preferences.reading_level = preferences_data.reading_level
    preferences.notification_frequency = preferences_data.notification_frequency
    preferences.language = preferences_data.language
    preferences.timezone = preferences_data.timezone
    preferences.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(preferences)
    
    return PreferencesResponse.model_validate(preferences)


# Bookmarks Endpoints

@router.get("/bookmarks", response_model=List[BookmarkResponse])
async def get_user_bookmarks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user bookmarks"""
    result = await db.execute(
        select(UserBookmark).where(UserBookmark.user_id == current_user.id).order_by(UserBookmark.created_at.desc())
    )
    bookmarks = result.scalars().all()
    
    return [BookmarkResponse.model_validate(bookmark) for bookmark in bookmarks]


@router.post("/bookmarks", response_model=BookmarkResponse, status_code=status.HTTP_201_CREATED)
async def create_bookmark(
    bookmark_data: BookmarkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new bookmark"""
    # Check if bookmark already exists
    result = await db.execute(
        select(UserBookmark).where(
            UserBookmark.user_id == current_user.id,
            UserBookmark.article_id == bookmark_data.article_id
        )
    )
    existing_bookmark = result.scalar_one_or_none()
    
    if existing_bookmark:
        raise HTTPException(
            status_code=400, detail="Article already bookmarked"
        )
    
    # Create new bookmark
    bookmark = UserBookmark(
        user_id=current_user.id,
        article_id=bookmark_data.article_id,
        title=bookmark_data.title,
        url=bookmark_data.url,
        notes=bookmark_data.notes,
        tags=bookmark_data.tags
    )
    
    db.add(bookmark)
    await db.commit()
    await db.refresh(bookmark)
    
    return BookmarkResponse.model_validate(bookmark)


@router.delete("/bookmarks/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bookmark(
    bookmark_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete bookmark"""
    result = await db.execute(
        select(UserBookmark).where(
            UserBookmark.id == bookmark_id,
            UserBookmark.user_id == current_user.id
        )
    )
    bookmark = result.scalar_one_or_none()
    
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    await db.delete(bookmark)
    await db.commit()
    
    return {"message": "Bookmark deleted successfully"}


# Admin endpoints (for superusers)

@router.get("/admin/users", response_model=List[UserResponse])
async def get_all_users(
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db)
):
    """Get all users (admin only)"""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    
    return [UserResponse.model_validate(user) for user in users]


@router.put("/admin/users/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: str,
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db)
):
    """Activate/deactivate user (admin only)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = not user.is_active
    user.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)
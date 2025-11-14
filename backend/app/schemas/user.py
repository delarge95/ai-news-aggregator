"""
User schemas for AI News Aggregator
"""

import re
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from pydantic import BaseModel, Field, validator, root_validator, field_serializer
from pydantic.types import conlist


class UserBase(BaseModel):
    """
    Base schema for users
    """
    email: str = Field(..., description="User email address")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username")
    full_name: Optional[str] = Field(None, min_length=2, max_length=100, description="Full name")
    
    @validator('email')
    def validate_email(cls, v):
        """Validate email format"""
        email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        if not email_pattern.match(v):
            raise ValueError('Invalid email format')
        return v.lower().strip()
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format"""
        if v is not None:
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
            if v.startswith('_') or v.startswith('-') or v.endswith('_') or v.endswith('-'):
                raise ValueError('Username cannot start or end with underscore or hyphen')
        return v
    
    @validator('full_name')
    def validate_full_name(cls, v):
        """Validate full name"""
        if v is not None:
            if len(v.strip()) < 2:
                raise ValueError('Full name must be at least 2 characters')
            if len(v) > 100:
                raise ValueError('Full name cannot exceed 100 characters')
        return v.strip() if v else v


class UserCreate(UserBase):
    """
    Schema for creating a new user
    """
    password: str = Field(..., min_length=8, max_length=128, description="Password")
    confirm_password: str = Field(..., description="Password confirmation")
    
    # Preferences
    preferred_sources: Optional[List[UUID]] = Field(default_factory=list, description="Preferred news sources")
    blocked_sources: Optional[List[UUID]] = Field(default_factory=list, description="Blocked news sources")
    preferred_topics: Optional[List[str]] = Field(default_factory=list, description="Preferred topics")
    ignored_topics: Optional[List[str]] = Field(default_factory=list, description="Ignored topics")
    sentiment_preference: str = Field('all', regex='^(positive|negative|neutral|all)$', description="Sentiment preference")
    reading_level: str = Field('mixed', regex='^(simple|mixed|complex)$', description="Reading level preference")
    notification_frequency: str = Field('daily', regex='^(realtime|hourly|daily|weekly)$', description="Notification frequency")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Validate that passwords match"""
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        # Check for at least one digit
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        return v
    
    @validator('preferred_topics', 'ignored_topics')
    def validate_topics(cls, v):
        """Validate topics list"""
        if v:
            for topic in v:
                if len(topic.strip()) == 0:
                    raise ValueError('Topics cannot be empty')
                if len(topic) > 50:
                    raise ValueError('Topics cannot exceed 50 characters')
            # Remove duplicates while preserving order
            return list(dict.fromkeys([topic.strip() for topic in v]))
        return v
    
    @root_validator
    def validate_preferences_consistency(cls, values):
        """Validate preference consistency"""
        preferred_topics = values.get('preferred_topics', [])
        ignored_topics = values.get('ignored_topics', [])
        
        # Check for conflicts between preferred and ignored topics
        conflicts = set(preferred_topics) & set(ignored_topics)
        if conflicts:
            raise ValueError(f'Cannot both prefer and ignore topics: {list(conflicts)}')
        
        return values


class UserLogin(BaseModel):
    """
    Schema for user login
    """
    email: str = Field(..., description="Email address")
    password: str = Field(..., description="Password")
    
    @validator('email')
    def validate_email(cls, v):
        """Validate email format"""
        email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        if not email_pattern.match(v):
            raise ValueError('Invalid email format')
        return v.lower().strip()


class UserResponse(UserBase):
    """
    Schema for user responses
    """
    id: UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Preferences
    preferred_sources: List[UUID] = Field(default_factory=list)
    blocked_sources: List[UUID] = Field(default_factory=list)
    preferred_topics: List[str] = Field(default_factory=list)
    ignored_topics: List[str] = Field(default_factory=list)
    sentiment_preference: str = 'all'
    reading_level: str = 'mixed'
    notification_frequency: str = 'daily'
    
    # Computed fields
    preferences_count: int = 0
    reading_streak: int = 0
    total_articles_read: int = 0
    
    class Config:
        from_attributes = True
    
    @field_serializer('created_at', 'updated_at', 'last_login')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """Serialize datetime objects to ISO format"""
        if value is None:
            return None
        return value.isoformat()
    
    @validator('preferences_count', 'reading_streak', 'total_articles_read')
    def validate_stats(cls, v):
        """Validate user statistics"""
        if v < 0:
            raise ValueError('Statistics cannot be negative')
        return v


class UserPreferenceUpdate(BaseModel):
    """
    Schema for updating user preferences
    """
    # Source preferences
    preferred_sources: Optional[List[UUID]] = Field(None, description="Preferred news sources")
    blocked_sources: Optional[List[UUID]] = Field(None, description="Blocked news sources")
    
    # Topic preferences
    preferred_topics: Optional[List[str]] = Field(None, description="Preferred topics")
    ignored_topics: Optional[List[str]] = Field(None, description="Ignored topics")
    
    # Content preferences
    sentiment_preference: Optional[str] = Field(None, regex='^(positive|negative|neutral|all)$', description="Sentiment preference")
    reading_level: Optional[str] = Field(None, regex='^(simple|mixed|complex)$', description="Reading level preference")
    notification_frequency: Optional[str] = Field(None, regex='^(realtime|hourly|daily|weekly)$', description="Notification frequency")
    
    @validator('preferred_topics', 'ignored_topics')
    def validate_topics(cls, v):
        """Validate topics list"""
        if v is not None:
            for topic in v:
                if len(topic.strip()) == 0:
                    raise ValueError('Topics cannot be empty')
                if len(topic) > 50:
                    raise ValueError('Topics cannot exceed 50 characters')
            # Remove duplicates while preserving order
            return list(dict.fromkeys([topic.strip() for topic in v]))
        return v
    
    @validator('preferred_sources', 'blocked_sources')
    def validate_sources(cls, v):
        """Validate sources list"""
        if v is not None:
            # Check for duplicates
            if len(v) != len(set(v)):
                raise ValueError('Sources list cannot contain duplicates')
            # Check list size
            if len(v) > 50:
                raise ValueError('Cannot have more than 50 sources')
        return v
    
    @root_validator
    def validate_preference_consistency(cls, values):
        """Validate preference consistency"""
        preferred_topics = values.get('preferred_topics')
        ignored_topics = values.get('ignored_topics')
        
        if preferred_topics is not None and ignored_topics is not None:
            conflicts = set(preferred_topics) & set(ignored_topics)
            if conflicts:
                raise ValueError(f'Cannot both prefer and ignore topics: {list(conflicts)}')
        
        return values


class UserStats(BaseModel):
    """
    Schema for user statistics
    """
    total_articles_read: int = Field(ge=0, description="Total articles read")
    articles_this_week: int = Field(ge=0, description="Articles read this week")
    articles_this_month: int = Field(ge=0, description="Articles read this month")
    reading_streak_days: int = Field(ge=0, description="Current reading streak in days")
    longest_reading_streak: int = Field(ge=0, description="Longest reading streak")
    favorite_sources: List[Dict[str, Any]] = Field(default_factory=list, description="Favorite news sources")
    favorite_topics: List[str] = Field(default_factory=list, description="Favorite topics")
    avg_reading_time: float = Field(ge=0.0, description="Average reading time in minutes")
    
    @validator('articles_this_week', 'articles_this_month')
    def validate_article_counts(cls, v, values):
        """Validate article counts are consistent"""
        total = values.get('total_articles_read', 0)
        if v > total:
            raise ValueError('Articles count for period cannot exceed total articles')
        return v
    
    @validator('reading_streak_days', 'longest_reading_streak')
    def validate_streaks(cls, v):
        """Validate streak values"""
        if v > 3650:  # 10 years max
            raise ValueError('Streak cannot exceed 10 years')
        return v


class UserActivity(BaseModel):
    """
    Schema for user activity tracking
    """
    user_id: UUID
    activity_type: str = Field(..., regex='^(read|search|share|bookmark|like|comment)$', description="Activity type")
    article_id: Optional[UUID] = None
    activity_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    @field_serializer('created_at')
    def serialize_datetime(self, value: datetime) -> str:
        """Serialize datetime to ISO format"""
        return value.isoformat()


# Utility functions for user validation
def validate_email_format(email: str) -> bool:
    """Validate email format using regex"""
    email_pattern = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    return bool(email_pattern.match(email))


def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Validate password strength and return detailed feedback
    """
    feedback = {
        'is_strong': False,
        'score': 0,
        'issues': [],
        'suggestions': []
    }
    
    score = 0
    
    # Length check
    if len(password) >= 8:
        score += 1
    else:
        feedback['issues'].append('Password is too short')
        feedback['suggestions'].append('Use at least 8 characters')
    
    if len(password) >= 12:
        score += 1
    
    # Character variety checks
    if re.search(r'[a-z]', password):
        score += 1
    else:
        feedback['issues'].append('Missing lowercase letters')
        feedback['suggestions'].append('Add lowercase letters')
    
    if re.search(r'[A-Z]', password):
        score += 1
    else:
        feedback['issues'].append('Missing uppercase letters')
        feedback['suggestions'].append('Add uppercase letters')
    
    if re.search(r'\d', password):
        score += 1
    else:
        feedback['issues'].append('Missing numbers')
        feedback['suggestions'].append('Add numbers')
    
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1
    else:
        feedback['issues'].append('Missing special characters')
        feedback['suggestions'].append('Add special characters')
    
    # Common password checks
    common_passwords = [
        'password', '123456', 'qwerty', 'abc123', 'password123',
        'admin', 'letmein', 'welcome', 'monkey', 'dragon'
    ]
    
    if password.lower() in common_passwords:
        feedback['issues'].append('Common password detected')
        feedback['suggestions'].append('Use a less common password')
        score = 0  # Fail completely
    
    # Repetitive characters check
    if re.search(r'(.)\1{3,}', password):
        feedback['issues']..append('Too many repetitive characters')
        feedback['suggestions'].append('Avoid repetitive characters')
        score = max(0, score - 1)
    
    feedback['score'] = score
    feedback['is_strong'] = score >= 4 and len(password) >= 8
    
    return feedback


def generate_username_suggestions(email: str, max_suggestions: int = 5) -> List[str]:
    """
    Generate username suggestions based on email
    """
    suggestions = []
    
    # Extract username part from email
    email_user = email.split('@')[0]
    
    # Clean the username
    clean_username = re.sub(r'[^a-zA-Z0-9_-]', '', email_user)
    
    if len(clean_username) >= 3:
        suggestions.append(clean_username[:20])  # Limit to 20 chars
    
    # Add numbers
    if len(clean_username) >= 3:
        for i in range(1, max_suggestions + 1):
            suggestion = f"{clean_username[:15]}{i}"
            if len(suggestion) <= 20:
                suggestions.append(suggestion)
    
    # Add underscores/hyphens variants
    if '_' not in clean_username and len(clean_username) >= 3:
        suggestions.append(f"{clean_username[:15]}_user")
    
    if '-' not in clean_username and len(clean_username) >= 3:
        suggestions.append(f"{clean_username[:15]}-user")
    
    return list(dict.fromkeys(suggestions))[:max_suggestions]  # Remove duplicates
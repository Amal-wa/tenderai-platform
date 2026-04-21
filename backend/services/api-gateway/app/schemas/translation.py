# ==============================================================================
# SCHEMAS — Pydantic models for Translation API
# ==============================================================================

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class TranslationRequest(BaseModel):
    """
    Single translation request.
    
    Example:
        {
            "text": "Hello world",
            "source_lang": "en",
            "target_lang": "fr",
            "context": "greeting"
        }
    """
    text: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Text to translate (1-10000 characters)"
    )
    source_lang: str = Field(
        default="auto",
        description="Source language code (e.g., 'en', 'fr', 'auto' for auto-detect)"
    )
    target_lang: str = Field(
        ...,
        description="Target language code (e.g., 'en', 'fr', 'es')"
    )
    context: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional context for translation (e.g., 'business', 'medical', 'legal')"
    )


class BulkTranslationRequest(BaseModel):
    """
    Batch translation request.
    
    Example:
        {
            "texts": ["Hello", "World", "Test"],
            "source_lang": "en",
            "target_lang": "fr"
        }
    """
    texts: List[str] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="List of texts to translate (1-100 items)"
    )
    source_lang: str = Field(
        default="auto",
        description="Source language code"
    )
    target_lang: str = Field(
        ...,
        description="Target language code"
    )


class TranslationResponse(BaseModel):
    """
    Translation response with metadata.
    
    Example:
        {
            "original": "Hello world",
            "translated": "Bonjour le monde",
            "source_lang": "en",
            "target_lang": "fr",
            "cached": true,
            "timestamp": "2024-03-31T10:30:00Z"
        }
    """
    original: str = Field(
        ...,
        description="Original text"
    )
    translated: str = Field(
        ...,
        description="Translated text"
    )
    source_lang: str = Field(
        ...,
        description="Detected or specified source language"
    )
    target_lang: str = Field(
        ...,
        description="Target language"
    )
    cached: bool = Field(
        default=False,
        description="Whether this result came from cache"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp (UTC)"
    )


class BulkTranslationResponse(BaseModel):
    """
    Batch translation response.
    
    Example:
        {
            "translations": [
                {"original": "Hello", "translated": "Bonjour", ...},
                {"original": "World", "translated": "Monde", ...}
            ],
            "count": 2,
            "success": true,
            "cached_count": 1
        }
    """
    translations: List[TranslationResponse] = Field(
        ...,
        description="List of translation results"
    )
    count: int = Field(
        ...,
        description="Total number of translations"
    )
    cached_count: int = Field(
        default=0,
        description="Number of results from cache"
    )
    success: bool = Field(
        default=True,
        description="Whether all translations succeeded"
    )


class LanguageInfo(BaseModel):
    """Information about a supported language."""
    code: str = Field(
        ...,
        description="Language code (e.g., 'en', 'fr', 'zh-CN')"
    )
    name: str = Field(
        ...,
        description="Language name (English, Français, 中文, etc.)"
    )


class LanguagesResponse(BaseModel):
    """
    List of supported languages.
    
    Example:
        {
            "languages": [
                {"code": "en", "name": "English"},
                {"code": "fr", "name": "French"},
                ...
            ],
            "count": 100
        }
    """
    languages: List[LanguageInfo] = Field(
        ...,
        description="List of supported languages"
    )
    count: int = Field(
        ...,
        description="Total count of languages"
    )


class TranslationErrorResponse(BaseModel):
    """Standard error response for translation endpoints."""
    error: str = Field(
        ...,
        description="Error type (UnsupportedLanguage, InvalidText, ServiceError, etc.)"
    )
    detail: str = Field(
        ...,
        description="Detailed error message"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp (UTC)"
    )


# Pydantic v2 Config
class Config:
    from_attributes = True
    json_schema_extra = {
        "example": {
            "text": "Hello world",
            "source_lang": "en",
            "target_lang": "fr"
        }
    }

"""
Main FastAPI application for Triple Performance Services.

This application provides web services to enhance Triple Performance.
"""
from fastapi import FastAPI, Path
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

app = FastAPI(
    title="Triple Performance Services",
    description="""
    ## Web services to enhance Triple Performance
    
    This API provides services for:
    * **Translation**: Translate pages between different languages
    * **Transcripts**: Retrieve transcripts for pages
    
    ### Getting Started
    
    Use the interactive documentation below to try out the endpoints.
    All endpoints are currently scaffolded and ready for implementation.
    
    ### Authentication
    
    Currently no authentication is required. This will be added in future versions.
    
    ### Support
    
    For issues or questions, please visit: https://github.com/neayi/tripleperformance-services
    """,
    version="1.0.0",
    contact={
        "name": "Triple Performance Team",
        "url": "https://github.com/neayi/tripleperformance-services",
    },
    license_info={
        "name": "License",
        "url": "https://github.com/neayi/tripleperformance-services/blob/main/LICENSE",
    },
)


class TranslationRequest(BaseModel):
    """Request model for translation endpoint."""
    content: Optional[Dict[str, Any]] = Field(
        None,
        description="Content to translate (page data, text, metadata, etc.)",
        examples=[{"text": "Hello World", "format": "html"}]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "content": {
                    "text": "Hello World",
                    "format": "html",
                    "metadata": {"author": "user123"}
                }
            }
        }


class TranslationResponse(BaseModel):
    """Response model for translation endpoint."""
    success: bool = Field(..., description="Whether the translation was successful")
    message: str = Field(..., description="Status message or error description")
    translated_content: Optional[Dict[str, Any]] = Field(
        None,
        description="Translated content",
        examples=[{"text": "Bonjour le monde", "format": "html"}]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Translation completed successfully",
                "translated_content": {
                    "text": "Bonjour le monde",
                    "format": "html"
                }
            }
        }


class TranscriptRequest(BaseModel):
    """Request model for transcripts endpoint."""
    options: Optional[Dict[str, Any]] = Field(
        None,
        description="Options for transcript retrieval (format, language, etc.)",
        examples=[{"format": "srt", "language": "en"}]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "options": {
                    "format": "srt",
                    "language": "en",
                    "include_timestamps": True
                }
            }
        }


class TranscriptResponse(BaseModel):
    """Response model for transcripts endpoint."""
    success: bool = Field(..., description="Whether the transcript retrieval was successful")
    message: str = Field(..., description="Status message or error description")
    transcripts: Optional[Dict[str, Any]] = Field(
        None,
        description="Transcript data",
        examples=[{"content": "This is the transcript...", "duration": 120}]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Transcripts retrieved successfully",
                "transcripts": {
                    "content": "This is the transcript...",
                    "duration": 120,
                    "language": "en"
                }
            }
        }


@app.get(
    "/",
    tags=["Health"],
    summary="Health Check",
    response_description="Service status information"
)
async def root():
    """
    ## Health Check Endpoint
    
    Returns the current status of the service.
    
    Use this endpoint to verify that the service is running and accessible.
    """
    return {
        "status": "ok",
        "service": "Triple Performance Services",
        "version": "1.0.0"
    }


@app.post(
    "/translation/translate/{source_lang}/{dest_lang}/page",
    response_model=TranslationResponse,
    tags=["Translation"],
    summary="Translate Page",
    response_description="Translation result with translated content"
)
async def translate_page(
    source_lang: str = Path(
        ...,
        description="Source language code",
        examples=["en", "fr", "de", "es"]
    ),
    dest_lang: str = Path(
        ...,
        description="Destination language code",
        examples=["en", "fr", "de", "es"]
    ),
    request: TranslationRequest = None
):
    """
    ## Translate a page from source language to destination language
    
    This endpoint translates page content between different languages.
    
    ### Parameters
    
    * **source_lang**: The source language code (ISO 639-1 format, e.g., 'en', 'fr', 'de')
    * **dest_lang**: The destination language code (ISO 639-1 format, e.g., 'en', 'fr', 'de')
    * **request body**: Optional content to translate with metadata
    
    ### Example Usage
    
    Translate from English to French:
    ```
    POST /translation/translate/en/fr/page
    {
        "content": {
            "text": "Hello World",
            "format": "html"
        }
    }
    ```
    
    ### Returns
    
    A JSON response containing:
    * Success status
    * Status message
    * Translated content (when successful)
    
    ### Note
    
    ⚠️ This endpoint is currently scaffolded. Implementation pending.
    """
    return TranslationResponse(
        success=True,
        message=f"Translation endpoint called: {source_lang} -> {dest_lang}",
        translated_content={"note": "Implementation pending"}
    )


@app.post(
    "/get_transcripts/{page}",
    response_model=TranscriptResponse,
    tags=["Transcripts"],
    summary="Get Page Transcripts",
    response_description="Transcript data for the specified page"
)
async def get_transcripts(
    page: str = Path(
        ...,
        description="Page identifier or URL slug",
        examples=["example-page", "my-video-page", "tutorial-123"]
    ),
    request: TranscriptRequest = None
):
    """
    ## Get transcripts for a specific page
    
    Retrieves transcript data for a given page, such as video transcripts,
    audio transcripts, or any text-based content associated with the page.
    
    ### Parameters
    
    * **page**: The unique identifier or slug for the page (e.g., 'example-page', 'video-123')
    * **request body**: Optional parameters for transcript retrieval (format, language, etc.)
    
    ### Example Usage
    
    Get transcripts for a page:
    ```
    POST /get_transcripts/example-page
    {
        "options": {
            "format": "srt",
            "language": "en",
            "include_timestamps": true
        }
    }
    ```
    
    ### Returns
    
    A JSON response containing:
    * Success status
    * Status message
    * Transcript data (content, duration, language, etc.)
    
    ### Supported Formats
    
    * Plain text
    * SRT (SubRip)
    * VTT (WebVTT)
    * JSON with timestamps
    
    ### Note
    
    ⚠️ This endpoint is currently scaffolded. Implementation pending.
    """
    return TranscriptResponse(
        success=True,
        message=f"Transcripts endpoint called for page: {page}",
        transcripts={"note": "Implementation pending"}
    )

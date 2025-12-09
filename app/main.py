"""
Main FastAPI application for Triple Performance Services.

This application provides web services to enhance Triple Performance.
"""
import requests
from fastapi import FastAPI, Path, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import os
from urllib.parse import urlencode
from pwiki.wiki import Wiki
import mwparserfromhell
import yt_dlp
from sqlalchemy.orm import Session
from pathlib import Path as PathLib
import logging
from datetime import datetime, timezone

from app.database import get_db, init_db
from app.models import Task, TaskStatus
from app import tasks as task_service
from app.transcription_service import TranscriptionService

logger = logging.getLogger(__name__)

# Initialize transcription service
transcription_service = TranscriptionService()

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


@app.on_event("startup")
def startup_event():
    """Initialize database on startup."""
    init_db()


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
    video_url: Optional[str] = Field(
        None,
        description="The YouTube URL being processed for transcription",
        examples=["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]
    )
    transcripts: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Transcripts retrieved successfully",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "transcripts": "This is the transcript..."
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
    "/fetch_transcripts/{wikilang}/{page}",
    response_model=TranscriptResponse,
    tags=["Transcripts"],
    summary="Get the page main youtube URL, and try to fetch its transcripts from youtube. If the page has multiple URLs, iterate though them until one has transcripts. Eventually, if no transcripts were found, use an external service to create the transcripts. If the page already has transcripts, do nothing. Then push the transcripts back to the page.",
    response_description="Transcript data for the specified page"
)
async def fetch_transcripts(
    wikilang: str = Path(
        ...,
        description="Wiki language code",
        examples=["fr", "en", "de", "es"]
    ),
    page: str = Path(
        ...,
        description="Page identifier or URL slug",
        examples=["14 ANS D'ESSAIS : L'azote disponible peut-il être un facteur limitant en ACS"]
    ),
    request: TranscriptRequest = None,
    db: Session = Depends(get_db)
):
    """
    ## Get transcripts for a specific page

    Get the page main youtube URL, and try to fetch its transcripts from youtube.
    If the page has multiple URLs, iterate though them until one has transcripts.
    Eventually, if no transcripts were found, use an external service to create the transcripts.
    If the page already has transcripts, do nothing. Then push the transcripts back to the page.

    ### Parameters

    * **page**: The unique identifier or slug for the page (e.g., 'example-page', 'video-123')
    * **request body**: Optional parameters for transcript retrieval (format, language, etc.)

    ### Example Usage

    Get transcripts for a page:
    ```
    POST /fetch_transcripts/example-page
    {
        "options": {
            "language": "en",
            "force_fetch": false
        }
    }
    ```

    ### Returns

    A JSON response containing:
    * Success status
    * Status message
    * Transcript data (content, duration, language, etc.)

    """

    # Start by extracting the list of the youtube URLs for the page, using semantic mediawiki API and the "A une URL de vidéo" property:
    apiEndpoint = f"https://{wikilang}.tripleperformance.ag/api.php"

    parameters = {
        "action": "ask",
        "api_version": "3",
        "query": f"[[A une URL de vidéo::+]][[{page}]]|?A une URL de vidéo|?A des transcriptions",
        "format": "json"
    }
    url = apiEndpoint + "?" + urlencode(parameters)

    response = requests.get(url)
    data = response.json()

    youtube_urls = []
    pageHasTranscripts = False

    try:
        # API v3 returns results as a list containing dictionaries
        # Each dict has the page title as key and page data as value
        results = data.get('query', {}).get('results', [])

        for result_item in results:
            # Each item is a dict with page title as key
            for page_title, page_data in result_item.items():
                printouts = page_data.get('printouts', {})
                urls = printouts.get('A une URL de vidéo', [])
                youtube_urls.extend(urls)
                transcripts = printouts.get('A des transcriptions', [])
                if transcripts:
                    pageHasTranscripts = True

    except (KeyError, TypeError) as e:
        return TranscriptResponse(
            success=False,
            message=f"Error parsing API response: {str(e)}",
            video_url=None,
            transcripts=None
        )

    # If the page has transcripts already, let's parse the page and return the transcripts:
    if pageHasTranscripts and not request.options.get("force_fetch", False):
        ret = get_existing_transcripts(wikilang, page)
        if ret["success"]:
            transcripts = ret["trancripts"]
    else:
        # Try to fetch the transcripts from each youtube URL until one works:
        for youtube_url in youtube_urls:
            # Here we would implement the logic to fetch transcripts from YouTube
            # For now, we will just simulate this step
            print(f"Attempting to fetch transcripts for URL: {youtube_url}")
            # Simulate fetching transcripts
            fetched_transcripts = fetch_transcripts_using_ytDLP(wikilang, youtube_url)
            if fetched_transcripts:
                transcripts = fetched_transcripts
                break

        # If all methods failed, spawn a transcription task as fallback
        if transcripts is None and youtube_urls:
            logger.info(f"No transcripts available, creating transcription task for page: {page}")
            result = transcription_service.create_transcription_task(
                db,
                video_url=youtube_urls[0],
                page_name=page,
                wiki_lang=wikilang
            )
            if result["success"]:
                logger.info(f"Created transcription task {result['task_id']} for {page}")

    return TranscriptResponse(
        success=True,
        message=f"Found {len(youtube_urls)} video URL(s) for page: {page}. Has transcripts: {pageHasTranscripts}",
        video_url=youtube_urls[0] if youtube_urls else None,
        transcripts=transcripts
    )

def get_existing_transcripts(wikilang: str, page: str) -> Dict[str, Any]:
    """
    Retrieve existing transcripts from the specified page.

    ### Parameters

    * **wikilang**: The wiki language code (e.g., 'en', 'fr', 'de')
    * **page**: The unique identifier or slug for the page

    ### How it works
    The trancripts are stored in the page using the "Transcript" template, like this:

    {{Transcript
    |Introduction= some text...
    |Suite= some more text... }}

    or this:

    {{Transcript
    |Transcript= some text... }}

    ### Returns

    A dictionary containing the existing transcripts data.
    """

    #Use mwparserfromhell to parse the page content and extract the Transcript template data
    site = Wiki(api_endpoint = f"https://{wikilang}.tripleperformance.ag/api.php")

    #dump the __repr__ :
    test = site.__repr__()

    content = site.page_text(page)

    wikicode = mwparserfromhell.parse(content)
    templates = wikicode.filter_templates()

    transcripts = ""

    for template in templates:
        if template.name.matches("Transcript"):
            transcriptsParts = {}
            for param in template.params:
                transcriptsParts[param.name.strip_code().strip()] = param.value.strip_code().strip()

            if ("Introduction" in transcriptsParts):
                transcripts += transcriptsParts["Introduction"] + "\n"
            if ("Suite" in transcriptsParts):
                transcripts += transcriptsParts["Suite"] + "\n"
            if ("Transcript" in transcriptsParts):
                transcripts += transcriptsParts["Transcript"] + "\n"

    return {
        "success": True,
        "trancripts": transcripts
       }


def fetch_transcripts_using_ytDLP(wikilanguage: str, youtube_url: str) -> Optional[str]:
    """
    Fetch transcripts from YouTube using yt-dlp.

    ### Parameters

    * **lang**: The language code for the transcripts (e.g., 'en', 'fr')
    * **youtube_url**: The YouTube video URL

    ### Returns

    The fetched transcripts as a string, or None if not found.
    """

    # Get the transcripts using  yt-dlp --ignore-errors --skip-download --write-auto-sub --sub-lang fr --sub-format=ttml -o 'TTML/%(id)s.%(ext)s' https://www.youtube.com/watch?v=8IvlcrmA4LA
    ydl_opts = {
            'skip_download': True,
            'writeautomaticsub': True,
            'subtitleslangs': [wikilanguage],
            'subtitlesformat': 'ttml',
            'ignoreerrors': True,
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)

            subtitlesURL = info.get('requested_subtitles', {}).get(wikilanguage, {}).get('url', None)
            if subtitlesURL:
                # Fetch the subtitles content
                response = requests.get(subtitlesURL)
                if response.status_code == 200:
                    xml = response.text
                    # Parse the TTML XML to extract text
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(xml)
                    texts = []
                    for elem in root.iter('{http://www.w3.org/ns/ttml}p'):
                        texts.append(''.join(elem.itertext()))
                    return '\n'.join(texts)

            return None

    except Exception as e:
        return None

    return None


# Task Management Endpoints

class TaskResponse(BaseModel):
    """Response model for task information."""
    id: int
    task_type: str
    status: str
    page_name: Optional[str] = None
    wiki_lang: Optional[str] = None
    video_url: Optional[str] = None
    result: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@app.get(
    "/tasks",
    response_model=List[TaskResponse],
    tags=["Tasks"],
    summary="List all tasks",
    response_description="List of tasks with optional filters"
)
async def list_tasks(
    task_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    ## List all tasks

    Get a list of all tasks with optional filtering by type and status.

    ### Parameters

    * **task_type**: Filter by task type (e.g., 'fetch_transcripts', 'translation')
    * **status**: Filter by status (pending, running, completed, failed, cancelled)
    * **limit**: Maximum number of tasks to return (default: 100)
    """
    status_enum = TaskStatus[status.upper()] if status else None
    tasks = task_service.get_tasks(db, task_type=task_type, status=status_enum, limit=limit)

    return [
        TaskResponse(
            id=task.id,
            task_type=task.task_type,
            status=task.status.value,
            page_name=task.page_name,
            wiki_lang=task.wiki_lang,
            video_url=task.video_url,
            result=task.result,
            error_message=task.error_message,
            created_at=task.created_at.isoformat() if task.created_at else None,
            started_at=task.started_at.isoformat() if task.started_at else None,
            completed_at=task.completed_at.isoformat() if task.completed_at else None
        )
        for task in tasks
    ]


@app.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    tags=["Tasks"],
    summary="Get task by ID",
    response_description="Task details"
)
async def get_task(
    task_id: int = Path(..., description="Task ID"),
    db: Session = Depends(get_db)
):
    """
    ## Get task details

    Retrieve detailed information about a specific task.
    """
    task = task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskResponse(
        id=task.id,
        task_type=task.task_type,
        status=task.status.value,
        page_name=task.page_name,
        wiki_lang=task.wiki_lang,
        video_url=task.video_url,
        result=task.result,
        error_message=task.error_message,
        created_at=task.created_at.isoformat() if task.created_at else None,
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None
    )


# Audio files directory
AUDIO_DIR = PathLib("/app/audio")
AUDIO_DIR.mkdir(exist_ok=True)


@app.get(
    "/audio/{filename}",
    tags=["Audio"],
    summary="Get audio file",
    response_description="Audio file"
)
async def get_audio_file(
    filename: str = Path(..., description="Audio filename")
):
    """
    ## Serve audio files

    Returns the audio file for downloaded YouTube videos.
    These files are used by Fireflies.ai for transcription.

    ### Security Note

    In production, consider adding authentication or using signed URLs.
    """
    audio_path = AUDIO_DIR / filename

    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    # Validate filename to prevent directory traversal
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    return FileResponse(
        path=audio_path,
        media_type="audio/mpeg",
        filename=filename
    )


# Fireflies Webhook Endpoint

class FirefliesWebhookPayload(BaseModel):
    """Request model for Fireflies webhook."""
    meeting_id: str = Field(..., description="Fireflies meeting ID")
    title: str = Field(..., description="Meeting title")
    status: str = Field(..., description="Meeting status (e.g., 'completed')")
    transcript: Optional[str] = Field(None, description="Full transcript text")
    language: Optional[str] = Field(None, description="Detected language")
    duration: Optional[int] = Field(None, description="Meeting duration in seconds")
    audio_url: Optional[str] = Field(None, description="Audio URL")

    class Config:
        json_schema_extra = {
            "example": {
                "meeting_id": "abc123",
                "title": "Video Transcription",
                "status": "completed",
                "transcript": "This is the full transcript text...",
                "language": "fr",
                "duration": 1200,
                "audio_url": "http://example.com/audio/video.mp3"
            }
        }


class FirefliesWebhookResponse(BaseModel):
    """Response model for Fireflies webhook."""
    success: bool
    message: str
    page_updated: Optional[bool] = None


@app.post(
    "/webhooks/fireflies",
    response_model=FirefliesWebhookResponse,
    tags=["Webhooks"],
    summary="Fireflies transcription webhook",
    response_description="Webhook processing result"
)
async def fireflies_webhook(
    payload: FirefliesWebhookPayload,
    db: Session = Depends(get_db)
):
    """
    ## Fireflies.ai Webhook Endpoint

    This endpoint receives callbacks from Fireflies.ai when transcription is completed.

    ### Workflow:

    1. Receives transcription data from Fireflies
    2. Finds the corresponding task in the database by meeting_id
    3. Updates the task with transcription results
    4. Stores the transcription in the MediaWiki page
    5. Sets the "A des transcriptions" semantic property to true

    ### Configuration:

    In your Fireflies.ai dashboard, configure the webhook URL:
    ```
    https://your-domain.com/webhooks/fireflies
    ```

    ### Parameters:

    * **meeting_id**: Fireflies meeting ID (used to find the task)
    * **title**: Meeting title
    * **status**: Processing status ('completed', 'failed', etc.)
    * **transcript**: Full transcript text
    * **language**: Detected language
    * **duration**: Duration in seconds
    * **audio_url**: Original audio URL

    ### Returns:

    Success/failure status and whether the wiki page was updated.
    """
    result = transcription_service.process_fireflies_webhook(
        db,
        meeting_id=payload.meeting_id,
        title=payload.title,
        status=payload.status,
        transcript=payload.transcript,
        language=payload.language,
        duration=payload.duration,
        audio_url=payload.audio_url
    )

    return FirefliesWebhookResponse(
        success=result["success"],
        message=result["message"],
        page_updated=result.get("page_updated")
    )
"""
Main FastAPI application for Triple Performance Services.

This application provides web services to enhance Triple Performance.
"""
import requests
from fastapi import FastAPI, Path
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import os
from urllib.parse import urlencode
from pwiki.wiki import Wiki
import mwparserfromhell
import yt_dlp

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
        examples=["14 ANS D'ESSAIS : L’azote disponible peut-il être un facteur limitant en ACS"]
    ),
    request: TranscriptRequest = None
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

        transcripts = None  # Implementation pending for fetching or generating transcripts

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
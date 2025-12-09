"""
Worker for processing transcription tasks.

This worker downloads audio from YouTube videos and sends them to Fireflies.ai
for transcription when transcripts are not readily available.
"""
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
import requests
import yt_dlp
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import TaskStatus
from app import tasks as task_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Audio storage directory
AUDIO_DIR = Path("/app/audio")
AUDIO_DIR.mkdir(exist_ok=True)

# Fireflies API configuration
FIREFLIES_API_URL = "https://api.fireflies.ai/graphql"
FIREFLIES_API_KEY = os.getenv("FIREFLIES_API_KEY")


def download_audio_from_youtube(video_url: str, output_path: str) -> bool:
    """
    Download audio from YouTube video using yt-dlp.
    Uses lowest quality audio available to minimize file size.

    Args:
        video_url: YouTube video URL
        output_path: Path where audio file will be saved

    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"Downloading audio from: {video_url}")

    ydl_opts = {
        'format': 'worstaudio/worst',  # Lowest quality audio
        'outtmpl': output_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '64',  # Low quality for smaller file size
        }],
        'quiet': False,
        'no_warnings': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            video_id = info.get('id', 'unknown')
            logger.info(f"Successfully downloaded audio for video: {video_id}")
            return True
    except Exception as e:
        logger.error(f"Failed to download audio: {e}", exc_info=True)
        return False


def upload_to_fireflies(audio_file_path: str, audio_url: str, title: str) -> dict:
    """
    Upload audio file to Fireflies.ai for transcription.

    Args:
        audio_file_path: Local path to audio file
        audio_url: Public URL where audio can be accessed
        title: Meeting title

    Returns:
        dict: Response from Fireflies API with meeting ID and status
    """
    logger.info(f"Uploading to Fireflies: {title}")

    if not FIREFLIES_API_KEY:
        logger.error("FIREFLIES_API_KEY not set in environment")
        return {"error": "FIREFLIES_API_KEY not configured"}

    # GraphQL mutation for creating a meeting
    mutation = """
    mutation CreateMeeting($input: MeetingInput!) {
        createMeeting(input: $input) {
            meeting {
                id
                title
                status
                audio_url
            }
        }
    }
    """

    variables = {
        "input": {
            "title": title,
            "audio_url": audio_url,
            "language": "auto",  # Auto-detect language
        }
    }

    headers = {
        "Authorization": f"Bearer {FIREFLIES_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            FIREFLIES_API_URL,
            json={"query": mutation, "variables": variables},
            headers=headers,
            timeout=30
        )
        response.raise_for_status()

        data = response.json()
        logger.info(f"Fireflies response: {data}")

        if "errors" in data:
            logger.error(f"Fireflies API errors: {data['errors']}")
            return {"error": data["errors"]}

        meeting_data = data.get("data", {}).get("createMeeting", {}).get("meeting", {})
        logger.info(f"Created Fireflies meeting: {meeting_data.get('id')}")
        return meeting_data

    except Exception as e:
        logger.error(f"Failed to upload to Fireflies: {e}", exc_info=True)
        return {"error": str(e)}


def process_transcription_task(task_id: int):
    """
    Process a transcription task by:
    1. Downloading audio from YouTube
    2. Making it accessible via URL endpoint
    3. Uploading to Fireflies for transcription

    Args:
        task_id: ID of the task to process
    """
    db = SessionLocal()

    try:
        # Get task details
        task = task_service.get_task(db, task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return

        logger.info(f"Processing task {task_id}: {task.page_name}")

        # Task is already in READY_TO_DOWNLOAD status from creation

        # Extract video ID from URL
        video_url = task.video_url
        import re
        video_id_match = re.search(r'(?:v=|/)([a-zA-Z0-9_-]{11})', video_url)
        if not video_id_match:
            raise ValueError(f"Could not extract video ID from URL: {video_url}")

        video_id = video_id_match.group(1)

        # Step 1: Download audio from YouTube
        audio_filename = f"{video_id}.mp3"
        audio_path = AUDIO_DIR / audio_filename

        if not download_audio_from_youtube(video_url, str(audio_path.with_suffix(''))):
            raise Exception("Failed to download audio from YouTube")

        logger.info(f"Audio downloaded successfully: {audio_path}")

        # Update task status to audio-downloaded
        task_service.update_task_status(db, task_id, TaskStatus.AUDIO_DOWNLOADED)

        # Step 2: Generate audio URL
        # The audio file will be served by FastAPI endpoint
        audio_url = f"{os.getenv('BASE_URL', 'http://localhost:8000')}/audio/{audio_filename}"
        logger.info(f"Audio available at: {audio_url}")

        # Step 3: Upload to Fireflies
        title = task.page_name or f"Video {video_id}"
        fireflies_result = upload_to_fireflies(str(audio_path), audio_url, title)

        if "error" in fireflies_result:
            raise Exception(f"Fireflies upload failed: {fireflies_result['error']}")

        logger.info(f"Audio uploaded to Fireflies. Meeting ID: {fireflies_result.get('id')}")

        # Update task status to audio-uploaded-to-fireflies
        task_service.update_task_status(db, task_id, TaskStatus.AUDIO_UPLOADED_TO_FIREFLIES)

        # Update task with results
        result = {
            "audio_file": audio_filename,
            "audio_url": audio_url,
            "fireflies_meeting_id": fireflies_result.get("id"),
            "fireflies_status": fireflies_result.get("status"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        task_service.update_task_result(db, task_id, result)

        logger.info(f"Task {task_id} audio processing complete, waiting for Fireflies callback")

    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}", exc_info=True)
        task_service.update_task_status(
            db,
            task_id,
            TaskStatus.FAILED,
            error_message=str(e)
        )
    finally:
        db.close()


def main():
    """Main entry point for the worker."""
    logger.info("=" * 60)
    logger.info("TRANSCRIPTION WORKER - STARTING")
    logger.info("=" * 60)

    db = SessionLocal()

    try:
        # Get transcription tasks that are ready to download
        ready_tasks = task_service.get_tasks(
            db,
            task_type="create_transcription",
            status=TaskStatus.READY_TO_DOWNLOAD
        )

        logger.info(f"Found {len(ready_tasks)} tasks ready to download")

        for task in ready_tasks:
            process_transcription_task(task.id)

        return 0

    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    exit(main())

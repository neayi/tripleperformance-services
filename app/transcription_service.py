"""
Transcription service for managing YouTube video transcription workflow.

This service handles:
- Creating transcription tasks
- Processing Fireflies webhook callbacks
- Storing transcripts in MediaWiki pages
"""
import logging
import os
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from pwiki.wiki import Wiki
from app.models import TaskStatus
from app import tasks as task_service

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Service for managing video transcription workflow."""

    def __init__(self):
        """Initialize transcription service."""
        self.mediawiki_username = os.getenv("MEDIAWIKI_USERNAME")
        self.mediawiki_password = os.getenv("MEDIAWIKI_PASSWORD")

    def create_transcription_task(
        self,
        db: Session,
        video_url: str,
        page_name: Optional[str] = None,
        wiki_lang: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new transcription task.

        Args:
            db: Database session
            video_url: YouTube video URL
            page_name: MediaWiki page name (optional)
            wiki_lang: Wiki language code (optional)

        Returns:
            Dictionary with success status and task information
        """
        try:
            task = task_service.create_task(
                db,
                task_type="create_transcription",
                page_name=page_name,
                wiki_lang=wiki_lang,
                video_url=video_url
            )

            logger.info(f"Created transcription task {task.id} for video: {video_url}")

            return {
                "success": True,
                "message": f"Transcription task created. Task ID: {task.id}",
                "task_id": task.id,
                "task": task
            }
        except Exception as e:
            logger.error(f"Failed to create transcription task: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Failed to create task: {str(e)}",
                "task_id": None,
                "task": None
            }

    def process_fireflies_webhook(
        self,
        db: Session,
        meeting_id: str,
        title: str,
        status: str,
        transcript: Optional[str] = None,
        language: Optional[str] = None,
        duration: Optional[int] = None,
        audio_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process Fireflies webhook callback.

        Args:
            db: Database session
            meeting_id: Fireflies meeting ID
            title: Meeting title
            status: Processing status
            transcript: Full transcript text
            language: Detected language
            duration: Duration in seconds
            audio_url: Original audio URL

        Returns:
            Dictionary with success status and processing results
        """
        logger.info(f"Processing Fireflies webhook for meeting: {meeting_id}")

        try:
            # Find matching task by meeting_id
            task = self._find_task_by_meeting_id(db, meeting_id)

            if not task:
                logger.warning(f"No task found for meeting_id: {meeting_id}")
                return {
                    "success": False,
                    "message": f"No task found for meeting_id: {meeting_id}",
                    "page_updated": False
                }

            logger.info(f"Found matching task: {task.id}")

            # Check if transcription is complete
            if status != "completed":
                logger.info(f"Transcription status is '{status}', not completed yet")
                return {
                    "success": True,
                    "message": f"Transcription status: {status}",
                    "page_updated": False
                }

            if not transcript:
                logger.error("Webhook payload missing transcript text")
                return {
                    "success": False,
                    "message": "Missing transcript text in payload",
                    "page_updated": False
                }

            # Update task with transcript
            self._update_task_with_transcript(
                db, task, transcript, language, duration, status
            )

            # Store transcription in wiki page if page info available
            page_updated = False
            if task.page_name and task.wiki_lang:
                page_updated = self._store_transcript_in_wiki(
                    db, task, transcript, language
                )

            return {
                "success": True,
                "message": f"Transcription processed for task {task.id}",
                "page_updated": page_updated
            }

        except Exception as e:
            logger.error(f"Error processing Fireflies webhook: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "page_updated": False
            }

    def _find_task_by_meeting_id(self, db: Session, meeting_id: str):
        """
        Find task by Fireflies meeting ID.

        Args:
            db: Database session
            meeting_id: Fireflies meeting ID

        Returns:
            Task object or None
        """
        tasks = task_service.get_tasks(
            db,
            task_type="create_transcription",
            limit=1000
        )

        for task in tasks:
            if task.result and meeting_id in task.result:
                return task

        return None

    def _update_task_with_transcript(
        self,
        db: Session,
        task,
        transcript: str,
        language: Optional[str],
        duration: Optional[int],
        status: str
    ):
        """
        Update task with transcript data.

        Args:
            db: Database session
            task: Task object
            transcript: Transcript text
            language: Detected language
            duration: Duration in seconds
            status: Processing status
        """
        import json

        result = json.loads(task.result) if task.result else {}
        result["transcript"] = transcript
        result["transcript_language"] = language
        result["transcript_duration"] = duration
        result["fireflies_status"] = status

        task_service.update_task_result(db, task.id, result)
        logger.info(f"Updated task {task.id} with transcript data")

    def _store_transcript_in_wiki(
        self,
        db: Session,
        task,
        transcript: str,
        language: Optional[str]
    ) -> bool:
        """
        Store transcript in MediaWiki page.

        Args:
            db: Database session
            task: Task object with page_name and wiki_lang
            transcript: Transcript text to store
            language: Language of transcript

        Returns:
            True if successful, False otherwise
        """
        import json

        try:
            if not self.mediawiki_username or not self.mediawiki_password:
                raise Exception("MediaWiki credentials not configured")

            # Initialize Wiki client
            wiki_url = f"{task.wiki_lang}.tripleperformance.ag"
            wiki = Wiki(f"{self.mediawiki_username}@{wiki_url}")

            # Login
            if not wiki.login(self.mediawiki_username, self.mediawiki_password):
                raise Exception("Failed to login to wiki")

            # Get current page content
            page = wiki.page(task.page_name)
            current_content = page.text()

            # Add or update transcription section
            new_content = self._add_transcription_section(
                current_content,
                transcript
            )

            # Update page
            edit_summary = f"Added automatic transcription from Fireflies.ai (language: {language or task.wiki_lang})"
            wiki.edit(task.page_name, new_content, edit_summary)

            logger.info(f"Successfully updated wiki page: {task.page_name}")

            # Update task result with wiki update status
            result = json.loads(task.result) if task.result else {}
            result["wiki_updated"] = True
            result["wiki_update_timestamp"] = datetime.now(timezone.utc).isoformat()
            task_service.update_task_result(db, task.id, result)

            return True

        except Exception as e:
            logger.error(f"Failed to update wiki page: {e}", exc_info=True)

            # Update task with error
            result = json.loads(task.result) if task.result else {}
            result["wiki_updated"] = False
            result["wiki_update_error"] = str(e)
            task_service.update_task_result(db, task.id, result)

            return False

    def _add_transcription_section(
        self,
        current_content: str,
        transcript: str
    ) -> str:
        """
        Add or update transcription section in page content.

        Args:
            current_content: Current page wikitext
            transcript: Transcript text to add

        Returns:
            Updated page content
        """
        transcription_section = "== Transcription =="

        if transcription_section in current_content:
            # Replace existing transcription
            pattern = r'(== Transcription ==\s*\n).*?(?=\n== |\Z)'
            replacement = f'\\1\n{transcript}\n'
            new_content = re.sub(pattern, replacement, current_content, flags=re.DOTALL)
        else:
            # Append new transcription section
            new_content = f"{current_content}\n\n{transcription_section}\n\n{transcript}\n"

        return new_content

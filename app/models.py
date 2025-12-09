"""
Database models for tracking long-running tasks.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum
from datetime import datetime, timezone
import enum
from app.database import Base


class TaskStatus(enum.Enum):
    """
    Task status enumeration for transcription workflow.

    Workflow stages:
    1. READY_TO_DOWNLOAD - Initial status when task is created
    2. AUDIO_DOWNLOADED - yt-dlp has finished downloading the MP3
    3. AUDIO_UPLOADED_TO_FIREFLIES - MP3 is fully uploaded to Fireflies
    4. TRANSCRIPTION_PROCESSED - Fireflies called callback, transcription ready
    5. TRANSCRIPTION_DOWNLOADED - Transcription downloaded and stored locally
    6. TRANSCRIPTION_UPDATED_ON_WIKI - Transcription uploaded to wiki page
    7. COMPLETED - Everything done, temporary files deleted

    Error states:
    - FAILED - Task failed at some stage
    - CANCELLED - Task was cancelled by user
    """
    READY_TO_DOWNLOAD = "ready-to-download"
    AUDIO_DOWNLOADED = "audio-downloaded"
    AUDIO_UPLOADED_TO_FIREFLIES = "audio-uploaded-to-fireflies"
    TRANSCRIPTION_PROCESSED = "transcription-processed"
    TRANSCRIPTION_DOWNLOADED = "transcription-downloaded"
    TRANSCRIPTION_UPDATED_ON_WIKI = "transcription-updated-on-wiki"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(Base):
    """Model for tracking long-running tasks."""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String(50), nullable=False, index=True)  # e.g., 'fetch_transcripts', 'translation'
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.READY_TO_DOWNLOAD, index=True)

    # Task parameters
    page_name = Column(String(255), nullable=True, index=True)
    wiki_lang = Column(String(10), nullable=True)
    video_url = Column(String(500), nullable=True)

    # Result data
    result = Column(Text, nullable=True)  # JSON string with task results
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Task(id={self.id}, type={self.task_type}, status={self.status.value})>"

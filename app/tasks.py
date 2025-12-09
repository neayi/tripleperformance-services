"""
Service layer for task management operations.
"""
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional, List
import json

from app.models import Task, TaskStatus


def create_task(
    db: Session,
    task_type: str,
    page_name: Optional[str] = None,
    wiki_lang: Optional[str] = None,
    video_url: Optional[str] = None
) -> Task:
    """Create a new task."""
    task = Task(
        task_type=task_type,
        status=TaskStatus.READY_TO_DOWNLOAD,
        page_name=page_name,
        wiki_lang=wiki_lang,
        video_url=video_url
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: int) -> Optional[Task]:
    """Get a task by ID."""
    return db.query(Task).filter(Task.id == task_id).first()


def get_tasks(
    db: Session,
    task_type: Optional[str] = None,
    status: Optional[TaskStatus] = None,
    limit: int = 100
) -> List[Task]:
    """Get tasks with optional filters."""
    query = db.query(Task)

    if task_type:
        query = query.filter(Task.task_type == task_type)
    if status:
        query = query.filter(Task.status == status)

    return query.order_by(Task.created_at.desc()).limit(limit).all()


def update_task_status(
    db: Session,
    task_id: int,
    status: TaskStatus,
    error_message: Optional[str] = None
) -> Optional[Task]:
    """Update task status."""
    task = get_task(db, task_id)
    if not task:
        return None

    task.status = status

    # Set started_at on first status change from READY_TO_DOWNLOAD
    if status != TaskStatus.READY_TO_DOWNLOAD and not task.started_at:
        task.started_at = datetime.now(timezone.utc)

    # Set completed_at on terminal states
    if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
        task.completed_at = datetime.now(timezone.utc)

    if error_message:
        task.error_message = error_message

    db.commit()
    db.refresh(task)
    return task


def update_task_result(
    db: Session,
    task_id: int,
    result: dict
) -> Optional[Task]:
    """Update task result."""
    task = get_task(db, task_id)
    if not task:
        return None

    task.result = json.dumps(result)
    db.commit()
    db.refresh(task)
    return task


def delete_old_tasks(db: Session, days: int = 7) -> int:
    """Delete tasks older than specified days."""
    from datetime import timedelta
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    deleted = db.query(Task).filter(Task.created_at < cutoff_date).delete()
    db.commit()
    return deleted

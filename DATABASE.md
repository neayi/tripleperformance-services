# Task Management Database

## Overview

This service uses SQLite to track long-running tasks. The database is created automatically on container startup and is ephemeral (recreated when container restarts).

## Database Schema

### Task Table

Tracks the status and results of long-running operations.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary key |
| `task_type` | String(50) | Type of task (e.g., 'create_transcription') |
| `status` | Enum | Task workflow status (see below) |
| `page_name` | String(255) | MediaWiki page name (optional) |
| `wiki_lang` | String(10) | Wiki language code (optional) |
| `video_url` | String(500) | YouTube video URL (optional) |
| `result` | Text | JSON string with task results |
| `error_message` | Text | Error message if task failed |
| `created_at` | DateTime | When task was created |
| `started_at` | DateTime | When task processing started |
| `completed_at` | DateTime | When task reached terminal state |

### Task Status Workflow

For transcription tasks, the status follows this progression:

1. **ready-to-download** - Initial status when task is created
2. **audio-downloaded** - yt-dlp has finished downloading the MP3
3. **audio-uploaded-to-fireflies** - MP3 is fully uploaded to Fireflies.ai
4. **transcription-processed** - Fireflies called webhook, transcription ready
5. **transcription-downloaded** - Transcription downloaded and stored locally
6. **transcription-updated-on-wiki** - Transcription uploaded to wiki page
7. **completed** - Everything done, temporary files deleted

**Error States:**
- **failed** - Task failed at some stage (see error_message)
- **cancelled** - Task was cancelled by user

## API Endpoints

### List Tasks

```bash
GET /tasks?task_type=fetch_transcripts&status=completed&limit=50
```

**Query Parameters:**
- `task_type` (optional): Filter by task type
- `status` (optional): Filter by status (ready-to-download, audio-downloaded, audio-uploaded-to-fireflies, transcription-processed, transcription-downloaded, transcription-updated-on-wiki, completed, failed, cancelled)
- `limit` (optional): Maximum results (default: 100)

**Response:**
```json
[
  {
    "id": 1,
    "task_type": "fetch_transcripts",
    "status": "completed",
    "page_name": "Example Page",
    "wiki_lang": "fr",
    "video_url": "https://youtube.com/watch?v=...",
    "result": "{\"transcript\": \"...\"}",
    "error_message": null,
    "created_at": "2025-12-06T10:00:00Z",
    "started_at": "2025-12-06T10:00:05Z",
    "completed_at": "2025-12-06T10:02:30Z"
  }
]
```

### Get Task Details

```bash
GET /tasks/{task_id}
```

**Response:** Same as individual task object above.

## Usage in Code

### Creating a Task

```python
from app import tasks as task_service
from app.database import SessionLocal
from app.models import TaskStatus

db = SessionLocal()

# Create a new task
task = task_service.create_task(
    db,
    task_type="fetch_transcripts",
    page_name="Example Page",
    wiki_lang="fr",
    video_url="https://youtube.com/watch?v=..."
)

print(f"Created task ID: {task.id}")
```

### Updating Task Status

```python
# Mark audio as downloaded
task_service.update_task_status(db, task.id, TaskStatus.AUDIO_DOWNLOADED)

# Mark transcription complete
task_service.update_task_status(db, task.id, TaskStatus.COMPLETED)
task_service.update_task_result(db, task.id, {"transcript": "..."})

# Or handle failure
task_service.update_task_status(
    db,
    task.id,
    TaskStatus.FAILED,
    error_message="Failed to download video"
)
```

### Querying Tasks

```python
# Get all pending tasks
pending_tasks = task_service.get_tasks(db, status=TaskStatus.PENDING)

# Get tasks by type
transcript_tasks = task_service.get_tasks(db, task_type="fetch_transcripts")

# Get specific task
task = task_service.get_task(db, task_id=1)
```

## Database Location

- Development: `./tripleperformance.db` (in container)
- The database file is **not mounted** to the host, so it will be lost on container restart
- This is intentional for task tracking - tasks are meant to be processed within a container's lifetime

## Cleanup

To automatically delete old completed tasks (older than 7 days):

```python
deleted_count = task_service.delete_old_tasks(db, days=7)
```

This can be added to a cron job in the workers.

## Testing

```bash
# List all tasks
curl http://localhost:8000/tasks

# Get specific task
curl http://localhost:8000/tasks/1

# Filter by status
curl "http://localhost:8000/tasks?status=completed"

# Filter by type
curl "http://localhost:8000/tasks?task_type=fetch_transcripts"
```

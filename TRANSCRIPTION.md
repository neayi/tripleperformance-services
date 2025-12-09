# Transcription Creation Feature

## Overview

This service can automatically create transcriptions for YouTube videos using Fireflies.ai when transcripts are not readily available on YouTube.

## Architecture

The transcription process consists of two main components:

### 1. API Endpoint (Synchronous)
Creates a task in the database and returns immediately.

### 2. Background Worker (Asynchronous)
Processes tasks every 5 minutes via cron job:
- Downloads audio from YouTube (lowest quality to minimize bandwidth)
- Stores audio file locally and makes it accessible via HTTP
- Uploads to Fireflies.ai for transcription

## Workflow

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ POST /transcriptions/create
       │ {video_url, page_name, wiki_lang}
       ▼
┌─────────────────────────────────┐
│  FastAPI                        │
│  - Creates Task (status=PENDING)│
│  - Returns task_id immediately  │
└─────────────────────────────────┘
       │
       │ Task stored in SQLite
       ▼
┌─────────────────────────────────┐
│  Cron Worker (every 5 min)      │
│  - Finds PENDING tasks          │
│  - Updates status=RUNNING       │
│  - Downloads audio (yt-dlp)     │
│  - Uploads to Fireflies         │
│  - Updates status=COMPLETED     │
└─────────────────────────────────┘
       │
       │ Client polls task status
       ▼
┌─────────────────────────────────┐
│  GET /tasks/{task_id}           │
│  - Returns current status       │
│  - Returns results when done    │
└─────────────────────────────────┘
```

## API Usage

### 1. Create Transcription Task

```bash
curl -X POST "http://localhost:8000/transcriptions/create" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://www.youtube.com/watch?v=8IvlcrmA4LA",
    "page_name": "Réparer le désert dans la vigne",
    "wiki_lang": "fr"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Transcription task created. Task ID: 1",
  "task_id": 1,
  "task": {
    "id": 1,
    "task_type": "create_transcription",
    "status": "pending",
    "page_name": "Réparer le désert dans la vigne",
    "wiki_lang": "fr",
    "video_url": "https://www.youtube.com/watch?v=8IvlcrmA4LA",
    "result": null,
    "error_message": null,
    "created_at": "2025-12-06T10:00:00Z",
    "started_at": null,
    "completed_at": null
  }
}
```

### 2. Check Task Status

```bash
curl "http://localhost:8000/tasks/1"
```

**Response (Completed):**
```json
{
  "id": 1,
  "task_type": "create_transcription",
  "status": "completed",
  "page_name": "Réparer le désert dans la vigne",
  "wiki_lang": "fr",
  "video_url": "https://www.youtube.com/watch?v=8IvlcrmA4LA",
  "result": "{\"audio_file\": \"8IvlcrmA4LA.mp3\", \"audio_url\": \"http://localhost:8000/audio/8IvlcrmA4LA.mp3\", \"fireflies_meeting_id\": \"abc123\", \"fireflies_status\": \"processing\"}",
  "error_message": null,
  "created_at": "2025-12-06T10:00:00Z",
  "started_at": "2025-12-06T10:05:00Z",
  "completed_at": "2025-12-06T10:07:30Z"
}
```

### 3. Access Audio File

The downloaded audio file is accessible via HTTP:

```bash
curl "http://localhost:8000/audio/8IvlcrmA4LA.mp3" --output video.mp3
```

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Fireflies.ai API Configuration
FIREFLIES_API_KEY=your_fireflies_api_key

# Base URL for audio file access (used by Fireflies to download audio)
BASE_URL=https://your-domain.com
```

### Fireflies API Key

1. Sign up at [Fireflies.ai](https://fireflies.ai/)
2. Go to Settings → Integrations → API Access
3. Generate an API key
4. Add to `.env` file

## Worker Configuration

The transcription worker runs automatically every 5 minutes via cron:

```
*/5 * * * * cd /app && /usr/local/bin/python /app/workers/process_transcriptions.py >> /var/log/cron.log 2>&1
```

### Manual Execution

For testing, you can run the worker manually:

```bash
docker exec -it tripleperformance-services python /app/workers/process_transcriptions.py
```

### View Worker Logs

```bash
docker exec -it tripleperformance-services tail -f /var/log/cron.log
```

## Task States

| Status | Description |
|--------|-------------|
| `pending` | Task created, waiting for worker to pick it up |
| `running` | Worker is processing the task |
| `completed` | Task completed successfully |
| `failed` | Task failed (see `error_message` for details) |
| `cancelled` | Task was manually cancelled |

## Audio Storage

- Audio files are stored in `/app/audio/` inside the container
- Files are **ephemeral** - deleted when container restarts
- Format: MP3, 64kbps (lowest quality for minimal file size)
- Naming: `{youtube_video_id}.mp3`

## Fireflies Integration

The service integrates with Fireflies.ai in two ways:

### 1. Create Meeting (Outbound)

The worker uses Fireflies.ai GraphQL API to create a meeting:

#### Mutation

```graphql
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
```

#### Input

```json
{
  "title": "Page Title or Video ID",
  "audio_url": "http://your-domain.com/audio/video_id.mp3",
  "language": "auto"
}
```

### 2. Webhook Callback (Inbound)

When transcription is complete, Fireflies calls our webhook:

#### Webhook Configuration

In your Fireflies.ai dashboard, configure:
- **Webhook URL**: `https://your-domain.com/webhooks/fireflies`
- **Events**: Select "Transcription Complete"

#### Webhook Payload

```json
{
  "meeting_id": "abc123",
  "title": "Video Transcription",
  "status": "completed",
  "transcript": "Full transcript text...",
  "language": "fr",
  "duration": 1200,
  "audio_url": "http://example.com/audio/video.mp3"
}
```

#### Webhook Handler Actions

When webhook is received:
1. ✅ Finds matching task by meeting_id
2. ✅ Updates task with transcript data
3. ✅ Stores transcript in MediaWiki page
4. ✅ Adds "== Transcription ==" section to page
5. ✅ Sets semantic property "A des transcriptions" to true

### Storing Transcripts in MediaWiki

The webhook handler automatically:
- Retrieves current page content
- Adds or updates "== Transcription ==" section
- Formats transcript as wikitext
- Saves page with edit summary: "Added automatic transcription from Fireflies.ai"

#### Example Page Update

Before:
```wikitext
== Description ==
This is a video about...

== Voir aussi ==
* Related page
```

After:
```wikitext
== Description ==
This is a video about...

== Voir aussi ==
* Related page

== Transcription ==

Full transcript text from Fireflies...
```

## Error Handling

Common errors and solutions:

### "Failed to download audio from YouTube"
- Video may be private or deleted
- Network connectivity issues
- yt-dlp version outdated

### "FIREFLIES_API_KEY not configured"
- Add API key to `.env` file
- Restart container

### "Failed to upload to Fireflies"
- Check API key validity
- Ensure BASE_URL is publicly accessible
- Verify Fireflies API is operational

## Testing

### End-to-End Test

```bash
# 1. Create task
TASK_ID=$(curl -X POST "http://localhost:8000/transcriptions/create" \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' \
  | jq -r '.task_id')

echo "Task ID: $TASK_ID"

# 2. Trigger worker manually (or wait 5 minutes)
docker exec tripleperformance-services python /app/workers/process_transcriptions.py

# 3. Check status
curl "http://localhost:8000/tasks/$TASK_ID" | jq

# 4. Download audio
curl "http://localhost:8000/audio/dQw4w9WgXcQ.mp3" --output test.mp3
```

### Testing Webhook Endpoint

#### Simulate Fireflies Callback

```bash
curl -X POST "http://localhost:8000/webhooks/fireflies" \
  -H "Content-Type: application/json" \
  -d '{
    "meeting_id": "abc123",
    "title": "Test Transcription",
    "status": "completed",
    "transcript": "This is a test transcript. It contains the full text of the conversation.",
    "language": "fr",
    "duration": 120
  }'
```

#### Expected Response

```json
{
  "success": true,
  "message": "Transcription processed for task 1",
  "page_updated": true
}
```

#### Verify Wiki Update

1. Check task was updated:
```bash
curl "http://localhost:8000/tasks/1" | jq '.result'
```

2. Verify page on wiki:
```bash
# Check the wiki page directly
curl "https://fr.tripleperformance.ag/wiki/Your_Page_Name"
```

3. Look for "== Transcription ==" section with the transcript text

## Production Considerations

1. **Audio Storage**: Consider using S3/Azure Blob for persistent storage
2. **Base URL**: Must be publicly accessible for Fireflies to download audio
3. **Authentication**: Add API key auth for `/audio/*` endpoints
4. **Rate Limiting**: Implement rate limiting to prevent abuse
5. **Cleanup**: Add cron job to delete old audio files
6. **Monitoring**: Track task success/failure rates

## Dependencies

- `yt-dlp`: YouTube download
- `ffmpeg`: Audio extraction and conversion
- `sqlalchemy`: Database ORM
- `requests`: HTTP requests to Fireflies API

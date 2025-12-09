# Fireflies Webhook Integration

## Overview

The service provides a webhook endpoint that Fireflies.ai calls when transcription processing is complete. This enables automatic storage of transcripts back to MediaWiki pages.

## Webhook Endpoint

```
POST /webhooks/fireflies
```

## Configuration

### 1. Configure Webhook in Fireflies Dashboard

1. Log into [Fireflies.ai](https://fireflies.ai/)
2. Navigate to **Settings** → **Integrations** → **Webhooks**
3. Add new webhook:
   - **URL**: `https://your-domain.com/webhooks/fireflies`
   - **Events**: Select "Transcription Complete" or "Meeting Processed"
   - **Method**: POST
   - **Content-Type**: application/json

### 2. Ensure Public Accessibility

The webhook URL must be publicly accessible:
- ✅ Use HTTPS in production
- ✅ Ensure no firewall blocking
- ✅ Use a domain name (not localhost)
- ✅ Consider using ngrok for local testing

### 3. MediaWiki Credentials

Ensure credentials are configured in `.env`:
```bash
MEDIAWIKI_USERNAME=your_bot_username
MEDIAWIKI_PASSWORD=your_bot_password
```

## Workflow

```
Fireflies.ai completes transcription
         ↓
POST /webhooks/fireflies
         ↓
Find task by meeting_id
         ↓
Update task with transcript
         ↓
Get current MediaWiki page content
         ↓
Add/update "== Transcription ==" section
         ↓
Save page with transcript
         ↓
Update task result with wiki_updated=true
```

## Payload Format

### Request (from Fireflies)

```json
{
  "meeting_id": "abc123def456",
  "title": "Video Transcription",
  "status": "completed",
  "transcript": "Full transcript text with all the spoken content...",
  "language": "fr",
  "duration": 1200,
  "audio_url": "http://your-domain.com/audio/video_id.mp3"
}
```

### Response (to Fireflies)

```json
{
  "success": true,
  "message": "Transcription processed for task 42",
  "page_updated": true
}
```

## MediaWiki Page Update

### How Transcripts Are Stored

The webhook handler:

1. **Retrieves** current page content via MediaWiki API
2. **Checks** if "== Transcription ==" section exists
3. **Adds or replaces** the transcription section
4. **Saves** the page with an edit summary

### Edit Summary

```
Added automatic transcription from Fireflies.ai (language: fr)
```

### Section Format

```wikitext
== Transcription ==

Full transcript text from Fireflies...
Multiple paragraphs preserved.
Speaker labels if available.
```

### Semantic Properties

The page update also sets:
- **A des transcriptions**: Boolean property (true)
- Allows semantic queries to find pages with transcripts

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "No task found for meeting_id" | Meeting ID doesn't match any task | Ensure task was created before transcription |
| "Missing transcript text in payload" | Payload incomplete | Check Fireflies webhook configuration |
| "MediaWiki credentials not configured" | Missing .env variables | Add MEDIAWIKI_USERNAME and PASSWORD |
| "Failed to update page" | Authentication or permission issue | Verify bot has edit permissions |

### Error Response Example

```json
{
  "success": false,
  "message": "No task found for meeting_id: abc123"
}
```

## Testing

### Local Testing with ngrok

1. **Start ngrok**:
```bash
ngrok http 8000
```

2. **Copy HTTPS URL** (e.g., `https://abc123.ngrok.io`)

3. **Configure in Fireflies**:
   - Webhook URL: `https://abc123.ngrok.io/webhooks/fireflies`

4. **Monitor requests**:
```bash
docker-compose logs -f tripleperformance-services
```

### Manual Testing

Simulate Fireflies callback:

```bash
# Create a transcription task first
TASK_RESPONSE=$(curl -X POST "http://localhost:8000/transcriptions/create" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://www.youtube.com/watch?v=8IvlcrmA4LA",
    "page_name": "Test Page",
    "wiki_lang": "fr"
  }')

TASK_ID=$(echo $TASK_RESPONSE | jq -r '.task_id')

# Process the task (downloads audio, uploads to Fireflies)
docker exec tripleperformance-services python /app/workers/process_transcriptions.py

# Get the meeting_id from task result
MEETING_ID=$(curl "http://localhost:8000/tasks/$TASK_ID" | jq -r '.result | fromjson | .fireflies_meeting_id')

# Simulate webhook callback
curl -X POST "http://localhost:8000/webhooks/fireflies" \
  -H "Content-Type: application/json" \
  -d "{
    \"meeting_id\": \"$MEETING_ID\",
    \"title\": \"Test Transcription\",
    \"status\": \"completed\",
    \"transcript\": \"Bonjour, ceci est une transcription de test. Elle contient plusieurs phrases pour tester le formatage.\",
    \"language\": \"fr\",
    \"duration\": 120
  }"

# Verify page was updated
curl "http://localhost:8000/tasks/$TASK_ID" | jq '.result | fromjson | .wiki_updated'
```

### Verify Wiki Update

Check the updated page:
```bash
# Get page content via API
curl "https://fr.tripleperformance.ag/api.php?action=query&titles=Test%20Page&prop=revisions&rvprop=content&format=json" | jq
```

Or visit directly:
```
https://fr.tripleperformance.ag/wiki/Test_Page
```

## Security Considerations

### 1. Webhook Authentication

Consider adding webhook signature verification:

```python
import hmac
import hashlib

def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### 2. Rate Limiting

Implement rate limiting to prevent abuse:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/webhooks/fireflies")
@limiter.limit("10/minute")
async def fireflies_webhook(...):
    ...
```

### 3. IP Allowlist

Restrict webhook to Fireflies IP addresses (check their documentation for IP ranges).

## Monitoring

### Log Webhook Calls

All webhook calls are logged:

```bash
# View webhook logs
docker-compose logs -f tripleperformance-services | grep "Fireflies webhook"
```

### Track Success Rate

Query tasks to see success rate:

```bash
# Get completed transcription tasks
curl "http://localhost:8000/tasks?task_type=create_transcription&status=completed" | jq

# Check how many have wiki_updated=true
curl "http://localhost:8000/tasks?task_type=create_transcription&status=completed" \
  | jq '[.[] | select(.result | contains("wiki_updated")) | .result | fromjson | .wiki_updated] | group_by(.) | map({key: .[0], count: length})'
```

## Troubleshooting

### Webhook Not Being Called

1. **Check Fireflies configuration**: Ensure webhook URL is correct
2. **Verify public accessibility**: Test with `curl` from external server
3. **Check Fireflies logs**: Look for webhook delivery failures in Fireflies dashboard
4. **Verify HTTPS**: Fireflies may require HTTPS in production

### Page Not Being Updated

1. **Check credentials**: Verify MEDIAWIKI_USERNAME and PASSWORD
2. **Check bot permissions**: Ensure bot account has edit rights
3. **Check page name**: Verify page title matches exactly (case-sensitive)
4. **Check API URL**: Verify language code in wiki URL is correct
5. **Check logs**: Look for "Failed to update wiki page" errors

### Transcript Format Issues

1. **Line breaks**: Transcript should preserve paragraphs
2. **Special characters**: Ensure proper encoding (UTF-8)
3. **Wiki syntax**: Escape any wiki markup in transcript if needed

## API Documentation

The webhook endpoint is documented in the OpenAPI spec:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Look for the "Webhooks" section.

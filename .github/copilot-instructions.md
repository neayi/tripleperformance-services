# AI Coding Agent Instructions for Triple Performance Services

## Project Overview

This is a Python FastAPI microservice providing web APIs and scheduled workers for Triple Performance. The project uses Docker for containerization and runs both a web service (FastAPI on port 8000) and cron-based workers in a single container.

**Key Architecture**: Single-container deployment running both web service (uvicorn) and cron daemon, orchestrated by `docker-entrypoint.sh`.

## Project Structure

- `app/main.py` - FastAPI application with all REST endpoints
- `workers/` - Scheduled background tasks (cron-based)
  - `check_interwiki_links.py` - Weekly link validation worker (Sundays 2 AM)
- `docker-entrypoint.sh` - Container startup: starts cron daemon, then uvicorn
- `Dockerfile` - Sets up cron jobs and Python environment in single container
- `docker-compose.yml` - Single-service deployment with health checks

## Development Workflow

### Quick Start
```bash
# Build and run (preferred)
docker-compose up --build

# View live logs
docker-compose logs -f

# Manual worker execution (for testing)
docker exec -it tripleperformance-services python /app/workers/check_interwiki_links.py

# View cron logs
docker exec -it tripleperformance-services tail -f /var/log/cron.log
```

### Local Development Without Docker
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Note**: Workers won't run automatically in local mode - execute manually for testing.

## API Architecture Patterns

### FastAPI Structure Convention
All endpoints in `app/main.py` follow this pattern:
- Pydantic models for request/response (e.g., `TranslationRequest`, `TranslationResponse`)
- Explicit tags for organization (`["Health"]`, `["Translation"]`, `["Transcripts"]`)
- Rich OpenAPI documentation with examples in `Field()` and `Config.json_schema_extra`
- Path parameters with validation and examples using `Path(..., examples=[...])`

Example from `app/main.py`:
```python
@app.post("/translation/translate/{source_lang}/{dest_lang}/page",
          response_model=TranslationResponse, tags=["Translation"])
async def translate_page(
    source_lang: str = Path(..., description="...", examples=["en", "fr"]),
    dest_lang: str = Path(..., description="...", examples=["en", "fr"]),
    request: TranslationRequest = None
):
```

### Current Implementation Status
⚠️ **All endpoints are scaffolded** - they return placeholder responses. When implementing:
1. Keep the response models and signatures intact
2. Replace placeholder returns with actual logic
3. Maintain the OpenAPI documentation style
4. Add error handling with appropriate HTTP status codes

## Worker Implementation Pattern

Workers in `workers/` follow this structure:
```python
import logging
logger = logging.getLogger(__name__)

def worker_function():
    logger.info("Starting...")
    # Implementation here
    logger.info("Completed")
    return {"status": "completed", "timestamp": ...}

def main():
    logger.info("=" * 60)
    try:
        result = worker_function()
        return 0
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())
```

**Cron Configuration**: Defined in `Dockerfile` as:
```dockerfile
RUN echo "0 2 * * 0 cd /app && /usr/local/bin/python /app/workers/check_interwiki_links.py >> /var/log/cron.log 2>&1" > /etc/cron.d/interwiki-check
```

## Testing and Validation

### API Testing
FastAPI provides automatic interactive documentation:
- Swagger UI: `http://localhost:8000/docs` (interactive testing)
- ReDoc: `http://localhost:8000/redoc` (clean documentation)
- OpenAPI JSON: `http://localhost:8000/openapi.json`

### Manual Endpoint Testing
```bash
# Health check
curl http://localhost:8000/

# Translation endpoint (scaffolded)
curl -X POST "http://localhost:8000/translation/translate/en/fr/page" \
  -H "Content-Type: application/json" \
  -d '{"content": {"text": "Hello World"}}'

# Transcripts endpoint (scaffolded)
curl -X POST "http://localhost:8000/fetch_transcripts/example-page" \
  -H "Content-Type: application/json" \
  -d '{"options": {"format": "srt"}}'
```

## Dependencies and Requirements

Stack: FastAPI 0.104.1, Uvicorn 0.24.0, Pydantic 2.5.0, Python 3.11

**Adding Dependencies**:
1. Add to `requirements.txt`
2. Rebuild: `docker-compose build`
3. Restart: `docker-compose up`

**No environment variables currently required** - add to `docker-compose.yml` when needed.

## Key Conventions

1. **Single-container architecture**: Don't separate web service and workers into different containers
2. **Pydantic V2**: Use `Field()` and `Config.json_schema_extra` for examples (not deprecated `example=`)
3. **Logging**: Use standard `logging` module, configured at module level
4. **Path references**: Use `/app/` as base path inside containers
5. **Health checks**: Defined in docker-compose.yml, used by orchestration tools
6. **Cron format**: `minute hour day month day_of_week` - modify in Dockerfile

## Documentation Updates

When adding/modifying endpoints:
- Update docstrings with markdown formatting for OpenAPI
- Add examples to Pydantic models using `Field(..., examples=[...])`
- Tag endpoints appropriately for grouping
- Keep `API_DOCUMENTATION.md` and `CONTRIBUTING.md` in sync with changes

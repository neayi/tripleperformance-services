# Contributing to Triple Performance Services

Thank you for your interest in contributing to Triple Performance Services!

## Development Setup

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Git

### Local Development Without Docker

1. Clone the repository:
```bash
git clone https://github.com/neayi/tripleperformance-services.git
cd tripleperformance-services
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the web service:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Access the API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Local Development With Docker

```bash
# Build and run
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Project Structure

```
tripleperformance-services/
├── app/                    # FastAPI web application
│   ├── __init__.py
│   └── main.py            # API endpoints
├── workers/               # Background workers
│   ├── __init__.py
│   └── check_interwiki_links.py
├── Dockerfile             # Container definition
├── docker-compose.yml     # Docker orchestration
└── requirements.txt       # Python dependencies
```

## Implementing the Endpoints

### Translation Service

The translation endpoint is located in `app/main.py`:

```python
@app.post("/translation/translate/{source_lang}/{dest_lang}/page")
async def translate_page(source_lang: str, dest_lang: str, request: TranslationRequest):
    # TODO: Implement translation logic here
    # Consider using libraries like:
    # - googletrans
    # - deep-translator
    # - Or integrate with translation APIs
    pass
```

### Transcripts Service

The transcripts endpoint is in `app/main.py`:

```python
@app.post("/fetch_transcripts/{page}")
async def fetch_transcripts(page: str, request: TranscriptRequest):
    # TODO: Implement transcript retrieval logic here
    # Connect to your data source
    pass
```

### Interwiki Links Checker

The worker is located in `workers/check_interwiki_links.py`:

```python
def check_all_interwiki_links():
    # TODO: Implement link checking logic
    # 1. Connect to Triple Performance database
    # 2. Fetch all interwiki links
    # 3. Validate each link
    # 4. Report/log results
    pass
```

## Testing Your Changes

### Manual Testing

1. Start the service:
```bash
docker-compose up
```

2. Test endpoints with curl:
```bash
# Health check
curl http://localhost:8000/

# Translation endpoint
curl -X POST "http://localhost:8000/translation/translate/en/fr/page" \
  -H "Content-Type: application/json" \
  -d '{"content": {"text": "Hello"}}'

# Transcripts endpoint
curl -X POST "http://localhost:8000/fetch_transcripts/test-page" \
  -H "Content-Type: application/json" \
  -d '{"options": {}}'
```

3. Test worker manually:
```bash
docker exec -it tripleperformance-services python /app/workers/check_interwiki_links.py
```

### Adding Unit Tests

When adding functionality, consider adding tests:

1. Create a `tests/` directory
2. Add test files (e.g., `test_translation.py`, `test_transcripts.py`)
3. Use pytest or unittest
4. Update requirements.txt with test dependencies

## Code Style

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions small and focused

## Submitting Changes

1. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes

3. Test thoroughly

4. Commit with clear messages:
```bash
git commit -m "Add: description of your changes"
```

5. Push and create a pull request

## Adding Dependencies

When adding new Python packages:

1. Add to `requirements.txt`
2. Rebuild the Docker image:
```bash
docker-compose build
```

## Environment Variables

To add environment variables:

1. Create a `.env` file (already in .gitignore)
2. Add variables to `docker-compose.yml`:
```yaml
environment:
  - YOUR_VAR=${YOUR_VAR}
```

## Cron Schedule

The interwiki links checker runs weekly (Sunday at 2 AM). To change:

Edit the cron expression in `Dockerfile`:
```dockerfile
RUN echo "0 2 * * 0 cd /app && python /app/workers/check_interwiki_links.py >> /var/log/cron.log 2>&1" > /etc/cron.d/interwiki-check
```

Cron format: `minute hour day month day_of_week`

## Questions?

If you have questions or need help, please open an issue on GitHub.

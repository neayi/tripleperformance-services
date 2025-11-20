# tripleperformance-services

Web services that are used to enhance Triple Performance

## Overview

This repository contains Python-based web services and scheduled workers for Triple Performance. The services are containerized using Docker and include:

### Web Services (FastAPI)

- **POST /translation/translate/{source_lang}/{dest_lang}/page** - Translate page content between languages
- **POST /get_transcripts/{page}** - Get transcripts for a specific page
- **GET /** - Health check endpoint

### Scheduled Workers

- **check-all-interwiki_links** - Validates interwiki links (runs weekly via cron on Sunday at 2 AM)

## Prerequisites

- Docker
- Docker Compose

## Quick Start

### Build and Run with Docker Compose

```bash
# Build the Docker image
docker-compose build

# Start the services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the services
docker-compose down
```

### Build and Run with Docker

```bash
# Build the Docker image
docker build -t tripleperformance-services .

# Run the container
docker run -p 8000:8000 tripleperformance-services
```

## API Documentation

Once the service is running, you can access:

- **API Documentation (Swagger UI)**: http://localhost:8000/docs
- **Alternative API Documentation (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/

## API Usage Examples

### Health Check

```bash
curl http://localhost:8000/
```

### Translation Endpoint

```bash
curl -X POST "http://localhost:8000/translation/translate/en/fr/page" \
  -H "Content-Type: application/json" \
  -d '{"content": {"text": "Hello World"}}'
```

### Get Transcripts

```bash
curl -X POST "http://localhost:8000/get_transcripts/example-page" \
  -H "Content-Type: application/json" \
  -d '{"options": {}}'
```

## Development

### Project Structure

```
tripleperformance-services/
├── app/                          # FastAPI application
│   ├── __init__.py
│   └── main.py                   # Main application with API endpoints
├── workers/                      # Scheduled workers
│   ├── __init__.py
│   └── check_interwiki_links.py  # Interwiki links checker
├── docker-compose.yml            # Docker Compose configuration
├── Dockerfile                    # Docker image definition
├── docker-entrypoint.sh          # Container startup script
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

### Manual Worker Execution

To manually run the interwiki links checker:

```bash
# Inside the container
docker exec -it tripleperformance-services python /app/workers/check_interwiki_links.py

# Or from host (if you have Python and dependencies installed)
python workers/check_interwiki_links.py
```

### Viewing Cron Logs

```bash
# View cron logs
docker exec -it tripleperformance-services tail -f /var/log/cron.log
```

## Environment Variables

Currently, no environment variables are required. Add them to `docker-compose.yml` as needed for your implementation.

## Testing

The endpoints are currently scaffolded (implementation pending). To test the scaffolding:

```bash
# Test health check
curl http://localhost:8000/

# Test translation endpoint
curl -X POST "http://localhost:8000/translation/translate/en/fr/page" \
  -H "Content-Type: application/json" \
  -d '{}'

# Test transcripts endpoint
curl -X POST "http://localhost:8000/get_transcripts/test-page" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Next Steps

The following items are scaffolded and require implementation:

1. **Translation Service Implementation**
   - Add translation logic in `/translation/translate/{source_lang}/{dest_lang}/page`
   - Integrate with translation APIs or libraries

2. **Transcripts Service Implementation**
   - Add transcript retrieval logic in `/get_transcripts/{page}`
   - Connect to data source

3. **Interwiki Links Checker Implementation**
   - Add link validation logic in `workers/check_interwiki_links.py`
   - Connect to Triple Performance database
   - Implement link checking and reporting

## License

See LICENSE file for details

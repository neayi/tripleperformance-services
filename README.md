# tripleperformance-services

Web services that are used to enhance Triple Performance

> 📚 **Interactive API Documentation**: Automatic API documentation is included! See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for details.

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

## 📚 API Documentation

**Interactive documentation is automatically generated and available as soon as you start the service!**

FastAPI provides beautiful, interactive API documentation out-of-the-box. No additional setup required.

### Available Documentation Interfaces

Once the service is running, access the documentation at:

#### 1. 🎯 Swagger UI (Interactive)
**URL**: http://localhost:8000/docs

The Swagger UI provides:
- ✨ **Interactive API explorer** - Try endpoints directly from your browser
- 📝 **Request/Response examples** - See example data for all endpoints
- 🔍 **Schema inspection** - View detailed models and data structures
- 🧪 **Live testing** - Execute API calls and see real responses
- 📋 **Copy-paste curl commands** - Easy integration with command line

#### 2. 📖 ReDoc (Clean & Professional)
**URL**: http://localhost:8000/redoc

The ReDoc interface offers:
- 📄 **Clean, readable format** - Professional documentation layout
- 🔎 **Search functionality** - Quickly find endpoints
- 🖨️ **Print-friendly** - Great for PDF exports
- 📱 **Responsive design** - Works on all devices
- 🎨 **Better for presentations** - Polished look for stakeholders

#### 3. 🔧 OpenAPI JSON Schema
**URL**: http://localhost:8000/openapi.json

Machine-readable API specification:
- 🤖 **API client generation** - Use with Swagger Codegen, OpenAPI Generator
- 🔗 **Integration tools** - Import into Postman, Insomnia, etc.
- 📊 **API testing frameworks** - Integrate with automated tests
- 📐 **Contract testing** - Validate API implementations

### Documentation Features

All endpoints include:
- **Detailed descriptions** with markdown formatting
- **Parameter examples** showing valid inputs
- **Response schemas** with field descriptions
- **Example requests and responses** 
- **Tags for organization** (Health, Translation, Transcripts)
- **HTTP status codes** for different scenarios

### Quick Start with Documentation

1. Start the service:
   ```bash
   docker-compose up
   ```

2. Open your browser to:
   ```
   http://localhost:8000/docs
   ```

3. Try the "Health Check" endpoint:
   - Click on `GET /` 
   - Click "Try it out"
   - Click "Execute"
   - See the live response!

4. Test the Translation endpoint:
   - Click on `POST /translation/translate/{source_lang}/{dest_lang}/page`
   - Click "Try it out"
   - Enter `en` for source_lang and `fr` for dest_lang
   - Modify the request body if desired
   - Click "Execute"

### Health Check Endpoint

- **URL**: http://localhost:8000/
- **Method**: GET
- **Purpose**: Verify service is running

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

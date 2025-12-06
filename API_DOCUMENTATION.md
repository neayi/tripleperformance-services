# API Documentation Guide

## Overview

Triple Performance Services provides **automatic, interactive API documentation** powered by FastAPI. The documentation is generated directly from the code and is always up-to-date.

## 🚀 Accessing the Documentation

### Prerequisites

Make sure the service is running:

```bash
# Start with Docker Compose
docker-compose up

# Or with Docker directly
docker run -p 8000:8000 tripleperformance-services
```

### Documentation URLs

Once running, access the documentation at:

| Interface | URL | Best For |
|-----------|-----|----------|
| **Swagger UI** | http://localhost:8000/docs | Interactive testing, exploration |
| **ReDoc** | http://localhost:8000/redoc | Reading, presentations, PDF export |
| **OpenAPI JSON** | http://localhost:8000/openapi.json | API tools, client generation |

## 📖 Documentation Interfaces

### Swagger UI (Interactive)

**URL**: http://localhost:8000/docs

The Swagger UI is an interactive interface that allows you to:

#### Features:
- 🎯 **Try it out** - Execute API calls directly from the browser
- 📝 **See examples** - View request/response examples for all endpoints
- 🔍 **Explore schemas** - Inspect data models and types
- 📋 **Copy curl commands** - Get ready-to-use command-line examples
- 🎨 **Organized by tags** - Endpoints grouped logically (Health, Translation, Transcripts)

#### How to Use:
1. Navigate to http://localhost:8000/docs
2. Click on any endpoint to expand it
3. Click "Try it out" button
4. Fill in the parameters
5. Click "Execute"
6. View the response below

### ReDoc (Professional)

**URL**: http://localhost:8000/redoc

ReDoc provides a clean, three-panel layout:

#### Features:
- 📄 **Clean layout** - Professional, readable format
- 🔎 **Search** - Quickly find endpoints or models
- 🖨️ **Print-friendly** - Great for documentation packages
- 📱 **Responsive** - Works on desktop, tablet, and mobile
- 🎨 **Polished design** - Perfect for stakeholder presentations

#### Best Uses:
- Reading through API capabilities
- Sharing with team members
- Including in documentation packages
- Presenting to stakeholders

### OpenAPI Schema (JSON)

**URL**: http://localhost:8000/openapi.json

The raw OpenAPI 3.0 specification in JSON format.

#### Use Cases:
- **Generate API clients** - Use with openapi-generator or swagger-codegen
- **Import to tools** - Postman, Insomnia, Paw, etc.
- **API testing** - Integrate with testing frameworks
- **Contract validation** - Ensure API implementations match specification
- **Documentation generation** - Create custom documentation

## 🎯 Available Endpoints

### Health Check

**Endpoint**: `GET /`

Check if the service is running and responsive.

**Example Request**:
```bash
curl http://localhost:8000/
```

**Example Response**:
```json
{
  "status": "ok",
  "service": "Triple Performance Services",
  "version": "1.0.0"
}
```

---

### Translation Service

**Endpoint**: `POST /translation/translate/{source_lang}/{dest_lang}/page`

Translate page content from one language to another.

**Parameters**:
- `source_lang` (path) - Source language code (e.g., 'en', 'fr', 'de', 'es')
- `dest_lang` (path) - Destination language code (e.g., 'en', 'fr', 'de', 'es')
- Request body (optional) - Content to translate with metadata

**Example Request**:
```bash
curl -X POST "http://localhost:8000/translation/translate/en/fr/page" \
  -H "Content-Type: application/json" \
  -d '{
    "content": {
      "text": "Hello World",
      "format": "html",
      "metadata": {
        "author": "user123"
      }
    }
  }'
```

**Example Response**:
```json
{
  "success": true,
  "message": "Translation completed successfully",
  "translated_content": {
    "text": "Bonjour le monde",
    "format": "html"
  }
}
```

**Status**: ⚠️ Currently scaffolded - implementation pending

---

### Get Transcripts

**Endpoint**: `POST /fetch_transcripts/{page}`

Retrieve transcripts for a specific page.

**Parameters**:
- `page` (path) - Page identifier or slug
- Request body (optional) - Options for transcript retrieval

**Example Request**:
```bash
curl -X POST "http://localhost:8000/fetch_transcripts/example-page" \
  -H "Content-Type: application/json" \
  -d '{
    "options": {
      "format": "srt",
      "language": "en",
      "include_timestamps": true
    }
  }'
```

**Example Response**:
```json
{
  "success": true,
  "message": "Transcripts retrieved successfully",
  "transcripts": {
    "content": "This is the transcript...",
    "duration": 120,
    "language": "en"
  }
}
```

**Supported Formats**:
- Plain text
- SRT (SubRip subtitle format)
- VTT (WebVTT subtitle format)
- JSON with timestamps

**Status**: ⚠️ Currently scaffolded - implementation pending

---

## 🛠️ Using the Documentation

### Testing with Swagger UI

1. **Open Swagger UI**: http://localhost:8000/docs
2. **Find your endpoint**: Scroll or use tags to locate the endpoint
3. **Expand the endpoint**: Click on the endpoint row
4. **Click "Try it out"**: Button in the top right of the endpoint section
5. **Fill parameters**: Enter required and optional parameters
6. **Execute**: Click the "Execute" button
7. **View response**: See the actual API response below

### Example Workflow

#### Testing the Health Endpoint:
1. Navigate to http://localhost:8000/docs
2. Find the `GET /` endpoint under "Health" tag
3. Click to expand
4. Click "Try it out"
5. Click "Execute"
6. See the response: `{"status": "ok", ...}`

#### Testing Translation:
1. Find `POST /translation/translate/{source_lang}/{dest_lang}/page` under "Translation" tag
2. Click "Try it out"
3. Enter `en` for `source_lang`
4. Enter `fr` for `dest_lang`
5. Modify the request body (optional)
6. Click "Execute"
7. View the translation response

### Importing to Postman

1. Open Postman
2. Click "Import"
3. Choose "Link"
4. Enter: `http://localhost:8000/openapi.json`
5. Click "Continue"
6. Click "Import"
7. All endpoints are now available in Postman!

### Generating API Clients

You can generate client libraries in various languages:

```bash
# Install openapi-generator
npm install @openapitools/openapi-generator-cli -g

# Generate Python client
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g python \
  -o ./python-client

# Generate JavaScript/TypeScript client
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g typescript-fetch \
  -o ./typescript-client

# Generate Java client
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g java \
  -o ./java-client
```

## 📚 Documentation Features

### Request Body Examples

Each endpoint includes example request bodies that you can use as templates:

```json
{
  "content": {
    "text": "Hello World",
    "format": "html"
  }
}
```

### Response Models

All responses are documented with:
- Field names and types
- Field descriptions
- Example values
- Required vs optional fields

### Parameter Descriptions

Every parameter includes:
- Data type
- Whether it's required
- Description of what it does
- Example values

### Tags for Organization

Endpoints are organized by tags:
- **Health** - Service health and status
- **Translation** - Translation services
- **Transcripts** - Transcript retrieval

## 🔒 Authentication

Currently, no authentication is required for any endpoint.

**Note**: Authentication will be added in future versions. The documentation will automatically update to show authentication requirements when implemented.

## 📊 Response Codes

All endpoints return standard HTTP status codes:

- **200 OK** - Request successful
- **400 Bad Request** - Invalid parameters or request body
- **404 Not Found** - Resource not found
- **422 Unprocessable Entity** - Validation error
- **500 Internal Server Error** - Server error

The Swagger UI shows all possible response codes for each endpoint.

## 🎨 Customization

The API documentation is generated from the code, so:

- **Docstrings** become endpoint descriptions
- **Type hints** define parameter types
- **Pydantic models** define request/response schemas
- **Field descriptions** appear in the documentation
- **Examples** are shown in the interactive UI

To customize documentation:
1. Edit docstrings in `app/main.py`
2. Update Pydantic model descriptions
3. Add more examples to Field definitions
4. Restart the service
5. Documentation updates automatically!

## 💡 Tips

### For Developers
- Use Swagger UI for quick testing during development
- Export OpenAPI JSON for CI/CD integration
- Generate clients for your preferred language

### For Testers
- Use Swagger UI to manually test all endpoints
- Try different parameter combinations
- Verify response formats match documentation

### For Integration
- Import OpenAPI schema into your tools
- Generate type-safe clients
- Use for contract testing

### For Documentation
- Share the ReDoc URL for readable docs
- Export to PDF for offline reference
- Use OpenAPI JSON for custom doc generation

## 🚀 Next Steps

1. **Explore**: Open http://localhost:8000/docs and explore the API
2. **Test**: Try out the endpoints with different parameters
3. **Integrate**: Import the API into your favorite tools
4. **Develop**: Add your implementation to the scaffolded endpoints

## 📞 Support

For questions or issues:
- Check the [README.md](README.md) for general information
- Check [CONTRIBUTING.md](CONTRIBUTING.md) for development setup
- Visit: https://github.com/neayi/tripleperformance-services

---

**The documentation is always up-to-date** - it's generated directly from the code! 🎉

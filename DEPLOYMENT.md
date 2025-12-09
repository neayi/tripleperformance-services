# Production Deployment Guide

## Docker Image

The Docker image is automatically built and published to GitHub Container Registry (ghcr.io) when a new release is created.

### Available Tags

- `ghcr.io/neayi/tripleperformance-services:latest` - Latest release
- `ghcr.io/neayi/tripleperformance-services:v1.0.0` - Specific version (semver)
- `ghcr.io/neayi/tripleperformance-services:1.0` - Major.minor version
- `ghcr.io/neayi/tripleperformance-services:1` - Major version

## Deployment

### 1. Pull the Image

```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Pull the latest image
docker pull ghcr.io/neayi/tripleperformance-services:latest
```

### 2. Configure Environment

Create a `.env` file with your configuration:

```bash
# MediaWiki API Configuration
MEDIAWIKI_USERNAME=your_bot_username
MEDIAWIKI_PASSWORD=your_bot_password
MEDIAWIKI_API_URL=https://wiki.tripleperformance.fr/api.php
```

### 3. Deploy with Docker Compose

```bash
# Use production compose file
docker-compose -f docker-compose-prod.yml up -d

# Or deploy with the pre-built image
docker-compose -f docker-compose-prod.yml pull
docker-compose -f docker-compose-prod.yml up -d
```

### 4. Deploy with Docker Run

```bash
docker run -d \
  --name tripleperformance-services \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/logs:/var/log \
  --restart unless-stopped \
  ghcr.io/neayi/tripleperformance-services:latest
```

## Health Check

```bash
curl http://localhost:8000/
```

## Viewing Logs

```bash
# Docker Compose
docker-compose -f docker-compose-prod.yml logs -f

# Docker Run
docker logs -f tripleperformance-services

# Cron logs
docker exec tripleperformance-services tail -f /var/log/cron.log
```

## Updates

To update to a new version:

```bash
# Pull new image
docker-compose -f docker-compose-prod.yml pull

# Recreate container
docker-compose -f docker-compose-prod.yml up -d
```

## Creating a Release

1. Go to GitHub repository
2. Click "Releases" → "Create a new release"
3. Create a new tag (e.g., `v1.0.0`)
4. Add release notes
5. Click "Publish release"
6. GitHub Actions will automatically build and push the Docker image

## Monitoring

- **API Documentation**: http://your-server:8000/docs
- **Health Endpoint**: http://your-server:8000/
- **Logs**: `/var/log/cron.log` (inside container)

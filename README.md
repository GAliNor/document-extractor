# ocr-backend

OCR & document extraction API built with FastAPI. Extracts text from images and PDFs using EasyOCR and Docling, with optional face detection via OpenCV.

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

The API will be available at `http://localhost:8000`.

## Usage

**Extract text from an image or PDF:**

```bash
curl -X POST http://localhost:8000/api/v1/ocr/extract \
  -F "file=@document.pdf"
```

**With face/photo extraction:**

```bash
curl -X POST "http://localhost:8000/api/v1/ocr/extract?extract_images=true" \
  -F "file=@photo.jpg"
```

**Using the Docling engine:**

```bash
curl -X POST http://localhost:8000/api/v1/ocr/docling-extract \
  -F "file=@document.pdf"
```

**Health check:**

```bash
curl http://localhost:8000/api/v1/health
```

## Configuration

Set these in `.env`:

| Variable | Default | Description |
|---|---|---|
| `ENVIRONMENT` | `development` | Environment mode |
| `MAX_FILE_SIZE_MB` | `10` | Max upload size |
| `API_KEY` | *(empty)* | API key for auth (disabled when empty) |

When `API_KEY` is set, all OCR endpoints require an `X-API-Key` header.

## Supported Formats

- Images: JPEG, PNG, WEBP
- PDFs: up to 10 pages
- Languages: French, English

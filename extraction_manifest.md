# Extraction Manifest — Future DI Notes Repository (Repository 2)

This document provides an audited inventory of all backend components, configuration, and supporting assets inside **Repository 1** that are required when transferring the **AI Content Engine** into **Repository 2 (DI Notes)**.

---

## 1. Required Backend Source Code (`backend/app/`)

These directories and files constitute the core backend service and MUST be transferred:

| Component Path | Description | Transfer Scope |
| :--- | :--- | :--- |
| `backend/app/main.py` | FastAPI entrypoint, router mounting, CORS middleware, health endpoint | Required |
| `backend/app/core/config.py` | Configuration settings (API keys, CORS origins, max file size) | Required |
| `backend/app/api/v1/endpoints/convert.py` | Phase 1: Conversion endpoint (`POST /convert`) & Download (`GET /download`) | Required |
| `backend/app/api/v1/endpoints/process.py` | Phase 2: AI Processing endpoint (`POST /process`) & Health check | Required |
| `backend/app/modules/ai_engine/` | AI Provider abstraction layer (Gemini, Grok, Groq, OpenRouter, OpenAI, Mock) | Required |
| `backend/app/modules/ingestion/` | Document ingestion, MarkItDown wrapper, PDF/DOCX extractors, OCR, image pipeline | Required |
| `backend/app/modules/prompts/builder.py` | PromptBuilder (Strict, Non-Strict, Scratch mode grounding logic) | Required |
| `backend/app/schemas/processing.py` | Pydantic request/response contract definitions | Required |
| `backend/app/services/content_processor.py` | Central Phase 2 AI engine orchestration service | Required |
| `backend/app/services/conversion_storage.py` | Storage manager for generated Markdown artifacts & metadata | Required |

---

## 2. Required Backend Test Suite (`backend/tests/`)

All automated PyTest test files MUST be transferred to guarantee continuous test coverage in Repository 2:

- `backend/tests/test_api.py`
- `backend/tests/test_convert.py`
- `backend/tests/test_extractors.py`
- `backend/tests/test_image_understanding.py`
- `backend/tests/test_markitdown.py`
- `backend/tests/test_prompts.py`
- `backend/tests/test_providers.py`

---

## 3. Required Configuration & Build Files

| File | Description | Transfer Scope |
| :--- | :--- | :--- |
| `backend/requirements.txt` | Backend Python dependencies | Required |
| `backend/Dockerfile` | Backend Docker build container definition | Required |
| `.env.example` | Template for environment variable configurations | Required |
| `docker-compose.yml` | Backend container service composition | Required (Backend service block) |

---

## 4. Temporary Test Frontend (Repository 1 Scope Only)

The following files belong **exclusively to the temporary test client** in Repository 1 and WILL NOT be transferred to Repository 2:

- `frontend/` (All Next.js frontend code, React components, package.json, node_modules)
- `frontend/Dockerfile`

---

## 5. Optional / Development Assets

- `backend/temp/conversions/` (Local runtime conversion storage directory; created dynamically on startup)
- `.pytest_cache/` & `__pycache__/` (Build and test execution caches)

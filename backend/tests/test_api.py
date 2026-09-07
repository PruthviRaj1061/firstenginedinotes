import pytest
from fastapi.testclient import TestClient
from app.modules.ai_engine.mock_provider import MockProvider
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def override_ai_provider(monkeypatch):
    import app.api.v1.endpoints.process as process_endpoint
    import app.services.content_processor as content_processor_module

    monkeypatch.setattr(process_endpoint, "get_ai_provider", lambda: MockProvider())
    monkeypatch.setattr(content_processor_module, "get_ai_provider", lambda: MockProvider())



def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    assert "provider" in data
    assert "tesseract_available" in data


def test_process_scratch_mode():
    response = client.post(
        "/api/v1/process",
        data={
            "mode": "scratch",
            "prompt": "Write a greeting message",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["mode"] == "scratch"
    assert "content" in data
    assert data["content"] != ""


def test_process_strict_mode_with_file():
    sample_text = "The launch date is October 15, 2026."
    files = [("files", ("info.txt", sample_text.encode("utf-8"), "text/plain"))]
    
    response = client.post(
        "/api/v1/process",
        data={
            "mode": "strict",
            "prompt": "What is the launch date?",
        },
        files=files,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["mode"] == "strict"
    assert "content" in data


def test_process_invalid_mode():
    response = client.post(
        "/api/v1/process",
        data={
            "mode": "invalid_mode",
            "prompt": "Test prompt",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "Invalid mode" in data["error"]

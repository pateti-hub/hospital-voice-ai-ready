from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from openai import APIConnectionError

from app import config
from app.services import agent


class FakeSession:
    def __init__(self):
        self.added = []

    async def get(self, model, conversation_id):
        return None

    def add(self, item):
        self.added.append(item)

    async def flush(self):
        for item in self.added:
            if hasattr(item, "channel") and getattr(item, "id", None) is None:
                item.id = uuid4()

    async def commit(self):
        return None


def test_settings_without_groq_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    settings = config.Settings(_env_file=None)

    assert settings.groq_api_key is None
    assert settings.groq_model == "llama-3.1-8b-instant"
    assert settings.groq_base_url == "https://api.groq.com/openai/v1"


@pytest.mark.asyncio
async def test_missing_groq_key_uses_deterministic_fallback(monkeypatch):
    monkeypatch.setattr(agent, "get_settings", lambda: SimpleNamespace(groq_api_key=None))

    assert await agent._llm_answer("hours?", "approved context") is None


@pytest.mark.asyncio
async def test_groq_client_receives_configured_base_url_and_model(monkeypatch):
    calls = {}

    class FakeCompletions:
        async def create(self, **kwargs):
            calls["request"] = kwargs
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="approved answer"))]
            )

    class FakeClient:
        def __init__(self, **kwargs):
            calls["client"] = kwargs
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr(agent, "get_settings", lambda: SimpleNamespace(
        groq_api_key="test-key",
        groq_base_url="https://example.invalid/openai/v1",
        groq_model="test-model",
    ))
    monkeypatch.setattr("openai.AsyncOpenAI", FakeClient)

    assert await agent._llm_answer("hours?", "approved context") == "approved answer"
    assert calls["client"] == {
        "api_key": "test-key",
        "base_url": "https://example.invalid/openai/v1",
        "timeout": 10.0,
    }
    assert calls["request"]["model"] == "test-model"
    assert calls["request"]["temperature"] == 0


@pytest.mark.asyncio
async def test_provider_failure_returns_safe_retrieval_fallback(monkeypatch):
    docs = [{"id": "doc-1", "title": "Hours", "content": "Open 9 to 5", "source_url": None}]

    async def return_docs(*args):
        return docs

    async def return_none(*args):
        return None

    monkeypatch.setattr(agent, "retrieve", return_docs)
    monkeypatch.setattr(agent, "_llm_answer", return_none)

    _, _, result, _ = await agent.respond(FakeSession(), "What are the hours?", None, "api")

    assert result.answer == "Here is the relevant hospital information: Open 9 to 5"


@pytest.mark.asyncio
async def test_provider_connection_failure_returns_none(monkeypatch):
    class FailingCompletions:
        async def create(self, **kwargs):
            raise APIConnectionError(
                message="provider unavailable",
                request=httpx.Request("POST", "https://example.invalid"),
            )

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(completions=FailingCompletions())

    monkeypatch.setattr(agent, "get_settings", lambda: SimpleNamespace(
        groq_api_key="test-key",
        groq_base_url="https://example.invalid/openai/v1",
        groq_model="test-model",
    ))
    monkeypatch.setattr("openai.AsyncOpenAI", FakeClient)

    assert await agent._llm_answer("hours?", "approved context") is None


@pytest.mark.asyncio
async def test_emergency_response_does_not_call_groq(monkeypatch):
    async def fail_if_called(*args, **kwargs):
        raise AssertionError("emergency requests must not reach retrieval or Groq")

    monkeypatch.setattr(agent, "retrieve", fail_if_called)
    monkeypatch.setattr(agent, "_llm_answer", fail_if_called)
    monkeypatch.setattr(agent, "get_settings", lambda: SimpleNamespace(emergency_phone="112"))

    _, _, result, _ = await agent.respond(FakeSession(), "I have chest pain", None, "api")

    assert result.emergency is True
    assert "call 112 now" in result.answer


def test_openai_environment_names_are_removed_from_app_and_docs():
    paths = [
        "app/config.py",
        "app/services/agent.py",
        "README.md",
        "docs/ARCHITECTURE.md",
        ".env.example",
    ]
    forbidden = ("OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_BASE_URL")

    for path in paths:
        content = open(path, encoding="utf-8").read()
        assert not any(name in content for name in forbidden), path
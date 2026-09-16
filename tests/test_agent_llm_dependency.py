import pytest
from fastapi import HTTPException

import src.api.dependencies as dependencies
from src.agent.openai_llm import OpenAIStructuredLLM


def _clear() -> None:
    dependencies.get_structured_llm.cache_clear()


def test_structured_llm_builds_openai_adapter(monkeypatch) -> None:
    _clear()
    monkeypatch.setattr(dependencies.settings, "LLM_PROVIDER", "openai")
    monkeypatch.setattr(dependencies.settings, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(dependencies.settings, "LLM_MODEL", "test-model")
    llm = dependencies.get_structured_llm()
    assert isinstance(llm, OpenAIStructuredLLM)
    assert llm.model == "test-model"
    _clear()


def test_structured_llm_rejects_unconfigured_provider(monkeypatch) -> None:
    _clear()
    monkeypatch.setattr(dependencies.settings, "LLM_PROVIDER", "")
    with pytest.raises(HTTPException) as exc:
        dependencies.get_structured_llm()
    assert exc.value.status_code == 503
    _clear()


def test_structured_llm_requires_key_and_model(monkeypatch) -> None:
    _clear()
    monkeypatch.setattr(dependencies.settings, "LLM_PROVIDER", "openai")
    monkeypatch.setattr(dependencies.settings, "LLM_API_KEY", "")
    monkeypatch.setattr(dependencies.settings, "LLM_MODEL", "")
    with pytest.raises(HTTPException) as exc:
        dependencies.get_structured_llm()
    assert exc.value.status_code == 503
    _clear()

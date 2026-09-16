from fastapi.testclient import TestClient

from src.agent.evidence import EvidenceStatus
from src.agent.explainer import GroundedExplanation
from src.api.app import app
from src.api.dependencies import get_agent_service, get_company_service, get_neo4j_connection, get_settings


class _CompanyService:
    def list_companies(self, *, limit, offset, search=None, industry_id=None, entity_type=None):
        assert search == "nvidia"
        assert industry_id == "semiconductors"
        assert entity_type == "public"
        return {"companies": [{"company_id": "nvidia", "name": "NVIDIA", "industry_id": "semiconductors", "entity_type": "public"}], "count": 1, "limit": limit, "offset": offset}

    def search_entities(self, query, *, limit):
        return {"query": query, "count": 1, "results": [{"label": "Company", "entity_id": "nvidia", "name": "NVIDIA", "properties": {"company_id": "nvidia"}}]}


class _AgentService:
    async def answer(self, question):
        return GroundedExplanation(answer="Grounded answer.", evidence_status=EvidenceStatus.SUFFICIENT, event_refs=["event:evt-1"], path_ids=["P1"])


class _Result:
    def single(self):
        return {"ok": 1}


class _Session:
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def run(self, *_args, **_kwargs): return _Result()


class _Driver:
    def session(self): return _Session()


class _Connection:
    driver = _Driver()


def test_company_list_supports_frontend_filters():
    app.dependency_overrides[get_company_service] = lambda: _CompanyService()
    try:
        response = TestClient(app).get("/companies?search=nvidia&industry_id=semiconductors&entity_type=public")
        assert response.status_code == 200
        assert response.json()["count"] == 1
    finally:
        app.dependency_overrides.clear()


def test_global_entity_search_is_typed():
    app.dependency_overrides[get_company_service] = lambda: _CompanyService()
    try:
        response = TestClient(app).get("/api/v1/search?q=nvidia")
        assert response.status_code == 200
        assert response.json()["results"][0]["label"] == "Company"
    finally:
        app.dependency_overrides.clear()


def test_agent_response_exposes_typed_provenance():
    app.dependency_overrides[get_agent_service] = lambda: _AgentService()
    try:
        response = TestClient(app).post("/api/v1/agent/query", json={"question": "How is NVIDIA exposed?"})
        assert response.status_code == 200
        assert response.json()["provenance"] == [{"source": None, "timestamp": None, "confidence": None, "event_id": "event:evt-1"}]
    finally:
        app.dependency_overrides.clear()


def test_detailed_health_reports_subsystems(monkeypatch):
    app.dependency_overrides[get_neo4j_connection] = lambda: _Connection()
    settings = get_settings()
    monkeypatch.setattr(settings, "LLM_PROVIDER", "")
    try:
        response = TestClient(app).get("/api/v1/health/detailed")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "healthy"
        assert body["services"]["neo4j"]["status"] == "healthy"
        assert body["services"]["agent_llm"]["status"] == "unconfigured"
    finally:
        app.dependency_overrides.clear()

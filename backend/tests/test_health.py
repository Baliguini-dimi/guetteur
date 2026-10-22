"""Vérifications du point de santé sans dépendance à une base réelle."""

from fastapi.testclient import TestClient

from guetteur.main import app


def test_health_response_has_security_headers() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["x-content-type-options"] == "nosniff"
    expected_csp = "default-src 'none'; frame-ancestors 'none'"
    assert response.headers["content-security-policy"] == expected_csp


def test_api_documentation_is_not_exposed() -> None:
    response = TestClient(app).get("/openapi.json")

    assert response.status_code == 404

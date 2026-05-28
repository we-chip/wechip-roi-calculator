"""Shared pytest fixtures."""
import base64
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def auth_env(monkeypatch):
    monkeypatch.setenv("BASIC_AUTH_USER", "admin")
    monkeypatch.setenv("BASIC_AUTH_PASS", "secret")
    yield ("admin", "secret")


@pytest.fixture
def no_auth_env(monkeypatch):
    monkeypatch.delenv("BASIC_AUTH_USER", raising=False)
    monkeypatch.delenv("BASIC_AUTH_PASS", raising=False)
    yield


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_links.db")


@pytest.fixture
def app(db_path):
    import app as app_module
    application = app_module.create_app(db_path=db_path)
    application.config["TESTING"] = True
    # Reset rate-limiter buckets between tests
    app_module._RATE_BUCKETS.clear()
    return application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def basic_auth_header(auth_env):
    user, pwd = auth_env
    token = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    return {"Authorization": f"Basic {token}"}

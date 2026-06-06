import base64


def test_admin_401_without_creds(client, auth_env):
    r = client.get("/admin/links")
    assert r.status_code == 401
    assert "Basic" in r.headers.get("WWW-Authenticate", "")


def test_admin_200_with_correct_creds(client, basic_auth_header):
    r = client.get("/admin/links", headers=basic_auth_header)
    assert r.status_code == 200


def test_admin_401_with_wrong_creds(client, auth_env):
    bad = base64.b64encode(b"admin:wrong").decode()
    r = client.get("/admin/links", headers={"Authorization": f"Basic {bad}"})
    assert r.status_code == 401


def test_admin_503_when_env_unset(no_auth_env, db_path):
    import importlib
    import app as app_module
    importlib.reload(app_module)
    application = app_module.create_app(db_path=db_path)
    application.config["TESTING"] = True
    c = application.test_client()
    r = c.get("/admin/links")
    assert r.status_code == 503


# --- Entra SSO (Easy Auth principal) -----------------------------------------

SSO_HEADER = {"X-MS-CLIENT-PRINCIPAL-NAME": "thomas@CHIP811.onmicrosoft.com"}


def test_admin_sso_principal_allowed_when_no_allowlist(client, no_auth_env):
    # SSO principal present, ADMIN_EMAILS unset -> any tenant member allowed.
    r = client.get("/admin/links", headers=SSO_HEADER)
    assert r.status_code == 200


def test_admin_sso_principal_allowed_when_listed(client, monkeypatch, no_auth_env):
    monkeypatch.setenv("ADMIN_EMAILS", "thomas@wechip.ch, thomas@CHIP811.onmicrosoft.com")
    r = client.get("/admin/links", headers=SSO_HEADER)
    assert r.status_code == 200


def test_admin_sso_principal_denied_when_not_listed(client, monkeypatch, no_auth_env):
    monkeypatch.setenv("ADMIN_EMAILS", "someone-else@wechip.ch")
    r = client.get("/admin/links", headers=SSO_HEADER)
    assert r.status_code == 403


def test_admin_redirects_to_login_when_sso_mode_and_anonymous(client, monkeypatch, no_auth_env):
    monkeypatch.setenv("ADMIN_SSO", "true")
    r = client.get("/admin/links")
    assert r.status_code == 302
    assert "/.auth/login/aad" in r.headers.get("Location", "")


def test_admin_basic_auth_still_works_alongside_sso(client, basic_auth_header):
    # No SSO header -> falls back to Basic auth (unchanged behavior).
    r = client.get("/admin/links", headers=basic_auth_header)
    assert r.status_code == 200


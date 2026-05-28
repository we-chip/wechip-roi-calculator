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

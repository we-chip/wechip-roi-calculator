import db as link_db


def _create_via_api(client, basic_auth_header, slug="acme-01", **config):
    body = {"slug": slug, "display_name": "Acme", "config": config or {"revPerColDay": 7}}
    return client.post("/admin/api/links", json=body, headers=basic_auth_header)


def test_create_and_list(client, basic_auth_header, db_path):
    r = _create_via_api(client, basic_auth_header)
    assert r.status_code == 200
    assert r.get_json()["ok"] is True
    links = link_db.list_links(db_path)
    assert len(links) == 1 and links[0]["slug"] == "acme-01"
    r = client.get("/admin/links", headers=basic_auth_header)
    assert b"acme-01" in r.data


def test_create_collision(client, basic_auth_header):
    r1 = _create_via_api(client, basic_auth_header, slug="dup")
    assert r1.status_code == 200
    r2 = _create_via_api(client, basic_auth_header, slug="dup")
    assert r2.status_code == 409
    assert "already exists" in " ".join(r2.get_json()["errors"])


def test_create_invalid_slug(client, basic_auth_header):
    r = _create_via_api(client, basic_auth_header, slug="BAD slug")
    assert r.status_code == 400


def test_create_invalid_config(client, basic_auth_header):
    r = client.post("/admin/api/links",
                    json={"slug": "x1", "display_name": "", "config": {"wechipSharePct": 200}},
                    headers=basic_auth_header)
    assert r.status_code == 400
    assert any("wechipSharePct" in e for e in r.get_json()["errors"])


def test_update_link(client, basic_auth_header, db_path):
    _create_via_api(client, basic_auth_header, slug="lead-1")
    r = client.put("/admin/api/links/lead-1",
                   json={"display_name": "Updated", "config": {"revPerColDay": 9}},
                   headers=basic_auth_header)
    assert r.status_code == 200
    link = link_db.get_link("lead-1", db_path)
    assert link["display_name"] == "Updated"
    assert link["config"]["revPerColDay"] == 9


def test_update_404(client, basic_auth_header):
    r = client.put("/admin/api/links/nope",
                   json={"display_name": "x", "config": {}},
                   headers=basic_auth_header)
    assert r.status_code == 404


def test_revoke_then_404(client, basic_auth_header, db_path):
    _create_via_api(client, basic_auth_header, slug="rev-me")
    assert client.get("/c/rev-me").status_code == 200
    r = client.post("/admin/api/links/rev-me/revoke", headers=basic_auth_header)
    assert r.status_code == 200
    assert client.get("/c/rev-me").status_code == 404
    r2 = client.post("/admin/api/links/rev-me/revoke", headers=basic_auth_header)
    assert r2.status_code == 200


def test_admin_calculator_shows_admin_panel(client, basic_auth_header):
    r = client.get("/admin", headers=basic_auth_header)
    assert r.status_code == 200
    html = r.data.decode()
    assert '"__admin": true' in html
    assert "admin-panel.js" in html


def test_admin_calculator_loads_existing_slug(client, basic_auth_header, db_path):
    _create_via_api(client, basic_auth_header, slug="prefill", revPerColDay=12)
    r = client.get("/admin?slug=prefill", headers=basic_auth_header)
    assert r.status_code == 200
    html = r.data.decode()
    assert '"__editing_slug": "prefill"' in html
    assert '"revPerColDay": 12' in html


def test_public_does_not_get_admin_flag(client):
    r = client.get("/")
    assert b"__admin" not in r.data


# ── model lock ────────────────────────────────────────────────────────────

def test_create_with_forced_model_solaire(client, basic_auth_header, db_path):
    r = client.post("/admin/api/links",
                    json={"slug": "force-sol", "display_name": "X", "config": {}, "model": "solaire"},
                    headers=basic_auth_header)
    assert r.status_code == 200
    link = link_db.get_link("force-sol", db_path)
    assert link["model"] == "solaire"
    # Customer page exposes model in the injected JSON.
    html = client.get("/c/force-sol").data.decode()
    assert '"model": "solaire"' in html


def test_create_default_model_is_auto_and_not_injected(client, basic_auth_header, db_path):
    r = client.post("/admin/api/links",
                    json={"slug": "auto-link", "display_name": "", "config": {}},
                    headers=basic_auth_header)
    assert r.status_code == 200
    link = link_db.get_link("auto-link", db_path)
    assert link["model"] == "auto"
    # 'auto' is omitted from the customer payload (no lock to apply).
    html = client.get("/c/auto-link").data.decode()
    assert '"model":' not in html
    assert '"model": ' not in html


def test_bad_model_coerced_to_auto(client, basic_auth_header, db_path):
    r = client.post("/admin/api/links",
                    json={"slug": "bad-model", "display_name": "", "config": {},
                          "model": "<script>"},
                    headers=basic_auth_header)
    assert r.status_code == 200
    link = link_db.get_link("bad-model", db_path)
    assert link["model"] == "auto"


def test_update_changes_model(client, basic_auth_header, db_path):
    _create_via_api(client, basic_auth_header, slug="mod-up")
    r = client.put("/admin/api/links/mod-up",
                   json={"display_name": "X", "config": {}, "model": "filaire"},
                   headers=basic_auth_header)
    assert r.status_code == 200
    link = link_db.get_link("mod-up", db_path)
    assert link["model"] == "filaire"
    html = client.get("/c/mod-up").data.decode()
    assert '"model": "filaire"' in html


def test_admin_calculator_exposes_model_for_editing(client, basic_auth_header):
    client.post("/admin/api/links",
                json={"slug": "edit-me", "display_name": "", "config": {}, "model": "solaire"},
                headers=basic_auth_header)
    html = client.get("/admin?slug=edit-me", headers=basic_auth_header).data.decode()
    assert '"model": "solaire"' in html

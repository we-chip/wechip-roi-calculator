import db as link_db


def _create_via_admin(client, basic_auth_header, slug="acme-01", **extra):
    # Need CSRF: first GET the form to get token in session
    r = client.get("/admin/links/new", headers=basic_auth_header)
    assert r.status_code == 200
    token = _extract_csrf(r.data.decode())
    form = {"slug": slug, "display_name": "Acme", "_csrf": token,
            "revPerColDay": "7", "discountPct": "10"}
    form.update(extra)
    return client.post("/admin/links/new", data=form, headers=basic_auth_header,
                       follow_redirects=False)


def _extract_csrf(html: str) -> str:
    import re
    m = re.search(r'name="_csrf"\s+value="([^"]+)"', html)
    assert m, "no csrf token in form"
    return m.group(1)


def test_create_and_list(client, basic_auth_header, db_path):
    r = _create_via_admin(client, basic_auth_header)
    assert r.status_code == 302
    links = link_db.list_links(db_path)
    assert len(links) == 1 and links[0]["slug"] == "acme-01"
    r = client.get("/admin/links", headers=basic_auth_header)
    assert b"acme-01" in r.data


def test_create_collision(client, basic_auth_header):
    r1 = _create_via_admin(client, basic_auth_header, slug="dup")
    assert r1.status_code == 302
    r2 = _create_via_admin(client, basic_auth_header, slug="dup")
    assert r2.status_code == 200
    assert b"already exists" in r2.data


def test_create_invalid_slug(client, basic_auth_header):
    r = _create_via_admin(client, basic_auth_header, slug="BAD slug")
    assert r.status_code == 200
    assert b"invalid" in r.data


def test_edit_link(client, basic_auth_header, db_path):
    _create_via_admin(client, basic_auth_header, slug="lead-1")
    r = client.get("/admin/links/lead-1", headers=basic_auth_header)
    assert r.status_code == 200
    token = _extract_csrf(r.data.decode())
    r = client.post("/admin/links/lead-1",
                    data={"_csrf": token, "display_name": "Updated", "revPerColDay": "9"},
                    headers=basic_auth_header)
    assert r.status_code == 302
    link = link_db.get_link("lead-1", db_path)
    assert link["display_name"] == "Updated"
    assert link["config"]["revPerColDay"] == 9


def test_revoke_then_404(client, basic_auth_header, db_path):
    _create_via_admin(client, basic_auth_header, slug="rev-me")
    # Customer view works first
    assert client.get("/c/rev-me").status_code == 200
    # Need fresh CSRF for revoke
    r = client.get("/admin/links", headers=basic_auth_header)
    token = _extract_csrf(r.data.decode())
    r = client.post("/admin/links/rev-me/revoke",
                    data={"_csrf": token}, headers=basic_auth_header)
    assert r.status_code == 302
    # Customer now 404
    assert client.get("/c/rev-me").status_code == 404
    # Revoke is idempotent (reuse same session token)
    r2 = client.post("/admin/links/rev-me/revoke",
                     data={"_csrf": token}, headers=basic_auth_header)
    assert r2.status_code == 302

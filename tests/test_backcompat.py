def test_root_still_renders(client):
    r = client.get("/")
    assert r.status_code == 200
    body = r.data
    assert b"WECHIP" in body
    assert b"modulesInput" in body
    # Existing share button still present
    assert b'id="btnShare"' in body


def test_query_string_share_link_loads(client):
    r = client.get("/?mod=4&cols=8&rev=6&rabais=10&modele=solaire")
    assert r.status_code == 200
    assert b"WECHIP" in r.data


def test_root_has_no_admin_config_leaked(client):
    r = client.get("/")
    html = r.data.decode()
    # The injected config block is empty `{}` on direct root visits.
    assert '<script id="wechip-link-config" type="application/json">{}</script>' in html

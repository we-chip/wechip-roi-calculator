import json

import db as link_db


def test_root_has_empty_config(client):
    r = client.get("/")
    assert r.status_code == 200
    html = r.data.decode()
    assert 'id="wechip-link-config"' in html
    # The JSON block should be exactly `{}` for direct visits.
    assert '<script id="wechip-link-config" type="application/json">{}</script>' in html


def test_customer_view_injects_config(client, db_path):
    cfg = {"revPerColDay": 8, "wechipSharePct": 65, "discountPct": 15}
    link_db.create_link("acme", "Acme Corp", cfg, db_path)
    r = client.get("/c/acme")
    assert r.status_code == 200
    html = r.data.decode()
    # Extract injected JSON
    needle = '<script id="wechip-link-config" type="application/json">'
    start = html.index(needle) + len(needle)
    end = html.index("</script>", start)
    payload = json.loads(html[start:end])
    assert payload["revPerColDay"] == 8
    assert payload["wechipSharePct"] == 65
    assert payload["discountPct"] == 15
    assert payload["display_name"] == "Acme Corp"


def test_customer_view_404_for_missing(client):
    assert client.get("/c/does-not-exist").status_code == 404


def test_customer_view_404_for_invalid_slug(client):
    assert client.get("/c/Bad_Slug").status_code == 404


def test_customer_view_logs_view_event(client, db_path):
    link_db.create_link("viewed", "", {}, db_path)
    client.get("/c/viewed")
    events = link_db.list_events("viewed", db_path=db_path)
    assert any(e["type"] == "view" for e in events)

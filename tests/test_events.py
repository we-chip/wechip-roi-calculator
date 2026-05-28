import db as link_db


def setup_link(db_path, slug="evt"):
    link_db.create_link(slug, "", {}, db_path)


def test_event_accepts_known_types(client, db_path):
    setup_link(db_path)
    for t in ("change", "print"):
        r = client.post("/c/evt/event", json={"type": t, "payload": {"x": 1}})
        assert r.status_code == 204
    events = link_db.list_events("evt", db_path=db_path)
    types = {e["type"] for e in events}
    assert {"change", "print"}.issubset(types)


def test_event_rejects_unknown_type(client, db_path):
    setup_link(db_path)
    r = client.post("/c/evt/event", json={"type": "view", "payload": {}})
    assert r.status_code == 400
    r = client.post("/c/evt/event", json={"type": "nope"})
    assert r.status_code == 400


def test_event_truncates_oversized_payload(client, db_path):
    setup_link(db_path)
    big = {"blob": "x" * 10000}
    r = client.post("/c/evt/event", json={"type": "change", "payload": big})
    assert r.status_code == 204
    evs = link_db.list_events("evt", db_path=db_path)
    change = [e for e in evs if e["type"] == "change"][0]
    assert len(change["payload_json"]) <= 2048


def test_event_rate_limit(client, db_path):
    setup_link(db_path)
    last_status = None
    for i in range(65):
        last_status = client.post("/c/evt/event", json={"type": "change"}).status_code
    assert last_status == 429


def test_event_404_on_revoked(client, db_path):
    setup_link(db_path, slug="gone")
    link_db.revoke_link("gone", db_path)
    r = client.post("/c/gone/event", json={"type": "change"})
    assert r.status_code == 404

def test_health_ok(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "ok"
    # build_commit is present (empty in dev/test where build_commit.txt is absent);
    # the deploy smoke-test relies on this field to verify the live commit.
    assert "build_commit" in body

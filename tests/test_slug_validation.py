from app import SLUG_RE


def test_slug_accepts_valid():
    for s in ["abc", "a1", "lead-acme", "x" * 60, "0lead", "a-b-c-1"]:
        assert SLUG_RE.match(s), s


def test_slug_rejects_invalid():
    for s in [
        "",
        "a",                  # too short
        "x" * 61,             # too long
        "-lead",              # leading hyphen
        "Lead",               # uppercase
        "lead_acme",          # underscore
        "lead acme",          # space
        "lead/acme",
        "lead.acme",
    ]:
        assert not SLUG_RE.match(s), s

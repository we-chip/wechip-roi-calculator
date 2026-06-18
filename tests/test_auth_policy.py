import auth_policy


def test_decide_unknown_subject_denied():
    matrix = auth_policy.AccessMatrix.from_dict(
        {
            "subjects": {},
            "roles": {"admin": ["read", "write", "manage"]},
        }
    )
    identity = auth_policy.Identity(subject="nobody@wechip.ch", tenant=None, claims={})
    decision = auth_policy.decide(identity, "roi-calculator", "admin", matrix)

    assert decision.allowed is False
    assert decision.reason == "unknown subject"


def test_decide_granted_subject_and_role_allowed():
    matrix = auth_policy.AccessMatrix.from_dict(
        {
            "subjects": {"thomas@wechip.ch": {"roi-calculator": ["admin"]}},
            "roles": {"admin": ["read", "write", "manage"]},
        }
    )
    identity = auth_policy.Identity(subject="thomas@wechip.ch", tenant=None, claims={})
    decision = auth_policy.decide(identity, "roi-calculator", "admin", matrix)

    assert decision.allowed is True
    assert decision.reason == "allowed"
    assert decision.role == "admin"

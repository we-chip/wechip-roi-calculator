from __future__ import annotations

"""Shared deny-by-default authorization policy contract.

Example access-matrix configuration (versioned per repository)::

    {
      "subjects": {
        "alex@example.com": {
          "locker-admin": ["admin", "operator"],
          "locker-view": ["viewer"]
        }
      },
      "roles": {
        "admin": ["read", "write", "manage"],
        "operator": ["read", "write"],
        "viewer": ["read"]
      }
    }
"""

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class Identity:
    subject: str
    tenant: str | None
    claims: dict[str, Any]


@dataclass(frozen=True)
class AccessMatrix:
    subjects: dict[str, dict[str, list[str]]]
    role_permissions: dict[str, list[str]]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AccessMatrix:
        if not isinstance(data, dict):
            raise ValueError("matrix must be a dict")

        raw_subjects = data.get("subjects")
        if not isinstance(raw_subjects, dict):
            raise ValueError("matrix.subjects must be a dict")

        subjects: dict[str, dict[str, list[str]]] = {}
        for subject, app_grants in raw_subjects.items():
            if not isinstance(subject, str) or not subject:
                raise ValueError("matrix.subjects keys must be non-empty strings")
            if not isinstance(app_grants, dict):
                raise ValueError("subject grants must be a dict")

            clean_grants: dict[str, list[str]] = {}
            for app, roles in app_grants.items():
                if not isinstance(app, str) or not app:
                    raise ValueError("app names must be non-empty strings")
                if not isinstance(roles, list) or not roles:
                    raise ValueError("app roles must be a non-empty list")
                if not all(isinstance(role, str) and role for role in roles):
                    raise ValueError("roles must be non-empty strings")
                clean_grants[app] = list(roles)

            subjects[subject] = clean_grants

        raw_role_permissions = data.get("roles", {})
        if raw_role_permissions is None:
            raw_role_permissions = {}
        if not isinstance(raw_role_permissions, dict):
            raise ValueError("matrix.roles must be a dict")

        role_permissions: dict[str, list[str]] = {}
        for role, permissions in raw_role_permissions.items():
            if not isinstance(role, str) or not role:
                raise ValueError("role names must be non-empty strings")
            if not isinstance(permissions, list):
                raise ValueError("role permissions must be a list")
            if not all(isinstance(permission, str) and permission for permission in permissions):
                raise ValueError("permissions must be non-empty strings")
            role_permissions[role] = list(permissions)

        return cls(subjects=subjects, role_permissions=role_permissions)


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str
    app: str
    role: str | None


def decide(
    identity: Identity,
    app: str,
    required_role: str | None,
    matrix: AccessMatrix,
    *,
    now: datetime | None = None,
) -> Decision:
    # Reserved so callers can pass an externally-controlled evaluation time when
    # time-window rules are added; current contract has no time-based branches.
    _ = now

    app_grants = matrix.subjects.get(identity.subject)
    if app_grants is None:
        return Decision(allowed=False, reason="unknown subject", app=app, role=None)

    granted_roles = app_grants.get(app)
    if granted_roles is None:
        return Decision(allowed=False, reason="no app grant", app=app, role=None)

    if required_role is not None and required_role not in granted_roles:
        return Decision(allowed=False, reason="missing role", app=app, role=None)

    if required_role is not None:
        matched_role = required_role
    else:
        if not granted_roles:
            return Decision(allowed=False, reason="missing role", app=app, role=None)
        matched_role = granted_roles[0]

    return Decision(allowed=True, reason="allowed", app=app, role=matched_role)


def audit_fields(identity: Identity, decision: Decision) -> dict[str, Any]:
    return {
        "subject": identity.subject,
        "app": decision.app,
        "role": decision.role,
        "allowed": decision.allowed,
        "reason": decision.reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate auth policy decision")
    parser.add_argument("--matrix", required=True, help="JSON access matrix")
    parser.add_argument("--subject", required=True, help="Identity subject")
    parser.add_argument("--app", required=True, help="Application key")
    parser.add_argument("--role", default=None, help="Required role")
    args = parser.parse_args(argv)

    try:
        raw_matrix = json.loads(args.matrix)
        matrix = AccessMatrix.from_dict(raw_matrix)
    except (json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))

    identity = Identity(subject=args.subject, tenant=None, claims={})
    decision = decide(identity, args.app, args.role, matrix)
    print(json.dumps(asdict(decision), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

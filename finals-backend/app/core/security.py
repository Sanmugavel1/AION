"""
AION Security - JWT, OAuth2, Password Hashing, RBAC
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ForbiddenError
from app.core.logging import get_logger

logger = get_logger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    DEPT_ADMIN = "dept_admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
    # SRS Section 6 tiers. Kept alongside the original roles rather than replacing
    # them so existing accounts and tokens keep resolving.
    EXECUTIVE = "executive"
    DEPT_HEAD = "dept_head"
    MANAGER = "manager"
    EMPLOYEE = "employee"


#: Roles whose data access is confined to their own department, enforced server-side
#: (SRS Section 10: "hard-scoped ... at the API layer, not left to UI convention").
DEPARTMENT_SCOPED_ROLES = frozenset(
    {UserRole.DEPT_HEAD, UserRole.MANAGER, UserRole.EMPLOYEE, UserRole.DEPT_ADMIN}
)

#: Approval chain, lowest to highest (SRS Sections 12-13). Index = authority level.
APPROVAL_CHAIN = (UserRole.EMPLOYEE, UserRole.MANAGER, UserRole.DEPT_HEAD, UserRole.ORG_ADMIN)


class Permission(str, Enum):
    # Knowledge
    READ_KNOWLEDGE = "read:knowledge"
    WRITE_KNOWLEDGE = "write:knowledge"
    DELETE_KNOWLEDGE = "delete:knowledge"
    # Graph
    READ_GRAPH = "read:graph"
    WRITE_GRAPH = "write:graph"
    # Intelligence
    READ_INTELLIGENCE = "read:intelligence"
    # Simulation
    RUN_SIMULATION = "run:simulation"
    # Healing
    READ_HEALING = "read:healing"
    APPROVE_HEALING = "approve:healing"
    # OCSIE
    READ_OCSIE = "read:ocsie"
    WRITE_OCSIE = "write:ocsie"
    # Admin
    MANAGE_USERS = "manage:users"
    MANAGE_ORG = "manage:org"
    VIEW_BOARD = "view:board"
    CONFIGURE_INTEGRATIONS = "configure:integrations"
    # --- SRS v2 (Appendix F permission matrix) ---
    # Document lifecycle (Sections 12-13)
    SUBMIT_DOCUMENT = "submit:document"
    REVIEW_DOCUMENT = "review:document"      # Manager first-pass
    APPROVE_DOCUMENT = "approve:document"    # Dept Head final
    # Cross-department reach (Section 5 isolation, Section 11 admin override)
    READ_CROSS_DEPARTMENT = "read:cross_department"
    # Executive layer (Section 27)
    VIEW_COMMAND_CENTER = "view:command_center"
    # Marketplace (Section 30)
    PUBLISH_MARKETPLACE = "publish:marketplace"
    # Governance and audit (Sections 15, 39)
    VIEW_AUDIT_LOG = "view:audit_log"
    MANAGE_GOVERNANCE = "manage:governance"


ROLE_PERMISSIONS: Dict[UserRole, List[Permission]] = {
    UserRole.SUPER_ADMIN: list(Permission),
    UserRole.ORG_ADMIN: [
        Permission.READ_KNOWLEDGE, Permission.WRITE_KNOWLEDGE,
        Permission.READ_GRAPH, Permission.WRITE_GRAPH,
        Permission.READ_INTELLIGENCE, Permission.RUN_SIMULATION,
        Permission.READ_HEALING, Permission.APPROVE_HEALING,
        Permission.READ_OCSIE, Permission.WRITE_OCSIE,
        Permission.MANAGE_USERS, Permission.VIEW_BOARD,
        Permission.CONFIGURE_INTEGRATIONS,
    ],
    UserRole.DEPT_ADMIN: [
        Permission.READ_KNOWLEDGE, Permission.WRITE_KNOWLEDGE,
        Permission.READ_GRAPH, Permission.READ_INTELLIGENCE,
        Permission.RUN_SIMULATION, Permission.READ_HEALING,
        Permission.APPROVE_HEALING, Permission.READ_OCSIE,
        Permission.VIEW_BOARD,
    ],
    UserRole.ANALYST: [
        Permission.READ_KNOWLEDGE, Permission.READ_GRAPH,
        Permission.READ_INTELLIGENCE, Permission.RUN_SIMULATION,
        Permission.READ_HEALING, Permission.READ_OCSIE,
    ],
    UserRole.VIEWER: [
        Permission.READ_KNOWLEDGE, Permission.READ_GRAPH,
        Permission.READ_INTELLIGENCE,
    ],
    # --- SRS Section 6 tiers, per the Appendix F matrix ---
    # Executive sees every department but in aggregate only, and never approves
    # documents or manages users — deliberately read-heavy, write-light.
    UserRole.EXECUTIVE: [
        Permission.READ_KNOWLEDGE, Permission.READ_GRAPH,
        Permission.READ_INTELLIGENCE, Permission.READ_OCSIE,
        Permission.READ_HEALING, Permission.RUN_SIMULATION,
        Permission.VIEW_BOARD, Permission.VIEW_COMMAND_CENTER,
        Permission.READ_CROSS_DEPARTMENT,
    ],
    UserRole.DEPT_HEAD: [
        Permission.READ_KNOWLEDGE, Permission.WRITE_KNOWLEDGE,
        Permission.READ_GRAPH, Permission.READ_INTELLIGENCE,
        Permission.RUN_SIMULATION, Permission.READ_HEALING,
        Permission.APPROVE_HEALING, Permission.READ_OCSIE,
        Permission.VIEW_BOARD, Permission.MANAGE_USERS,
        Permission.SUBMIT_DOCUMENT, Permission.REVIEW_DOCUMENT,
        Permission.APPROVE_DOCUMENT, Permission.PUBLISH_MARKETPLACE,
        Permission.VIEW_AUDIT_LOG,
    ],
    UserRole.MANAGER: [
        Permission.READ_KNOWLEDGE, Permission.WRITE_KNOWLEDGE,
        Permission.READ_GRAPH, Permission.READ_INTELLIGENCE,
        Permission.READ_HEALING, Permission.READ_OCSIE,
        Permission.SUBMIT_DOCUMENT, Permission.REVIEW_DOCUMENT,
        Permission.PUBLISH_MARKETPLACE,
    ],
    UserRole.EMPLOYEE: [
        Permission.READ_KNOWLEDGE, Permission.WRITE_KNOWLEDGE,
        Permission.READ_GRAPH, Permission.READ_INTELLIGENCE,
        Permission.SUBMIT_DOCUMENT,
    ],
}

# Admin tiers gain the v2 permissions too. Appended here rather than typed into the
# literals above so the two admin roles cannot silently drift from the Permission enum.
ROLE_PERMISSIONS[UserRole.ORG_ADMIN].extend([
    Permission.SUBMIT_DOCUMENT, Permission.REVIEW_DOCUMENT, Permission.APPROVE_DOCUMENT,
    Permission.READ_CROSS_DEPARTMENT, Permission.VIEW_COMMAND_CENTER,
    Permission.PUBLISH_MARKETPLACE, Permission.VIEW_AUDIT_LOG, Permission.MANAGE_GOVERNANCE,
])
ROLE_PERMISSIONS[UserRole.DEPT_ADMIN].extend([
    Permission.SUBMIT_DOCUMENT, Permission.REVIEW_DOCUMENT, Permission.APPROVE_DOCUMENT,
    Permission.PUBLISH_MARKETPLACE,
])


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: str,
    org_id: str,
    role: UserRole,
    dept_id: Optional[str] = None,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload: Dict[str, Any] = {
        "sub": subject,
        "org_id": org_id,
        "role": role.value,
        "dept_id": dept_id,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "permissions": [p.value for p in ROLE_PERMISSIONS.get(role, [])],
    }
    if additional_claims:
        payload.update(additional_claims)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str, org_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub": subject,
        "org_id": org_id,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as e:
        raise AuthenticationError(f"Invalid token: {e}")


def has_permission(role: UserRole, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, [])


def require_permission(role: UserRole, permission: Permission) -> None:
    if not has_permission(role, permission):
        raise ForbiddenError(
            f"Role '{role.value}' lacks permission '{permission.value}'"
        )

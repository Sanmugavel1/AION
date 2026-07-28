"""
AION Custom Exception Hierarchy
"""
from __future__ import annotations

from typing import Any, Dict, Optional


class AIONBaseException(Exception):
    """Base exception for all AION errors."""

    def __init__(
        self,
        message: str,
        code: str = "AION_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


# Authentication & Authorization
class AuthenticationError(AIONBaseException):
    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message, code="AUTHENTICATION_ERROR")


class ForbiddenError(AIONBaseException):
    def __init__(self, message: str = "Access forbidden") -> None:
        super().__init__(message, code="FORBIDDEN")


class TokenExpiredError(AuthenticationError):
    def __init__(self) -> None:
        super().__init__("Token has expired")


# Resource Errors
class NotFoundError(AIONBaseException):
    def __init__(self, resource: str, identifier: Any) -> None:
        super().__init__(
            f"{resource} with identifier '{identifier}' not found",
            code="NOT_FOUND",
            details={"resource": resource, "identifier": str(identifier)},
        )


class ConflictError(AIONBaseException):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="CONFLICT")


class ValidationError(AIONBaseException):
    def __init__(self, message: str, field: Optional[str] = None) -> None:
        super().__init__(
            message,
            code="VALIDATION_ERROR",
            details={"field": field} if field else {},
        )


# Database Errors
class DatabaseError(AIONBaseException):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="DATABASE_ERROR")


class GraphDatabaseError(AIONBaseException):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="GRAPH_DATABASE_ERROR")


# Integration Errors
class IntegrationError(AIONBaseException):
    def __init__(self, source: str, message: str) -> None:
        super().__init__(
            f"Integration error for {source}: {message}",
            code="INTEGRATION_ERROR",
            details={"source": source},
        )


class ConnectorAuthError(IntegrationError):
    def __init__(self, source: str) -> None:
        super().__init__(source, "Authentication failed")


# AI Errors
class LLMError(AIONBaseException):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="LLM_ERROR")


class EmbeddingError(AIONBaseException):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="EMBEDDING_ERROR")


class SimulationError(AIONBaseException):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="SIMULATION_ERROR")


# Business Logic Errors
class InsufficientDataError(AIONBaseException):
    def __init__(self, context: str) -> None:
        super().__init__(
            f"Insufficient data for {context}",
            code="INSUFFICIENT_DATA",
            details={"context": context},
        )


class KnowledgeDecayError(AIONBaseException):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="KNOWLEDGE_DECAY_ERROR")


class HealingActionError(AIONBaseException):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="HEALING_ACTION_ERROR")

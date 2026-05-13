"""Shared Pydantic schema primitives for AlterScore API contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SchemaModel(BaseModel):
    """Common base model that rejects undocumented fields."""

    model_config = ConfigDict(extra="forbid", protected_namespaces=())


class ApiError(SchemaModel):
    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    details: dict[str, Any] = Field(default_factory=dict)
    request_id: str = Field(..., min_length=1)
    timestamp: datetime


class ErrorResponse(SchemaModel):
    error: ApiError


__all__ = [
    "ApiError",
    "ErrorResponse",
    "SchemaModel",
]

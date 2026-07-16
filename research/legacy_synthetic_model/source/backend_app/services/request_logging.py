"""Append-only runtime request logging for AlterScore backend routes."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from threading import Lock
from typing import Any

from backend.app.core.artifact_loader import LoadedArtifactBundle
from backend.app.schemas.score import ScoreResponse


class RequestLoggingService:
    """Persist scoring outcomes to a local JSONL file without storing raw inputs."""

    def __init__(self, log_path: Path, artifacts: LoadedArtifactBundle) -> None:
        self.log_path = log_path
        self.artifacts = artifacts
        self._lock = Lock()
        self._dir_ready = False

    def log_score_success(
        self,
        *,
        request_id: str,
        session_id: str,
        latency_ms: float,
        response: ScoreResponse,
    ) -> None:
        entry = self._base_entry(
            request_id=request_id,
            session_id=session_id,
            latency_ms=latency_ms,
            status_code=200,
            outcome="success",
        )
        entry.update(
            {
                "credit_score": response.credit_score,
                "repayment_probability": response.repayment_probability,
                "percentile": response.percentile,
            }
        )
        self._append_entry(entry)

    def log_score_failure(
        self,
        *,
        request_id: str,
        session_id: str,
        latency_ms: float,
        status_code: int,
        error_code: str,
        error_message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        entry = self._base_entry(
            request_id=request_id,
            session_id=session_id,
            latency_ms=latency_ms,
            status_code=status_code,
            outcome="error",
        )
        entry.update(
            {
                "error_code": error_code,
                "error_message": error_message,
            }
        )
        if details:
            entry["details"] = details
        self._append_entry(entry)

    def _base_entry(
        self,
        *,
        request_id: str,
        session_id: str,
        latency_ms: float,
        status_code: int,
        outcome: str,
    ) -> dict[str, Any]:
        model_version = _as_optional_string(self.artifacts.report.model_version)
        manifest_version = _as_optional_string(self.artifacts.report.manifest_version)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id,
            "session_id": session_id,
            "endpoint": "/api/score",
            "status_code": status_code,
            "outcome": outcome,
            "latency_ms": round(max(latency_ms, 0.0), 3),
            "artifact_source": self.artifacts.report.source,
            "runtime_model_name": self.artifacts.report.runtime_model_name,
            "runtime_model_type": self.artifacts.report.runtime_model_type,
            "runtime_model_path": _as_optional_string(
                self.artifacts.report.runtime_model_path
            ),
            "model_version": model_version,
            "manifest_version": manifest_version,
            "manifest_path": _as_optional_string(self.artifacts.report.manifest_path),
        }

    def _append_entry(self, entry: dict[str, Any]) -> None:
        payload = json.dumps(entry, sort_keys=True)

        with self._lock:
            # Create the log directory once rather than on every write. The
            # callers in the score route already guard against logging failures,
            # so a read-only destination degrades to "no logs" instead of
            # breaking scoring.
            if not self._dir_ready:
                self.log_path.parent.mkdir(parents=True, exist_ok=True)
                self._dir_ready = True
            with self.log_path.open("a", encoding="utf-8") as handle:
                handle.write(payload)
                handle.write("\n")


def _as_optional_string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


__all__ = ["RequestLoggingService"]

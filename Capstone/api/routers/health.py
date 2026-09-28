from __future__ import annotations

from fastapi import APIRouter

from api.dependencies import list_runs

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, object]:
	try:
		runs = len(list_runs())
		return {
			"status": "ok",
			"db_status": "ok",
			"runs": runs,
		}
	except Exception as exc:
		return {
			"status": "degraded",
			"db_status": "error",
			"runs": 0,
			"db_error": str(exc),
		}

from __future__ import annotations

from fastapi import APIRouter

from api.dependencies import list_runs

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, object]:
	return {
		"status": "ok",
		"runs": len(list_runs()),
	}

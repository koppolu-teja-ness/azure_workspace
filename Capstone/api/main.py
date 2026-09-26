from __future__ import annotations

from fastapi import FastAPI

from api.routers import approval, discovery, health, migration_runs, reports


def create_app() -> FastAPI:
	app = FastAPI(title="Azure AWS Migration Assistant API", version="0.1.0")
	app.include_router(health.router)
	app.include_router(discovery.router)
	app.include_router(approval.router)
	app.include_router(migration_runs.router)
	app.include_router(reports.router)
	return app


app = create_app()

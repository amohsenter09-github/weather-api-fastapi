from fastapi import FastAPI

from air_quality_app.api.air_quality import router as air_quality_router
from air_quality_app.api.health import router as health_router
from air_quality_app.core.config import get_settings
from air_quality_app.core.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title=settings.app_name)
    app.include_router(health_router)
    app.include_router(air_quality_router)

    @app.get("/")
    async def root():
        return {"service": settings.app_name}

    return app


app = create_app()

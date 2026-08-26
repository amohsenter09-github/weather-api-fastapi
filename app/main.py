import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from app.api.health import router as health_router
from app.api.places import router as places_router
from app.api.weather import router as weather_router
from app.core.config import UI_THEMES, get_settings
from app.core.logging import configure_logging
from app.db.session import close_db, init_db

STATIC_DIR = Path(__file__).resolve().parent / "static"
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        await init_db()
    except Exception:
        logger.exception("Postgres is not reachable; GET /weather still works, POST /places will fail")
    yield
    await close_db()


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.include_router(health_router)
    app.include_router(weather_router)
    app.include_router(places_router)

    @app.exception_handler(SQLAlchemyError)
    async def db_error(_request, _exc):
        logger.exception("Database error")
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})

    @app.get("/", include_in_schema=False)
    async def ui():
        html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
        theme = (settings.ui_theme or "orange").strip().lower()
        if theme == "grey":
            theme = "gray"
        if theme not in UI_THEMES:
            theme = "orange"
        html = html.replace('data-theme="orange"', f'data-theme="{theme}"', 1)
        if theme == "green":
            html = html.replace(">Weather API<", ">Weather API · production<")
            html = html.replace("<title>Weather</title>", "<title>Weather · production</title>")
        elif theme == "blue":
            html = html.replace(">Weather API<", ">Weather API · development<")
            html = html.replace("<title>Weather</title>", "<title>Weather · development</title>")
        return HTMLResponse(html)

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


app = create_app()

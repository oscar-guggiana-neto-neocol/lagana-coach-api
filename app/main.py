import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    app = FastAPI(title=settings.project_name, debug=settings.debug)

    origins = settings.allowed_origins_list
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def _startup() -> None:
        storage_path = Path(settings.file_storage_dir) / "invoices"
        storage_path.mkdir(parents=True, exist_ok=True)
        logger.info("Storage directory ready at %%s", storage_path)

    app.include_router(api_router)
    return app


app = create_application()

from dotenv import load_dotenv
import os

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.api.v1 import router as api_v1_router
from app.core.config import get_settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(
        title=s.app_name,
        version="1.0.0",
        description="External platform APIs for BrandVoice (social media auth, scheduling, etc.).",
        docs_url="/docs", redoc_url="/redoc",
        swagger_ui_init_oauth={
            "usePkceWithAuthorizationCodeGrant": True,
            "useBasicAuthenticationWithAccessCodeGrant": True
        }
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.allow_origins, allow_credentials=True,
        allow_methods=["*"], allow_headers=["*"],
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=s.secret_key,
        session_cookie="session",
        max_age=3600,
        same_site="lax",
        https_only=False
    )

    app.include_router(api_v1_router, prefix="/api/v1")
    return app

external_app = create_app()

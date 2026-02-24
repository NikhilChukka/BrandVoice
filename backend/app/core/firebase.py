import logging
import os
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore, storage
from google.auth import default as google_auth_default
from google.auth.exceptions import DefaultCredentialsError

logger = logging.getLogger(__name__)

_firebase_app: firebase_admin.App | None = None
_firestore_client: firestore.Client | None = None
_storage_bucket = None

STORAGE_BUCKET_NAME = os.getenv("FIREBASE_STORAGE_BUCKET", "brandvoice-images")


def _load_credentials():
    """
    Try credentials in this order:
      1. Application Default Credentials (metadata server on GCP, gcloud auth locally)
      2. Base64-encoded JSON in GOOGLE_CREDENTIALS_B64 (ideal for Render/Heroku/Railway)
      3. JSON file at path in GOOGLE_APPLICATION_CREDENTIALS (e.g. mounted Secret)
      4. JSON file specified by settings.google_application_credentials (local fallback)
    Return a (cred, project_id) tuple; project_id may be None for file-based creds.
    """
    # 1️⃣ ADC – succeeds automatically on Cloud Run / GCF / GKE Workload Identity
    try:
        cred, project_id = google_auth_default()
        logger.info("Using Application Default Credentials")
        return cred, project_id
    except DefaultCredentialsError:
        logger.debug("ADC not available, checking key files")

    # 2️⃣ Base64-encoded service account JSON (Render, Heroku, Railway, etc.)
    b64_creds = os.getenv("GOOGLE_CREDENTIALS_B64")
    if b64_creds:
        import base64
        import json
        try:
            decoded = base64.b64decode(b64_creds).decode("utf-8")
            sa_dict = json.loads(decoded)
            cred = credentials.Certificate(sa_dict)
            logger.info("Using credentials from GOOGLE_CREDENTIALS_B64")
            return cred, sa_dict.get("project_id")
        except Exception as e:
            logger.warning("Failed to load GOOGLE_CREDENTIALS_B64: %s", e)

    # 3️⃣ Env-var path (works with Cloud Run Secret mount)
    key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if key_path and Path(key_path).exists():
        logger.info("Using credentials file from $GOOGLE_APPLICATION_CREDENTIALS")
        return credentials.Certificate(key_path), None

    # 4️⃣ Local settings path
    from app.core.config import get_settings

    settings = get_settings()
    key_path = settings.google_application_credentials
    if key_path and Path(key_path).exists():
        logger.info("Using credentials file from settings.google_application_credentials")
        return credentials.Certificate(key_path), None

    raise FileNotFoundError(
        "No valid GCP credentials found via ADC, "
        "GOOGLE_CREDENTIALS_B64, $GOOGLE_APPLICATION_CREDENTIALS, "
        "or settings.google_application_credentials"
    )


def initialize_firebase():
    """Return a lazily initialised Firestore client (safe for reuse within one process)."""
    global _firebase_app, _firestore_client, _storage_bucket
    if _firebase_app:  # already initialised
        return _firestore_client

    cred, project_id = _load_credentials()
    options = {"storageBucket": STORAGE_BUCKET_NAME}
    if project_id:
        options["projectId"] = project_id

    _firebase_app = firebase_admin.initialize_app(cred, options)
    _firestore_client = firestore.client()
    _storage_bucket = storage.bucket()
    logger.info(
        "Firebase initialised (project=%s, app_name=%s, bucket=%s)",
        project_id or "<from key file>",
        _firebase_app.name,
        STORAGE_BUCKET_NAME,
    )
    return _firestore_client


def get_firestore_client():
    return initialize_firebase()


def get_firebase_app():
    initialize_firebase()
    return _firebase_app


def get_storage_bucket():
    initialize_firebase()
    return _storage_bucket


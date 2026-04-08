"""Service for uploading receipt photos to Google Drive."""

import logging
import os
from io import BytesIO

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.service_account import Credentials

from config import settings
from bot.utils.dates import today_msk

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/drive",
]

_service = None


def get_drive_service():
    global _service
    if _service is None:
        creds = Credentials.from_service_account_file(
            settings.google_credentials_file, scopes=SCOPES
        )
        _service = build("drive", "v3", credentials=creds)
    return _service


def ensure_folder(parent_id: str, folder_name: str) -> str:
    """Create folder if not exists, return folder ID."""
    service = get_drive_service()
    query = (
        f"'{parent_id}' in parents and "
        f"name='{folder_name}' and "
        f"mimeType='application/vnd.google-apps.folder' and "
        f"trashed=false"
    )
    results = service.files().list(q=query, fields="files(id)").execute()
    files = results.get("files", [])

    if files:
        return files[0]["id"]

    file_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(body=file_metadata, fields="id").execute()
    return folder["id"]


def get_month_folder_id() -> str:
    """Get or create the folder for current month: /COLIZEUM/Чеки/2026-04/"""
    base_folder_id = settings.drive_receipts_folder_id
    if not base_folder_id:
        raise ValueError("DRIVE_RECEIPTS_FOLDER_ID not configured")

    dt = today_msk()
    month_folder_name = dt.strftime("%Y-%m")
    return ensure_folder(base_folder_id, month_folder_name)


def upload_receipt(
    file_data: bytes,
    filename: str,
    mime_type: str = "image/jpeg",
) -> tuple[str, str]:
    """
    Upload receipt photo to Drive.
    Returns (file_id, web_view_link).
    """
    service = get_drive_service()
    folder_id = get_month_folder_id()

    file_metadata = {
        "name": filename,
        "parents": [folder_id],
    }

    media = MediaIoBaseUpload(BytesIO(file_data), mimetype=mime_type, resumable=True)

    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id,webViewLink")
        .execute()
    )

    file_id = file["id"]
    web_link = file.get("webViewLink", "")

    # Make file accessible via link
    service.permissions().create(
        fileId=file_id,
        body={"type": "anyone", "role": "reader"},
    ).execute()

    if not web_link:
        web_link = f"https://drive.google.com/file/d/{file_id}/view"

    return file_id, web_link


def build_receipt_filename(
    date_str: str, category: str, amount: float, ext: str = "jpg"
) -> str:
    """Build receipt filename like: чек_07.04_барная_3500.jpg"""
    amount_str = str(int(amount)) if amount == int(amount) else str(amount)
    return f"\u0447\u0435\u043a_{date_str}_{category}_{amount_str}.{ext}"

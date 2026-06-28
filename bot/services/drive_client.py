import asyncio
import io
import json
import logging
import os
from typing import Any, TypedDict

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

from config import GOOGLE_APPLICATION_CREDENTIALS, GOOGLE_DRIVE_SCOPES

logger = logging.getLogger(__name__)

FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"


class DriveFile(TypedDict, total=False):
    name: str
    id: str
    mimeType: str
    webViewLink: str
    size: str


class DriveClientError(Exception):
    """Базовая ошибка клиента Google Drive."""


class DriveUnavailableError(DriveClientError):
    """Google Drive недоступен или не настроен."""


def _get_credentials() -> service_account.Credentials:
    """
    Загружает credentials Google Drive.
    Поддерживает:
    - путь к JSON-файлу (как было раньше)
    - сам JSON-ключ как строку (для Railway / переменных окружения)
    """
    if not GOOGLE_APPLICATION_CREDENTIALS:
        raise DriveUnavailableError("GOOGLE_APPLICATION_CREDENTIALS is not configured")

    creds_data = GOOGLE_APPLICATION_CREDENTIALS

    # Проверяем, является ли значение путём к существующему файлу
    if os.path.exists(creds_data):
        logger.info("Loading Google credentials from file: %s", creds_data)
        credentials = service_account.Credentials.from_service_account_file(
            creds_data,
            scopes=GOOGLE_DRIVE_SCOPES,
        )
    else:
        # Пытаемся интерпретировать как JSON-строку
        try:
            logger.info("Loading Google credentials from JSON string")
            info = json.loads(creds_data)
            credentials = service_account.Credentials.from_service_account_info(
                info,
                scopes=GOOGLE_DRIVE_SCOPES,
            )
        except json.JSONDecodeError as exc:
            raise DriveUnavailableError(
                "GOOGLE_APPLICATION_CREDENTIALS не является ни путём к файлу, ни валидным JSON"
            ) from exc

    logger.info("Credentials loaded successfully")
    return credentials


def _build_drive_service():
    credentials = _get_credentials()
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def _find_folder_id(service: Any, folder_name: str) -> str | None:
    logger.info("Searching for folder: %s", folder_name)

    escaped = folder_name.replace("'", "\\'")
    query = (
        f"name = '{escaped}' and "
        f"mimeType = '{FOLDER_MIME_TYPE}' and trashed = false"
    )

    result = (
        service.files()
        .list(
            q=query,
            pageSize=1,
            fields="files(id, name)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        .execute()
    )
    files = result.get("files", [])
    if not files:
        logger.info("Folder not found: %s", folder_name)
        return None

    folder_id = files[0]["id"]
    logger.info("Folder found: %s (id=%s)", folder_name, folder_id)
    return folder_id


def _list_files_in_folder(service: Any, folder_id: str, folder_name: str) -> list[DriveFile]:
    query = f"'{folder_id}' in parents and trashed = false"

    result = (
        service.files()
        .list(
            q=query,
            pageSize=100,
            fields="files(id, name, mimeType, webViewLink, size)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            orderBy="name",
        )
        .execute()
    )

    files: list[DriveFile] = []
    for item in result.get("files", []):
        if item.get("mimeType") == FOLDER_MIME_TYPE:
            continue
        files.append(
            {
                "name": item.get("name", ""),
                "id": item.get("id", ""),
                "mimeType": item.get("mimeType", ""),
                "webViewLink": item.get("webViewLink", ""),
                "size": str(item.get("size", "0")),
            }
        )

    logger.info("Found %s files in folder %s", len(files), folder_name)
    return files


def _get_files_from_folder_sync(folder_name: str) -> list[DriveFile]:
    service = _build_drive_service()
    folder_id = _find_folder_id(service, folder_name)
    if not folder_id:
        return []
    return _list_files_in_folder(service, folder_id, folder_name)


def _download_file_bytes_sync(file_id: str) -> bytes:
    service = _build_drive_service()
    request = service.files().get_media(fileId=file_id, supportsAllDrives=True)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()

    return buffer.getvalue()


async def get_files_from_folder(folder_name: str) -> list[DriveFile]:
    """
    Возвращает файлы из папки Google Drive с именем folder_name.

    Каждый элемент: name, id, mimeType, webViewLink.
    При отсутствии папки — пустой список.
    При ошибке API/конфигурации — DriveUnavailableError.
    """
    try:
        return await asyncio.to_thread(_get_files_from_folder_sync, folder_name)
    except DriveUnavailableError as exc:
        logger.exception("Google Drive configuration error for folder=%s: %s", folder_name, exc)
        raise
    except HttpError as exc:
        logger.exception("Google Drive API error for folder=%s", folder_name)
        raise DriveUnavailableError(str(exc)) from exc
    except OSError as exc:
        logger.exception("Google Drive credentials file error for folder=%s", folder_name)
        raise DriveUnavailableError(str(exc)) from exc
    except Exception as exc:
        logger.exception("Google Drive unexpected error for folder=%s", folder_name)
        raise DriveUnavailableError(str(exc)) from exc


async def download_file_bytes(file_id: str) -> bytes:
    """Скачивает содержимое файла через API (для отправки фото в Telegram)."""
    try:
        return await asyncio.to_thread(_download_file_bytes_sync, file_id)
    except HttpError as exc:
        logger.exception("Google Drive download error file_id=%s", file_id)
        raise DriveUnavailableError(str(exc)) from exc
    except Exception as exc:
        logger.exception("Google Drive download unexpected error file_id=%s", file_id)
        raise DriveUnavailableError(str(exc)) from exc

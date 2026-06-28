from bot.services.drive_client import DriveFile

_sessions: dict[int, dict] = {}


def set_category_files(
    user_id: int,
    category_key: str,
    category_name: str,
    files: list[DriveFile],
) -> None:
    """Сохраняет список файлов категории для пагинации без повторных запросов к Drive."""
    _sessions[user_id] = {
        "category_key": category_key,
        "category_name": category_name,
        "files": files,
    }


def get_session(user_id: int) -> dict | None:
    return _sessions.get(user_id)


def get_file_by_index(user_id: int, file_idx: int) -> DriveFile | None:
    session = _sessions.get(user_id)
    if not session:
        return None
    files: list[DriveFile] = session.get("files", [])
    if file_idx < 0 or file_idx >= len(files):
        return None
    return files[file_idx]

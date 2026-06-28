import logging

from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, Message

from bot.keyboards.pagination import (
    PAGE_SIZE,
    MAX_VIDEO_BYTES,
    back_to_list_keyboard,
    pagination_keyboard,
    view_file_keyboard,
)
from bot.services.drive_client import DriveFile, DriveUnavailableError, download_file_bytes
from bot.services.portfolio_cache import get_file_by_index, get_session

logger = logging.getLogger(__name__)


def _file_size_bytes(file_item: DriveFile) -> int:
    raw = file_item.get("size", 0)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


def _is_mp4(file_item: DriveFile) -> bool:
    mime_type = file_item.get("mimeType", "")
    name = file_item.get("name", "").lower()
    return mime_type == "video/mp4" or name.endswith(".mp4")


def _can_send_video_in_telegram(file_item: DriveFile) -> bool:
    if not _is_mp4(file_item):
        return False
    size = _file_size_bytes(file_item)
    if size > MAX_VIDEO_BYTES:
        return False
    return True


async def _send_list_file(
    message: Message,
    file_item: DriveFile,
    reply_markup: InlineKeyboardMarkup | None,
) -> None:
    name = file_item.get("name", "Без названия")
    file_id = file_item.get("id", "")
    mime_type = file_item.get("mimeType", "")
    web_link = file_item.get("webViewLink", "")

    if mime_type.startswith("image/"):
        try:
            content = await download_file_bytes(file_id)
            photo = BufferedInputFile(content, filename=name)
            await message.answer_photo(photo=photo, caption=name, reply_markup=reply_markup)
        except DriveUnavailableError as exc:
            logger.error("Failed to download image %s: %s", name, exc)
            if web_link:
                await message.answer(f"📷 {name}\n{web_link}", reply_markup=reply_markup)
            else:
                await message.answer(f"📷 {name}", reply_markup=reply_markup)
        except Exception as exc:
            logger.error("Failed to send photo %s: %s", name, exc)
            if web_link:
                await message.answer(f"📷 {name}\n{web_link}", reply_markup=reply_markup)
            else:
                await message.answer(f"📷 {name}", reply_markup=reply_markup)
    elif mime_type.startswith("video/"):
        if _can_send_video_in_telegram(file_item):
            try:
                content = await download_file_bytes(file_id)
                video = BufferedInputFile(content, filename=name)
                await message.answer_video(video=video, caption=name, reply_markup=reply_markup)
                return
            except Exception as exc:
                logger.error("Failed to send video %s: %s", name, exc)
        if web_link:
            await message.answer(f"🎬 {name}\n{web_link}", reply_markup=reply_markup)
        else:
            await message.answer(f"🎬 {name}", reply_markup=reply_markup)
    else:
        if web_link:
            await message.answer(f"📄 {name}\n{web_link}", reply_markup=reply_markup)
        else:
            await message.answer(f"📄 {name}", reply_markup=reply_markup)


async def send_portfolio_page(
    message: Message,
    user_id: int,
    category_key: str,
    page: int,
) -> bool:
    """
    Отправляет страницу файлов (новые сообщения).
    Возвращает False, если сессия недоступна.
    """
    session = get_session(user_id)
    if not session or session.get("category_key") != category_key:
        return False

    files: list[DriveFile] = session.get("files", [])
    category_name = session.get("category_name", category_key)
    total = len(files)

    if total == 0:
        await message.answer(f"В категории «{category_name}» пока нет файлов.")
        return True

    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    page = max(0, min(page, total_pages - 1))

    start = page * PAGE_SIZE
    end = min(start + PAGE_SIZE, total)
    page_files = files[start:end]

    range_text = f"Показаны файлы {start + 1}–{end} из {total}"
    header = f"Категория «{category_name}»\n{range_text}"
    pagination_kb = pagination_keyboard(category_key, page, total_pages, total)

    await message.answer(header, reply_markup=pagination_kb)

    for offset, file_item in enumerate(page_files):
        file_idx = start + offset
        view_kb = view_file_keyboard(
            category_key,
            page,
            file_idx,
            file_item.get("name", "Без названия"),
            file_item.get("mimeType", ""),
        )
        await _send_list_file(message, file_item, view_kb)

    return True


async def send_file_view(
    message: Message,
    user_id: int,
    category_key: str,
    page: int,
    file_idx: int,
) -> None:
    """Отправляет полный просмотр файла с кнопкой возврата к списку."""
    file_item = get_file_by_index(user_id, file_idx)
    back_kb = back_to_list_keyboard(category_key, page)

    if not file_item:
        await message.answer(
            "Файл недоступен. Возможно, список устарел — выберите категорию заново.",
            reply_markup=back_kb,
        )
        return

    name = file_item.get("name", "Без названия")
    file_id = file_item.get("id", "")
    mime_type = file_item.get("mimeType", "")
    web_link = file_item.get("webViewLink", "")

    try:
        if mime_type.startswith("image/"):
            content = await download_file_bytes(file_id)
            photo = BufferedInputFile(content, filename=name)
            await message.answer_photo(photo=photo, caption=name, reply_markup=back_kb)
        elif mime_type.startswith("video/"):
            if _can_send_video_in_telegram(file_item):
                content = await download_file_bytes(file_id)
                video = BufferedInputFile(content, filename=name)
                await message.answer_video(video=video, caption=name, reply_markup=back_kb)
            elif web_link:
                await message.answer(f"🎬 {name}\n{web_link}", reply_markup=back_kb)
            else:
                await message.answer(f"🎬 {name}", reply_markup=back_kb)
        elif web_link:
            await message.answer(f"📄 {name}\n{web_link}", reply_markup=back_kb)
        else:
            await message.answer(f"📄 {name}", reply_markup=back_kb)
    except DriveUnavailableError as exc:
        logger.error("File view unavailable file_idx=%s: %s", file_idx, exc)
        await message.answer(
            f"Не удалось открыть «{name}». Попробуйте позже или вернитесь к списку.",
            reply_markup=back_kb,
        )
    except Exception as exc:
        logger.error("File view error file_idx=%s: %s", file_idx, exc)
        await message.answer(
            f"Не удалось открыть «{name}». Попробуйте позже или вернитесь к списку.",
            reply_markup=back_kb,
        )

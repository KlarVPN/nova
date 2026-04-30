from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.config import Settings, get_settings
from app.database.dal import message_log_dal, payment_dal, subscription_dal, user_dal
from app.database.database_setup import init_db_connection
from app.services.panel_api_service import PanelApiService
from app.services.subscription_service import SubscriptionService

_session_factory: Optional[sessionmaker] = None
_settings: Optional[Settings] = None
_panel_service: Optional[PanelApiService] = None
_subscription_service: Optional[SubscriptionService] = None


def _get_runtime() -> tuple[sessionmaker, SubscriptionService]:
    global _session_factory, _settings, _panel_service, _subscription_service

    if _settings is None:
        _settings = get_settings()
    if _session_factory is None:
        _session_factory = init_db_connection(_settings)
    if _panel_service is None:
        _panel_service = PanelApiService(_settings)
    if _subscription_service is None:
        _subscription_service = SubscriptionService(_settings, _panel_service)

    return _session_factory, _subscription_service


def _format_language(lang_code: Optional[str]) -> str:
    mapping = {
        "ru": "Русский",
        "en": "English",
    }
    if not lang_code:
        return "не указан"
    return mapping.get(lang_code.lower(), lang_code)


def _format_datetime(value: Optional[datetime]) -> str:
    if value is None:
        return "не указано"
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone().strftime("%Y-%m-%d %H:%M")


def _format_traffic_gb(used_bytes: Optional[int], limit_bytes: Optional[int]) -> str:
    used_gb = float(used_bytes or 0) / (1024 ** 3)
    if not limit_bytes or limit_bytes <= 0:
        return f"{used_gb:.2f} GB / Безлимит"
    limit_gb = float(limit_bytes) / (1024 ** 3)
    return f"{used_gb:.2f} GB / {limit_gb:.2f} GB"


def _format_tariff(duration_months: Optional[int]) -> str:
    if duration_months is None:
        return "не указан"
    if duration_months == 1:
        return "1 месяц"
    if duration_months in (2, 3, 4):
        return f"{duration_months} месяца"
    return f"{duration_months} месяцев"


def _format_status_with_indicator(status: str) -> str:
    normalized = (status or "UNKNOWN").upper()
    if normalized == "ACTIVE":
        return f"🟢 {normalized}"
    if normalized in {"EXPIRED", "DISABLED", "REVOKED", "INACTIVE"}:
        return f"🔴 {normalized}"
    if normalized in {"LIMITED", "PAUSED"}:
        return f"🟡 {normalized}"
    return f"⚪ {normalized}"


def _parse_dt(value: object) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _pick_str(data: dict, keys: tuple[str, ...]) -> str:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


async def build_support_user_info_message(user_id: int) -> str:
    session_factory, subscription_service = _get_runtime()

    async with session_factory() as session:
        user = await user_dal.get_user_by_id(session, user_id)

        display_name = "не найден"
        username = "не указан"
        profile_link = f"tg://user?id={user_id}"
        language = "не указан"
        registration_date = "не указано"
        panel_uuid = "не указан"
        is_admin = False

        if user:
            first_name = (user.first_name or "").strip()
            last_name = (user.last_name or "").strip()
            full_name = f"{first_name} {last_name}".strip()
            display_name = full_name or "не указан"

            if user.username:
                username = f"@{user.username.lstrip('@')}"
                profile_link = f"https://t.me/{user.username.lstrip('@')}"

            language = _format_language(user.language_code)
            registration_date = _format_datetime(user.registration_date)
            panel_uuid = user.panel_user_uuid or "не указан"
            is_admin = user.user_id in (_settings.ADMIN_IDS if _settings else [])

        active_sub = None
        if user:
            active_sub = await subscription_dal.get_active_subscription_by_user_id(
                session,
                user_id,
                user.panel_user_uuid,
            )

        sub_details = await subscription_service.get_active_subscription_details(session, user_id)

        tariff = _format_tariff(active_sub.duration_months) if active_sub else "не активен"
        panel_status = "UNKNOWN"
        active_until = "не указано"
        days_left_text = "0"
        traffic_text = "0.00 GB / Безлимит"
        device_count_text = "0 / 0"
        last_client_text = "не определен"
        last_online_text = "не определен"

        if sub_details:
            panel_status = str(sub_details.get("status_from_panel") or "UNKNOWN")
            end_date = sub_details.get("end_date")
            active_until = _format_datetime(end_date)
            if isinstance(end_date, datetime):
                if end_date.tzinfo is None:
                    end_date = end_date.replace(tzinfo=timezone.utc)
                seconds_left = (end_date - datetime.now(timezone.utc)).total_seconds()
                days_left_text = str(max(0, int(seconds_left // 86400)))

            traffic_text = _format_traffic_gb(
                sub_details.get("traffic_used_bytes"),
                sub_details.get("traffic_limit_bytes"),
            )
            max_devices = sub_details.get("max_devices")
            if isinstance(max_devices, int):
                device_count_text = f"0 / {max_devices if max_devices > 0 else 'Безлимит'}"

        panel_user_data = None
        if user and user.panel_user_uuid:
            panel_user_data = await subscription_service.panel_service.get_user_by_uuid(user.panel_user_uuid)

        devices: list[object] = []
        if user and user.panel_user_uuid:
            devices = await subscription_service.panel_service.get_user_devices(user.panel_user_uuid) or []

        if sub_details:
            max_devices = sub_details.get("max_devices")
            if isinstance(max_devices, int):
                max_devices_text = str(max_devices) if max_devices > 0 else "Безлимит"
                device_count_text = f"{len(devices)} / {max_devices_text}"

        normalized_devices: list[dict] = []
        for item in devices:
            if isinstance(item, dict):
                normalized_devices.append(item)
            elif isinstance(item, str):
                normalized_devices.append({"hwid": item})

        latest_device = None
        if normalized_devices:
            def _device_sort_key(item: dict) -> datetime:
                parsed = (
                    _parse_dt(item.get("lastOnlineAt"))
                    or _parse_dt(item.get("lastConnectedAt"))
                    or _parse_dt(item.get("lastSeenAt"))
                    or _parse_dt(item.get("updatedAt"))
                    or _parse_dt(item.get("createdAt"))
                )
                if parsed is None:
                    return datetime.min.replace(tzinfo=timezone.utc)
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=timezone.utc)
                return parsed

            latest_device = sorted(normalized_devices, key=_device_sort_key, reverse=True)[0]

        if latest_device:
            platform = _pick_str(latest_device, ("platform", "client", "app", "application"))
            model = _pick_str(latest_device, ("deviceModel", "device_model", "model", "deviceName", "device_name"))
            os_version = _pick_str(latest_device, ("osVersion", "os_version", "os", "version"))
            user_agent = _pick_str(latest_device, ("userAgent", "user_agent", "ua"))

            chunks = [v for v in (platform, model, os_version) if v]
            if chunks:
                last_client_text = " / ".join(chunks)
            elif user_agent:
                last_client_text = user_agent[:120]
            else:
                hwid_hint = _pick_str(latest_device, ("hwid", "id"))
                if hwid_hint:
                    last_client_text = f"устройство {hwid_hint[:12]}"

        candidate_online_values = []
        if panel_user_data and isinstance(panel_user_data, dict):
            candidate_online_values.extend([
                panel_user_data.get("onlineAt"),
                panel_user_data.get("lastConnectAt"),
                panel_user_data.get("lastOnlineAt"),
                panel_user_data.get("lastSeenAt"),
                panel_user_data.get("updatedAt"),
                panel_user_data.get("lastTrafficAt"),
            ])
            user_traffic = panel_user_data.get("userTraffic") or {}
            if isinstance(user_traffic, dict):
                candidate_online_values.extend([
                    user_traffic.get("lastConnectAt"),
                    user_traffic.get("lastOnlineAt"),
                    user_traffic.get("lastSeenAt"),
                    user_traffic.get("updatedAt"),
                ])

        for device in normalized_devices:
            candidate_online_values.extend([
                device.get("lastOnlineAt"),
                device.get("lastConnectedAt"),
                device.get("lastSeenAt"),
                device.get("updatedAt"),
                device.get("createdAt"),
            ])

        parsed_candidates = []
        for value in candidate_online_values:
            parsed = _parse_dt(value)
            if parsed is None:
                continue
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            parsed_candidates.append(parsed)
        if parsed_candidates:
            last_online_text = _format_datetime(max(parsed_candidates))

        panel_status_display = _format_status_with_indicator(panel_status)

        actions_count = await message_log_dal.count_user_message_logs(session, user_id)
        had_trial_or_subscription = await subscription_dal.has_any_subscription_for_user(session, user_id)
        total_paid = await payment_dal.get_user_total_paid(session, user_id)
        referral_revenue = await payment_dal.get_referral_revenue(session, user_id)

        invited_count_result = await session.execute(
            text("SELECT COUNT(*) FROM users WHERE referred_by_id = :user_id"),
            {"user_id": user_id},
        )
        invited_count = invited_count_result.scalar() or 0

        purchased_count_result = await session.execute(
            text(
                """
                SELECT COUNT(DISTINCT u.user_id)
                FROM users u
                JOIN payments p ON u.user_id = p.user_id
                WHERE u.referred_by_id = :user_id
                  AND p.status = 'succeeded'
                """
            ),
            {"user_id": user_id},
        )
        purchased_count = purchased_count_result.scalar() or 0

        trial_text = "использовал" if had_trial_or_subscription else "не использовал"
        admin_line = "<b>🛡 Роль:</b> администратор бота\n" if is_admin else ""

        return (
            f"<b>👤 Клиент:</b> {escape(display_name)}\n"
            f"<b>🆔 ID:</b> <code>{user_id}</code>\n"
            f"<b>📛 Никнейм:</b> {escape(username)}\n"
            f"<b>🔗 Профиль:</b> <a href=\"{profile_link}\">открыть профиль</a>\n"
            f"<b>🌐 Язык:</b> {escape(language)}\n"
            f"<b>📅 Регистраци:</b> <code>{escape(registration_date)}</code>\n"
            f"<b>🧬 Панель UUID:</b> <code>{escape(panel_uuid)}</code>\n"
            f"{admin_line}"
            "<b>------------------------</b>\n"
            f"<b>💳 Тариф:</b> {escape(tariff)}\n"
            f"<b>📡 Статус:</b> {escape(panel_status_display)}\n"
            f"<b>⏳ Действует до:</b> <code>{escape(active_until)}</code>\n"
            f"<b>🗓 Дней осталось:</b> {days_left_text}\n"
            f"<b>📶 Трафик:</b> {escape(traffic_text)}\n"
            f"<b>📱 Устройства:</b> {escape(device_count_text)}\n"
            f"<b>🧩 Последний клиент:</b> {escape(last_client_text)}\n"
            f"<b>🟢 Последний онлайн:</b> <code>{escape(last_online_text)}</code>\n"
            f"<b>🧾 Всего действия:</b> {actions_count}\n"
            f"<b>🎁 Триал:</b> {trial_text}\n"
            f"<b>💰 Всего оплачено:</b> {total_paid:.2f} RUB\n"
            f"<b>🤝 Доход по рефералам:</b> {referral_revenue:.2f} RUB\n"
            f"<b>👥 Приглашено друзей:</b> {invited_count}\n"
            f"<b>✅ Купили подписку:</b> {purchased_count}"
        )

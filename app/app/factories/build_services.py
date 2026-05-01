import logging
from aiogram import Bot
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.middlewares.i18n import JsonI18n
from app.services.yookassa_service import YooKassaService
from app.services.panel_api_service import PanelApiService
from app.services.subscription_service import SubscriptionService
from app.services.referral_service import ReferralService
from app.services.promo_code_service import PromoCodeService
from app.services.stars_service import StarsService
from app.services.crypto_pay_service import CryptoPayService
from app.services.panel_webhook_service import PanelWebhookService
from app.services.freekassa_service import FreeKassaService
from app.services.platega_service import PlategaService
from app.services.severpay_service import SeverPayService
from app.services.kassa_ai_service import KassaAiService
from app.services.lknpd_service import LknpdService


def build_core_services(
    settings: Settings,
    bot: Bot,
    async_session_factory: sessionmaker,
    i18n: JsonI18n,
    bot_username_for_default_return: str,
):
    panel_service = PanelApiService(settings)
    subscription_service = SubscriptionService(settings, panel_service, bot, i18n)
    referral_service = ReferralService(settings, subscription_service, bot, i18n)
    promo_code_service = PromoCodeService(settings, subscription_service, bot, i18n)
    stars_service = StarsService(bot, settings, i18n, subscription_service, referral_service)
    cryptopay_service = CryptoPayService(
        settings.CRYPTOPAY_TOKEN,
        settings.CRYPTOPAY_NETWORK,
        bot,
        settings,
        i18n,
        async_session_factory,
        subscription_service,
        referral_service,
    )
    freekassa_service = FreeKassaService(
        bot=bot,
        settings=settings,
        i18n=i18n,
        async_session_factory=async_session_factory,
        subscription_service=subscription_service,
        referral_service=referral_service,
    )
    platega_service = PlategaService(
        bot=bot,
        settings=settings,
        i18n=i18n,
        async_session_factory=async_session_factory,
        subscription_service=subscription_service,
        referral_service=referral_service,
        default_return_url=bot_username_for_default_return,
    )
    severpay_service = SeverPayService(
        bot=bot,
        settings=settings,
        i18n=i18n,
        async_session_factory=async_session_factory,
        subscription_service=subscription_service,
        referral_service=referral_service,
        default_return_url=bot_username_for_default_return,
    )
    kassa_ai_service = KassaAiService(settings)
    panel_webhook_service = PanelWebhookService(bot, settings, i18n, async_session_factory, panel_service)
    yookassa_service = YooKassaService(
        shop_id=settings.YOOKASSA_SHOP_ID,
        secret_key=settings.YOOKASSA_SECRET_KEY,
        configured_return_url=settings.YOOKASSA_RETURN_URL,
        bot_username_for_default_return=bot_username_for_default_return,
        settings_obj=settings,
    )
    lknpd_service = LknpdService(
        settings.LKNPD_INN,
        settings.LKNPD_PASSWORD,
        api_url=settings.LKNPD_API_URL,
    )

    # Wire services that depend on each other
    try:
        # Allow subscription service to consume promo codes
        setattr(subscription_service, "promo_code_service", promo_code_service)
        # Attach YooKassa to subscription service for auto-renew charges
        setattr(subscription_service, "yookassa_service", yookassa_service)
        # Allow panel webhook to trigger renewals through subscription service
        setattr(panel_webhook_service, "subscription_service", subscription_service)
    except Exception as exc:
        logging.debug("Suppressed exception in bot/app/factories/build_services.py: %s", exc)

    return {
        "panel_service": panel_service,
        "subscription_service": subscription_service,
        "referral_service": referral_service,
        "promo_code_service": promo_code_service,
        "stars_service": stars_service,
        "cryptopay_service": cryptopay_service,
        "freekassa_service": freekassa_service,
        "panel_webhook_service": panel_webhook_service,
        "yookassa_service": yookassa_service,
        "lknpd_service": lknpd_service,
        "platega_service": platega_service,
        "severpay_service": severpay_service,
        "kassa_ai_service": kassa_ai_service,
    }

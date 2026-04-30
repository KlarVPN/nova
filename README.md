<div align="center">

# 🌌 Nova

**Telegram-бот для автоматизации продажи VPN-подписок на базе [Remnawave](https://github.com/remnawave/backend)**

Принимает оплату, выдаёт подписки, управляет пользователями — пока вы спите.

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docs.docker.com)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-green?style=for-the-badge)](LICENSE)

</div>

---

## ✨ Возможности

<table>
<tr>
<td width="50%" valign="top">

### 📦 Подписки

- 🎯 Гибкие тарифные планы по периодам
- 📊 Трафик: безлимит или фиксированный пакет
- 📱 Управление подключёнными устройствами
- 🆓 Пробный период для новых пользователей
- 🔄 Уведомления об истечении подписки
- 🌍 Режим продажи трафика (пакеты GB)

</td>
<td width="50%" valign="top">

### 💳 Платежи

- 🏦 **6 платёжных провайдеров** одновременно
- ⭐ Telegram Stars — без внешних сервисов
- 🪙 CryptoPay — USDT, TON, BTC и другие
- 💾 Рекуррентные платежи (YooKassa)
- 🧾 Фискализация через НалоGo
- 🔍 Автообработка webhook от провайдеров

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 📣 Маркетинг

- 🏷️ Промокоды — скидки и бонусные дни
- 👥 Реферальная программа с бонусами
- 📨 Рассылки по всей базе пользователей
- 🎯 Автоприменение промокода через deeplink
- 🌐 Обязательная подписка на канал

</td>
<td width="50%" valign="top">

### 🛠️ Администрирование

- 🤖 Панель управления прямо в Telegram
- 📊 Статистика — пользователи, платежи, подписки
- 👤 Управление пользователями и банами
- 🔄 Ручная синхронизация с панелью Remnawave
- 📝 Логи действий с экспортом
- 🔐 Доступ строго по `ADMIN_IDS`

</td>
</tr>
</table>

---

## 💳 Платёжные провайдеры

<div align="center">

| | Провайдер | Методы оплаты | Валюта |
|:---:|:---|:---|:---:|
| ⭐ | **Telegram Stars** | Встроенная валюта Telegram | XTR |
| 🏦 | **YooKassa** | Карты, СБП, автоплатежи | RUB |
| 🪙 | **CryptoPay** | USDT, TON, BTC, ETH | Crypto |
| 💳 | **FreeKassa** | Карты, СБП | RUB |
| 💳 | **Platega** | Карты, СБП | RUB |
| 💳 | **SeverPay** | Карты, СБП | RUB |

</div>

---

## 🚀 Быстрый старт

```bash
git clone https://github.com/your-repo/nova.git
cd nova
cp .env.example .env   # заполните переменные
docker network create remnawave-network
docker compose up -d
```

### Отдельный Support Bot

В репозиторий добавлен отдельный бот поддержки, который работает независимо от VPN-бота и может стартовать вместе с ним:

- код: `src/support_bot`
- локальный запуск: `python support_bot_main.py`
- docker-запуск: `docker compose up -d support-bot`
- автозапуск вместе с основным ботом: просто задайте `SUPPORT_BOT_TOKEN` и `SUPPORT_BOT_GROUP_ID`

Для него используются отдельные переменные окружения: `SUPPORT_BOT_*` (см. `.env.example`).
Администраторы support-бота берутся из `ADMIN_IDS` (все ID из списка).

### Обязательные переменные

```env
BOT_TOKEN=              # Токен бота от @BotFather
ADMIN_IDS=              # Telegram ID администраторов (через запятую)
WEBHOOK_BASE_URL=       # Публичный домен для вебхуков

POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres

PANEL_API_URL=          # URL API Remnawave (например: http://remnawave/api)
PANEL_API_KEY=          # Ключ доступа к панели
```

Полный список переменных — в [`.env.example`](.env.example).

---

## 🏗️ Стек

<div align="center">

| | Компонент | Технология |
|:---:|:---|:---|
| 🐍 | Язык | Python 3.12, полностью async |
| 🤖 | Telegram | Aiogram 3.x |
| 🗄️ | База данных | PostgreSQL 17 + SQLAlchemy 2.0 + Alembic |
| ⚡ | Web-сервер | aiohttp (webhook, платёжные callback-и) |
| ⚙️ | Конфигурация | Pydantic Settings v2 |
| 🐳 | Контейнеризация | Docker + Docker Compose |

</div>

---

## 🗄️ База данных

Миграции применяются **автоматически** при каждом старте. Для ручного управления:

```bash
alembic upgrade head                              # Применить все миграции
alembic downgrade -1                              # Откатить последнюю
alembic revision --autogenerate -m "description"  # Создать новую
```

---

## 💬 Поддержка

- 🐛 **Баги и предложения** — [GitHub Issues](../../issues)

---

<div align="center">

**[AGPL-3.0 License](LICENSE)**

</div>

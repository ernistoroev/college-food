# CLAUDE.md

## О проекте

**College Food** — меню столовой колледжа. Сервис только показывает меню (блюда, цены, фото и т.п.).
**Заказов, корзины и оплаты нет** — не добавлять такую функциональность без явной просьбы.

- **Backend** (этот репозиторий) — Django + Django REST Framework. Backend пишет владелец репозитория.
- **Frontend** — отдельное приложение на React, получает данные через REST API (JSON). В этом репозитории фронтенда нет.

## Стек

- Python 3.13 (виртуальное окружение в `venv/`)
- Django 6.1
- Django REST Framework 3.18
- Pillow (для `ImageField`, фото блюд)
- SQLite (`db.sqlite3`, в `.gitignore`)

Зависимости — в `requirements.txt`. После установки нового пакета обновлять: `pip freeze > requirements.txt`.

## Переменные окружения

| Переменная | По умолчанию (dev) | Назначение |
|---|---|---|
| `DJANGO_SECRET_KEY` | `django-insecure-dev-only-...` | секретный ключ, в продакшене обязателен |
| `DJANGO_DEBUG` | `False` | для локальной разработки `True` (через `.env`) |
| `DJANGO_ALLOWED_HOSTS` | пусто | список хостов через запятую, нужен при `DEBUG=False` |

`settings.py` сам читает файл `.env` из корня проекта (без сторонних библиотек); реальные переменные окружения имеют приоритет.
Для локальной разработки: `Copy-Item .env.example .env`. Файл `.env` в `.gitignore`, `.env.example` — коммитится.

## Структура

```
config/      # настройки проекта: settings.py, urls.py, wsgi/asgi
menu/        # основное приложение: модели, API меню, админка
manage.py
```

Текущее состояние: проект только создан. `menu` подключено в `INSTALLED_APPS` вместе с `rest_framework`,
но модели, сериализаторы, представления и маршруты API ещё не написаны. В `config/urls.py` есть только `admin/`.
Медиафайлы: `MEDIA_URL = '/media/'`, `MEDIA_ROOT = BASE_DIR / 'media'`.

## Команды (Windows, PowerShell)

```powershell
venv\Scripts\Activate.ps1          # активировать окружение
pip install -r requirements.txt    # установить зависимости
Copy-Item .env.example .env        # один раз: включает DEBUG для локальной разработки
python manage.py runserver         # dev-сервер на http://127.0.0.1:8000
python manage.py makemigrations    # после изменения моделей
python manage.py migrate
python manage.py createsuperuser   # доступ к /admin/
python manage.py test menu         # тесты приложения menu
```

## Соглашения

- API — только через DRF (сериализаторы + ViewSet/generic views), ответы в JSON для React-фронтенда.
- Маршруты API держать под префиксом `/api/` (например, `menu/urls.py`, подключённый через `include` в `config/urls.py`).
- Публичное API меню — в основном только чтение; редактирование меню — через Django admin.
- Для запросов с React dev-сервера (другой порт) понадобится CORS (`django-cors-headers`) — пока не установлен.
- В dev раздавать медиа через `static()` в `config/urls.py` при `DEBUG = True`.
- `venv/`, `db.sqlite3`, `media/` в `.gitignore` — не коммитить.
- Секреты и настройки окружения — только через переменные окружения (см. выше), не хардкодить в `settings.py`.

# CLAUDE.md

## О проекте

**College Food** — меню столовой колледжа. Сервис только показывает меню (блюда, цены, фото и т.п.).
**Заказов, корзины и оплаты нет** — не добавлять такую функциональность без явной просьбы.

Backend и frontend лежат в одном репозитории, в корне:

- **Backend** — Django + Django REST Framework (`config/`, `menu/`, `manage.py`). Backend пишет владелец репозитория.
- **Frontend** — React + Vite (`src/`, `public/`, `index.html`, `package.json`), получает данные через REST API (JSON).

## Стек

Backend:
- Python 3.13 (виртуальное окружение в `venv/`)
- Django 6.1
- Django REST Framework 3.18
- django-cors-headers (запросы с dev-сервера Vite)
- Pillow (для `ImageField`, фото блюд)
- SQLite (`db.sqlite3`, в `.gitignore`)

Зависимости — в `requirements.txt`. После установки нового пакета обновлять: `pip freeze > requirements.txt`.

Frontend:
- React 19, Vite 8, ESLint
- lucide-react (иконки), axios (запросы к API), react-router-dom (установлен, пока не используется)

Зависимости — в `package.json` / `package-lock.json`, `node_modules/` в `.gitignore`.

## Переменные окружения

| Переменная | По умолчанию (dev) | Назначение |
|---|---|---|
| `DJANGO_SECRET_KEY` | `django-insecure-dev-only-...` | секретный ключ, в продакшене обязателен |
| `DJANGO_DEBUG` | `False` | для локальной разработки `True` (через `.env`) |
| `DJANGO_ALLOWED_HOSTS` | пусто | список хостов через запятую, нужен при `DEBUG=False` |
| `DJANGO_CORS_ALLOWED_ORIGINS` | пусто | адреса фронтенда через запятую, которым можно обращаться к API |

`settings.py` сам читает файл `.env` из корня проекта (без сторонних библиотек); реальные переменные окружения имеют приоритет.
Для локальной разработки: `Copy-Item .env.example .env`. Файл `.env` в `.gitignore`, `.env.example` — коммитится.

## Структура

```
config/      # backend: настройки проекта — settings.py, urls.py, wsgi/asgi
menu/        # backend: основное приложение — модели, API меню, админка
manage.py
src/         # frontend: App.jsx (страница меню), App.css, index.css, main.jsx
public/      # frontend: статические файлы, фото блюд в public/images/
index.html   # frontend: точка входа Vite
package.json
```

Текущее состояние: в `menu` есть модели `Category` (название, порядок) и `Dish` (категория, название,
описание, цена в сомах, фото в `media/dishes/`, флаг `is_available`), обе зарегистрированы в админке.
Категорию с блюдами удалить нельзя (`on_delete=PROTECT`).

API (только чтение, `menu/urls.py` через `DefaultRouter`, подключён в `config/urls.py` под `/api/`):
- `GET /api/categories/` — категории в порядке `order`;
- `GET /api/dishes/` — только блюда с `is_available=True`, фильтр `?category=<id>`; `GET /api/dishes/<id>/`.
Цена отдаётся числом (`COERCE_DECIMAL_TO_STRING = False`), `image` — полный URL или `null`.
Поиска по названию в API нет: `icontains` в SQLite не учитывает регистр кириллицы, фронтенд ищет сам.
Медиафайлы: `MEDIA_URL = '/media/'`, `MEDIA_ROOT = BASE_DIR / 'media'`.

Frontend берёт блюда и категории из API через axios (`src/App.jsx`), адрес — `VITE_API_URL`,
по умолчанию `http://127.0.0.1:8000/api`. Поиск и фильтр по категории — на клиенте. Фото — из админки,
блюда без фото показываются с заглушкой; картинки в `public/images/` больше не используются. В шапке есть кнопки
«Корзина» и «Мои заказы» — это только вёрстка, заказов в проекте нет (см. выше).
`src/App.backup.jsx` — старая копия `App.jsx`, нигде не импортируется.

## Команды (Windows, PowerShell)

Backend:

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

Frontend:

```powershell
npm install        # установить зависимости
npm run dev        # dev-сервер Vite на http://127.0.0.1:5173 (host задан в vite.config.js)
npm run build      # сборка в dist/
npm run lint       # ESLint
```

## Соглашения

- API — только через DRF (сериализаторы + ViewSet/generic views), ответы в JSON для React-фронтенда.
- Маршруты API держать под префиксом `/api/` (например, `menu/urls.py`, подключённый через `include` в `config/urls.py`).
- Публичное API меню — в основном только чтение; редактирование меню — через Django admin.
- CORS — через `django-cors-headers`; разрешённые адреса фронтенда в `DJANGO_CORS_ALLOWED_ORIGINS` (через запятую).
- В dev медиа раздаются через `static()` в `config/urls.py` при `DEBUG = True`.
- `venv/`, `db.sqlite3`, `media/` в `.gitignore` — не коммитить.
- Секреты и настройки окружения — только через переменные окружения (см. выше), не хардкодить в `settings.py`.

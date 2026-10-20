# CLAUDE.md

## О проекте

**College Food** — меню столовой колледжа: блюда, цены, фото, поиск и фильтр по категориям.
Во фронтенде есть корзина, оформление заказа и «Мои заказы», но они работают только в браузере (`localStorage`).
**На бэкенде заказов и оплаты нет** — не добавлять их без явной просьбы.

Репозиторий разделён на две независимые части:

- **`backend/`** — Django + Django REST Framework, отдаёт меню через REST API (JSON). Backend пишет владелец репозитория.
- **`frontend/`** — React + Vite, сайт для студентов.

Команды каждой части запускаются из её папки (`cd backend` / `cd frontend`).

## Структура

```
backend/
  config/            # настройки проекта: settings.py, urls.py, wsgi/asgi
  menu/              # основное приложение: модели, API меню, админка, тесты
  manage.py
  requirements.txt
  .env.example       # пример настроек; локальный .env, venv/, db.sqlite3, media/ — тоже здесь, в .gitignore
frontend/
  src/
    App.jsx          # корень приложения: состояние корзины и заказов, шапка, корзина, «Мои заказы»
    pages/menu/      # страница меню (MenuPage)
    entities/        # dish (данные блюд), cart (логика корзины), order (заказы в localStorage)
    features/        # checkout (форма оформления заказа)
  public/images/     # фото блюд
  index.html, vite.config.js, eslint.config.js, package.json
.gitignore           # общий для обеих частей
CLAUDE.md
```

## Backend

Стек: Python 3.13 (окружение в `backend/venv/`), Django 6.1, Django REST Framework 3.18,
django-cors-headers, Pillow (для `ImageField`), SQLite (`backend/db.sqlite3`).
Зависимости — в `backend/requirements.txt`. После установки нового пакета: `pip freeze > requirements.txt`.

Модели в `menu`: `Category` (название, порядок) и `Dish` (категория, название, описание, цена в сомах,
фото в `media/dishes/`, флаг `is_available`), обе зарегистрированы в админке.
Категорию с блюдами удалить нельзя (`on_delete=PROTECT`).

API (только чтение, `menu/urls.py` через `DefaultRouter`, подключён в `config/urls.py` под `/api/`):
- `GET /api/categories/` — категории в порядке `order`;
- `GET /api/dishes/` — только блюда с `is_available=True`, фильтр `?category=<id>`; `GET /api/dishes/<id>/`.
Цена отдаётся числом (`COERCE_DECIMAL_TO_STRING = False`), `image` — полный URL или `null`.
Поиска по названию в API нет: `icontains` в SQLite не учитывает регистр кириллицы.
Медиафайлы: `MEDIA_URL = '/media/'`, `MEDIA_ROOT = BASE_DIR / 'media'` (`BASE_DIR` — это `backend/`).

### Переменные окружения

| Переменная | По умолчанию (dev) | Назначение |
|---|---|---|
| `DJANGO_SECRET_KEY` | `django-insecure-dev-only-...` | секретный ключ, в продакшене обязателен |
| `DJANGO_DEBUG` | `False` | для локальной разработки `True` (через `.env`) |
| `DJANGO_ALLOWED_HOSTS` | пусто | список хостов через запятую, нужен при `DEBUG=False` |
| `DJANGO_CORS_ALLOWED_ORIGINS` | пусто | адреса фронтенда через запятую, которым можно обращаться к API |

`settings.py` сам читает `backend/.env` (без сторонних библиотек); реальные переменные окружения имеют приоритет.
Файл `.env` в `.gitignore`, `.env.example` — коммитится.

### Команды (из `backend/`, Windows PowerShell)

```powershell
python -m venv venv                # один раз: создать окружение
venv\Scripts\Activate.ps1          # активировать окружение
python -m pip install -r requirements.txt
Copy-Item .env.example .env        # один раз: включает DEBUG и CORS для локальной разработки
python manage.py migrate
python manage.py createsuperuser   # доступ к /admin/
python manage.py runserver         # http://127.0.0.1:8000
python manage.py makemigrations    # после изменения моделей
python manage.py test menu         # тесты приложения menu
```

## Frontend

Стек: React 19, Vite 8, ESLint, lucide-react (иконки). axios и react-router-dom установлены, но пока не используются.
Зависимости — в `frontend/package.json` / `package-lock.json`.

Текущее состояние: к API фронтенд **не подключён** — 28 блюд и категории захардкожены в
`src/entities/dish/model/dishes.js` (с полями `stock`, `weight`, `rating`, которых нет в модели `Dish`).
Фото — из `public/images/`, для части блюд файлов нет, тогда показывается заглушка.
Поиск и фильтр по категории — на клиенте. Остаток порций (`stock`) уменьшается при добавлении в корзину,
только в памяти браузера.
`src/App.backup.jsx`, `src/App.backup2.jsx`, `src/App.css.save` — старые копии, нигде не используются.

### Команды (из `frontend/`)

```powershell
npm install        # установить зависимости
npm run dev        # dev-сервер Vite на http://localhost:5173
npm run build      # сборка в dist/
npm run lint       # ESLint
```

## Соглашения

- API — только через DRF (сериализаторы + ViewSet/generic views), ответы в JSON для React-фронтенда.
- Маршруты API держать под префиксом `/api/` (`menu/urls.py`, подключённый через `include` в `config/urls.py`).
- Публичное API меню — только чтение; редактирование меню — через Django admin.
- CORS — через `django-cors-headers`; разрешённые адреса фронтенда в `DJANGO_CORS_ALLOWED_ORIGINS`.
- В dev медиа раздаются через `static()` в `config/urls.py` при `DEBUG = True`.
- `venv/`, `db.sqlite3`, `media/`, `.env`, `node_modules/`, `dist/` в `.gitignore` — не коммитить.
- Секреты и настройки окружения — только через переменные окружения, не хардкодить в `settings.py`.
- Каждая задача — в отдельной ветке и через Pull Request в `main`.

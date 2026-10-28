# CLAUDE.md

## О проекте

**College Food** — сайт столовой колледжа: меню с поиском и категориями, корзина, заказ с выбором времени
получения, «Мои заказы», регистрация и вход, профиль студента, отзывы.
Всё хранится на бэкенде. **Оплата — только демо** (QR-код без настоящих платежей), реальную оплату
не добавлять без явной просьбы.

Репозиторий разделён на две независимые части:

- **`backend/`** — Django + Django REST Framework, REST API (JSON) и админка. Backend пишет владелец репозитория.
- **`frontend/`** — React + Vite, сайт для студентов.

Команды каждой части запускаются из её папки (`cd backend` / `cd frontend`).

## Структура

```
backend/
  config/            # настройки проекта: settings.py, urls.py, wsgi/asgi
  menu/              # меню: Category, Dish, API меню, команда import_dishes
  accounts/          # регистрация, вход по токену, профиль студента (Profile)
  orders/            # заказы (Order, OrderItem)
  reviews/           # отзывы (Review)
  manage.py
  requirements.txt
  .env.example       # пример настроек; локальный .env, venv/, db.sqlite3, media/ — тоже здесь, в .gitignore
frontend/
  src/
    App.jsx          # корень приложения: меню, корзина, оплата (демо), «Мои заказы», модальные окна
    shared/api/      # client.js: axios с адресом API и токеном, getErrorMessage
    entities/        # запросы к API: dish, auth, order, review; cart — логика корзины (в памяти)
    pages/           # menu, reviews, profile
    features/        # auth (окно входа), checkout (форма заказа)
  public/images/     # фото блюд (import_dishes копирует их в backend/media/dishes/)
  index.html, vite.config.js, eslint.config.js, package.json
.gitignore           # общий для обеих частей
CLAUDE.md
```

## Backend

Стек: Python 3.13 (окружение в `backend/venv/`), Django 6.1, Django REST Framework 3.18,
django-cors-headers, Pillow (для `ImageField`), SQLite (`backend/db.sqlite3`).
Зависимости — в `backend/requirements.txt`. После установки нового пакета: `pip freeze > requirements.txt`.

Модели:
- `menu`: `Category` (название, порядок) и `Dish` (категория, название, описание, цена в сомах, вес и
  единица `г`/`мл`, `portions_today` — порций на сегодня, фото в `media/dishes/`, флаг `is_available`).
  Категорию с блюдами удалить нельзя (`on_delete=PROTECT`).
- `accounts`: стандартный `User` (почта = `username`, имя = `first_name`) + `Profile` (курс, факультет, аватар).
- `orders`: `Order` (пользователь, имя студента, время получения из `PICKUP_TIMES`, статус, сумма) и
  `OrderItem` (блюдо, копия названия и цены на момент заказа, количество).
- `reviews`: `Review` (пользователь, оценка 1–5, текст).

API (всё под `/api/`, авторизация — заголовок `Authorization: Token <key>`):
- `GET /api/categories/`, `GET /api/dishes/`, `GET /api/dishes/<id>/` — меню, только чтение; в меню только
  `is_available=True`, фильтр `?category=<id>`;
- `POST /api/auth/register/` `{name, email, password}`, `POST /api/auth/login/` `{email, password}` → `{token, user}`;
  `POST /api/auth/logout/`; `GET`/`PATCH /api/auth/me/` (имя, курс, факультет, аватар — multipart);
- `GET /api/orders/` — заказы текущего пользователя; `POST /api/orders/` `{student_name, pickup_time, items: [{dish, quantity}]}`.
  Сумму считает сервер по ценам из базы; `portions_today` проверяется и уменьшается в одной транзакции
  (`select_for_update`), при нехватке порций — 400 и ничего не списывается;
- `GET /api/reviews/` — всем; `POST /api/reviews/` `{rating, text}` — только вошедшим.
Цена отдаётся числом (`COERCE_DECIMAL_TO_STRING = False`), `image` — полный URL или `null`.
Язык `ru` — сообщения об ошибках API на русском, фронтенд показывает их как есть. Часовой пояс `Asia/Bishkek`.
Поиска по названию в API нет: `icontains` в SQLite не учитывает регистр кириллицы.
Медиафайлы: `MEDIA_URL = '/media/'`, `MEDIA_ROOT = BASE_DIR / 'media'` (`BASE_DIR` — это `backend/`).

В админке: блюда (вес, порции, наличие правятся прямо в списке), заказы (статус меняется в списке:
«Принят» → «Готовится» → «Готов к выдаче» → «Выдан»), отзывы, пользователи с профилем.

`python manage.py import_dishes` — загружает 28 блюд меню (команда Ханзады) и прикрепляет фото из
`frontend/public/images/`, если у блюда фото ещё нет.

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
python manage.py import_dishes     # один раз: меню и фото
python manage.py createsuperuser   # доступ к /admin/
python manage.py runserver         # http://127.0.0.1:8000
python manage.py makemigrations    # после изменения моделей
python manage.py test              # все тесты
```

## Frontend

Стек: React 19, Vite 8, ESLint, lucide-react (иконки), axios (запросы к API), qrcode.react (QR демо-оплаты).
react-router-dom установлен, но не используется. Зависимости — в `frontend/package.json` / `package-lock.json`.

Адрес API — `VITE_API_URL`, по умолчанию `http://127.0.0.1:8000/api` (`src/shared/api/client.js`).
Токен хранится в `localStorage` (`college-food-token`); при загрузке страницы `fetchCurrentUser()` проверяет его.
Меню, заказы, отзывы и профиль — с сервера; модули в `src/entities/*` переводят поля API (`portions_today`,
`status_display`, …) в имена, которые использует разметка (`stock`, `status`, …).
Корзина живёт только в памяти; при добавлении `stock` уменьшается на экране, настоящий остаток считает сервер,
после заказа меню перезагружается. Оформить заказ, открыть «Мои заказы» и оставить отзыв можно только после входа.
Поиск и фильтр по категории — на клиенте.
`src/App.backup.jsx`, `src/App.backup2.jsx`, `src/App.css.save` и другие `*.backup` / `*.before-*` — старые
копии, нигде не используются.

### Команды (из `frontend/`)

```powershell
npm install        # установить зависимости
npm run dev        # dev-сервер Vite на http://localhost:5173
npm run build      # сборка в dist/
npm run lint       # ESLint
```

## Соглашения

- API — только через DRF (сериализаторы + ViewSet/generic views), ответы в JSON для React-фронтенда.
- Маршруты API держать под префиксом `/api/`: у каждого приложения свой `urls.py`, подключённый через `include` в `config/urls.py`.
- API меню — только чтение; редактирование меню и статусов заказов — через Django admin.
- Не доверять данным из браузера: цены, суммы, автора отзыва и владельца заказа берёт сервер.
- CORS — через `django-cors-headers`; разрешённые адреса фронтенда в `DJANGO_CORS_ALLOWED_ORIGINS`.
- В dev медиа раздаются через `static()` в `config/urls.py` при `DEBUG = True`.
- `venv/`, `db.sqlite3`, `media/`, `.env`, `node_modules/`, `dist/` в `.gitignore` — не коммитить.
- Секреты и настройки окружения — только через переменные окружения, не хардкодить в `settings.py`.
- Каждая задача — в отдельной ветке и через Pull Request в `main`.

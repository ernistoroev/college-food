# CLAUDE.md

## О проекте

**College Food** — сайт столовой колледжа: меню с поиском и категориями, корзина, заказ с выбором времени
получения, «Мои заказы», чат по заказу, регистрация и вход, профиль студента, отзывы.
Две роли: **студент** и **сотрудник столовой** (управляет меню, заказами и отзывами).
Всё хранится на бэкенде. **Оплата — только демо** (QR-код без настоящих платежей), реальную оплату
не добавлять без явной просьбы.

Репозиторий разделён на две независимые части:

- **`backend/`** — Django + Django REST Framework, REST API (JSON) и админка. Backend пишет владелец репозитория.
- **`frontend/`** — React + Vite, сайт для студентов.

Команды каждой части запускаются из её папки (`cd backend` / `cd frontend`).

## Структура

```
backend/
  config/            # настройки, urls.py, pagination.py (StandardPagination), tests.py (документация API)
  menu/              # меню: Category, Dish, CRUD для сотрудника, команда import_dishes
  accounts/          # регистрация и вход (JWT), профиль (Profile), permissions.py — роли и классы прав
  orders/            # заказы (Order, OrderItem) и чат по заказу (Message)
  reviews/           # отзывы о блюдах и о столовой (Review), модерация
  staff/             # панель сотрудника: /api/staff/dashboard/ (без моделей)
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
djangorestframework-simplejwt (JWT), drf-spectacular (Swagger), django-cors-headers, Pillow (для `ImageField`),
SQLite (`backend/db.sqlite3`).
Зависимости — в `backend/requirements.txt`. После установки нового пакета: `pip freeze > requirements.txt`.

**Документация API — `/api/docs/` (Swagger) и `/api/schema/` (OpenAPI).** У каждого эндпоинта есть
`extend_schema` с `summary`/`description` на русском; при добавлении эндпоинта подписывать так же и проверять
`python manage.py spectacular --validate --fail-on-warn --file schema.yml` (без предупреждений).
Во вьюхах с фильтром по пользователю в `get_queryset` есть проверка `swagger_fake_view` — для генерации схемы.

### Роли и права (`accounts/permissions.py`)

- **Сотрудник** — член группы Django «Сотрудники столовой» (`STAFF_GROUP`, создаётся миграцией
  `accounts/0002`) или суперпользователь. Назначают в админке: Пользователи → Группы. `is_staff` даёт только
  вход в Django-админку и на роль в API не влияет. Все остальные — **студенты**.
- `get_role(user)` → `'staff'` / `'student'`; отдаётся в `user.role` при входе, регистрации и в `/api/auth/me/`.
- Классы прав: `IsCanteenStaff`, `IsStaffOrReadOnly`, `IsStudent`, `IsStudentOrReadOnly`.
- Правила: меню читают все, меняет только сотрудник; отзыв и заказ создаёт только студент (сотруднику 403);
  модерация отзывов, смена статусов заказов, сводка — только сотрудник. Аноним на запись — 401, нет прав — 403,
  чужой заказ для студента — 404.

### Модели

- `menu`: `Category` (название, порядок) и `Dish` (категория, название, описание, цена в сомах, вес и
  единица `г`/`мл`, `portions_today`, фото в `media/dishes/`, `is_available`, служебное `search_name` — название
  в нижнем регистре, заполняется в `save()`). Категорию с блюдами удалить нельзя (`PROTECT`, API отвечает 400).
- `accounts`: стандартный `User` (почта = `username`, имя = `first_name`) + `Profile` (курс, факультет, аватар).
- `orders`: `Order` (пользователь, имя студента, время получения из `PICKUP_TIMES`, комментарий, статус
  `new`/`cooking`/`ready`/`done`/`cancelled`, сумма), `OrderItem` (блюдо, копия названия и цены, количество),
  `Message` (заказ, автор, текст). `done` и `cancelled` — финальные (`FINAL_STATUSES`); при отмене
  `Order.return_portions()` возвращает порции — и через API, и в админке (`OrderAdmin.save_model`).
- `reviews`: `Review` (пользователь, `dish` — необязательно: пусто = отзыв о столовой, оценка 1–5, текст,
  `is_visible`). `UniqueConstraint`: один отзыв на блюдо от пользователя (отзывы о столовой не ограничены).

### API

Полный список — в Swagger (`/api/docs/`). Коротко:
- авторизация: JWT, заголовок `Authorization: Bearer <access>`; `access` живёт 30 минут, `refresh` — 7 дней
  (`SIMPLE_JWT`). `register`/`login` → `{access, refresh, user}`, `refresh` → `{access}`. Выхода на сервере нет —
  фронтенд просто удаляет токены;
- меню: `ModelViewSet` для `/api/dishes/` и `/api/categories/`; фильтры `?category=`, `?search=`, `?available=`;
  `PATCH /api/dishes/{id}/availability/`; `GET /api/dishes/{id}/reviews/`; в блюде `rating` и `reviews_count`
  (по видимым отзывам, `annotate`); недоступные блюда тоже в списке (`is_available=false`), но заказать их нельзя;
- заказы: `/api/orders/` (студент — свои, сотрудник — все, `?status=`), `PATCH /api/orders/{id}/status/`,
  `GET`/`POST /api/orders/{id}/messages/`; контакты студента (`customer_name`, `customer_email`) — только в
  карточке заказа для сотрудника. Сумму и остаток порций считает сервер в одной транзакции (`select_for_update`);
- отзывы: `/api/reviews/` (`?dish=<id>` / `?dish=none`); скрытые видит только сотрудник;
- `GET /api/staff/dashboard/` — сводка для панели сотрудника.

Ответы — плоский JSON, рядом с id название (`category_name`, `dish_name`, `user_name`, `author_name`,
`status_display`). Списки — страницами `{count, next, previous, results}` (`config/pagination.py`: по 20,
`?page_size=` до 100); без страниц только чат по заказу.
Цена отдаётся числом (`COERCE_DECIMAL_TO_STRING = False`), `image` — полный URL или `null`.
Язык `ru` — сообщения об ошибках API на русском. Часовой пояс `Asia/Bishkek`.
Поиск: SQLite не сравнивает кириллицу без учёта регистра, поэтому `?search=` ищет по `search_name`.
В формах DRF считает отсутствующую галочку `False`, поэтому в `availability` и модерации отзыва поле
проверяется на наличие явно. Медиафайлы: `MEDIA_URL = '/media/'`, `MEDIA_ROOT = BASE_DIR / 'media'`.

В админке: блюда (вес, порции, наличие правятся прямо в списке), заказы со статусом в списке и чатом внутри,
отзывы (галочка «показывать» в списке), пользователи с профилем и группами.

`python manage.py import_dishes` — загружает 28 блюд меню (команда Ханзады) и прикрепляет фото из
`frontend/public/images/`, если у блюда фото ещё нет.

### Переменные окружения

| Переменная | По умолчанию (dev) | Назначение |
|---|---|---|
| `DJANGO_SECRET_KEY` | `django-insecure-dev-only-...` | секретный ключ, в продакшене обязателен |
| `DJANGO_DEBUG` | `False` | для локальной разработки `True` (через `.env`) |
| `DJANGO_ALLOWED_HOSTS` | пусто | список хостов через запятую, нужен при `DEBUG=False` |
| `DJANGO_CORS_ALLOWED_ORIGINS` | пусто | адреса фронтенда через запятую, которым можно обращаться к API |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | пусто | на хостинге — `https://адрес`, чтобы работал вход в админку |

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
python manage.py test              # все тесты (пароли в тестах — быстрый MD5, только при `test`)
```

## Frontend

Стек: React 19, Vite 8, ESLint, lucide-react (иконки), axios (запросы к API), qrcode.react (QR демо-оплаты).
react-router-dom установлен, но не используется. Зависимости — в `frontend/package.json` / `package-lock.json`.

Адрес API — `VITE_API_URL`, по умолчанию `http://127.0.0.1:8000/api` (`src/shared/api/client.js`).
JWT: `access` и `refresh` хранятся в `localStorage` (`college-food-access`, `college-food-refresh`); axios
добавляет `Authorization: Bearer`, а при 401 один раз обновляет `access` через `/auth/refresh/` и повторяет
запрос. Выход — просто `clearTokens()`. При загрузке страницы `fetchCurrentUser()` проверяет токен.
Списки API приходят страницами — `getList()` в `client.js` берёт `results` с `page_size=100`.
Меню, заказы, отзывы и профиль — с сервера; модули в `src/entities/*` переводят поля API (`portions_today`,
`status_display`, `dish_name`, `user_name`, …) в имена, которые использует разметка (`stock`, `status`, `name`, …).
Недоступное блюдо (`is_available=false`) приходит со `stock: 0` — карточка показывает «закончилось».
Страница «Отзывы» показывает отзывы о столовой (`?dish=none`). Интерфейса сотрудника во фронтенде пока нет —
сотрудник работает в Django-админке; `user.role` для будущей панели уже приходит.
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

## Хостинг (демо)

Демо выложено на PythonAnywhere, пошаговая инструкция — `DEPLOY.md`. Один адрес для всего: Django отдаёт
API, админку, Swagger и собранный React-сайт. `npm run build:deploy` (в `frontend/`, режим `deploy`,
`.env.deploy` → `VITE_API_URL=/api`) собирает сайт в `backend/frontend_build/` — эта папка **коммитится**,
потому что на хостинге фронтенд не собирается. После изменений во фронтенде её нужно пересобрать.
`whitenoise` отдаёт `staticfiles/` (после `collectstatic`, в `.gitignore`) и файлы сборки с корня сайта
(`WHITENOISE_ROOT`), `config/views.py:frontend` отдаёт `index.html` на `/`. Медиа на хостинге раздаёт
PythonAnywhere (Static files: `/media/`). Продакшен-настройки — через `.env`: `DJANGO_DEBUG=False`,
`DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`.

## Соглашения

- API — только через DRF (сериализаторы + ViewSet/generic views), ответы в JSON для React-фронтенда.
- Права — только через классы из `accounts/permissions.py`, роль не проверять вручную по `is_staff`.
- На каждый эндпоинт — тесты прав: аноним, студент, сотрудник.
- Маршруты API держать под префиксом `/api/`: у каждого приложения свой `urls.py`, подключённый через `include` в `config/urls.py`.
- API меню — только чтение; редактирование меню и статусов заказов — через Django admin.
- Не доверять данным из браузера: цены, суммы, автора отзыва и владельца заказа берёт сервер.
- CORS — через `django-cors-headers`; разрешённые адреса фронтенда в `DJANGO_CORS_ALLOWED_ORIGINS`.
- В dev медиа раздаются через `static()` в `config/urls.py` при `DEBUG = True`.
- `venv/`, `db.sqlite3`, `media/`, `.env`, `node_modules/`, `dist/` в `.gitignore` — не коммитить.
- Секреты и настройки окружения — только через переменные окружения, не хардкодить в `settings.py`.
- Каждая задача — в отдельной ветке и через Pull Request в `main`.

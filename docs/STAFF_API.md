# Авторизация администрации и управление меню — Ханзада

## Что проверено и добавлено

Проект использует стандартный Django User, JWT и Profile. Роль определяется сервером: член группы «Сотрудники столовой» или superuser — staff; остальные — student. Флаг is_staff сам по себе даёт доступ к Django admin, но не к API столовой. Публичная регистрация не назначает роли. Неактивный пользователь не получает доступ.

Существующие CRUD API блюд, поля порций/доступности и загрузка фото сохранены. Добавлены отдельный вход сотрудников и панель управления меню. Дополнительные миграции не нужны: группа уже создаётся миграцией accounts/0002.

## Запуск на Mac

Из корня проекта в терминале:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
python manage.py migrate
python manage.py createsuperuser
DJANGO_DEBUG=True DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1 DJANGO_CORS_ALLOWED_ORIGINS=http://localhost:5173 python manage.py runserver
```

Во втором терминале из корня проекта:

```bash
cd frontend
npm ci
npm run dev -- --host localhost
```

Панель: http://localhost:5173/#/staff
Меню: http://localhost:5173/
Админка: http://127.0.0.1:8000/admin/
Swagger: http://127.0.0.1:8000/api/docs/

Для входа через панель требуется email-логин: создавайте сотрудника с username, равным его email в нижнем регистре. В Django admin владелец создаёт пользователя, задаёт пароль и добавляет в группу «Сотрудники столовой». Для сотрудника панели не нужно включать is_staff или superuser. Не назначайте сотрудникам право редактирования пользователей/групп. Вход superuser в панель также возможен, если его username — email.

## API для согласования с Омурбеком

Статус: подготовлено для согласования; сообщение Омурбеку не отправлено.
Базовый путь `/api/`. Завершающий `/` обязателен.

| Метод | Путь | Доступ / назначение |
|---|---|---|
| POST | staff/auth/login/ | Отдельный вход сотрудника: email, password |
| POST | auth/login/ | Существующий общий вход, без изменения контракта |
| POST | auth/refresh/ | refresh → access |
| GET | auth/me/ | Текущий пользователь, включая role |
| GET | dishes/ | Публичный список блюд |
| GET | dishes/{id}/ | Публичная карточка |
| POST | dishes/ | Только staff: создать |
| PATCH / PUT | dishes/{id}/ | Только staff: изменить |
| DELETE | dishes/{id}/ | Только staff: удалить, ответ 204 |
| PATCH | dishes/{id}/availability/ | Только staff: is_available |
| GET | categories/ | Публичные категории |
| POST / PATCH / DELETE | categories/ или categories/{id}/ | Только staff |
| GET | staff/dashboard/ | Только staff: сводка |

Вход: `{ "email": "cook@college.kg", "password": "..." }`.
Ответ 200: `{ "access": "...", "refresh": "...", "user": { "id": 1, "name": "...", "email": "...", "role": "staff", "course": "", "faculty": "", "avatar": null } }`.
Неверные данные/неактивный аккаунт: 400; студент на отдельном входе: 403 без токенов.

Все защищённые запросы: `Authorization: Bearer <access>`.
Без авторизации изменение меню: 401. С JWT студента: 403, даже при прямом вызове API.

Создание/редактирование блюда принимает JSON или multipart/form-data:

```json
{
  "name": "Плов",
  "description": "Рис с мясом",
  "category": 1,
  "price": "230.00",
  "weight": 300,
  "weight_unit": "г",
  "portions_today": 12,
  "is_available": true
}
```

`name`, `category`, `price` обязательны при создании; PATCH принимает только изменённые поля. `category` — id существующей категории. `weight_unit`: г / мл. Цена неотрицательная, вес и порции — неотрицательные целые. Для изменения порций отправить PATCH dishes/{id}/ с `{"portions_today":20}`. Ноль означает, что порции закончились; is_available управляется отдельно.

Фото: поле `image`, файл действительного изображения до 5 МБ, multipart/form-data. Не задавайте Content-Type вручную при отправке FormData: браузер добавляет boundary. Ответ содержит URL image или null. Замена фото — PATCH того же блюда. Сервер проверяет содержимое файла.

Список: `{count,next,previous,results}`. Фильтры `category=<id>`, `search=<текст>`, `available=true|false`, `page`, `page_size` (до 100). Карточка дополнительно возвращает id, category_name, rating, reviews_count. Создание — 201, редактирование — 200, ошибки валидации — 400 с полями ошибок. Удаление блюда сохраняет имя/цену в старых заказах. Категория с блюдами не удаляется: 400.

## Проверка перед сдачей

```bash
cd backend
python manage.py test
python manage.py makemigrations --check --dry-run
python manage.py spectacular --validate --file /tmp/college-food-schema.yaml
cd ../frontend
npm run build
```

Откройте панель сотрудником: создайте блюдо с фото, измените порции и доступность, проверьте меню студента и удалите тестовое блюдо. Попытка входа студента в панель должна вернуть отказ. Серверные тесты проверяют также прямые запросы с JWT студента.

Production: медиафайлы должен обслуживать веб-сервер/хранилище, а не Django DEBUG. Настройте MEDIA_ROOT/MEDIA_URL и сохранность загрузок. Эта ветка — исходники основного проекта; ранее опубликованная демонстрация с локальными данными не обновляется автоматически.

# Как выложить College Food в интернет (PythonAnywhere)

Сайт и API работают по одному адресу `https://ЛОГИН.pythonanywhere.com`:
Django отдаёт API (`/api/`), админку (`/admin/`), Swagger (`/api/docs/`) и собранный React-сайт (`/`).
Бесплатного тарифа хватает. Вместо `ЛОГИН` везде — ваш логин на PythonAnywhere.

## 1. Регистрация

1. Откройте https://www.pythonanywhere.com → **Pricing & signup** → **Create a Beginner account**.
2. Логин станет адресом сайта: например, логин `collegefood` → `collegefood.pythonanywhere.com`.

## 2. Код и зависимости

Вкладка **Consoles** → **Bash**. Команды можно вставлять целиком:

```bash
git clone https://github.com/ernistoroev/college-food.git
cd college-food/backend
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Если `python3.13` не найден — замените на `python3.12` (здесь и в шаге 4). Ниже 3.12 нельзя: Django 6 не запустится.

## 3. Настройки (.env)

Команда сама придумает секретный ключ и подставит ваш логин (`$USER`):

```bash
cat > .env << EOF
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(50))')
DJANGO_ALLOWED_HOSTS=$USER.pythonanywhere.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://$USER.pythonanywhere.com
EOF
```

`.env` не попадает в Git — ключ остаётся только на сервере.

## 4. База, меню, файлы, администратор

```bash
python manage.py migrate
python manage.py import_dishes
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

`createsuperuser` спросит логин (почту), почту и пароль — это аккаунт для `/admin/`.
Суперпользователь — сотрудник столовой. Других сотрудников добавляют в админке:
Пользователи → нужный человек → Группы → «Сотрудники столовой».

## 5. Веб-приложение

Вкладка **Web** → **Add a new web app** → Next → **Manual configuration** → **Python 3.13** → Next.

На открывшейся странице:

1. **Virtualenv**: `/home/ЛОГИН/college-food/backend/venv`
2. **Code → WSGI configuration file**: нажмите на ссылку, удалите всё содержимое и вставьте:

   ```python
   import os
   import sys

   path = '/home/ЛОГИН/college-food/backend'
   if path not in sys.path:
       sys.path.insert(0, path)

   os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```

   Замените `ЛОГИН` и нажмите **Save**.
3. **Static files** → добавьте строку (фото блюд и аватары):
   - URL: `/media/`
   - Directory: `/home/ЛОГИН/college-food/backend/media`
4. Нажмите зелёную кнопку **Reload** вверху страницы.

Готово: откройте `https://ЛОГИН.pythonanywhere.com`.

## Обновить сайт после изменений в GitHub

```bash
cd ~/college-food && git pull
cd backend && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Затем **Web** → **Reload**.

Если менялся фронтенд, сначала пересоберите его на своём компьютере и закоммитьте сборку:
в папке `frontend/` выполните `npm run build:deploy` — сайт соберётся в `backend/frontend_build/`.

## Если что-то не работает

- Вкладка **Web** → ссылка **Error log** — там текст ошибки.
- «DisallowedHost» — проверьте `DJANGO_ALLOWED_HOSTS` в `.env`, затем Reload.
- Админка не пускает (CSRF) — проверьте `DJANGO_CSRF_TRUSTED_ORIGINS` (с `https://`).
- Нет фото блюд — проверьте строку `/media/` в Static files и выполните `python manage.py import_dishes`.
- На бесплатном тарифе раз в 3 месяца нужно нажать **Run until 3 months from today** на вкладке Web,
  иначе сайт выключится.

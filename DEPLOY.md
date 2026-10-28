# Как выложить College Food в интернет (PythonAnywhere)

Сайт и API работают по одному адресу `https://ЛОГИН.pythonanywhere.com`:
Django отдаёт API (`/api/`), админку (`/admin/`), Swagger (`/api/docs/`) и собранный React-сайт (`/`).
Бесплатного тарифа хватает. Вместо `ЛОГИН` везде — ваш логин на PythonAnywhere: он виден в правом
верхнем углу сайта, домашняя папка — `/home/ЛОГИН`.

> **Важно про консоль PythonAnywhere.** При вставке длинная команда разбивается на несколько строк,
> а перед каждой строкой появляются пробелы. Поэтому:
> - вставляйте команды **по одной строке** и нажимайте Enter после каждой;
> - не используйте многострочные команды (`cat > файл << EOF` … `EOF`): консоль «зависает» в ожидании
>   конца, и всё, что вы вставляете потом, молча пропадает. Если такое случилось — нажмите **Ctrl+C**
>   или откройте новую консоль;
> - файлы с кодом (WSGI) правьте в редакторе на вкладке **Files** / **Web**, проверяя, что перед первой
>   строкой нет пробелов, — иначе Python напишет `IndentationError: unexpected indent`.

## 1. Регистрация

1. Откройте https://www.pythonanywhere.com → **Pricing & signup** → **Create a Beginner account**.
2. Логин станет адресом сайта: например, логин `collegefood` → `collegefood.pythonanywhere.com`.

## 2. Код и зависимости

Вкладка **Consoles** → **Bash**. Команды — по одной:

```bash
git clone https://github.com/ernistoroev/college-food.git
```
```bash
cd college-food/backend
```
```bash
python3.13 -m venv venv
```
```bash
source venv/bin/activate
```
```bash
pip install -r requirements.txt
```

Если `python3.13` не найден — замените на `python3.12` (здесь и в шаге 4). Ниже 3.12 нельзя: Django 6 не запустится.

## 3. Настройки (.env)

Из папки `~/college-food/backend`, по одной команде (`$USER` сам подставит ваш логин,
последняя команда сама придумает секретный ключ):

```bash
echo "DJANGO_DEBUG=False" > .env
```
```bash
echo "DJANGO_ALLOWED_HOSTS=$USER.pythonanywhere.com" >> .env
```
```bash
echo "DJANGO_CSRF_TRUSTED_ORIGINS=https://$USER.pythonanywhere.com" >> .env
```
```bash
python3 -c "import secrets;print('DJANGO_SECRET_KEY='+secrets.token_urlsafe(50))" >> .env
```

Проверка (ключ не покажет): `grep -v SECRET .env` — три строки с `False` и вашим адресом.
`.env` должен лежать именно в `college-food/backend/` и не попадает в Git — ключ остаётся только на сервере.

## 4. База, меню, файлы, администратор

По одной команде:

```bash
python manage.py migrate
```
```bash
python manage.py import_dishes
```
```bash
python manage.py collectstatic --noinput
```
```bash
python manage.py createsuperuser
```

`migrate` выведет список `Applying … OK`, `import_dishes` — «Создано: 28 … добавлено фото: 14».
`createsuperuser` спросит логин (почту), почту и пароль — это аккаунт для `/admin/`.
Суперпользователь — сотрудник столовой. Других сотрудников добавляют в админке:
Пользователи → нужный человек → Группы → «Сотрудники столовой».

## 5. Веб-приложение

Вкладка **Web** → **Add a new web app** → Next → **Manual configuration** → **Python 3.13** → Next.

На открывшейся странице:

1. **Virtualenv**: `/home/ЛОГИН/college-food/backend/venv`
2. **Code → WSGI configuration file**: нажмите на ссылку, удалите всё содержимое (Ctrl+A → Delete) и
   вставьте **одну строку** (она подключает `config/wsgi.py` из проекта):

```
import sys; sys.path.insert(0, '/home/ЛОГИН/college-food/backend'); from config.wsgi import application
```

   Замените `ЛОГИН`, проверьте, что перед `import` нет пробелов и других строк в файле нет, нажмите **Save**.
3. **Static files** → добавьте строку (фото блюд и аватары):
   - URL: `/media/`
   - Directory: `/home/ЛОГИН/college-food/backend/media`
4. Нажмите зелёную кнопку **Reload** вверху страницы.

Готово: откройте `https://ЛОГИН.pythonanywhere.com`.

## Обновить сайт после изменений в GitHub

По одной команде:

```bash
cd ~/college-food
```
```bash
git pull
```
```bash
cd backend
```
```bash
source venv/bin/activate
```
```bash
pip install -r requirements.txt
```
```bash
python manage.py migrate
```
```bash
python manage.py collectstatic --noinput
```

Затем **Web** → **Reload**.

Если менялся фронтенд, сначала пересоберите его на своём компьютере и закоммитьте сборку:
в папке `frontend/` выполните `npm run build:deploy` — сайт соберётся в `backend/frontend_build/`.

## Если что-то не работает

Текст ошибки — в логе. Последние строки показывает команда:

```bash
tail -25 /var/log/ЛОГИН.pythonanywhere.com.error.log
```

| Что видно | Причина и что делать |
|---|---|
| Страница «Coming Soon!» | Для этого адреса нет веб-приложения: проверьте логин (адрес — `ЛОГИН.pythonanywhere.com`) и шаг 5 |
| 500 на всех страницах, в логе `IndentationError` | В WSGI-файле пробелы в начале или лишние строки — вставьте одну строку из шага 5 заново |
| 500 на всех страницах, в логе `ModuleNotFoundError` | Неверный путь в WSGI-файле или Virtualenv — должно быть `/home/ЛОГИН/...` |
| 400 Bad Request на сайте и API, а картинки открываются | Django не видит адрес: нет `.env` в `college-food/backend/` или в нём неверный `DJANGO_ALLOWED_HOSTS`. Проверьте `ls -a` и `grep -v SECRET .env`, затем Reload |
| 500 только на API, в логе `no such table` | Не выполнен `python manage.py migrate` (и `import_dishes`) |
| Консоль ничего не выводит после вставки | Она ждёт конца многострочной команды — Ctrl+C или новая консоль |

Ещё:

- Любое изменение `.env` или WSGI-файла начинает работать только после **Reload**.
- Админка не пускает (CSRF) — проверьте `DJANGO_CSRF_TRUSTED_ORIGINS` (с `https://`).
- Нет фото блюд — проверьте строку `/media/` в Static files и выполните `python manage.py import_dishes`.
- На бесплатном тарифе раз в 3 месяца нужно нажать **Run until 3 months from today** на вкладке Web,
  иначе сайт выключится.

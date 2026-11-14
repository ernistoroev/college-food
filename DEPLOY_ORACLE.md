# Как запустить College Food на своём сервере (Oracle Cloud, бесплатно)

Это второй способ выложить проект — на собственный сервер (VPS) с Ubuntu. Первый, попроще, — PythonAnywhere
(`DEPLOY.md`); оба могут работать одновременно.

Как всё устроено на сервере:

```
Интернет → nginx (порты 80/443) → gunicorn (127.0.0.1:8000) → Django → SQLite
```

- **nginx** принимает запросы и отдаёт фото блюд из `media/`, остальное передаёт в Django.
- **gunicorn** запускает Django (`config.wsgi`), **systemd** следит, чтобы он работал и после перезагрузки.
- Django сам отдаёт API, админку, Swagger, собранный React-сайт и статику (whitenoise) — как на PythonAnywhere.

Готовые файлы настроек лежат в папке `deploy/`: `college-food.service` (systemd) и `nginx-college-food.conf`.
Пути в них рассчитаны на пользователя `ubuntu` и папку `/home/ubuntu/college-food` — так и будет, если делать
по этой инструкции.

Что понадобится: аккаунт Oracle Cloud (при регистрации просят **банковскую карту** для проверки; с бесплатного
тарифа деньги не списываются), компьютер с Windows и PowerShell, примерно час времени.

> Интерфейс Oracle Cloud иногда меняется: если кнопка называется чуть иначе — ищите по смыслу.

## 1. Регистрация

1. Откройте https://www.oracle.com/cloud/free/ → **Start for free**.
2. Заполните данные и карту. **Home Region** (регион) выберите поближе, например во Франкфурте, — потом его не
   поменять, а бесплатные серверы создаются только в нём.
3. Дождитесь письма, что аккаунт готов, и войдите в консоль (https://cloud.oracle.com).

## 2. Создать сервер

1. Меню ☰ → **Compute** → **Instances** → **Create instance**.
2. **Name**: `college-food`.
3. **Image and shape** → **Edit**:
   - **Image**: **Canonical Ubuntu 24.04**;
   - **Shape**: **Ampere** → `VM.Standard.A1.Flex`, 1 OCPU и 6 GB памяти (с пометкой **Always Free-eligible**).
     Если при создании пишет **Out of capacity** — попробуйте позже или возьмите **AMD** → `VM.Standard.E2.1.Micro`
     (тоже бесплатный, 1 GB памяти — проекту хватит).
4. **Add SSH keys** → **Generate a key pair for me** → **Save private key**. Файл `ssh-key-….key` — это ключ
   от сервера, без него не войти. Не теряйте его и никому не отправляйте.
5. Остальное оставьте как есть → **Create**. Через пару минут статус станет **Running**.
6. На странице сервера скопируйте **Public IP address**, например `123.45.67.89`. Дальше вместо `IP` везде — он.

## 3. Открыть порты 80 и 443 в Oracle

Без этого сайт не откроется: Oracle по умолчанию пропускает только SSH.

1. На странице сервера → **Primary VNIC** → ссылка на **Subnet** → **Security Lists** →
   **Default Security List for …** → **Add Ingress Rules**.
2. **Source CIDR**: `0.0.0.0/0`, **IP Protocol**: TCP, **Destination Port Range**: `80,443` → **Add Ingress Rules**.

## 4. Подключиться к серверу

В **PowerShell** на своём компьютере (команды по одной; `ssh` уже есть в Windows 11):

```powershell
New-Item -ItemType Directory -Force $HOME\.ssh
```
```powershell
Move-Item $HOME\Downloads\ssh-key-*.key $HOME\.ssh\oracle.key
```

Windows требует, чтобы ключ мог читать только владелец:

```powershell
icacls $HOME\.ssh\oracle.key /inheritance:r
```
```powershell
icacls $HOME\.ssh\oracle.key /grant:r "$($env:USERNAME):(R)"
```

Подключение (вместо `IP` — адрес сервера), на вопрос `Are you sure…` ответьте `yes`:

```powershell
ssh -i $HOME\.ssh\oracle.key ubuntu@IP
```

Появится строка `ubuntu@college-food:~$` — вы на сервере. Все команды дальше вводятся **там**, по одной.

## 5. Программы и порты внутри Ubuntu

```bash
sudo apt update
```
```bash
sudo apt install -y python3-venv python3-pip nginx git
```
```bash
python3 --version
```

Нужна версия 3.12 или новее (в Ubuntu 24.04 так и есть) — Django 6 на старых не работает.

В образах Ubuntu от Oracle есть ещё и свой фаервол, который закрывает порты. Откройте 80 и 443 и сохраните:

```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
```
```bash
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
```
```bash
sudo netfilter-persistent save
```

## 6. Код и зависимости

```bash
cd ~
```
```bash
git clone https://github.com/ernistoroev/college-food.git
```
```bash
cd ~/college-food/backend
```
```bash
python3 -m venv venv
```
```bash
source venv/bin/activate
```
```bash
pip install -r requirements.txt
```

## 7. Настройки (.env)

Сначала запомните адрес сервера в переменной (вместо `123.45.67.89` — ваш IP):

```bash
IP=123.45.67.89
```

Потом по одной команде, из `~/college-food/backend`:

```bash
echo "DJANGO_DEBUG=False" > .env
```
```bash
echo "DJANGO_ALLOWED_HOSTS=$IP" >> .env
```
```bash
echo "DJANGO_CSRF_TRUSTED_ORIGINS=http://$IP" >> .env
```
```bash
echo "DJANGO_BEHIND_PROXY=True" >> .env
```
```bash
python3 -c "import secrets;print('DJANGO_SECRET_KEY='+secrets.token_urlsafe(50))" >> .env
```

Проверка (ключ не покажет): `grep -v SECRET .env`. `DJANGO_BEHIND_PROXY=True` нужен только здесь, за nginx:
Django узнаёт, что посетитель пришёл по https, и ссылки на фото тоже будут https.

## 8. База, меню, администратор

```bash
python manage.py migrate
```
```bash
python manage.py import_dishes
```
```bash
python manage.py import_dish_photos
```
```bash
python manage.py collectstatic --noinput
```
```bash
python manage.py createsuperuser
```

`createsuperuser` спросит логин (почту), почту и пароль — это аккаунт для `/admin/` и панели `/staff/login`.

## 9. Запустить Django (gunicorn + systemd)

```bash
sudo cp ~/college-food/deploy/college-food.service /etc/systemd/system/
```
```bash
sudo systemctl daemon-reload
```
```bash
sudo systemctl enable --now college-food
```
```bash
systemctl status college-food --no-pager
```

Должно быть `active (running)`. Если нет — смотрите лог: `sudo journalctl -u college-food -n 50 --no-pager`.

## 10. Настроить nginx

```bash
sudo cp ~/college-food/deploy/nginx-college-food.conf /etc/nginx/sites-available/college-food
```
```bash
sudo ln -s /etc/nginx/sites-available/college-food /etc/nginx/sites-enabled/college-food
```
```bash
sudo rm /etc/nginx/sites-enabled/default
```

nginx работает от другого пользователя, поэтому ему нужно разрешить читать фото из домашней папки:

```bash
chmod o+x /home/ubuntu /home/ubuntu/college-food /home/ubuntu/college-food/backend
```
```bash
chmod -R o+rX /home/ubuntu/college-food/backend/media
```

Проверка настроек и перезапуск:

```bash
sudo nginx -t
```
```bash
sudo systemctl reload nginx
```

Готово: откройте в браузере `http://IP` — сайт, `http://IP/admin/` — админка, `http://IP/staff/login` — панель
сотрудника, `http://IP/api/docs/` — Swagger.

## 11. HTTPS и красивый адрес (по желанию)

Сертификат выдают только на домен, не на IP. Бесплатный домен — DuckDNS:

1. https://www.duckdns.org → войдите (например, через GitHub) → придумайте имя, например `collegefood` →
   **add domain** → в поле **current ip** впишите IP сервера → **update ip**. Адрес: `collegefood.duckdns.org`.
2. На сервере (вместо `ДОМЕН` — ваш адрес):

```bash
sudo sed -i 's/server_name _;/server_name ДОМЕН;/' /etc/nginx/sites-available/college-food
```
```bash
sudo apt install -y certbot python3-certbot-nginx
```
```bash
sudo certbot --nginx -d ДОМЕН
```

certbot спросит почту и согласие с условиями, сам настроит nginx на https и будет продлевать сертификат.

3. Добавьте домен в настройки Django — откройте `.env` в редакторе: `nano ~/college-food/backend/.env`,
   допишите через запятую: `DJANGO_ALLOWED_HOSTS=IP,ДОМЕН` и
   `DJANGO_CSRF_TRUSTED_ORIGINS=http://IP,https://ДОМЕН`. Сохранить — Ctrl+O, Enter, выйти — Ctrl+X.

```bash
sudo systemctl restart college-food
```

Теперь сайт открывается по `https://ДОМЕН`.

## Обновить сайт после изменений в GitHub

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
```bash
sudo systemctl restart college-food
```

Фронтенд на сервере не собирается: перед `git pull` пересоберите его у себя (`npm run build:deploy` в `frontend/`)
и закоммитьте `backend/frontend_build/`, как и для PythonAnywhere.

## Если что-то не работает

| Что видно | Причина и что делать |
|---|---|
| `ssh`: `UNPROTECTED PRIVATE KEY FILE` | Ключ доступен не только вам — повторите две команды `icacls` из шага 4 |
| `ssh`: `Connection timed out` | Сервер ещё не запустился или неверный IP — проверьте статус **Running** и **Public IP** |
| Сайт в браузере долго грузится и не открывается | Закрыты порты: проверьте шаг 3 (Security List) и шаг 5 (`iptables`) |
| **502 Bad Gateway** | Django не запущен: `sudo journalctl -u college-food -n 50 --no-pager`, исправьте ошибку, затем `sudo systemctl restart college-food` |
| **400 Bad Request** | Адреса нет в `DJANGO_ALLOWED_HOSTS` (`.env`) — допишите и перезапустите `college-food` |
| Админка не пускает (CSRF) | Нет адреса со схемой в `DJANGO_CSRF_TRUSTED_ORIGINS` (`http://IP` или `https://ДОМЕН`) |
| Нет фото блюд (403 в логе nginx) | Повторите две команды `chmod` из шага 10 (после загрузки новых фото — вторую) |
| `Out of capacity` при создании сервера | Бесплатных Ampere сейчас нет — попробуйте позже или возьмите `VM.Standard.E2.1.Micro` |

Логи: Django — `sudo journalctl -u college-food -n 50 --no-pager`, nginx — `sudo tail -n 30 /var/log/nginx/error.log`.

Бесплатный сервер Oracle может остановить, если он долго простаивает. Если сайт пропал — проверьте в консоли
статус сервера и нажмите **Start**; gunicorn и nginx запустятся сами.

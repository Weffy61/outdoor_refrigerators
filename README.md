# Outdoor Refrigerators

Система контроля выносного холодильного оборудования у арендаторов. Торговые представители фотографируют холодильник на точке и отправляют отчёт с GPS-меткой — менеджер видит, что оборудование на месте и не перемещено. Кластеризация на карте показывает географическое распределение точек по районам.

### Требования

- Python 3.13
- [uv](https://docs.astral.sh/uv/) для управления зависимостями
- PostgreSQL (для продакшена) или SQLite (для разработки)

### Установка

Клонировать репозиторий:

```
git clone <адрес репозитория>
cd outdoor_refrigerators
```

Установить зависимости:

```
uv sync
```

### Создание и настройка .env

Создайте в корне проекта файл `.env`. Скопируйте содержимое `.env.example` и заполните значения:

- **SECRET_KEY** — секретный ключ Django (например: `python -c "import secrets; print(secrets.token_hex(32))"`)
- **DEBUG** — дебаг-режим, по умолчанию `True`
- **DATABASE_URL** — строка подключения к БД, по умолчанию SQLite
- **ALLOWED_HOSTS** — список разрешённых хостов, по умолчанию `127.0.0.1`
- **YANDEX_GEOCODER_API_KEY** — опционально, для обратного геокодирования в EXIF-проверке

### Подготовка к запуску

```
uv run python manage.py migrate
uv run python manage.py loaddata db.json
uv run python manage.py generate_test_data
```

`loaddata` загружает организации, холодильники и пользователей.
`generate_test_data` привязывает торговых представителей к менеджеру и генерирует тестовые GPS-отчёты.

### Запуск (разработка)

```
uv run python manage.py runserver
```

Сайт откроется по адресу http://127.0.0.1:8000
Административная панель: http://127.0.0.1:8000/admin/
Кластеризация на карте: http://127.0.0.1:8000/map/clusters/

### Запуск через Docker

```
cp .env.example .env
```

Заполните `.env`, затем в `Caddyfile` замените `your.domain.com` на свой домен.

```
docker compose up -d --build
docker compose exec web python manage.py loaddata db.json
docker compose exec web python manage.py generate_test_data
```

### Роли пользователей

- **Торговый представитель** — видит свои холодильники, создаёт фотоотчёты
- **Менеджер** — проверяет отчёты подчинённых, видит карту и кластеризацию
- **Администратор** — полный доступ через Django Admin

### Импорт оборудования из Excel

Пример:
```
uv run python manage.py import_users refs.xls
```

# Checkarium

Checkarium — веб-приложение на Django для владельцев рептилий и других экзотических животных.  
Проект помогает хранить карточки питомцев, фиксировать события ухода, отслеживать статус животного и получать регулярные напоминания в Telegram.

## Функциональность

- регистрация и аутентификация пользователей;
- личный кабинет владельца;
- CRUD для питомцев;
- CRUD для событий ухода;
- расчёт статуса питомца на основе последних событий;
- Telegram-уведомления;
- фоновая обработка задач через Celery + Redis;
- запуск в Docker.

## Стек

- Python 3.13
- Django
- PostgreSQL
- Celery
- Redis
- Gunicorn
- Nginx
- Docker / Docker Compose

## Локальный запуск без Docker

1. Установите зависимости:
```bash
poetry install
```

2. Создайте файл **.env** на основе **.env.sample**

3. Примените миграции:
```bash
python manage.py makemigrations
python manage.py migrate
```

4. Запустите сервер:
```bash
python manage.py runserver
```

## Локальный запуск в Docker

Для dev-запуска используется docker-compose.yml:
```bash
docker compose up --build
```

Продакшен-запуск в Docker

Для запуска на сервере используется docker-compose.prod.yml.

Подготовьте .env:
```bash
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=127.0.0.1,localhost,<VM_EXTERNAL_IP>,<YOUR_DOMAIN>
CSRF_TRUSTED_ORIGINS=http://127.0.0.1,http://localhost,http://<VM_EXTERNAL_IP>,https://<YOUR_DOMAIN>
SITE_URL=http://<VM_EXTERNAL_IP>

DB_NAME=checkarium
DB_USER=checkarium_user
DB_PASSWORD=strong-password
DB_HOST=db
DB_PORT=5432

REDIS_URL=redis://redis:6379/0

TELEGRAM_BOT_TOKEN=
TELEGRAM_BOT_USERNAME=
```
Соберите и поднимите контейнеры:
```bash
docker compose -f docker-compose.prod.yml up -d --build
```
Посмотрите логи:
```bash
docker compose -f docker-compose.prod.yml logs -f
```

## Деплой на Yandex Cloud
1. Создайте виртуальную машину.
2. Установите Docker и Docker Compose.
3. Клонируйте репозиторий:
```bash
git clone <REPOSITORY_URL>
cd checkarium
```
4. Создайте .env.
5. Запустите:
```bash
docker compose -f docker-compose.prod.yml up -d --build
```
Откройте в браузере:
```
http://<VM_EXTERNAL_IP>/
```
### Полезные команды

Остановить контейнеры:
```bash
docker compose -f docker-compose.prod.yml down
```
Пересобрать проект:
```bash
docker compose -f docker-compose.prod.yml up -d --build
```
Выполнить команду внутри контейнера web:
```bash
docker compose -f docker-compose.prod.yml exec web bash
Тестовые данные
```
Для заполнения БД демо-данными можно использовать management-команду проекта:
```bash
python manage.py load_test_data --reset
```



1. Установите зависимости:
```bash
poetry install
```



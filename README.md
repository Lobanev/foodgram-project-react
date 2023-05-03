![example workflow](https://github.com/Lobanev/foodgram-project-react/actions/workflows/foodgram_workflowse.yml/badge.svg?branch=master&event=push)
### Опиание проекта!
Приложение «Продуктовый помощник»: сайт, на котором пользователи будут публиковать рецепты,
добавлять чужие рецепты в избранное и подписываться на публикации других авторов. 
Сервис «Список покупок» позволит пользователям создавать список продуктов, которые нужно 
купить для приготовления выбранных блюд.
## Проект доступен по ссылкам:

```
- http://51.250.24.197/
- http://51.250.24.197/admin/
- http://51.250.24.197/api/docs/
```
Foodgram - проект позволяет:

- Просматривать рецепты
- Добавлять рецепты в избранное
- Добавлять рецепты в список покупок
- Создавать, удалять и редактировать собственные рецепты
- Скачивать список покупок
## Инструкции по установке!
***- Клонируйте репозиторий:***
```
git clone git@github.com:Lobanev/foodgram-project-react.git
```

***- Установите и активируйте виртуальное окружение:***
- для MacOS
```
python3 -m venv venv
```
- для Windows
```
python -m venv venv
source venv/bin/activate
source venv/Scripts/activate
```
- Установите зависимости из файла requirements.txt
```
pip install -r requirements.txt
``` 
- Перейдите в папку yatube_api и выполните:

Миграции
```
python manage.py makemigrations
python manage.py migrate
```
Запустите сервер
```
python manage.py runserver
```
### Собираем контейнерыы:

Из папки infra/ разверните контейнеры при помощи docker-compose:
```
docker-compose up -d --build
```
Выполните миграции:
```
docker-compose exec backend python manage.py migrate
```
Создайте суперпользователя:
```
docker-compose exec backend python manage.py createsuperuser
```
Соберите статику:
```
docker-compose exec backend python manage.py collectstatic --no-input
```
Наполните базу данных ингредиентами и тегами. Выполняйте команду из дериктории где находится файл manage.py:
```
docker-compose exec backend python manage.py load_data

```
Остановка проекта:
```
docker-compose down
```

### Подготовка к запуску проекта на удаленном сервере

Cоздать и заполнить .env файл в директории infra
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
TOKEN=252132607137
ALLOWED_HOSTS=*
```

### Автор

Лобанев Александр [Telegram](https:/пш/t.me/Djakomo13) 
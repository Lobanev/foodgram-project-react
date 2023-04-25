### Опиание проекта!
Приложение «Продуктовый помощник»: сайт, на котором пользователи будут публиковать рецепты,
добавлять чужие рецепты в избранное и подписываться на публикации других авторов. 
Сервис «Список покупок» позволит пользователям создавать список продуктов, которые нужно 
купить для приготовления выбранных блюд.
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
### Документация:
После запуска на localhost доступна [документация](http://127.0.0.1:8000/redoc/).


### Автор

Лобанев Александр [Telegram](https:/пш/t.me/Djakomo13) 
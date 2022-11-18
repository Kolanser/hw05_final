# hw05_final

## Yatube - социальная сеть блогеров.
Инструменты: Django, ORM, HTML, Bootstrap.

В проекте реализовано:
* регистрация пользователей
* админ-зона
* восстановление пароля по электронной почте
* публикация постов с изображениями и редактированием, комментирование постов, подписка на авторов.

Регистрация, добавление и редактирование постов осуществляется в соответствующих формах. Для удобства просмотра постов используется пагинация. При повторном обращении к сайту для оптимизации применяется кэширование. Все данные хранятся в базе данных. Приложение протестировано (Unittest).

### Для запуска проекта необходимо:

Клонировать репозиторий и перейти в него в командной строке:

```sh
git clone git@github.com:Kolanser/hw05_final.git
cd hw05_final
```

Cоздать и активировать виртуальное окружение:

```sh
python -m venv env
source venv/Scripts/activate
```

Обновить pip:

```sh
python3 -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```sh
pip install -r requirements.txt
```

Выполнить миграции:

```sh
python3 manage.py migrate
```

Запустить проект:
```sh
python3 manage.py runserver
```
 ### Автор
[**Николай Слесарев**](github.com/Kolanser)

[![CI](https://github.com/yandex-praktikum/hw05_final/actions/workflows/python-app.yml/badge.svg?branch=master)](https://github.com/yandex-praktikum/hw05_final/actions/workflows/python-app.yml)
# Подготовка окружения (Ubuntu 20.04)

## Установка MongoDB
Импортируйте GPG ключ:

``wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | sudo apt-key add -``

Если появилась ошибка в которой говорится что <b>gnupg</b> не установлен, то тогда вначале установите <b>gnupg</b>: 

``sudo apt-get install gnupg``

А затем снова попытайтесь импортировать GPG ключ:

``wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | sudo apt-key add -``

Создайте в системе .list файл для MongoDB:

``echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/4.4 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.4.list``

Обновите базу данных пакетного менеджера:

``sudo apt-get update``

Установите пакеты MongoDB:

``sudo apt-get install -y mongodb-org``

Запустите базу данных MongoDB:

``sudo systemctl start mongod``

Введите эту команду для того чтобы MognoDB самостоятельно запускалась при перезагрузке сервера:

``sudo systemctl enable mongod``

## Установка git

Выполните команду:

``sudo apt install git``


## Создание виртуального окружения

Установите venv:

``sudo apt-get install python3-venv``

Создайте виртуальное окружение:

``python3 -m venv rest-app``

# Развёртывание приложения

Активируйте виртуальное окружение:

``source rest-app/bin/activate``

Скачайте исходный код на свой сервер:

``git clone https://github.com/deadln/yandex-academy-backend.git``

Перейдите в папку проекта:

``cd yandex-academy-backend``

Переключите в проекте ветку на <i>production</i>:

``git checkout production``

Установите необходимые зависимости в виртуальное окружение:

``pip install -r requirements.txt``

# Запуск приложения

Находясь в папке HOME, убедитесь что вы активировали виртуальное окружение:

``source rest-app/bin/activate``

Из папки HOME выполните команду:

``python3 yandex-academy-backend/app.py`` 
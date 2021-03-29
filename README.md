# Подготовка окружения (Ubuntu 20.04)

## Установка MongoDB
Импортируйте GPG ключ:

``wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | sudo apt-key add -``

Если появилась ошибка в которой говорится что <b>gnupg</b> не установлен, то тогда вначале установите <b>gnupg</b>: 

``sudo apt-get install gnupg``

А затем снова попытайтесь импортировать GPG ключ:

``wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | sudo apt-key add -``

Создайте в системе .list файл для MongoDB:

``echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/4.4 multiverse" | 
sudo tee /etc/apt/sources.list.d/mongodb-org-4.4.list``

Обновите базу данных пакетного менеджера:

``sudo apt-get update``

Установите пакеты MongoDB:

``sudo apt-get install -y mongodb-org``

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

Установите необходимые зависимости в виртуальное окружение:

``pip install -r requirements.txt``

# Запуск приложения

Запустите базу данных MongoDB:

``sudo systemctl start mongod``

Находясь в папке HOME, убедитесь что вы активировали виртуальное окружение:

``source rest-app/bin/activate``

Из папки HOME выполните команду:

``python3 yandex-academy-backend/app.py [адрес хоста] [номер порта]`` 

Для того чтобы REST-API был доступен для запросов извне запустите вот так:

``python3 yandex-academy-backend/app.py 0.0.0.0 8080`` 

# Тестирование REST-API

Чтобы запустить тесты, вначале перейдите в папку с приложением:

``cd ~/yandex-academy-backend``

А затем выполните:

``python3 -m unittest tests.py``

# Настройка автоматического возобновления работы REST-API после перезагрузки

Введите эту команду для того чтобы MongoDB самостоятельно запускалась при перезагрузке сервера:

``sudo systemctl enable mongod``

В папке HOME создайте файл <i>start.sh</i> следующего содержания:

````
#!/bin/bash

# Запуск виртуального окружения
source /home/entrant/rest-app/bin/activate
# Запуск REST-API
until python3 /home/entrant/yandex-academy-backend/app.py 0.0.0.0 8080; do
        echo "Server REST-API crashed with exit code $?.  Respawning.." >&2
        sleep 1
done
````

Создайте файл сервиса:

``sudo vim /lib/systemd/system/restapi.service``

И запишите в нём:

````
[Unit]
Description=Script for REST-API startup
After=multi-user.target

[Service]
Type=idle
ExecStart=/home/entrant/start.sh

[Install]
WantedBy=multi-user.target
````

Дайте права на чтение файла:

``sudo chmod 644 /lib/systemd/system/restapi.service``

Обновите список доступных сервисов systemd:

``sudo systemctl daemon-reload``

И включите автозагрузку сервиса <i>restapi.service</i>

``sudo systemctl enable restapi.service``

Теперь скрипт REST-API будет запускаться после перезагрузки сервера, а также перезапускаться после аварийного завершения
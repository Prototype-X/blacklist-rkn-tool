# blacklist-rkn-tool

[![Code Health](https://landscape.io/github/Prototype-X/blacklist-rkn-tool/master/landscape.svg?style=flat)](https://landscape.io/github/Prototype-X/blacklist-rkn-tool/master)

Python3 скрипт **bl-rkn.py** для работы с реестром запрещенных сайтов http://vigruzki.rkn.gov.ru/

Сделано на базе проектов:
* [python-zapret-info](https://github.com/yegorov-p/python-zapret-info)
* [php от Wingman](https://www.evernote.com/shard/s185/sh/ceb0b021-47e7-4c61-ab43-bc6db27fe919/c535b6e5047ec69d304519fe81c2c9ac?noteKey=c535b6e5047ec69d304519fe81c2c9ac)

####Возможности:####
* Получение дампа реестра
* Хранение файлов дампа реестра
* Сохранение дампа реестра в БД MySQL/SQLite
* Уведомление по email о изменениях в реестре
* Генерация и подпись запроса для Rutoken
* Сохранение истории запросов на получение дампа реестра в БД
* Поддержка формата файла выгрузки версии 2.2
* Вывод списка актуальных ip, url, domain и истории запросов

####Установка:####

    pip3 install -r requirements.txt
    OR
    pip3 install suds-jurko
    pip3 install pymysql
    pip3 install peewee

####Запуск:####

    python3 bl-rkn.py

После первого запуска скрипта будет создан файл конфигурации **bl-rkn.cfg**

####Ключи:####

    --url показать список URL
    --ip показать список ip
    --domain показать список доменов
    --history показать список запросов на получение дампа
    --help, -h краткая справка
    --version, -v версия скрипта

####Файл конфигурации:####
**bl-rkn.cfg**

    [DataBase]
    MySQL = 1 # использовать MySQL, 0 - SQlite
    MySQLUser = user
    MySQLPassword = password
    MySQLHost = localhost
    MySQLPort = 3306
    DBName = blacklist # имя БД, для SQlite имя файла DBName.db

    [Log]
    LogRewrite = 1 # перезаписывать log файл при каждом запуске
    LogPathFName = bl-rkn.log # имя и путь log файла

    [Notify]
    Notify = 0 # не отправлять письмо при изменении в реестре
    FromMailAddress = zapret-info@rsoc.ru # адрес отправителя
    ToMailAddress = tech@mail.ru # адрес получателя

    [Request]
    GenerateRequest = 0 # генерировать запрос .xml и .xml.p7s автоматически
    OperatorName = ООО "Телеком" # параметры необходимые для создания файла подписи
    inn = 1234567890
    ogrn = 1234567890123
    email = support@mail.ru
    XMLPathFName = request.xml # путь и имя файла запроса
    P7SPathFName = request.xml.p7s # путь и имя файла подписи
    PEMPathFName = cert.pem # сертификат подписи
    ID = 12345006000000007089123456789001 # id ключа в rutoken

    [History]
    HistoryCount = 0 # не используется

    [Dump]
    DumpFileSave = 1 # сохранять дампы в директории скрипта/dumps/
    GetResultMaxCount = 10 # количество попыток получения дампа

Описание процедуры получения реестра: http://vigruzki.rkn.gov.ru/docs/description_for_operators_actual.pdf

####Обзор аналогов:####

* https://github.com/yegorov-p/python-zapret-info - python
* https://github.com/vnaum/zapret-rss - python
* https://github.com/aleksandr-rakov/zapret2acl  - python
* https://github.com/ircop/zapret - perl
* https://github.com/gh0stwizard/rkn  - perl
* https://github.com/ulav/zapret-checker - C
* https://github.com/chelaxe/BlackList - C#
* https://github.com/apofiget/rkn_registry - Erlang
* https://github.com/konachan700/RKN_Sync - Visual Basic
* https://github.com/alamer/ZapretParser - Java
* [Подборка скриптов от пользователей forum.nag.ru](https://www.evernote.com/shard/s185/sh/ceb0b021-47e7-4c61-ab43-bc6db27fe919/c535b6e5047ec69d304519fe81c2c9ac?noteKey=c535b6e5047ec69d304519fe81c2c9ac)

[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/Prototype-X/blacklist-rkn-tool?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)
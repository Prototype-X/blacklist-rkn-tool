# blacklist-rkn-tool

[![Code Health](https://landscape.io/github/Prototype-X/blacklist-rkn-tool/master/landscape.svg?style=flat)](https://landscape.io/github/Prototype-X/blacklist-rkn-tool/master)

Python3 скрипт **bl-rkn.py** для работы с реестром запрещенных сайтов http://vigruzki.rkn.gov.ru/

Сделано на базе проектов:
* [python-zapret-info](https://github.com/yegorov-p/python-zapret-info)
* [php от Wingman](https://www.evernote.com/shard/s185/sh/ceb0b021-47e7-4c61-ab43-bc6db27fe919/c535b6e5047ec69d304519fe81c2c9ac?noteKey=c535b6e5047ec69d304519fe81c2c9ac)

###Возможности:###
* Получение дампа реестра
* Хранение файлов дампа реестра
* Сохранение дампа реестра в БД SQLite/MySQL/PostgreSQL
* Уведомление по email о изменениях в реестре, статистика
* Уведомление по email об обновлении: веб сервиса, формата выгрузки, памятки оператору
* [Генерация и подпись запроса с Rutoken](https://github.com/Prototype-X/blacklist-rkn-tool/blob/master/Rutoken.md)
* Хранение истории идентификаторов запросов
* Поддержка формата файла выгрузки версии 2.2
* Хранение нескольких версий реестра (--rollback)
* Вывод изменений в реестре (--diff)
* Вывод списка актуальных ip, url, domain и истории запросов

###Требования:###
Python версии 3.4.0 и выше

Установленные пакеты: peewee, lxml, suds-jurko, psycopg2, pymysql

###Установка:###
1. unzip blacklist-rkn-tool.zip  -d /opt 
2. chmod a+x /opt/blacklist-rkn-tool/bl-rkn.py
3. Установите пакеты:

        pip3 install peewee lxml suds-jurko
    
    Для работы достаточно установить один Database Adapter, для типа БД который будет использоваться (SQLite установлен по умолчанию):
    
        pip3 install psycopg2   #для PostgreSQL
        OR
        pip3 install pymysql    #для MySQL
    
    Установить все пакеты:
        
        pip3 install -r requirements.txt
    
4. Запустите скрипт, затем отредактируйте **bl-rkn.cfg**
5. Настройте запуск по cron

6. Для отправки писем:

        sudo apt-get install sendmail

###Запуск:###

    python3 bl-rkn.py

После первого запуска скрипта будет создан файл конфигурации **bl-rkn.cfg**.

При запуске без параметров командной строки будет запущена процедура получения реестра.

###Ключи:###

    --url показать список URL
    --ip показать список ip
    --domain показать список доменов
    --history показать список запросов на получение дампа
    --help, -h краткая справка
    --bt атрибут реестра blockType [default, ip, domain, domain-mask]
    --version, -v версия скрипта

###Файл конфигурации:###
**bl-rkn.cfg**

    [DataBase]
    Type = 0 # 0 - SQLite, 1 - MySQL, 2 - PostgreSQL
    Name = blacklist # имя БД, для SQLite имя файла, без расширения
    Host = localhost
    Port = 5432
    User = user
    Password = password

    [Log]
    LogRewrite = 1 # перезаписывать log файл при каждом запуске
    LogPathFName = /opt/bl-rkn/bl-rkn.log # имя и путь log файла

    [Notify]
    Notify = 0 # не отправлять письмо при изменении в реестре
    Auth = 0 # не использовать авторизацию на почтовом сервере
    Server = mail.domain.ru # адрес почтового сервера
    Port = 25 # порт почтового сервера
    StartTLS = 0 # шифрование
    Login = zapret@domain.ru # логин для почтового сервера
    Password = 159753 # пароль для почтового сервера
    Subject = vigruzki.rkn.gov.ru ver. 2.2 update # тема письма
    From = zapret-info@rsoc.ru # адрес отправителя
    To = tech@mail.ru # адрес получателя

    [Request]
    GenerateRequest = 0 # 1 - генерировать запрос .xml и .xml.p7s автоматически нужен usb ключ Rutoken
    OperatorName = ООО "Телеком" # параметры необходимые для создания файла запроса актуально,
    inn = 1234567890             # если GenerateRequest = 1
    ogrn = 1234567890123         #
    email = support@mail.ru      #
    XMLPathFName = /opt/bl-rkn/request.xml # путь и имя файла запроса
    P7SPathFName = /opt/bl-rkn/request.xml.p7s # путь и имя файла подписи
    PEMPathFName = /opt/bl-rkn/cert.pem # сертификат подписи, актуально если GenerateRequest = 1
    ID = 12345006000000007089123456789001 # id ключа в rutoken, актуально если GenerateRequest = 1

    [History]
    HistoryCount = 0 # не используется
    DiffCount = 3 # количество версий реестра хранимых в БД, минимальное значение 1 

    [Dump]
    DumpFileSave = 1 # сохранять дампы в директории скрипта/dumps/
    GetResultMaxCount = 3 # количество попыток получения дампа

###Использование:###
Получение полного списка для блокировки по url:

1. Список url подлежащих блокировке 
    
        bl-rkn.py --url

2. Список доменов, где блокировка должна осуществлятся только по имени домена т.е. blockType = domain

        bl-rkn.py --domain --bt domain

3. Список доменов, где блокировка должна осуществлятся только по маске домена т.е. blockType = domain-mask

        bl-rkn.py --domain --bt domain-mask

4. Список ip, где блокировка должна осуществлятся только по ip адресам т.е. blockType = ip

        bl-rkn.py --ip --bt ip

###Для PostgreSQL:###

* Запуск CLI:

        sudo -u postgres psql
    
* Установить пароль для пользователя postgres:
    
        postgres=# \password postgres

* Создать нового пользователя: 

        CREATE USER blrkn WITH PASSWORD 'passwd' CREATEDB;

###Примечания:###
Описание процедуры получения реестра: http://vigruzki.rkn.gov.ru/docs/description_for_operators_actual.pdf

**Версии 1.5.0 и выше не совместимы с предыдущими версиями blacklist-rkn-tool, создайте БД заново, перед этим экспортируйте таблицу history, а затем импортируйте в новую БД.**

###Обзор аналогов:###

* https://github.com/yegorov-p/python-zapret-info - python
* https://github.com/DmitryFillo/rknfilter - python
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
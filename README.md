# blacklist-rkn-tool

[![Code Health](https://landscape.io/github/Prototype-X/blacklist-rkn-tool/master/landscape.svg?style=flat)](https://landscape.io/github/Prototype-X/blacklist-rkn-tool/master)

Python3 скрипт **bl-rkn.py** для работы с реестром запрещенных сайтов http://vigruzki.rkn.gov.ru/

Сделано на базе проектов:
* [python-zapret-info](https://github.com/yegorov-p/python-zapret-info)
* [php от Wingman](https://www.evernote.com/shard/s185/sh/ceb0b021-47e7-4c61-ab43-bc6db27fe919/c535b6e5047ec69d304519fe81c2c9ac?noteKey=c535b6e5047ec69d304519fe81c2c9ac)

###Возможности:###
* Получение дампа реестра
* Хранение файлов дампа реестра
* Сохранение дампа реестра в БД SQLite/PostgreSQL
* Уведомление по email о изменениях в реестре, статистика (--stat)
* Уведомление по email об обновлении: веб сервиса, формата выгрузки, памятки оператору
* [Генерация и подпись запроса с Rutoken](https://github.com/Prototype-X/blacklist-rkn-tool/blob/master/Rutoken16.md)
* Хранение истории идентификаторов запросов
* Поддержка формата файла выгрузки версии 2.2
* Перекодировка доменов и url в кириллице
* Фильтрация ip: 127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 0.0.0.0/0, 0.0.0.0
* Хранение нескольких версий реестра (--rollback)
* Вывод изменений в реестре (--diff)
* DNS резолвинг доменов из реестра в ipv4 и ipv6 адреса 
* Вывод списка актуальных ip, url, domain и истории запросов

###Требования:###
Python версии 3.4.0 и выше

Установленные пакеты: peewee, lxml, suds-jurko, psycopg2, dnspython

###Установка:###
1. unzip blacklist-rkn-tool.zip  -d /opt 
2. chmod a+x /opt/blacklist-rkn-tool/bl-rkn.py
3. Установите пакеты:

        pip3 install peewee lxml suds-jurko dnspython
    
    Для работы достаточно установить один Database Adapter, для типа БД который будет использоваться (SQLite установлен по умолчанию):
    
        apt install libpq-dev
        pip3 install psycopg2   #для PostgreSQL
    
    Установить все пакеты:
        
        pip3 install -r requirements.txt
    
4. Запустите скрипт, затем отредактируйте **bl-rkn.cfg**
5. Настройте запуск по cron

       19 */3 * * *  root  /usr/bin/python3 /opt/blacklist-rkn-tool/bl-rkn.py --dump   
       #права root нужны для подписи запроса с использованием rutoken

6. Для отправки писем:

    [sudo apt-get install postfix](https://www.digitalocean.com/community/tutorials/how-to-install-and-configure-postfix-as-a-send-only-smtp-server-on-ubuntu-14-04)

###Запуск:###

    python3 bl-rkn.py

После первого запуска скрипта будет создан файл конфигурации **bl-rkn.cfg**.

###Ключи:###

    --url показать список URL
    --ip показать список ip
    --domain показать список доменов
    --history показать список запросов на получение дампа
    --help, -h краткая справка
    --bt атрибут реестра blockType [default, ip, domain, domain-mask]  
    --dump получить последний дамп
    --rollback 0 - последняя версия дампа, 1 - предпоследняя и т.д.
    --diff 0 - изменения дампа относительно предыдущей версии дампа
    --stat 0 - статистика по последней версии дампа
    --resolve - принудительно запускает DNS резолвинг последней версии дампа
    --version, -v версия скрипта
    
###Файл конфигурации:###
**bl-rkn.cfg**

    [DataBase]
    Type = 0 # 0 - SQLite, 1 - PostgreSQL
    Name = blacklist # имя БД, для SQLite имя файла, без расширения
    Host = localhost
    Port = 5432
    User = user
    Password = password

    [Log]
    LogCount = 7 #количество файлов для ротации логов
    LogRotate = midnight # время ротации s - секунды, h - часы, d - дни
    LogInterval = 1 # если LogRotate = h, LogInterval = 2, тогда ротация лога будет каждые 2 часа
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
    HistoryCount = 3000 # количество хранимых id запросов
    DiffCount = 3 # количество версий реестра хранимых в БД, минимальное значение 1 

    [Dump]
    lastDumpDateUrgently = 1 # проверять новый дамп по параметру lastDumpDateUrgently
    lastDumpDate = 1 # проверять новый дамп по параметру lastDumpDate (обновляется один раз в час)
    DumpFileSave = 1 # сохранять дампы
    DumpPath = # если не указано тогда сохранять дампы в директории скрипта/dumps/
    GetResultMaxCount = 3 # количество попыток получения дампа
    
    [Resolver]
    Resolver = 1 # вкл. резолвинг доменов
    IPv6 = 0 
    DNS = 8.8.4.4 77.88.8.1

    [OpenSSL]
    Path =

###Использование:###

####Получение полного списка для блокировки по url:####

1. Список url подлежащих блокировке 
    
        bl-rkn.py --url

2. Список доменов, где блокировка должна осуществлятся только по имени домена т.е. blockType = domain

        bl-rkn.py --domain --bt domain

3. Список доменов, где блокировка должна осуществлятся только по маске домена т.е. blockType = domain-mask

        bl-rkn.py --domain --bt domain-mask

4. Список ip, где блокировка должна осуществлятся только по ip адресам т.е. blockType = ip

        bl-rkn.py --ip --bt ip

####Примеры использования аргументов коммандной строки --diff x, --rollback x, --stat x:####

Количество версий реестра задается в конфигурации опцией DiffCount.

Когда аргумент --rollback не указан, что эквивалентно --rollback 0 и соответствует самой последней версии реестра.

Аргумент --diff 0 показывает разницу между поледней и предпоследней версией реестра, что позволяет сделать однократную полную выгрузку IP/URL/Domain в систему фильтрации трафика, а в дальнейшем выгружать только изменения в реестре, что позволяет экономить ресурсы и ускоряет обновление данных в системе фильтрации.  
Разница отображается с помощью символов '+' и '-' перед IP/URL/Domain.

Пример однократной полной выгрузки IP/URL/Domain в систему фильтрации трафика и накат изменений в реестре:

У нас хранится три версии реестра т.е. DiffCount = 3

    bl-rkn.py --rollback 2 --ip #вывод ip самой старой версии реестра [0, 1, 2]
    bl-rkn.py --diff 1 --ip #изменения в предпоследней версии реестра
    bl-rkn.py --diff 0 --ip #изменения последней версии реестра

В дальнейшем для поддержания реестра в актуальном состоянии достаточно после получения нового реестра выполнить:
    
    bl-rkn.py --diff 0 --ip

Аргумент --stat x показывает подробную статистику изменений в реестре
 
    bl-rkn.py --stat 0
    
####Получение ip адресов методом разрешения доменных имен из реестра.####
Включается когда в конфигурации Resolver = 1. Запускается автоматически после получения нового реестра
    
    bl-rkn.py --dump
    
При отображении списка ip адресов, будет выведен результат работы резолвера:
    
    bl-rkn.py --ip
    
Для получения списка ip из реестра, необходимо в конфигурации сделать Resolver = 0

Как показала практика количество ip адресов полученное методом разрешения доменных имен, почти в два раза меньше, чем в реестре.

###Для PostgreSQL:###

* Запуск CLI:

        sudo -u postgres psql
    
* Установить пароль для пользователя postgres:
    
        postgres=# \password postgres

* Создать нового пользователя: 

        CREATE USER blrkn WITH PASSWORD 'passwd' CREATEDB;

####Оптимизация настроек сервера PostgreSQL:####

[mamonsu](https://github.com/postgrespro/mamonsu)

[pgtune](http://pgtune.leopard.in.ua/)

####Документация PostgreSQL:####

[Документация PostgreSQL на русском языке](https://postgrespro.ru/docs/)

[Книга Работа с PostgreSQL настройка и масштабирование](http://postgresql.leopard.in.ua/)

[Видео администрирование PostgreSQL](https://postgrespro.ru/education/courses)

[Сравнение РСУБД](https://en.wikipedia.org/wiki/Comparison_of_relational_database_management_systems)

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

###GNU GPL утилиты для блокировки сайтов:###

[nfqfilter](https://github.com/max197616/nfqfilter)

[extfilter](https://github.com/max197616/extfilter)

[Пообщаться с авторами утилит, получить ответы на вопросы forum.nag.ru](http://forum.nag.ru/forum/index.php?showtopic=79886&st=0)

[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/Prototype-X/blacklist-rkn-tool?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)
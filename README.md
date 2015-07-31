# blacklist-rkn-tool

[![Code Health](https://landscape.io/github/Prototype-X/blacklist-rkn-tool/master/landscape.svg?style=flat)](https://landscape.io/github/Prototype-X/blacklist-rkn-tool/master)

Python3 скрипт **bl-rkn.py** для работы с реестром запрещенных сайтов http://vigruzki.rkn.gov.ru/

####Возможности **bl-rkn.py**:####
* Получение дампа реестра
* Хранение дампа реестра в БД MySQL или SqLite
* Уведомление по email при обновлении реестра
* Генерация и подпись запроса для получения дампа*
* Сохранение запросов (рекомендация Роскомнадзора)
* Поддержка xml-файла выгрузки версии 2.2
* Вывод актуальных ip, url, domain и истории запрсов

####Установка:####

    pip3 install suds-jurko
    pip3 install pymysql
    pip3 install peewee

После первого запуска скрипта будет создан файл конфигурации **bl-rkn.cfg**

####Запуск:####
**python3 bl-rkn.py**

####Ключи:####

    --url показать список URL
    --ip показать список ip
    --domain показать список доменов
    --history показать список запросов на получение дампа

####Файл конфигурации:####
**bl-rkn.cfg**

    [DataBase]
    MySQL = 1 # использовать MySQL, 0 - SQlite
    MySQLUser = user
    MySQLPassword = password
    MySQLHost = localhost
    MySQLPort = 3306

    [Log]
    LogRewrite = 1 # перезаписывать log файл при каждом запуске
    LogPathFName = bl-rkn.log # имя и путь log файла

    [Notify]
    Notify = 0 # не отправлять письмо при изменении в реестре
    FromMailAddress = zapret-info@rsoc.ru # адрес отправителя
    ToMailAddress = tech@mail.ru # адрес получателя

    [Request]
    GenerateRequest = 0 # генерировать запрос .xml и .xml.p7s автоматически
    OperatorName = ООО "Телеком"
    inn = 1234567890
    ogrn = 1234567890123
    email = support@mail.ru
    XMLPathFName = request.xml
    P7SPathFName = request.xml.p7s
    PEMPathFName = cert2015.pem # сертификат подписи
    ID = 12345006000000007089123456789001 # id ключа в rutoken

    [History]
    HistoryCount = 0 # не работает

    [Dump]
    DumpFileSave = 1 # сохранять дампы в директории скрипта/dumps/
    GetResultMaxCount = 10 # количество попыток получения дампа`

Описание текущего API http://vigruzki.rkn.gov.ru/docs/description_for_operators_actual.pdf

[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/Prototype-X/blacklist-rkn-tool?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)
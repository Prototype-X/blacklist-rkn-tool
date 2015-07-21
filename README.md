# blacklist-rkn-tool

[![Code Health](https://landscape.io/github/Prototype-X/blacklist-rkn-tool/master/landscape.svg?style=flat)](https://landscape.io/github/Prototype-X/blacklist-rkn-tool/master)

Python3 скрипт для работы с реестром запрещенных сайтов http://vigruzki.rkn.gov.ru/

Возможности bl-rkn.ru:
* Получение дампа реестра
* Хранение дампа реестра в БД MySQL или SqLite
* Уведомление по email при обновлении реестра
* Генерация и подпись запроса для получения дампа*
* Сохранение запросов (рекомендация Роскомнадзора)
* Поддержка xml-файла выгрузки версии 2.2
* Вывод актуальных ip, url, domain и истории запрсов

##Запуск##
**python3 bl-rkn.py**
###Ключи###
**--url** показать список URL

**--ip** показать список ip

**--domain** показать список доменов

**--history** показать список запросов на получение дампа

###Файл конфигурации###
**bl-rkn.cfg**

MySQL = 0 - использовать БД sqlite
MySQL = 1 - БД mysql
Если используется mysql необходимо указать:
MySQLUser = user
MySQLPassword = password
MySQLHost = localhost
MySQLPort = 3306
БД mysql должна быть настроена для работы с кодировкой utf-8, сортировки utf8_unicode_ci


LogRewrite = 0 - дописывать log
LogRewrite = 1 - перезаписывать log при каждом запуске скрипта
LogPathFName = bl-rkn.log

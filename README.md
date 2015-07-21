# blacklist-rkn-tool

[![Code Health](https://landscape.io/github/Prototype-X/blacklist-rkn-tool/master/landscape.svg?style=flat)](https://landscape.io/github/Prototype-X/blacklist-rkn-tool/master)

Python3 скрипт для работы с реестром запрещенных сайтов http://vigruzki.rkn.gov.ru/

Возможности rf-tool.ru:
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

###файл конфигурации###
**bl-rkn.cfg**

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'maximus'

from peewee import Proxy, Model, CharField, TextField, DateField, DateTimeField, IntegerField, BigIntegerField, \
                   BooleanField, SqliteDatabase, MySQLDatabase, PostgresqlDatabase, ForeignKeyField, CompositeKey
import os

import logging
logger = logging.getLogger(__name__)

database_proxy = Proxy()


class Dump(Model):
    param = CharField(primary_key=True, max_length=255, null=False)
    value = TextField(null=False)

    class Meta(object):
        database = database_proxy


class Item(Model):
    content_id = BigIntegerField(null=False, index=True)
    includeTime = DateTimeField(null=False)
    urgencyType = IntegerField(null=False, default=0)
    entryType = IntegerField(null=False)
    blockType = TextField(null=False, default='default')
    hashRecord = TextField(null=False)
    decision_date = DateField(null=False)
    decision_num = TextField(null=False)
    decision_org = TextField(null=False)
    add = BigIntegerField(null=False)
    purge = BigIntegerField(null=True)

    class Meta(object):
        database = database_proxy


class IP(Model):
    item = ForeignKeyField(Item, on_delete='CASCADE', on_update='CASCADE', index=True)
    content_id = BigIntegerField(null=False, index=True)
    # version - версия ip 4 или 6
    # version = IntegerField(null=False, default=4)
    ip = TextField(null=False)
    mask = IntegerField(null=False, default=32)
    # source - источник записи dump или resolver
    # source = TextField(null=False)
    add = BigIntegerField(null=False)
    purge = BigIntegerField(null=True)

    class Meta(object):
        database = database_proxy


class IPResolve(Model):
    domain = TextField(null=False)
    ip = TextField(null=False)

    class Meta(object):
        database = database_proxy


class Domain(Model):
    item = ForeignKeyField(Item, on_delete='CASCADE', on_update='CASCADE', index=True)
    content_id = BigIntegerField(null=False, index=True)
    domain = TextField(null=False)
    add = BigIntegerField(null=False)
    purge = BigIntegerField(null=True)

    class Meta(object):
        database = database_proxy


class URL(Model):
    item = ForeignKeyField(Item, on_delete='CASCADE', on_update='CASCADE', index=True)
    content_id = BigIntegerField(null=False, index=True)
    url = TextField(null=False)
    add = BigIntegerField(null=False)
    purge = BigIntegerField(null=True)

    class Meta(object):
        database = database_proxy


class History(Model):
    requestCode = TextField(null=False)
    diff = BooleanField(null=False, default=True)
    date = DateTimeField(null=False)

    class Meta(object):
        database = database_proxy


def init_db(cfg):
    path_py = str(os.path.dirname(os.path.abspath(__file__)))
    login = cfg.User()
    password = cfg.Password()
    host = cfg.Host()
    port = cfg.Port()
    name_db = cfg.Name()
    type_db = int(cfg.Type())
    blacklist_db = False

    if type_db == 0:
        blacklist_db = SqliteDatabase(path_py + '/' + name_db + '.db', pragmas=(('foreign_keys', 1),))
        database_proxy.initialize(blacklist_db)
        database_proxy.create_tables([Dump, Item, IP, IPResolve, Domain, URL, History], safe=True)
        init_dump_tbl()
        logger.info('Check database: SQLite Ok')

    elif type_db == 1:
        import pymysql

        db = pymysql.connect(host=host, port=port, user=login, passwd=password)
        cursor = db.cursor()
        check_db = "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '" + name_db + "'"
        cursor.execute(check_db)
        db_exist_flag = cursor.fetchone()
        if not db_exist_flag:
            create_db = "CREATE DATABASE IF NOT EXISTS `" + name_db + \
                        "` CHARACTER SET utf8 COLLATE utf8_unicode_ci"
            cursor.execute(create_db)

        cursor.close()
        blacklist_db = MySQLDatabase(name_db, host=host, port=port, user=login, passwd=password)
        database_proxy.initialize(blacklist_db)
        database_proxy.create_tables([Dump, Item, IP, IPResolve, Domain, URL, History], safe=True)
        if not db_exist_flag:
            init_dump_tbl()
        logger.info('Check database: MySQL Ok')

    elif type_db == 2:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

        db = psycopg2.connect(dbname='postgres', host=host, port=port, user=login, password=password)
        db.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = db.cursor()
        check_db = "SELECT datname FROM pg_catalog.pg_database WHERE lower(datname) = lower('" + name_db + "')"
        cursor.execute(check_db)
        db_exist_flag = cursor.fetchone()
        if not db_exist_flag:
            create_db = "CREATE DATABASE " + name_db + " WITH ENCODING = 'UTF8' " \
                                                       "LC_COLLATE = 'ru_RU.UTF-8' " \
                                                       "LC_CTYPE = 'ru_RU.UTF-8'"
            cursor.execute(create_db)
            privileges_set = "GRANT ALL PRIVILEGES ON DATABASE " + name_db + " TO " + login
            cursor.execute(privileges_set)
        cursor.close()
        blacklist_db = PostgresqlDatabase(name_db, host=host, port=port, user=login, password=password)
        database_proxy.initialize(blacklist_db)
        database_proxy.create_tables([Dump, Item, IP, IPResolve, Domain, URL, History], safe=True)
        if not db_exist_flag:
            init_dump_tbl()
        logger.info('Check database: PostgreSQL Ok')

    else:
        logger.info('Wrong type DB. Check configuration.')
        exit()

    return blacklist_db


def init_dump_tbl():
    try:
        Dump.get(Dump.param == 'lastDumpDate')
    except Dump.DoesNotExist:
        Dump.create(param='lastDumpDate', value='1325376000')

    try:
        Dump.get(Dump.param == 'lastDumpDateUrgently')
    except Dump.DoesNotExist:
        Dump.create(param='lastDumpDateUrgently', value='1325376000')

    try:
        Dump.get(Dump.param == 'lastAction')
    except Dump.DoesNotExist:
        Dump.create(param='lastAction', value='getLastDumpDate')

    try:
        Dump.get(Dump.param == 'lastResult')
    except Dump.DoesNotExist:
        Dump.create(param='lastResult', value='default')

    try:
        Dump.get(Dump.param == 'lastCode')
    except Dump.DoesNotExist:
        Dump.create(param='lastCode', value='default')

    try:
        Dump.get(Dump.param == 'dumpFormatVersion')
    except Dump.DoesNotExist:
        Dump.create(param='dumpFormatVersion', value='2.2')

    try:
        Dump.get(Dump.param == 'webServiceVersion')
    except Dump.DoesNotExist:
        Dump.create(param='webServiceVersion', value='3')

    try:
        Dump.get(Dump.param == 'docVersion')
    except Dump.DoesNotExist:
        Dump.create(param='docVersion', value='4')

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'maximus'

from peewee import Proxy, Model, CharField, TextField, DateField, DateTimeField, IntegerField, SqliteDatabase, \
    MySQLDatabase, PostgresqlDatabase, fn, IntegrityError
import os

database_proxy = Proxy()


class Dump(Model):
    param = CharField(primary_key=True, max_length=255, null=False)
    value = TextField(null=False)

    class Meta(object):
        database = database_proxy


class Item(Model):
    content_id = IntegerField(null=False, index=True)
    includeTime = DateTimeField(null=False)
    urgencyType = IntegerField(null=False, default=0)
    entryType = IntegerField(null=False)
    blockType = TextField(null=False, default='default')
    hashRecord = TextField(null=False)
    decision_date = DateField(null=False)
    decision_num = TextField(null=False)
    decision_org = TextField(null=False)
    date_added = DateTimeField(null=False)

    class Meta(object):
        database = database_proxy


class IP(Model):
    item = IntegerField(null=False, index=True)
    ip = TextField(null=False)
    mask = IntegerField(null=False, default=32)
    date_added = DateTimeField(null=False)

    class Meta(object):
        database = database_proxy


class Domain(Model):
    item = IntegerField(null=False, index=True)
    domain = TextField(null=False)
    date_added = DateTimeField(null=False)

    class Meta(object):
        database = database_proxy


class URL(Model):
    item = IntegerField(null=False, index=True)
    url = TextField(null=False)
    date_added = DateTimeField(null=False)

    class Meta(object):
        database = database_proxy


class History(Model):
    requestCode = TextField(null=False)
    date = DateTimeField(null=False)

    class Meta(object):
        database = database_proxy


def init_db(logger, cfg):
    path_py = str(os.path.dirname(os.path.abspath(__file__)))
    login = cfg.User()
    password = cfg.Password()
    host = cfg.Host()
    port = cfg.Port()
    name_db = cfg.Name()
    type_db = int(cfg.Type())
    blacklist_db = None

    if type_db == 0:
        blacklist_db = SqliteDatabase(path_py + '/' + name_db + '.db', threadlocals=True)
        init_dump_tbl()
        logger.info('Check database: SQLite Ok')

    elif type_db == 1:
        import pymysql

        db = pymysql.connect(host=host, port=port, user=login, passwd=password)
        cursor = db.cursor()
        check_db = "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '" + name_db + "'"
        cursor.execute(check_db)
        if not cursor.fetchone():
            create_db = "CREATE DATABASE IF NOT EXISTS `" + name_db + \
                        "` CHARACTER SET utf8 COLLATE utf8_unicode_ci"
            cursor.execute(create_db)
            init_dump_tbl()
        cursor.close()
        blacklist_db = MySQLDatabase(name_db, host=host, port=port, user=login, passwd=password)
        logger.info('Check database: MySQL Ok')

    elif type_db == 2:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

        db = psycopg2.connect(dbname='postgres', host=host, port=port, user=login, password=password)
        db.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = db.cursor()
        check_db = "SELECT datname FROM pg_catalog.pg_database WHERE lower(datname) = lower('" + name_db + "')"
        cursor.execute(check_db)
        if not cursor.fetchone():
            create_db = "CREATE DATABASE " + name_db + " WITH ENCODING = 'UTF8' " \
                                                       "LC_COLLATE = 'ru_RU.UTF-8' " \
                                                       "LC_CTYPE = 'ru_RU.UTF-8'"
            cursor.execute(create_db)
            privileges_set = "GRANT ALL PRIVILEGES ON DATABASE " + name_db + " TO " + login
            cursor.execute(privileges_set)
            init_dump_tbl()
        cursor.close()
        blacklist_db = PostgresqlDatabase(name_db, host=host, port=port, user=login, password=password)
        logger.info('Check database: PostgreSQL Ok')

    else:
        logger.info('Wrong type DB. Check configuration.')
        exit()

    database_proxy.initialize(blacklist_db)
    database_proxy.create_tables([Dump, Item, IP, Domain, URL, History], safe=True)


def init_dump_tbl():
    try:
        Dump.create(param='lastDumpDate', value='1325376000')
    except IntegrityError:
        pass

    try:
        Dump.create(param='lastDumpDateUrgently', value='1325376000')
    except IntegrityError:
        pass

    try:
        Dump.create(param='lastAction', value='getLastDumpDate')
    except IntegrityError:
        pass

    try:
        Dump.create(param='lastResult', value='default')
    except IntegrityError:
        pass

    try:
        Dump.create(param='lastCode', value='default')
    except IntegrityError:
        pass

    try:
        Dump.create(param='dumpFormatVersion', value='2.2')
    except IntegrityError:
        pass

    try:
        Dump.create(param='webServiceVersion', value='3')
    except IntegrityError:
        pass

    try:
        Dump.create(param='docVersion', value='4')
    except IntegrityError:
        pass


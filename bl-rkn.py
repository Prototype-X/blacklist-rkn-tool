#!/usr/bin/env python3
# -*- coding: utf-8 -*-


__author__ = 'Prototype-X'

from xml.etree.ElementTree import ElementTree
from datetime import datetime
import time
import zipfile
from base64 import b64decode
import argparse
import os.path
import logging
import hashlib
import smtplib
from email.mime.text import MIMEText
import subprocess

from peewee import *
import pymysql

from zapretinfo import ZapretInfo
from config import Config

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


def date_time_xml_to_db(date_time_xml):
    date_time_db = date_time_xml.replace('T', ' ')
    return date_time_db


def init_dump_db(logger, cfg):
    path_py = str(os.path.dirname(os.path.abspath(__file__)))
    if cfg.MySQL():
        login = cfg.MySQLUser()
        password = cfg.MySQLPassword()
        host = cfg.MySQLHost()
        port = cfg.MySQLPort()
        db = pymysql.connect(host=host, port=port, user=login, passwd=password)
        cursor = db.cursor()
        check_db = "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '" + cfg.DBName() + "'"
        cursor.execute(check_db)
        if not cursor.fetchone():
            create_db = "CREATE DATABASE IF NOT EXISTS `" + cfg.DBName() + \
                        "` CHARACTER SET utf8 COLLATE utf8_unicode_ci"
            cursor.execute(create_db)
        blacklist_db = MySQLDatabase(cfg.DBName(), host=host, port=port, user=login, passwd=password)
        logger.info('Check database: MySQL Ok')
    else:
        blacklist_db = SqliteDatabase(path_py + '/' + cfg.DBName() + '.db', threadlocals=True)
        logger.info('Check database: SQLite Ok')

    database_proxy.initialize(blacklist_db)
    database_proxy.create_tables([Dump, Item, IP, Domain, URL, History], safe=True)

    try:
        Dump.create(param='lastDumpDate', value='1325376000')
    except IntegrityError:
        pass
        # logger.info('Parameter lastDumpDate already exists.')
    try:
        Dump.create(param='lastDumpDateUrgently', value='1325376000')
    except IntegrityError:
        pass
        # logger.info('Parameter lastDumpDateUrgently already exists.')
    try:
        Dump.create(param='lastAction', value='getLastDumpDate')
    except IntegrityError:
        pass
        # logger.info('Parameter lastAction already exists.')
    try:
        Dump.create(param='lastResult', value='default')
    except IntegrityError:
        pass
        # logger.info('Parameter lastResult already exists.')
    try:
        Dump.create(param='lastCode', value='default')
    except IntegrityError:
        pass
        # logger.info('Parameter lastCode already exists.')
    try:
        Dump.create(param='dumpFormatVersion', value='2.2')
    except IntegrityError:
        pass
        # logger.info('Parameter dumpFormatVersion already exists.')
    try:
        Dump.create(param='webServiceVersion', value='3')
    except IntegrityError:
        pass
        # logger.info('Parameter webServiceVersion already exists.')
    try:
        Dump.create(param='docVersion', value='4')
    except IntegrityError:
        pass
        # logger.info('Parameter docVersion already exists.')
    return True


def check_new_dump(logger, session):
    logger.info('Check if dump.xml has updates since last sync.')
    last_dump = session.getLastDumpDateEx()
    last_date_dump = max(last_dump.lastDumpDate // 1000, last_dump.lastDumpDateUrgently // 1000)
    current_date_dump = max(int(Dump.get(Dump.param == 'lastDumpDate').value),
                            int(Dump.get(Dump.param == 'lastDumpDateUrgently').value))
    logger.info('Current versions: webservice: %s, dump: %s, doc: %s',
                Dump.get(Dump.param == 'webServiceVersion').value,
                Dump.get(Dump.param == 'dumpFormatVersion').value,
                Dump.get(Dump.param == 'docVersion').value)
    if last_dump.webServiceVersion != Dump.get(Dump.param == 'webServiceVersion').value:
        logger.warning('New webservice: %s', last_dump.webServiceVersion)
        Dump.update(value=last_dump.webServiceVersion).where(Dump.param == 'webServiceVersion').execute()
    if last_dump.dumpFormatVersion != Dump.get(Dump.param == 'dumpFormatVersion').value:
        logger.warning('New dumpFormatVersion: %s', last_dump.dumpFormatVersion)
        Dump.update(value=last_dump.dumpFormatVersion).where(Dump.param == 'dumpFormatVersion').execute()
    if last_dump.docVersion != Dump.get(Dump.param == 'docVersion').value:
        logger.warning('New docVersion: %s', last_dump.docVersion)
        Dump.update(value=last_dump.docVersion).where(Dump.param == 'docVersion').execute()
    logger.info('Current date: lastDumpDate: %s, lastDumpDateUrgently: %s',
                datetime.fromtimestamp(int(Dump.get(Dump.param == 'lastDumpDate').value))
                .strftime('%Y-%m-%d %H:%M:%S'),
                datetime.fromtimestamp(int(Dump.get(Dump.param == 'lastDumpDateUrgently').value))
                .strftime('%Y-%m-%d %H:%M:%S'))
    logger.info('Last date: lastDumpDate: %s, lastDumpDateUrgently: %s',
                datetime.fromtimestamp(int(last_dump.lastDumpDate // 1000)).strftime('%Y-%m-%d %H:%M:%S'),
                datetime.fromtimestamp(int(last_dump.lastDumpDateUrgently // 1000)).strftime('%Y-%m-%d %H:%M:%S'))
    if last_date_dump != current_date_dump:
        logger.info('New dump is available.')
        # Dump.update(value=last_dump.lastDumpDate // 1000).where(Dump.param == 'lastDumpDate').execute()
        # Dump.update(value=last_dump.lastDumpDateUrgently // 1000) \
        #     .where(Dump.param == 'lastDumpDateUrgently').execute()
        Dump.update(value='getLastDumpDate').where(Dump.param == 'lastAction').execute()
        Dump.update(value='NewDump').where(Dump.param == 'lastResult').execute()
        return True
    else:
        logger.info('Dump date without changes.')
        Dump.update(value='getLastDumpDate').where(Dump.param == 'lastAction').execute()
        Dump.update(value='lastDump').where(Dump.param == 'lastResult').execute()
        return False


def send_request(logger, session, xml_file, p7s_file, version='2.1'):
    logger.info('Sending request.')
    request = session.sendRequest(xml_file, p7s_file, version)
    logger.info('Checking request status.')
    if request['result']:
        code = request['code']
        logger.info('Got code %s', code)
        Dump.update(value=code).where(Dump.param == 'lastCode').execute()
        Dump.update(value='sendRequest').where(Dump.param == 'lastAction').execute()
        Dump.update(value='Code').where(Dump.param == 'lastResult').execute()
        logger.info('Save code in History')
        History.create(requestCode=code, date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return code
    else:
        Dump.update(value='sendRequest').where(Dump.param == 'lastAction').execute()
        Dump.update(value='Error').where(Dump.param == 'lastResult').execute()
        logger.error(request['resultComment'])
        return False


def get_request(logger, session, code, cfg):
    path_py = str(os.path.dirname(os.path.abspath(__file__)))
    logger.info('Waiting for a 90 sec.')
    time.sleep(90)
    logger.info('Trying to get result...')
    request = session.getResult(code)
    Dump.update(value='getRequest').where(Dump.param == 'lastAction').execute()
    max_count = cfg.GetResultMaxCount()
    for count in range(1, max_count + 1):
        if request['result']:
            logger.info('Got a dump ver. %s for the %s (INN %s)',
                        request['dumpFormatVersion'],
                        request['operatorName'],
                        request['inn'])
            with open(path_py + '/result.zip', "wb") as f:
                f.write(b64decode(request['registerZipArchive']))
            logger.info('Downloaded dump %d bytes, MD5 hashsum: %s',
                        os.path.getsize(path_py + '/result.zip'),
                        hashlib.md5(open(path_py + '/result.zip', 'rb')
                                    .read()).hexdigest())
            try:
                logger.info('Unpacking.')
                zip_file = zipfile.ZipFile(path_py + '/result.zip', 'r')
                zip_file.extract('dump.xml', path_py + '/')
                if cfg.DumpFileSave():
                    zip_file.extractall(path_py + '/dumps/%s' % datetime.now().strftime("%Y-%m-%d %H-%M-%S"))
                zip_file.close()
            except zipfile.BadZipfile:
                logger.error('Wrong file format.')
                Dump.update(value='Error').where(Dump.param == 'lastResult').execute()
                return False
            Dump.update(value='Ok').where(Dump.param == 'lastResult').execute()
            return True
        else:
            if not request['resultCode']:
                logger.info('Not ready yet. Waiting for a minute. Attempt number %s', count)
                time.sleep(60)
            else:
                logger.error('Got an error, code %d: %s',
                             request['resultCode'],
                             request['resultComment'])
                Dump.update(value='Error').where(Dump.param == 'lastResult').execute()
                return False
    logger.info('Cant get result.')
    return False


def parse_dump(logger):
    path_py = str(os.path.dirname(os.path.abspath(__file__)))
    if os.path.exists(path_py + '/dump.xml'):
        logger.info('dump.xml already exists.')
        tree_xml = ElementTree().parse(path_py + '/dump.xml')

        dt = datetime.strptime(tree_xml.attrib['updateTime'][:19], '%Y-%m-%dT%H:%M:%S')
        update_time = int(time.mktime(dt.timetuple()))
        Dump.update(value=update_time).where(Dump.param == 'lastDumpDate').execute()
        logger.info('Got updateTime: %s.', update_time)

        dt = datetime.strptime(tree_xml.attrib['updateTimeUrgently'][:19], '%Y-%m-%dT%H:%M:%S')
        update_time_urgently = int(time.mktime(dt.timetuple()))
        Dump.update(value=update_time_urgently).where(Dump.param == 'lastDumpDateUrgently').execute()
        logger.info('Got updateTimeUrgently: %s.', update_time_urgently)

        list_xml = tree_xml.findall(".//*[@id]")
        id_set_dump = set()
        id_set_db = set()
        for content_xml in list_xml:
            # print(content_xml.tag, content_xml.attrib, content_xml.text)
            id_set_dump.add(int(content_xml.attrib['id']))

        select_content_id_db = Item.select(Item.content_id)
        for content_db in select_content_id_db:
            id_set_db.add(content_db.content_id)

        common_id_set = id_set_dump.intersection(id_set_db)
        delete_id_set = id_set_db.difference(common_id_set)
        add_id_set = id_set_dump.difference(common_id_set)
        # print(delete_id_set)
        # print(add_id_set)

        url_inform_del_set = set()
        ip_inform_del_set = set()
        sub_ip_inform_del_set = set()
        domain_inform_del_set = set()
        id_inform_del_set = set()

        url_inform_add_set = set()
        ip_inform_add_set = set()
        sub_ip_inform_add_set = set()
        domain_inform_add_set = set()
        id_inform_add_set = set()

        if len(delete_id_set) > 0:
            for del_item in delete_id_set:
                logger.info('Full delete Item, IP, Domain, URL id: %s.', del_item)

                id_inform_del_set.add(del_item)
                url_del_sql = URL.select().where(URL.item == del_item)
                for url_del_txt in url_del_sql:
                    url_inform_del_set.add(url_del_txt.url)
                ip_del_sql = IP.select().where(IP.item == del_item)
                for ip_del_txt in ip_del_sql:
                    ip_inform_del_set.add(ip_del_txt.ip)
                for sub_ip_del_txt in ip_del_sql:
                    if sub_ip_del_txt.mask < 32:
                        sub_ip_inform_del_set.add(sub_ip_del_txt.ip + '/' + str(sub_ip_del_txt.mask))
                domain_del_sql = Domain.select().where(Domain.item == del_item)
                for domain_del_txt in domain_del_sql:
                    domain_inform_del_set.add(domain_del_txt.domain)

                Domain.delete().where(Domain.item == del_item).execute()
                URL.delete().where(URL.item == del_item).execute()
                IP.delete().where(IP.item == del_item).execute()
                Item.delete().where(Item.content_id == del_item).execute()

        if len(add_id_set) > 0:
            include_time = str()
            urgency_type = int()
            entry_type = int()
            block_type = str()
            hash_value = str()
            for new_item in add_id_set:
                logger.info('New Item, IP, Domain, URL id: %s.', new_item)
                id_inform_add_set.add(new_item)
                new_item_xml = tree_xml.find(".//*[@id='" + str(new_item) + "']")
                for data_xml in new_item_xml.iter():
                    if data_xml.tag == 'content':
                        content_id = int(data_xml.attrib['id'])
                        try:
                            urgency_type = int(data_xml.attrib['urgencyType'])
                        except KeyError:
                            urgency_type = 0
                        include_time = date_time_xml_to_db(data_xml.attrib['includeTime'])
                        try:
                            block_type = data_xml.attrib['blockType']
                        except KeyError:
                            block_type = 'default'
                        entry_type = int(data_xml.attrib['entryType'])
                        hash_value = data_xml.attrib['hash']
                    if data_xml.tag == 'decision':
                        decision_date = data_xml.attrib['date']
                        decision_number = data_xml.attrib['number']
                        decision_org = data_xml.attrib['org']
                        Item.create(content_id=content_id, includeTime=include_time, urgencyType=urgency_type,
                                    entryType=entry_type, blockType=block_type, hashRecord=hash_value,
                                    decision_date=decision_date, decision_num=decision_number,
                                    decision_org=decision_org, date_added=datetime.now().strftime("%Y-%m-%d %H-%M-%S"))
                    if data_xml.tag == 'url':
                        url = data_xml.text
                        url_inform_add_set.add(url)
                        URL.create(item=content_id, url=url, date_added=datetime.now().strftime("%Y-%m-%d %H-%M-%S"))
                    if data_xml.tag == 'domain':
                        domain = data_xml.text
                        domain_inform_add_set.add(domain)
                        Domain.create(item=content_id, domain=domain,
                                      date_added=datetime.now().strftime("%Y-%m-%d %H-%M-%S"))
                    if data_xml.tag == 'ip':
                        ip = data_xml.text
                        ip_inform_add_set.add(ip)
                        IP.create(item=content_id, ip=ip, date_added=datetime.now().strftime("%Y-%m-%d %H-%M-%S"))
                    if data_xml.tag == 'ipSubnet':
                        net = data_xml.text.split('/')
                        sub_ip_inform_add_set.add(data_xml.text)
                        ip = net[0]
                        mask = net[1]
                        IP.create(item=content_id, ip=ip, mask=mask,
                                  date_added=datetime.now().strftime("%Y-%m-%d %H-%M-%S"))

        url_db_set = set()
        url_xml_set = set()
        ip_db_set = set()
        ip_xml_set = set()
        sub_ip_xml_set = set()
        sub_ip_db_set = set()
        domain_db_set = set()
        domain_xml_set = set()
        data_update = False
        for item_xml in list_xml:
            for data_xml in item_xml.iter():
                # print(data_xml.tag, data_xml.attrib, data_xml.text)
                if data_xml.tag == 'content':
                    content_id = int(data_xml.attrib['id'])
                    hash_value = data_xml.attrib['hash']
                    item_db = Item.get(Item.content_id == content_id)

                    if hash_value != item_db.hashRecord:
                        logger.info('Hashes not equal, update hash id: %s', content_id)
                        try:
                            urgency_type = int(data_xml.attrib['urgencyType'])
                        except KeyError:
                            urgency_type = 0
                        include_time = date_time_xml_to_db(data_xml.attrib['includeTime'])
                        try:
                            block_type = data_xml.attrib['blockType']
                        except KeyError:
                            block_type = 'default'
                        entry_type = int(data_xml.attrib['entryType'])

                        Item.update(hashRecord=hash_value).where(Item.content_id == content_id).execute()
                        data_update = True
                    else:
                        data_update = False
                        break

                if data_xml.tag == 'decision':
                    decision_date = data_xml.attrib['date']
                    decision_number = data_xml.attrib['number']
                    decision_org = data_xml.attrib['org']
                    # print(item_db)
                    if str(item_db.includeTime) != include_time:
                        logger.info('content_id: %s.', content_id)
                        logger.info('XML includeTime: %s.', include_time)
                        logger.info('DB includeTime: %s.', item_db.includeTime)
                        Item.update(includeTime=include_time).where(Item.content_id == content_id).execute()
                    if item_db.urgencyType != urgency_type:
                        logger.info('content_id: %s.', content_id)
                        logger.info('XML urgencyType: %s.', urgency_type)
                        logger.info('DB urgencyType: %s.', item_db.urgencyType)
                        Item.update(urgencyType=urgency_type).where(Item.content_id == content_id).execute()
                    if item_db.blockType != block_type:
                        logger.info('content_id: %s.', content_id)
                        logger.info('XML blockType: %s.', block_type)
                        logger.info('DB blockType: %s.', item_db.blockType)
                        Item.update(blockType=block_type).where(Item.content_id == content_id).execute()
                    if item_db.entryType != entry_type:
                        logger.info('content_id: %s.', content_id)
                        logger.info('XML entryType: %s.', entry_type)
                        logger.info('DB entryType: %s.', item_db.entryType)
                        Item.update(entryType=entry_type).where(Item.content_id == content_id).execute()
                    if str(item_db.decision_date) != decision_date:
                        logger.info('content_id: %s.', content_id)
                        logger.info('XML date: %s.', decision_date)
                        logger.info('DB date: %s.', str(item_db.decision_date))
                        Item.update(decision_date=decision_date).where(Item.content_id == content_id).execute()
                    if item_db.decision_num != decision_number:
                        logger.info('content_id: %s.', content_id)
                        logger.info('XML number: %s.', decision_number)
                        logger.info('DB number: %s.', item_db.decision_num)
                        Item.update(decision_numbe=decision_number).where(Item.content_id == content_id).execute()
                    if item_db.decision_org != decision_org:
                        logger.info('content_id: %s.', content_id)
                        logger.info('XML org: %s.', decision_org)
                        logger.info('DB org: %s.', item_db.decision_org)
                        Item.update(decision_org=decision_org).where(Item.content_id == content_id).execute()

                if data_xml.tag == 'url':
                    url_xml_set.add(data_xml.text)

                if data_xml.tag == 'domain':
                    domain_xml_set.add(data_xml.text)

                if data_xml.tag == 'ip':
                    ip_xml_set.add(data_xml.text)

                if data_xml.tag == 'ipSubnet':
                    sub_ip_xml_set.add(data_xml.text)

            if data_update:
                url_db = URL.select().where(URL.item == content_id)

                for url_item in url_db:
                    url_db_set.add(url_item.url)
                if url_db_set != url_xml_set:
                    common_url_set = url_xml_set.intersection(url_db_set)
                    delete_url_set = url_db_set.difference(common_url_set)
                    add_url_set = url_xml_set.difference(common_url_set)
                    if len(delete_url_set) > 0:
                        logger.info('Delete id %s URL: %s', content_id, delete_url_set)
                        url_inform_del_set.update(delete_url_set)
                        for delete_url in delete_url_set:
                            URL.delete().where(URL.url == delete_url).execute()
                    if len(add_url_set) > 0:
                        logger.info('Add id %s URL: %s', content_id, add_url_set)
                        url_inform_add_set.update(add_url_set)
                        for add_url in add_url_set:
                            URL.create(item=content_id, url=add_url,
                                       date_added=datetime.now().strftime("%Y-%m-%d %H-%M-%S"))
                url_db_set.clear()
                url_xml_set.clear()

                domain_db = Domain.select().where(Domain.item == content_id)

                for domain_item in domain_db:
                    domain_db_set.add(domain_item.domain)
                if domain_db_set != domain_xml_set:
                    common_domain_set = domain_xml_set.intersection(domain_db_set)
                    delete_domain_set = domain_db_set.difference(common_domain_set)
                    add_domain_set = domain_xml_set.difference(common_domain_set)
                    if len(delete_domain_set) > 0:
                        logger.info('Delete id %s Domain: %s', content_id, delete_domain_set)
                        domain_inform_del_set.update(delete_domain_set)
                        for delete_domain in delete_domain_set:
                            Domain.delete().where(Domain.domain == delete_domain).execute()
                    if len(add_domain_set) > 0:
                        logger.info('Add id %s Domain: %s', content_id, add_domain_set)
                        domain_inform_add_set.update(add_domain_set)
                        for add_domain in add_domain_set:
                            Domain.create(item=content_id, domain=add_domain,
                                          date_added=datetime.now().strftime("%Y-%m-%d %H-%M-%S"))
                domain_db_set.clear()
                domain_xml_set.clear()

                ip_db = IP.select().where(IP.item == content_id, IP.mask == 32)

                for ip_item in ip_db:
                    ip_db_set.add(ip_item.ip)
                if ip_db_set != ip_xml_set:
                    common_ip_set = ip_xml_set.intersection(ip_db_set)
                    delete_ip_set = ip_db_set.difference(common_ip_set)
                    add_ip_set = ip_xml_set.difference(common_ip_set)
                    if len(delete_ip_set) > 0:
                        logger.info('Delete id %s ip: %s', content_id, delete_ip_set)
                        ip_inform_del_set.update(delete_ip_set)
                        for delete_ip in delete_ip_set:
                            IP.delete().where(IP.ip == delete_ip).execute()
                    if len(add_ip_set) > 0:
                        logger.info('Add id %s ip: %s', content_id, add_ip_set)
                        ip_inform_add_set.update(add_ip_set)
                        for add_ip in add_ip_set:
                            IP.create(item=content_id, ip=add_ip,
                                      date_added=datetime.now().strftime("%Y-%m-%d %H-%M-%S"))
                ip_db_set.clear()
                ip_xml_set.clear()

                sub_ip_db = IP.select().where(IP.item == content_id, IP.mask < 32)

                for sub_ip_item in sub_ip_db:
                    sub_ip_db_set.add(str(sub_ip_item.ip) + '/' + str(sub_ip_item.mask))
                if sub_ip_db_set != sub_ip_xml_set:
                    common_sub_ip_set = sub_ip_xml_set.intersection(sub_ip_db_set)
                    delete_sub_ip_set = sub_ip_db_set.difference(common_sub_ip_set)
                    add_sub_ip_set = sub_ip_xml_set.difference(common_sub_ip_set)
                    if len(delete_sub_ip_set) > 0:
                        logger.info('Delete id %s subnet: %s', content_id, delete_sub_ip_set)
                        sub_ip_inform_del_set.update(delete_sub_ip_set)
                        for delete_sub_ip in delete_sub_ip_set:
                            del_subnet = str(delete_sub_ip).split('/')
                            del_ip = del_subnet[0]
                            del_mask = del_subnet[1]
                            IP.delete().where(IP.ip == del_ip, IP.mask == del_mask).execute()
                    if len(add_sub_ip_set) > 0:
                        logger.info('Add id %s subnet: %s', content_id, add_sub_ip_set)
                        sub_ip_inform_add_set.update(add_sub_ip_set)
                        for add_sub_ip in add_sub_ip_set:
                            add_subnet = str(add_sub_ip).split('/')
                            add_ip = add_subnet[0]
                            add_mask = add_subnet[1]
                            IP.create(item=content_id, ip=add_ip, mask=add_mask,
                                      date_added=datetime.now().strftime("%Y-%m-%d %H-%M-%S"))
                sub_ip_db_set.clear()
                sub_ip_xml_set.clear()

        if len(url_inform_del_set) == 0 and len(ip_inform_del_set) == 0 and len(domain_inform_del_set) == 0 and \
                len(id_inform_del_set) == 0 and len(sub_ip_inform_del_set) == 0 and len(url_inform_add_set) == 0 and \
                len(ip_inform_add_set) == 0 and len(domain_inform_add_set) == 0 and len(id_inform_add_set) == 0 and \
                len(sub_ip_inform_add_set) == 0:
            return 2, str()

        report_data = {'url_del': url_inform_del_set, 'ip_del': ip_inform_del_set, 'domain_del': domain_inform_del_set,
                       'id_del': id_inform_del_set, 'sub_ip_del': sub_ip_inform_del_set, 'url_add': url_inform_add_set,
                       'ip_add': ip_inform_add_set, 'domain_add': domain_inform_add_set, 'id_add': id_inform_add_set,
                       'sub_ip_add': sub_ip_inform_add_set}
        msg = gen_report(**report_data)
        # print(msg)
        return 1, msg
    else:
        return 0, str()


def gen_report(**data):
    domain_count = Domain.select(fn.Count(fn.Distinct(Domain.domain))).scalar()
    url_count = URL.select(fn.Count(fn.Distinct(URL.url))).scalar()
    ip_count = IP.select(fn.Count(fn.Distinct(IP.ip))).scalar()
    id_count = Item.select(fn.Count(fn.Distinct(Item.content_id))).scalar()

    date_time = datetime.fromtimestamp(int(Dump.get(Dump.param == 'lastDumpDate')
                                           .value)).strftime('%Y-%m-%d %H:%M:%S')

    message = 'vigruzki.rkn.gov.ru update: ' + date_time + '\n'

    url_inform_add = data.get('url_add')
    if len(url_inform_add) > 0:
        message += '\nURLs added: \n\n'
        for url_a in url_inform_add:
            message += url_a + '\n'

    ip_inform_add = data.get('ip_add')
    if len(ip_inform_add) > 0:
        message += '\nIPs added: \n\n'
        for ip_a in ip_inform_add:
            message += ip_a + '\n'

    sub_ip_inform_add = data.get('sub_ip_add')
    if len(sub_ip_inform_add) > 0:
        message += '\nSUBNETs added: \n\n'
        for sub_ip_a in sub_ip_inform_add:
            message += sub_ip_a + '\n'

    domain_inform_add = data.get('domain_add')
    if len(domain_inform_add) > 0:
        message += '\nDOMAINs added: \n\n'
        for domain_a in domain_inform_add:
            message += domain_a + '\n'

    url_inform_del = data.get('url_del')
    if len(url_inform_del) > 0:
        message += '\nURLs deleted: \n\n'
        for url_d in url_inform_del:
            message += url_d + '\n'

    ip_inform_del = data.get('ip_del')
    if len(ip_inform_del) > 0:
        message += '\nIPs deleted: \n\n'
        for ip_d in ip_inform_del:
            message += ip_d + '\n'

    sub_ip_inform_del = data.get('sub_ip_del')
    if len(sub_ip_inform_del) > 0:
        message += '\nSUBNETs deleted: \n\n'
        for sub_ip_d in sub_ip_inform_del:
            message += sub_ip_d + '\n'

    domain_inform_del = data.get('domain_del')
    if len(domain_inform_del) > 0:
        message += '\nDOMAINs deleted: \n\n'
        for domain_d in domain_inform_del:
            message += domain_d + '\n'

    message += '\nURLs count: ' + str(url_count) + '\n'
    message += 'IPs count: ' + str(ip_count) + '\n'
    message += 'DOMAINs count: ' + str(domain_count) + '\n'
    message += 'Item count: ' + str(id_count) + '\n'

    id_inform_add = data.get('id_add')
    if len(id_inform_add) > 0:
        message += 'Items added: ' + str(len(id_inform_add)) + '\n'

    id_inform_del = data.get('id_del')
    if len(id_inform_del) > 0:
        message += 'Items deleted: ' + str(len(id_inform_del)) + '\n'

    return message


def gen_request(logger, cfg):
    logger.info('Generate request file %s', cfg.XMLPathFName())
    dt = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    request_xml = '<?xml version="1.0" encoding="windows-1251"?>\n'
    request_xml += '<request>\n'
    request_xml += '<requestTime>' + dt + '.000+04:00</requestTime>\n'
    request_xml += '<operatorName>' + cfg.OperatorName() + '</operatorName>\n'
    request_xml += '<inn>' + str(cfg.inn()) + '</inn>\n'
    request_xml += '<ogrn>' + str(cfg.ogrn()) + '</ogrn>\n'
    request_xml += '<email>' + cfg.email() + '</email>\n'
    request_xml += '</request>'
    with open(cfg.XMLPathFName(), 'wb') as f:
        f.write(request_xml.encode(encoding='cp1251'))
    return True


def sign_request(logger, cfg):
    logger.info('Sign file %s', cfg.XMLPathFName())
    subprocess.call("sudo openssl smime -engine pkcs11_gost -sign -in " + cfg.XMLPathFName() + " -out " +
                    cfg.P7SPathFName() + " -outform der -noverify -binary -signer " + cfg.PEMPathFName() +
                    " -inkey " + cfg.ID() + " -keyform engine", shell=True)
    return True


def notify(logger, message, cfg):
    from_address = cfg.FromMail()
    to_address = cfg.ToMail()
    msg = MIMEText(message)
    msg['Subject'] = 'vigruzki.rkn.gov.ru ver. 2.2 update'
    msg['From'] = from_address
    msg['To'] = to_address
    # Send the message via local SMTP server.
    logger.info('Send email from %s to %s', from_address, to_address)
    logger.info('%s', message)
    server = smtplib.SMTP()
    server.connect()
    server.sendmail(from_address, to_address, msg.as_string())
    server.quit()
    return True


def domain_show():
    domain_sql = Domain.select()
    domain_set = set()
    for domain_row in domain_sql:
        domain_set.add(domain_row.domain)

    for domain in domain_set:
        print(domain)
    return True


def ip_show():
    ip_sql = IP.select()
    ip_set = set()
    for ip_row in ip_sql:
        if ip_row.mask < 32:
            ip_set.add(ip_row.ip + '/' + str(ip_row.mask))
        else:
            ip_set.add(ip_row.ip)

    for ip in ip_set:
        print(ip)
    return True


def url_show():
    url_set = set()
    url_sql = URL.select()
    for url_row in url_sql:
        url_set.add(url_row.url)

    item_sql = Item.select()
    for item_row in item_sql:
        if item_row.blockType == 'domain':
            url_set.add('http://' + Domain.get(Domain.item == item_row.content_id).domain)

    for url in url_set:
        print(url)
    return True


def history_show():
    history_sql = History.select()
    for history_row in history_sql:
        print(history_row.date, history_row.requestCode)
    return True


def main():
    parser = argparse.ArgumentParser(add_help=True,
                                     description='Tool for list of restricted websites http://vigruzki.rkn.gov.ru/')
    parser.add_argument("--url", action="store_true", required=False, default=False, help="url list show")
    parser.add_argument("--ip", action="store_true", required=False, default=False, help="ip list show")
    parser.add_argument("--domain", action="store_true", required=False, default=False, help="domain list show")
    parser.add_argument("--history", action="store_true", required=False, default=False, help="history list show")
    parser.add_argument("-v", "--version", action='version', version='version 1.1', help="show version")
    args = parser.parse_args()

    ip_print = args.ip
    url_print = args.url
    domain_print = args.domain
    history_print = args.history

    cfg = Config()

    if cfg.LogRewrite():
        filemode = 'w'
    else:
        filemode = 'a'

    logging.basicConfig(filename=cfg.LogPathFName(), filemode=filemode,
                        format=u'%(asctime)s  %(message)s', level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info('Starting script.')

    init_dump_db(logger, cfg)

    if ip_print:
        ip_show()
    elif url_print:
        url_show()
    elif domain_print:
        domain_show()
    elif history_print:
        history_show()
    else:
        session = ZapretInfo()
        if check_new_dump(logger, session):
            if cfg.GenRequest():
                gen_request(logger, cfg)
                sign_request(logger, cfg)
            code = send_request(logger, session, cfg.XMLPathFName(), cfg.P7SPathFName(), '2.2')
            if code:
                if get_request(logger, session, code, cfg):
                    result_bool, message = parse_dump(logger)
                    if result_bool == 1:
                        if cfg.Notify():
                            notify(logger, message, cfg)
                    elif result_bool == 2:
                        logger.info('No updates')
                    elif result_bool == 0:
                        if cfg.Notify():
                            message = 'Houston, we have a problem'
                            notify(logger, message, cfg)
                        logger.info('parse_dump error')
    logger.info('Script stopped.')
    # todo parse_dump() добавить состояние
    # todo оповещение по почте при изменении dumpFormatVersion, webServiceVersion, docVersion
    # todo HistoryCount функционал
    # todo DumpPath добавить новую опцию путь хранения дампов
    # todo поиск в базе + аргументы командной строки
    # todo обработка исключений и прочих нестандартных ситуации
    # todo больше объектов: ZapretInfo, Config, Dump
    # todo venv
    # todo создать пакет pypi
    # todo openssl path добавить параметр
    # todo отправка почты с аутентификацией и ssl, tls
    # todo сделать вывод последних изменений ip, url, domain


if __name__ == '__main__':
    main()

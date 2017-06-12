#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'maximus'

from lxml.etree import ElementTree
from datetime import datetime
import time
import zipfile
from base64 import b64decode
import os.path
import logging
import hashlib
import re
import urllib
from peewee import fn
from db import Dump, Item, IP, Domain, URL, History
from zapretinfo import ZapretInfo

logger = logging.getLogger(__name__)


class Core(object):
    def __init__(self, transact, cfg):
        self.path_py = str(os.path.dirname(os.path.abspath(__file__)))
        self.transact = transact
        self.session = ZapretInfo()
        self.update_dump = self.session.getLastDumpDateEx()
        self.cfg = cfg
        self.code = None
        self.code_id = None

    @staticmethod
    def date_time_xml_to_db(date_time_xml):
        date_time_db = date_time_xml.replace('T', ' ')
        return date_time_db

    def check_service_upd(self):
        msg = ''

        logger.info('Current versions: webservice: %s, dump: %s, doc: %s',
                    Dump.get(Dump.param == 'webServiceVersion').value,
                    Dump.get(Dump.param == 'dumpFormatVersion').value,
                    Dump.get(Dump.param == 'docVersion').value)
        if self.update_dump.webServiceVersion != Dump.get(Dump.param == 'webServiceVersion').value:
            logger.warning('New webservice: %s', self.update_dump.webServiceVersion)
            msg = msg + 'Current webservice:' + Dump.get(Dump.param == 'webServiceVersion').value + \
                        '\nNew webservice: ' + self.update_dump.webServiceVersion + '\n\n'
            Dump.update(value=self.update_dump.webServiceVersion).where(Dump.param == 'webServiceVersion').execute()

        if self.update_dump.dumpFormatVersion != Dump.get(Dump.param == 'dumpFormatVersion').value:
            logger.warning('New dumpFormatVersion: %s', self.update_dump.dumpFormatVersion)
            msg = msg + 'Current dumpFormatVersion: ' + Dump.get(Dump.param == 'dumpFormatVersion').value + \
                        '\nNew dumpFormatVersion: ' + self.update_dump.dumpFormatVersion + '\n\n'
            Dump.update(value=self.update_dump.dumpFormatVersion).where(Dump.param == 'dumpFormatVersion').execute()

        if self.update_dump.docVersion != Dump.get(Dump.param == 'docVersion').value:
            logger.warning('New docVersion: %s', self.update_dump.docVersion)
            msg = msg + 'Current docVersion: ' + Dump.get(Dump.param == 'docVersion').value + '\nNew docVersion: ' + \
                        self.update_dump.docVersion + '\n\n'
            Dump.update(value=self.update_dump.docVersion).where(Dump.param == 'docVersion').execute()
        # print(msg)
        return msg

    def check_new_dump(self):
        logger.info('Check if dump.xml has updates since last sync.')

        if self.cfg.lastDumpDateUrgently() and not self.cfg.lastDumpDate():
            last_date_dump = self.update_dump.lastDumpDateUrgently // 1000
            current_date_dump = int(Dump.get(Dump.param == 'lastDumpDateUrgently').value)

        elif self.cfg.lastDumpDate() and not self.cfg.lastDumpDateUrgently():
            last_date_dump = self.update_dump.lastDumpDate // 1000
            current_date_dump = int(Dump.get(Dump.param == 'lastDumpDate').value)
        else:
            last_date_dump = max(self.update_dump.lastDumpDate // 1000, self.update_dump.lastDumpDateUrgently // 1000)
            current_date_dump = max(int(Dump.get(Dump.param == 'lastDumpDate').value),
                                    int(Dump.get(Dump.param == 'lastDumpDateUrgently').value))

        logger.info('Current date: lastDumpDate: %s, lastDumpDateUrgently: %s',
                    datetime.fromtimestamp(int(Dump.get(Dump.param == 'lastDumpDate').value))
                    .strftime('%Y-%m-%d %H:%M:%S'),
                    datetime.fromtimestamp(int(Dump.get(Dump.param == 'lastDumpDateUrgently').value))
                    .strftime('%Y-%m-%d %H:%M:%S'))
        logger.info('Last date: lastDumpDate: %s, lastDumpDateUrgently: %s',
                    datetime.fromtimestamp(int(self.update_dump.lastDumpDate // 1000)).strftime('%Y-%m-%d %H:%M:%S'),
                    datetime.fromtimestamp(int(self.update_dump.lastDumpDateUrgently // 1000))
                    .strftime('%Y-%m-%d %H:%M:%S'))
        if last_date_dump != current_date_dump or Dump.get(Dump.param == 'lastResult').value == 'Error':
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

    def send_request(self):
        logger.info('Sending request.')
        request = self.session.sendRequest(self.cfg.XMLPathFName(), self.cfg.P7SPathFName())
        logger.info('Checking request status.')
        if request['result']:
            self.code = request['code']
            logger.info('Got code %s', self.code)
            Dump.update(value=self.code).where(Dump.param == 'lastCode').execute()
            Dump.update(value='sendRequest').where(Dump.param == 'lastAction').execute()
            Dump.update(value='Code').where(Dump.param == 'lastResult').execute()
            logger.info('Save code in History')
            History.create(requestCode=self.code, date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            self.code_id = History.get(History.requestCode == self.code).id
            return self.code
        else:
            Dump.update(value='sendRequest').where(Dump.param == 'lastAction').execute()
            Dump.update(value='Error').where(Dump.param == 'lastResult').execute()
            logger.error(request['resultComment'])
            return False

    def get_request(self):
        path_py = str(os.path.dirname(os.path.abspath(__file__)))
        logger.info('Waiting for a 90 sec.')
        time.sleep(90)
        logger.info('Trying to get result...')
        Dump.update(value='getRequest').where(Dump.param == 'lastAction').execute()
        max_count = self.cfg.GetResultMaxCount()
        for count in range(1, max_count + 1):
            request = self.session.getResult(self.code)
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
                    if self.cfg.DumpFileSave():
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
        Dump.update(value='Error').where(Dump.param == 'lastResult').execute()
        # History.update(dump=False).where(History.id == self.code_id).execute()
        logger.info('Cant get result.')
        return False

    def parse_dump(self):
        if not os.path.exists(self.path_py + '/dump.xml'):
            logger.info('dump.xml not found: s%', self.path_py + '/dump.xml')
            return 0
        logger.info('dump.xml already exists.')
        tree_xml = ElementTree().parse(self.path_py + '/dump.xml')

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

        select_content_id_db = Item.select(Item.content_id).where(Item.purge >> None)
        for content_db in select_content_id_db:
            id_set_db.add(content_db.content_id)

        common_id_set = id_set_dump.intersection(id_set_db)
        delete_id_set = id_set_db.difference(common_id_set)
        add_id_set = id_set_dump.difference(common_id_set)
        # print(delete_id_set)
        # print(add_id_set)

        if len(delete_id_set) > 0:
            with self.transact.atomic():
                for del_item in delete_id_set:
                    logger.info('Full delete Item, IP, Domain, URL id: %s.', del_item)

                    Item.update(purge=self.code_id).where(Item.content_id == del_item, Item.purge >> None).execute()
                    Domain.update(purge=self.code_id).where(Domain.content_id == del_item,
                                                            Domain.purge >> None).execute()
                    URL.update(purge=self.code_id).where(URL.content_id == del_item, URL.purge >> None).execute()
                    IP.update(purge=self.code_id).where(IP.content_id == del_item, IP.purge >> None).execute()

        if len(add_id_set) > 0:
            include_time = str()
            urgency_type = int()
            entry_type = int()
            block_type = str()
            hash_value = str()
            with self.transact.atomic():
                for new_item in add_id_set:
                    logger.info('New Item, IP, Domain, URL id: %s.', new_item)
                    new_item_xml = tree_xml.find(".//content[@id='" + str(new_item) + "']")
                    for data_xml in new_item_xml.iter():
                        if data_xml.tag == 'content':
                            content_id = int(data_xml.attrib['id'])
                            try:
                                urgency_type = int(data_xml.attrib['urgencyType'])
                            except KeyError:
                                urgency_type = 0
                            include_time = self.date_time_xml_to_db(data_xml.attrib['includeTime'])
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
                            item_new = Item(content_id=content_id, includeTime=include_time,
                                            urgencyType=urgency_type, entryType=entry_type, blockType=block_type,
                                            hashRecord=hash_value, decision_date=decision_date,
                                            decision_num=decision_number, decision_org=decision_org,
                                            add=self.code_id)
                            item_new.save()
                        if data_xml.tag == 'url':
                            if not self.only_ascii(data_xml.text):
                                url_split = str(data_xml.text).split(':')
                                url = url_split[0] + ':' + urllib.parse.quote(url_split[1])
                            else:
                                url = data_xml.text
                            URL.create(item=item_new.id, content_id=content_id, url=url, add=self.code_id)
                        if data_xml.tag == 'domain':
                            if not self.only_ascii(data_xml.text):
                                domain = (str(data_xml.text).encode('idna')).decode()
                            else:
                                domain = data_xml.text
                            Domain.create(item=item_new.id, content_id=content_id, domain=domain, add=self.code_id)
                        if data_xml.tag == 'ip':
                            ip = data_xml.text
                            IP.create(item=item_new.id, content_id=content_id, ip=ip, add=self.code_id)
                        if data_xml.tag == 'ipSubnet':
                            net = data_xml.text.split('/')
                            ip = net[0]
                            mask = net[1]
                            IP.create(item=item_new.id, content_id=content_id, ip=ip, mask=mask, add=self.code_id)

        url_db_set = set()
        url_xml_set = set()
        ip_db_set = set()
        ip_xml_set = set()
        sub_ip_xml_set = set()
        sub_ip_db_set = set()
        domain_db_set = set()
        domain_xml_set = set()
        data_update = False
        with self.transact.atomic():
            for item_xml in list_xml:
                for data_xml in item_xml.iter():
                    # print(data_xml.tag, data_xml.attrib, data_xml.text)
                    if data_xml.tag == 'content':
                        content_id = int(data_xml.attrib['id'])
                        hash_value = data_xml.attrib['hash']
                        item_db = Item.get(Item.content_id == content_id, Item.purge >> None)

                        if hash_value != item_db.hashRecord:
                            logger.info('Hashes not equal, update hash id: %s', content_id)
                            try:
                                urgency_type = int(data_xml.attrib['urgencyType'])
                            except KeyError:
                                urgency_type = 0
                            include_time = self.date_time_xml_to_db(data_xml.attrib['includeTime'])
                            try:
                                block_type = data_xml.attrib['blockType']
                            except KeyError:
                                block_type = 'default'
                            entry_type = int(data_xml.attrib['entryType'])
                            item_db.hashRecord = hash_value
                            # Item.update(purge=None).where(Item.content_id == content_id).execute()
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
                            item_db.includeTime = include_time
                            # Item.update(includeTime=include_time).where(Item.content_id == content_id,
                            #                                             Item.purge >> None).execute()
                        if item_db.urgencyType != urgency_type:
                            logger.info('content_id: %s.', content_id)
                            logger.info('XML urgencyType: %s.', urgency_type)
                            logger.info('DB urgencyType: %s.', item_db.urgencyType)
                            item_db.urgencyType = urgency_type
                            # Item.update(urgencyType=urgency_type).where(Item.content_id == content_id,
                            #                                             Item.purge >> None).execute()
                        if item_db.blockType != block_type:
                            logger.info('content_id: %s.', content_id)
                            logger.info('XML blockType: %s.', block_type)
                            logger.info('DB blockType: %s.', item_db.blockType)
                            item_db.blockType = block_type
                            # Item.update(blockType=block_type).where(Item.content_id == content_id,
                            #                                         Item.purge >> None).execute()
                        if item_db.entryType != entry_type:
                            logger.info('content_id: %s.', content_id)
                            logger.info('XML entryType: %s.', entry_type)
                            logger.info('DB entryType: %s.', item_db.entryType)
                            item_db.entryType = entry_type
                            # Item.update(entryType=entry_type).where(Item.content_id == content_id,
                            #                                         Item.purge >> None).execute()
                        if str(item_db.decision_date) != decision_date:
                            logger.info('content_id: %s.', content_id)
                            logger.info('XML date: %s.', decision_date)
                            logger.info('DB date: %s.', str(item_db.decision_date))
                            item_db.decision_date = decision_date
                            # Item.update(decision_date=decision_date).where(Item.content_id == content_id,
                            #                                                Item.purge >> None).execute()
                        if item_db.decision_num != decision_number:
                            logger.info('content_id: %s.', content_id)
                            logger.info('XML number: %s.', decision_number)
                            logger.info('DB number: %s.', item_db.decision_num)
                            item_db.decision_num = decision_number
                            # Item.update(decision_num=decision_number).where(Item.content_id == content_id,
                            #                                                 Item.purge >> None).execute()
                        if item_db.decision_org != decision_org:
                            logger.info('content_id: %s.', content_id)
                            logger.info('XML org: %s.', decision_org)
                            logger.info('DB org: %s.', item_db.decision_org)
                            item_db.decision_org = decision_org
                            # Item.update(decision_org=decision_org).where(Item.content_id == content_id,
                            #                                              Item.purge >> None).execute()

                    if data_xml.tag == 'url':
                        if not self.only_ascii(data_xml.text):
                            url_split = str(data_xml.text).split(':')
                            url = url_split[0] + ':' + urllib.parse.quote(url_split[1])
                        else:
                            url = data_xml.text
                        url_xml_set.add(url)

                    if data_xml.tag == 'domain':
                        if not self.only_ascii(data_xml.text):
                            domain = (str(data_xml.text).encode('idna')).decode()
                        else:
                            domain = data_xml.text
                        domain_xml_set.add(domain)

                    if data_xml.tag == 'ip':
                        ip_xml_set.add(data_xml.text)

                    if data_xml.tag == 'ipSubnet':
                        sub_ip_xml_set.add(data_xml.text)

                if data_update:
                    url_db = URL.select().where(URL.item == item_db.id, URL.purge >> None)

                    for url_item in url_db:
                        url_db_set.add(url_item.url)
                    if url_db_set != url_xml_set:
                        common_url_set = url_xml_set.intersection(url_db_set)
                        delete_url_set = url_db_set.difference(common_url_set)
                        add_url_set = url_xml_set.difference(common_url_set)
                        if len(delete_url_set) > 0:
                            logger.info('Delete id %s URL: %s', content_id, delete_url_set)
                            for delete_url in delete_url_set:
                                URL.update(purge=self.code_id).where(URL.item == item_db.id, URL.url == delete_url,
                                                                     URL.purge >> None).execute()
                        if len(add_url_set) > 0:
                            logger.info('Add id %s URL: %s', content_id, add_url_set)
                            for add_url in add_url_set:
                                URL.create(item=item_db.id, content_id=item_db.content_id, url=add_url,
                                           add=self.code_id)
                    url_db_set.clear()
                    url_xml_set.clear()

                    domain_db = Domain.select().where(Domain.item == item_db.id, Domain.purge >> None)

                    for domain_item in domain_db:
                        domain_db_set.add(domain_item.domain)
                    if domain_db_set != domain_xml_set:
                        common_domain_set = domain_xml_set.intersection(domain_db_set)
                        delete_domain_set = domain_db_set.difference(common_domain_set)
                        add_domain_set = domain_xml_set.difference(common_domain_set)
                        if len(delete_domain_set) > 0:
                            logger.info('Delete id %s Domain: %s', content_id, delete_domain_set)
                            for delete_domain in delete_domain_set:
                                Domain.update(purge=self.code_id).where(Domain.item == item_db.id,
                                                                        Domain.domain == delete_domain,
                                                                        Domain.purge >> None).execute()
                        if len(add_domain_set) > 0:
                            logger.info('Add id %s Domain: %s', content_id, add_domain_set)
                            for add_domain in add_domain_set:
                                Domain.create(item=item_db.id, content_id=item_db.content_id, domain=add_domain,
                                              add=self.code_id)
                    domain_db_set.clear()
                    domain_xml_set.clear()

                    ip_db = IP.select().where(IP.item == item_db.id, IP.mask == 32, IP.purge >> None)

                    for ip_item in ip_db:
                        ip_db_set.add(ip_item.ip)
                    if ip_db_set != ip_xml_set:
                        common_ip_set = ip_xml_set.intersection(ip_db_set)
                        delete_ip_set = ip_db_set.difference(common_ip_set)
                        add_ip_set = ip_xml_set.difference(common_ip_set)
                        if len(delete_ip_set) > 0:
                            logger.info('Delete id %s ip: %s', content_id, delete_ip_set)
                            for delete_ip in delete_ip_set:
                                IP.update(purge=self.code_id).where(IP.item == item_db.id, IP.ip == delete_ip,
                                                                    IP.mask == 32, IP.purge >> None).execute()
                        if len(add_ip_set) > 0:
                            logger.info('Add id %s ip: %s', content_id, add_ip_set)
                            for add_ip in add_ip_set:
                                IP.create(item=item_db.id, content_id=item_db.content_id, ip=add_ip,
                                          add=self.code_id)
                    ip_db_set.clear()
                    ip_xml_set.clear()

                    sub_ip_db = IP.select().where(IP.item == item_db.id, IP.mask < 32, IP.purge >> None)

                    for sub_ip_item in sub_ip_db:
                        sub_ip_db_set.add(str(sub_ip_item.ip) + '/' + str(sub_ip_item.mask))
                    if sub_ip_db_set != sub_ip_xml_set:
                        common_sub_ip_set = sub_ip_xml_set.intersection(sub_ip_db_set)
                        delete_sub_ip_set = sub_ip_db_set.difference(common_sub_ip_set)
                        add_sub_ip_set = sub_ip_xml_set.difference(common_sub_ip_set)
                        if len(delete_sub_ip_set) > 0:
                            logger.info('Delete id %s subnet: %s', content_id, delete_sub_ip_set)
                            for delete_sub_ip in delete_sub_ip_set:
                                del_subnet = str(delete_sub_ip).split('/')
                                del_ip = del_subnet[0]
                                del_mask = del_subnet[1]
                                IP.update(purge=self.code_id).where(IP.item == item_db.id, IP.ip == del_ip,
                                                                    IP.mask == del_mask, IP.purge >> None).execute()
                        if len(add_sub_ip_set) > 0:
                            logger.info('Add id %s subnet: %s', content_id, add_sub_ip_set)
                            for add_sub_ip in add_sub_ip_set:
                                add_subnet = str(add_sub_ip).split('/')
                                add_ip = add_subnet[0]
                                add_mask = add_subnet[1]
                                IP.create(item=item_db.id, content_id=item_db.content_id, ip=add_ip, mask=add_mask,
                                          add=self.code_id)
                    item_db.save()
                    sub_ip_db_set.clear()
                    sub_ip_xml_set.clear()

        if self.check_diff():
            self.cleaner()
            return 1
        else:
            logger.info('no updates')
            # print('no updates')
            return 2

    def check_diff(self):
        idx_list = [idx.id for idx in History.select(History.id).order_by(History.id.desc())
                    .limit(self.cfg.DiffCount())]
        ip_diff_add_sql = IP.select(fn.Count(fn.Distinct(IP.ip))).join(Item).where(IP.add == idx_list[0]).scalar()
        ip_diff_purge_sql = IP.select(fn.Count(fn.Distinct(IP.ip))).join(Item).where(IP.purge == idx_list[0]).scalar()
        domain_diff_add_sql = Domain.select(fn.Count(fn.Distinct(Domain.domain)))\
            .join(Item).where(Domain.add == idx_list[0]).scalar()
        domain_diff_purge_sql = Domain.select(fn.Count(fn.Distinct(Domain.domain)))\
            .join(Item).where(Domain.purge == idx_list[0]).scalar()
        url_diff_add_sql = URL.select(fn.Count(fn.Distinct(URL.url)))\
            .join(Item).where(URL.add == idx_list[0]).scalar()
        url_diff_purge_sql = URL.select(fn.Count(fn.Distinct(URL.url)))\
            .join(Item).where(URL.purge == idx_list[0]).scalar()

        if ip_diff_add_sql or ip_diff_purge_sql or domain_diff_add_sql or \
                domain_diff_purge_sql or url_diff_add_sql or url_diff_purge_sql:
            History.update(dump=True).where(History.id == idx_list[0]).execute()
            return True
        else:
            # History.update(dump=False).where(History.id == idx_list[0]).execute()
            return False

    @staticmethod
    def conv_domain(domain):
        return (domain.encode('idna')).decode()

    @staticmethod
    def conv_url(url):
        url_encode = url.split(':')
        return url_encode[0] + ':' + urllib.parse.quote(url_encode[1])

    @staticmethod
    def only_ascii(string):
        return True if re.match('^[\x00-\x7F]+$', string) else False

    def cleaner(self):
        private_nets = ['0.%', '127.%', '192.168.%', '10.%', '172.16.%', '172.17.%', '172.18.%', '172.19.%', '172.20.%',
                        '172.21.%', '172.22.%', '172.23.%', '172.24.%', '172.25.%', '172.26.%', '172.27.%', '172.28.%',
                        '172.29.%', '172.30.%', '172.31.%']
        logger.info('Dump cleaner run')
        # history = History.select(History.id).order_by(History.id.desc()).limit(self.cfg.DiffCount())
        # Item.delete().where(~(Item.purge << history)).execute()
        history_clear = History.select(History.id).order_by(History.id.desc()).offset(self.cfg.DiffCount())
        item_del = Item.delete().where(Item.purge << history_clear).execute()
        logger.info('Item deleted: %d', item_del)
        ip_del = IP.delete().where(IP.purge << history_clear).execute()
        logger.info('IP deleted: %d', ip_del)
        domain_del = Domain.delete().where(Domain.purge << history_clear).execute()
        logger.info('Domain deleted: %d', domain_del)
        url_del = URL.delete().where(URL.purge << history_clear).execute()
        logger.info('URL deleted: %d', url_del)
        history_rm = History.select(History.id).order_by(History.id.desc()).offset(self.cfg.HistoryCount())
        hist_del = History.delete().where(History.id << history_rm).execute()
        logger.info('History deleted: %d', hist_del)
        for net in private_nets:
            ip_count = IP.delete().where(IP.ip % net).execute()
            if ip_count:
                logger.info('IP error LIKE %s, count %d', net, ip_count)


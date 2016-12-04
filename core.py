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
from db import Dump, Item, IP, Domain, URL, History
from zapretinfo import ZapretInfo

logger = logging.getLogger(__name__)


class Core(object):
    def __init__(self, transact):
        self.path_py = str(os.path.dirname(os.path.abspath(__file__)))
        self.transact = transact
        self.session = ZapretInfo()
        self.update_dump = self.session.getLastDumpDateEx()
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

    def send_request(self, xml_file, p7s_file, version='2.2'):
        logger.info('Sending request.')
        request = self.session.sendRequest(xml_file, p7s_file, version)
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

    def get_request(self, cfg):
        path_py = str(os.path.dirname(os.path.abspath(__file__)))
        logger.info('Waiting for a 90 sec.')
        time.sleep(90)
        logger.info('Trying to get result...')
        request = self.session.getResult(self.code)
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
        Dump.update(value='Error').where(Dump.param == 'lastResult').execute()
        logger.info('Cant get result.')
        return False

    def parse_dump(self):
        if os.path.exists(self.path_py + '/dump.xml'):
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
                with self.transact.atomic():
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

                        Domain.update(purge=self.code_id).where(Domain.item == del_item).execute()
                        URL.update(purge=self.code_id).where(URL.item == del_item).execute()
                        IP.update(purge=self.code_id).where(IP.item == del_item).execute()
                        Item.update(purge=self.code_id).where(Item.content_id == del_item).execute()

            if len(add_id_set) > 0:
                include_time = str()
                urgency_type = int()
                entry_type = int()
                block_type = str()
                hash_value = str()
                with self.transact.atomic():
                    for new_item in add_id_set:
                        logger.info('New Item, IP, Domain, URL id: %s.', new_item)
                        id_inform_add_set.add(new_item)
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
                                Item.create(content_id=content_id, includeTime=include_time, urgencyType=urgency_type,
                                            entryType=entry_type, blockType=block_type, hashRecord=hash_value,
                                            decision_date=decision_date, decision_num=decision_number,
                                            decision_org=decision_org, add=self.code_id)
                            if data_xml.tag == 'url':
                                url = data_xml.text
                                url_inform_add_set.add(url)
                                URL.create(item=content_id, url=url, add=self.code_id)
                            if data_xml.tag == 'domain':
                                domain = data_xml.text
                                domain_inform_add_set.add(domain)
                                Domain.create(item=content_id, domain=domain, add=self.code_id)
                            if data_xml.tag == 'ip':
                                ip = data_xml.text
                                ip_inform_add_set.add(ip)
                                IP.create(item=content_id, ip=ip, add=self.code_id)
                            if data_xml.tag == 'ipSubnet':
                                net = data_xml.text.split('/')
                                sub_ip_inform_add_set.add(data_xml.text)
                                ip = net[0]
                                mask = net[1]
                                IP.create(item=content_id, ip=ip, mask=mask, add=self.code_id)

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
                            item_db = Item.get(Item.content_id == content_id)

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

                                Item.update(hashRecord=hash_value).where(Item.content_id == content_id).execute()
                                Item.update(purge=None).where(Item.content_id == content_id).execute()
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
                                Item.update(decision_num=decision_number).where(Item.content_id == content_id).execute()
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
                                    URL.update(purge=self.code_id).where(URL.url == delete_url).execute()
                            if len(add_url_set) > 0:
                                logger.info('Add id %s URL: %s', content_id, add_url_set)
                                url_inform_add_set.update(add_url_set)
                                for add_url in add_url_set:
                                    URL.create(item=content_id, url=add_url, add=self.code_id)
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
                                    Domain.update(purge=self.code_id).where(Domain.domain == delete_domain).execute()
                            if len(add_domain_set) > 0:
                                logger.info('Add id %s Domain: %s', content_id, add_domain_set)
                                domain_inform_add_set.update(add_domain_set)
                                for add_domain in add_domain_set:
                                    Domain.create(item=content_id, domain=add_domain, add=self.code_id)
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
                                    IP.update(purge=self.code_id).where(IP.ip == delete_ip).execute()
                            if len(add_ip_set) > 0:
                                logger.info('Add id %s ip: %s', content_id, add_ip_set)
                                ip_inform_add_set.update(add_ip_set)
                                for add_ip in add_ip_set:
                                    IP.create(item=content_id, ip=add_ip, add=self.code_id)
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
                                    IP.update(purge=self.code_id).where(IP.ip == del_ip, IP.mask == del_mask).execute()
                            if len(add_sub_ip_set) > 0:
                                logger.info('Add id %s subnet: %s', content_id, add_sub_ip_set)
                                sub_ip_inform_add_set.update(add_sub_ip_set)
                                for add_sub_ip in add_sub_ip_set:
                                    add_subnet = str(add_sub_ip).split('/')
                                    add_ip = add_subnet[0]
                                    add_mask = add_subnet[1]
                                    IP.create(item=content_id, ip=add_ip, mask=add_mask, add=self.code_id)
                        sub_ip_db_set.clear()
                        sub_ip_xml_set.clear()

            if (
                len(url_inform_del_set) == 0 and
                len(ip_inform_del_set) == 0 and
                len(domain_inform_del_set) == 0 and
                len(id_inform_del_set) == 0 and
                len(sub_ip_inform_del_set) == 0 and
                len(url_inform_add_set) == 0 and
                len(ip_inform_add_set) == 0 and
                len(domain_inform_add_set) == 0 and
                len(id_inform_add_set) == 0 and
                len(sub_ip_inform_add_set) == 0
            ):
                return 2, str()

            report_data = {'url_del': url_inform_del_set, 'ip_del': ip_inform_del_set,
                           'domain_del': domain_inform_del_set, 'id_del': id_inform_del_set,
                           'sub_ip_del': sub_ip_inform_del_set, 'url_add': url_inform_add_set,
                           'ip_add': ip_inform_add_set, 'domain_add': domain_inform_add_set,
                           'id_add': id_inform_add_set, 'sub_ip_add': sub_ip_inform_add_set}

            return 1, report_data
        else:
            return 0, dict()

    def cleaner(self):
        History.select()
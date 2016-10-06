#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Prototype-X'


from datetime import datetime
import argparse
import logging
import smtplib
from email.mime.text import MIMEText
import subprocess
from peewee import fn

from config import Config
from db import Dump, Item, IP, Domain, URL, History, init_db
from core import Core

logger = logging.getLogger(__name__)


class Rutoken(object):
    def __init__(self, cfg_obj):
        self.cfg = cfg_obj

    def gen_request(self):
        logger.info('Generate request file %s', self.cfg.XMLPathFName())
        dt = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        request_xml = '<?xml version="1.0" encoding="windows-1251"?>\n'
        request_xml += '<request>\n'
        request_xml += '<requestTime>' + dt + '.000+04:00</requestTime>\n'
        request_xml += '<operatorName>' + self.cfg.OperatorName() + '</operatorName>\n'
        request_xml += '<inn>' + str(self.cfg.inn()) + '</inn>\n'
        request_xml += '<ogrn>' + str(self.cfg.ogrn()) + '</ogrn>\n'
        request_xml += '<email>' + self.cfg.email() + '</email>\n'
        request_xml += '</request>'
        with open(self.cfg.XMLPathFName(), 'wb') as f:
            f.write(request_xml.encode(encoding='cp1251'))
        return True

    def sign_request(self):
        logger.info('Sign file %s', self.cfg.XMLPathFName())
        subprocess.call("sudo openssl smime -engine pkcs11_gost -sign -in " + self.cfg.XMLPathFName() + " -out " +
                        self.cfg.P7SPathFName() + " -outform der -noverify -binary -signer " + self.cfg.PEMPathFName() +
                        " -inkey " + self.cfg.ID() + " -keyform engine", shell=True)
        return True


class Notifier(object):
    def __init__(self, cfg):
        self.from_address = cfg.MailFrom()
        self.to_address = cfg.MailTo()
        self.auth = cfg.MailAuth()
        self.starttls = cfg.StartTLS()
        self.server_address = cfg.MailServer()
        self.server_port = cfg.MailPort()
        self.subject = cfg.MailSubject()
        if self.auth:
            self.login = cfg.MailLogin()
            self.password = cfg.MailPassword()

    def send_mail(self, message, subject=''):
        if subject:
            self.subject = subject
        msg = MIMEText(message)
        msg['Subject'] = self.subject
        msg['From'] = self.from_address
        msg['To'] = self.to_address
        if self.auth:
            server = smtplib.SMTP(self.server_address, self.server_port)
            server.ehlo()
            if self.starttls:
                server.starttls()
            server.login(self.login, self.password)
            server.sendmail(self.from_address, self.to_address, msg.as_string())
            server.quit()
        else:
            server = smtplib.SMTP(self.server_address, self.server_port)
            server.ehlo()
            server.connect()
            server.sendmail(self.from_address, self.to_address, msg.as_string())
            server.quit()
        logger.info('Send email from %s to %s', self.from_address, self.to_address)
        logger.info('%s', message)


class Reporter(object):
    def __init__(self):
        pass

    @staticmethod
    def statistics_show(**data):
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

    @staticmethod
    def domain_show(bt):
        if bt == 'ignore':
            domain_sql = Domain.select(fn.Distinct(Domain.domain))
            for domain_row in domain_sql:
                print(domain_row.domain)
        elif bt == 'domain':
            domain_unique = set()
            item_sql = Item.select(Item.content_id, Item.blockType).where(Item.blockType == 'domain')
            for item_row in item_sql:
                domain_sql = Domain.select().where(Domain.item == item_row.content_id)
                for domain_row in domain_sql:
                    domain_unique.add(domain_row.domain)
            for domain in domain_unique:
                print(domain)
        elif bt == 'domain-mask':
            domain_unique = set()
            item_sql = Item.select(Item.content_id, Item.blockType).where(Item.blockType == 'domain-mask')
            for item_row in item_sql:
                domain_sql = Domain.select().where(Domain.item == item_row.content_id)
                for domain_row in domain_sql:
                    domain_unique.add(domain_row.domain)
            for domain in domain_unique:
                print(domain)
        else:
            print("Invalid --bt " + bt)

    @staticmethod
    def ip_show(bt):
        if bt == 'ignore':
            ip_sql = IP.select(fn.Distinct(IP.ip))
            for ip_row in ip_sql:
                if ip_row.mask < 32:
                    print(ip_row.ip + '/' + str(ip_row.mask))
                else:
                    print(ip_row.ip)
        elif bt == 'ip':
            ip_unique = set()
            item_sql = Item.select(Item.content_id, Item.blockType).where(Item.blockType == 'ip')
            for item_row in item_sql:
                ip_sql = IP.select().where(IP.item == item_row.content_id)
                for ip_row in ip_sql:
                    if ip_row.mask < 32:
                        ip_unique.add(ip_row.ip + '/' + str(ip_row.mask))
                    else:
                        ip_unique.add(ip_row.ip)
            for ip in ip_unique:
                print(ip)
        else:
            print("Invalid --bt " + bt)

    @staticmethod
    def url_show():
        url_sql = URL.select(fn.Distinct(URL.url))
        for url_row in url_sql:
            print(url_row.url)

        # item_sql = Item.select(Item.content_id, Item.blockType).where((Item.blockType == 'domain') |
        #                                                               (Item.blockType == 'domain-mask'))
        # for item_row in item_sql:
        #     print('http://' + Domain.get(Domain.item == item_row.content_id).domain)

    @staticmethod
    def history_show():
        history_sql = History.select()
        for history_row in history_sql:
            print(history_row.date, history_row.requestCode)


class BlrknCLI(object):
    def __init__(self):
        self.parser = argparse.ArgumentParser(add_help=True,
                                              description='Tool for list of restricted websites '
                                                          'http://vigruzki.rkn.gov.ru/')
        self.parser.add_argument("--url", action="store_true", required=False, default=False, help="url list show")
        self.parser.add_argument("--ip", action="store_true", required=False, default=False, help="ip list show")
        self.parser.add_argument("--domain", action="store_true", required=False, default=False,
                                 help="domain list show")
        self.parser.add_argument("--history", action="store_true", required=False, default=False,
                                 help="history list show")
        self.parser.add_argument('--bt', action='store', default='ignore',
                                 choices=['default', 'ip', 'domain', 'domain-mask'], help='blockType')
        self.parser.add_argument("-v", "--version", action='version', version='version 1.5.0', help="show version")

        self.args = self.parser.parse_args()

        self.ip_print = self.args.ip
        self.url_print = self.args.url
        self.domain_print = self.args.domain
        self.history_print = self.args.history
        self.block_type = self.args.bt

        self.cfg = Config()
        self._cfg_logging()
        logger.info('Starting script.')

        self.rept = Reporter()

        init_db(self.cfg)

        if self.ip_print:
            self.rept.ip_show(self.block_type)
        elif self.url_print:
            self.rept.url_show()
        elif self.domain_print:
            self.rept.domain_show(self.block_type)
        elif self.history_print:
            self.rept.history_show()
        else:
            # self._parse_dump_only()
            self._get_dump()

        logger.info('Script stopped.')

    def _get_dump(self):
        self.dump = Core()
        srv_msg = self.dump.check_service_upd()
        if srv_msg:
            if self.cfg.Notify():
                self.notice = Notifier(self.cfg)
                self.notice.send_mail(srv_msg, subject='vigruzki.rkn.gov.ru service update')
        if self.dump.check_new_dump():
            if self.cfg.GenRequest():
                signer = Rutoken(self.cfg)
                signer.gen_request()
                signer.sign_request()
            code = self.dump.send_request(self.cfg.XMLPathFName(), self.cfg.P7SPathFName(), '2.2')
            if code:
                if self.dump.get_request(code, self.cfg):
                    result_bool, raw_rept = self.dump.parse_dump()
                    if result_bool == 1:
                        if self.cfg.Notify():
                            message = self.rept.statistics_show(**raw_rept)
                            self.notice.send_mail(message)
                    elif result_bool == 2:
                        logger.info('No updates')
                    elif result_bool == 0:
                        if self.cfg.Notify():
                            message = 'Houston, we have a problem'
                            self.notice.send_mail(message)
                        logger.info('parse_dump error')

    def _parse_dump_only(self):
        self.dump = Core()
        self.dump.parse_dump()

    def _cfg_logging(self):
        """
        Configure logging output format.
        """
        if self.cfg.LogRewrite():
            filemode = 'w'
        else:
            filemode = 'a'

        logging.basicConfig(filename=self.cfg.LogPathFName(), filemode=filemode,
                            format=u'%(asctime)s  %(message)s', level=logging.INFO)


def main():
    BlrknCLI()

if __name__ == '__main__':
    main()

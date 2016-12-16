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
import random

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
        subprocess.call("sudo " + self.cfg.Path() + "openssl smime -engine pkcs11_gost -sign -in " +
                        self.cfg.XMLPathFName() + " -out " + self.cfg.P7SPathFName() +
                        " -outform der -noverify -binary -signer " + self.cfg.PEMPathFName() +
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
    def __init__(self, cfg):
        self.cfg = cfg
        self.idx_list = [idx.id for idx in History.select(History.id).where(History.diff == True)
                         .order_by(History.id.desc()).limit(self.cfg.DiffCount())]

    def statistics_show(self, diff=0, stdout=False):

        date_time = datetime.fromtimestamp(int(Dump.get(Dump.param == 'lastDumpDate')
                                               .value)).strftime('%Y-%m-%d %H:%M:%S')

        message = 'vigruzki.rkn.gov.ru update: ' + date_time + '\n'

        url_add_sql = self._url_diff_sql(diff, 'ignore', 1)
        message += '\nURLs added: \n\n'
        for url_add in url_add_sql:
            message += url_add.url + '\n'

        ip_add_sql = self._ip_diff_sql(diff, 'ignore', 1)
        message += '\nIPs added: \n\n'
        for ip_add in ip_add_sql:
            if ip_add.mask < 32:
                message += ip_add.ip + '/' + str(ip_add.mask)
            else:
                message += ip_add.ip + '\n'

        domain_add_sql = self._domain_diff_sql(diff, 'ignore', 1)
        message += '\nDOMAINs added: \n\n'
        for domain_add in domain_add_sql:
            message += domain_add.domain + '\n'

        url_del_sql = self._url_diff_sql(diff, 'ignore', 0)
        message += '\nURLs deleted: \n\n'
        for url_del in url_del_sql:
            message += url_del.url + '\n'

        ip_del_sql = self._ip_diff_sql(diff, 'ignore', 0)
        message += '\nIPs deleted: \n\n'
        for ip_del in ip_del_sql:
            if ip_del.mask < 32:
                message += ip_del.ip + '/' + str(ip_del.mask)
            else:
                message += ip_del.ip + '\n'

        domain_del_sql = self._domain_diff_sql(diff, 'ignore', 0)
        message += '\nDOMAINs deleted: \n\n'
        for domain_del in domain_del_sql:
            message += domain_del.domain + '\n'

        rb_list = self.idx_list[:diff]
        domain_count = Domain.select(fn.Count(fn.Distinct(Domain.domain)))\
            .where(~(Domain.add << rb_list) & ((Domain.purge >> None) | (Domain.purge << rb_list))).scalar()
        url_count = URL.select(fn.Count(fn.Distinct(URL.url)))\
            .where(~(URL.add << rb_list) & ((URL.purge >> None) | (URL.purge << rb_list))).scalar()
        ip_count = IP.select(fn.Count(fn.Distinct(IP.ip)))\
            .where(~(IP.add << rb_list) & ((IP.purge >> None) | (IP.purge << rb_list))).scalar()
        id_count = Item.select(fn.Count(fn.Distinct(Item.content_id)))\
            .where(~(Item.add << rb_list) & ((Item.purge >> None) | (Item.purge << rb_list))).scalar()

        message += '\nURLs count: ' + str(url_count) + '\n'
        message += 'IPs count: ' + str(ip_count) + '\n'
        message += 'DOMAINs count: ' + str(domain_count) + '\n'
        message += 'Item count: ' + str(id_count) + '\n'

        if stdout:
            print(message)
            return False
        else:
            return message

    def domain_show(self, bt='ignore', diff=None, rollback=None):

        if diff is not None:
            logger.info('bl-rkn.py --diff %d --domain --bt %s', diff, bt)
            # domain_sql = self._domain_diff_sql(diff, bt, 1)
            domain_sql = self._domain_dedup_sql(diff, bt, 1)
            self._domain_output(domain_sql, '+')
            # domain_sql = self._domain_diff_sql(diff, bt, 0)
            domain_sql = self._domain_dedup_sql(diff, bt, 0)
            self._domain_output(domain_sql, '-')

        if rollback is not None:
            logger.info('bl-rkn.py --rollback %d --domain --bt %s', rollback)
            domain_sql = self.domain_rollback_sql(rollback, bt)
            self._domain_output(domain_sql)

    def _domain_diff_sql(self, diff, bt, stat):
        if stat and (bt == 'ip' or bt == 'default' or bt == 'domain' or bt == 'domain-mask'):
            domain_sql = Domain.select(fn.Distinct(Domain.domain)).join(Item)\
                .where(Item.blockType == bt, Domain.add == self.idx_list[diff])
            return domain_sql
        elif not stat and (bt == 'ip' or bt == 'default' or bt == 'domain' or bt == 'domain-mask'):
            domain_sql = Domain.select(fn.Distinct(Domain.domain)).join(Item)\
                .where(Item.blockType == bt, Domain.purge == self.idx_list[diff])
            return domain_sql
        elif stat and bt == 'ignore':
            domain_sql = Domain.select(fn.Distinct(Domain.domain)).where(Domain.add == self.idx_list[diff])
            return domain_sql
        elif not stat and bt == 'ignore':
            domain_sql = Domain.select(fn.Distinct(Domain.domain)).where(Domain.purge == self.idx_list[diff])
            return domain_sql

    def _domain_dedup_sql(self, diff, bt, stat):
        rb_list_add = self.idx_list[:diff+1]
        rb_list_purge = self.idx_list[:diff]
        if stat and bt == 'ignore':
            domain_diff_sql = Domain.select(fn.Distinct(Domain.domain)).where(Domain.add == self.idx_list[diff])
            domain_dup_sql = Domain.select(fn.Distinct(Domain.domain))\
                .where(~(Domain.add << rb_list_add) & ((Domain.purge >> None) | (Domain.purge << rb_list_add)) &
                       (Domain.domain << domain_diff_sql))
            domain_dedup_sql = Domain.select(fn.Distinct(Domain.domain)).where((Domain.add == self.idx_list[diff]) &
                                                                               ~(Domain.domain << domain_dup_sql))
            return domain_dedup_sql
        elif not stat and bt == 'ignore':
            domain_diff_sql = Domain.select(fn.Distinct(Domain.domain)).where(Domain.purge == self.idx_list[diff])
            domain_dup_sql = Domain.select(fn.Distinct(Domain.domain))\
                .where(~(Domain.add << rb_list_purge) & (Domain.purge >> None) &
                       (Domain.domain << domain_diff_sql))
            domain_dedup_sql = Domain.select(fn.Distinct(Domain.domain)).where((Domain.purge == self.idx_list[diff]) &
                                                                               ~(Domain.domain << domain_dup_sql))
            return domain_dedup_sql
        elif stat and (bt == 'ip' or bt == 'default' or bt == 'domain' or bt == 'domain-mask'):
            domain_diff_sql = Domain.select(fn.Distinct(Domain.domain)).join(Item)\
                .where(Item.blockType == bt, Domain.add == self.idx_list[diff])
            domain_dup_sql = Domain.select(fn.Distinct(Domain.domain)).join(Item)\
                .where((Item.blockType == bt) & ~(Domain.add << rb_list_add) &
                       (Domain.purge >> None) & (Domain.domain << domain_diff_sql))

            domain_dedup_sql = Domain.select(fn.Distinct(Domain.domain)).join(Item)\
                .where((Item.blockType == bt) & (Domain.add == self.idx_list[diff]) &
                       ~(Domain.domain << domain_dup_sql))
            return domain_dedup_sql
        elif not stat and (bt == 'ip' or bt == 'default' or bt == 'domain' or bt == 'domain-mask'):
            domain_diff_sql = Domain.select(fn.Distinct(Domain.domain)).join(Item)\
                .where(Item.blockType == bt, Domain.purge == self.idx_list[diff])
            domain_dup_sql = Domain.select(fn.Distinct(Domain.domain)).join(Item)\
                .where((Item.blockType == bt) & ~(Domain.add << rb_list_purge) &
                       (Domain.purge >> None) & (Domain.domain << domain_diff_sql))
            domain_dedup_sql = Domain.select(fn.Distinct(Domain.domain)).join(Item)\
                .where((Item.blockType == bt) & (Domain.purge == self.idx_list[diff]) &
                       ~(Domain.domain << domain_dup_sql))
            return domain_dedup_sql

    def domain_rollback_sql(self, rollback, bt):
        rb_list = self.idx_list[:rollback]
        if bt == 'ignore':
            domain_sql = Domain.select(fn.Distinct(Domain.domain))\
                .where(~(Domain.add << rb_list) & ((Domain.purge >> None) | (Domain.purge << rb_list)))
            return domain_sql
        elif bt == 'ip' or bt == 'default' or bt == 'domain' or bt == 'domain-mask':
            domain_sql = Domain.select(fn.Distinct(Domain.domain))\
                .join(Item).where((Item.blockType == bt) & ~(Domain.add << rb_list) &
                                  ((Domain.purge >> None) | (Domain.purge << rb_list)))
            return domain_sql

    def ip_show(self, bt='ignore', diff=None, rollback=None):

        if diff is not None:
            logger.info('bl-rkn.py --diff %d --ip --bt %s', diff, bt)
            ip_sql = self._ip_dedup_sql(diff, bt, 1)
            self._ip_output(ip_sql, '+')
            ip_sql = self._ip_dedup_sql(diff, bt, 0)
            self._ip_output(ip_sql, '-')

        if rollback is not None:
            logger.info('bl-rkn.py --rollback %d --ip --bt %s', rollback, bt)
            ip_sql = self.ip_rollback_sql(rollback, bt)
            self._ip_output(ip_sql)

    def _ip_diff_sql(self, diff, bt, stat):
        if stat and (bt == 'ip' or bt == 'default' or bt == 'domain' or bt == 'domain-mask'):
            ip_sql = IP.select(fn.Distinct(IP.ip), IP.mask).join(Item)\
                     .where(Item.blockType == bt, IP.add == self.idx_list[diff])
            return ip_sql
        elif not stat and (bt == 'ip' or bt == 'default' or bt == 'domain' or bt == 'domain-mask'):
            ip_sql = IP.select(fn.Distinct(IP.ip), IP.mask).join(Item)\
                     .where(Item.blockType == bt, IP.purge == self.idx_list[diff])
            return ip_sql
        elif stat and bt == 'ignore':
            ip_sql = IP.select(fn.Distinct(IP.ip), IP.mask).where(IP.add == self.idx_list[diff])
            return ip_sql

        elif not stat and bt == 'ignore':
            ip_sql = IP.select(fn.Distinct(IP.ip), IP.mask).where(IP.purge == self.idx_list[diff])
            return ip_sql

    def _ip_dedup_sql(self, diff, bt, stat):
        rb_list_add = self.idx_list[:diff+1]
        rb_list_purge = self.idx_list[:diff]
        if stat and bt == 'ignore':
            ip_diff_sql = IP.select(fn.Distinct(IP.ip)).where(IP.add == self.idx_list[diff])
            ip_dup_sql = IP.select(fn.Distinct(IP.ip))\
                .where(~(IP.add << rb_list_add) & ((IP.purge >> None) | (IP.purge << rb_list_add)) &
                       (IP.ip << ip_diff_sql))
            ip_dedup_sql = IP.select(fn.Distinct(IP.ip), IP.mask).where((IP.add == self.idx_list[diff]) &
                                                                        ~(IP.ip << ip_dup_sql))
            return ip_dedup_sql
        elif not stat and bt == 'ignore':
            ip_diff_sql = IP.select(fn.Distinct(IP.ip)).where(IP.purge == self.idx_list[diff])
            ip_dup_sql = IP.select(fn.Distinct(IP.ip))\
                .where(~(IP.add << rb_list_purge) & (IP.purge >> None) &
                       (IP.ip << ip_diff_sql))
            ip_dedup_sql = IP.select(fn.Distinct(IP.ip), IP.mask).where((IP.purge == self.idx_list[diff]) &
                                                                        ~(IP.ip << ip_dup_sql))
            return ip_dedup_sql
        elif stat and (bt == 'ip' or bt == 'default' or bt == 'domain' or bt == 'domain-mask'):
            ip_diff_sql = IP.select(fn.Distinct(IP.ip)).join(Item)\
                .where(Item.blockType == bt, IP.add == self.idx_list[diff])
            ip_dup_sql = IP.select(fn.Distinct(IP.ip)).join(Item)\
                .where((Item.blockType == bt) & ~(IP.add << rb_list_add) &
                       (IP.purge >> None) & (IP.ip << ip_diff_sql))

            ip_dedup_sql = IP.select(fn.Distinct(IP.ip), IP.mask).join(Item)\
                .where((Item.blockType == bt) & (IP.add == self.idx_list[diff]) &
                       ~(IP.ip << ip_dup_sql))
            return ip_dedup_sql
        elif not stat and (bt == 'ip' or bt == 'default' or bt == 'domain' or bt == 'domain-mask'):
            ip_diff_sql = IP.select(fn.Distinct(IP.ip)).join(Item)\
                .where(Item.blockType == bt, IP.purge == self.idx_list[diff])
            ip_dup_sql = IP.select(fn.Distinct(IP.ip)).join(Item)\
                .where((Item.blockType == bt) & ~(IP.add << rb_list_purge) &
                       (IP.purge >> None) & (IP.ip << ip_diff_sql))
            ip_dedup_sql = IP.select(fn.Distinct(IP.ip), IP.mask).join(Item)\
                .where((Item.blockType == bt) & (IP.purge == self.idx_list[diff]) &
                       ~(IP.ip << ip_dup_sql))
            return ip_dedup_sql

    def ip_rollback_sql(self, rollback, bt):
        rb_list = self.idx_list[:rollback]
        if bt == 'ignore':
            ip_sql = IP.select(fn.Distinct(IP.ip), IP.mask)\
                .where(~(IP.add << rb_list) & ((IP.purge >> None) | (IP.purge << rb_list)))
            return ip_sql
        elif bt == 'ip' or bt == 'default' or bt == 'domain' or bt == 'domain-mask':
            ip_sql = IP.select(fn.Distinct(IP.ip), IP.mask)\
                .join(Item).where((Item.blockType == bt) & ~(IP.add << rb_list) &
                                  ((IP.purge >> None) | (IP.purge << rb_list)))
            return ip_sql

    def url_show(self, bt='ignore', diff=None, rollback=None):
        if diff is not None:
            logger.info('bl-rkn.py --diff %d --url --bt %s', diff, bt)
            url_sql = self._url_dedup_sql(diff, bt, 1)
            self._url_output(url_sql, '+')
            url_sql = self._url_dedup_sql(diff, bt, 0)
            self._url_output(url_sql, '-')

        if rollback is not None:
            logger.info('bl-rkn.py --rollback %d --url --bt %s', rollback, bt)
            url_sql = self.url_rollback_sql(rollback, bt)
            self._url_output(url_sql)

    def _url_diff_sql(self, diff, bt, stat):
        if stat and (bt == 'ip' or bt == 'default' or bt == 'domain' or bt == 'domain-mask'):
            url_sql = URL.select(fn.Distinct(URL.url)).join(Item)\
                .where(Item.blockType == bt, URL.add == self.idx_list[diff])
            return url_sql
        elif not stat and (bt == 'ip' or bt == 'default' or bt == 'domain' or bt == 'domain-mask'):
            url_sql = URL.select(fn.Distinct(URL.url)).join(Item)\
                .where(Item.blockType == bt, URL.purge == self.idx_list[diff])
            return url_sql
        elif stat and bt == 'ignore':
            url_sql = URL.select(fn.Distinct(URL.url)).where(URL.add == self.idx_list[diff])
            return url_sql

        elif not stat and bt == 'ignore':
            url_sql = URL.select(fn.Distinct(URL.url)).where(URL.purge == self.idx_list[diff])
            return url_sql

    def _url_dedup_sql(self, diff, bt, stat):
        rb_list_add = self.idx_list[:diff+1]
        rb_list_purge = self.idx_list[:diff]
        if stat and bt == 'ignore':
            url_diff_sql = URL.select(fn.Distinct(URL.url)).where(URL.add == self.idx_list[diff])
            url_dup_sql = URL.select(fn.Distinct(URL.url))\
                .where(~(URL.add << rb_list_add) & ((URL.purge >> None) | (URL.purge << rb_list_add)) &
                       (URL.url << url_diff_sql))
            url_dedup_sql = URL.select(fn.Distinct(URL.url)).where((URL.add == self.idx_list[diff]) &
                                                                   ~(URL.url << url_dup_sql))
            return url_dedup_sql
        elif not stat and bt == 'ignore':
            url_diff_sql = URL.select(fn.Distinct(URL.url)).where(URL.purge == self.idx_list[diff])
            url_dup_sql = URL.select(fn.Distinct(URL.url))\
                .where(~(URL.add << rb_list_purge) & (URL.purge >> None) &
                       (URL.url << url_diff_sql))
            url_dedup_sql = URL.select(fn.Distinct(URL.url)).where((URL.purge == self.idx_list[diff]) &
                                                                   ~(URL.url << url_dup_sql))
            return url_dedup_sql
        elif stat and (bt == 'ip' or bt == 'default' or bt == 'domain' or bt == 'domain-mask'):
            url_diff_sql = URL.select(fn.Distinct(URL.url)).join(Item)\
                .where(Item.blockType == bt, URL.add == self.idx_list[diff])
            url_dup_sql = URL.select(fn.Distinct(URL.url)).join(Item)\
                .where((Item.blockType == bt) & ~(URL.add << rb_list_add) &
                       (URL.purge >> None) & (URL.url << url_diff_sql))
            url_dedup_sql = URL.select(fn.Distinct(URL.url)).join(Item)\
                .where((Item.blockType == bt) & (URL.add == self.idx_list[diff]) &
                       ~(URL.url << url_dup_sql))
            return url_dedup_sql
        elif not stat and (bt == 'ip' or bt == 'default' or bt == 'domain' or bt == 'domain-mask'):
            url_diff_sql = URL.select(fn.Distinct(URL.url)).join(Item)\
                .where(Item.blockType == bt, URL.purge == self.idx_list[diff])
            url_dup_sql = URL.select(fn.Distinct(URL.url)).join(Item)\
                .where((Item.blockType == bt) & ~(URL.add << rb_list_purge) &
                       (URL.purge >> None) & (URL.url << url_diff_sql))
            url_dedup_sql = URL.select(fn.Distinct(URL.url)).join(Item)\
                .where((Item.blockType == bt) & (URL.purge == self.idx_list[diff]) &
                       ~(URL.url << url_dup_sql))
            return url_dedup_sql

    def url_rollback_sql(self, rollback, bt):
        rb_list = self.idx_list[:rollback]
        if bt == 'ignore':
            url_sql = URL.select(fn.Distinct(URL.url))\
                .where(~(URL.add << rb_list) & ((URL.purge >> None) | (URL.purge << rb_list)))
            return url_sql
        elif bt == 'ip' or bt == 'default' or bt == 'domain' or bt == 'domain-mask':
            url_sql = URL.select(fn.Distinct(URL.url))\
                .join(Item).where((Item.blockType == bt) & ~(URL.add << rb_list) &
                                  ((URL.purge >> None) | (URL.purge << rb_list)))
            return url_sql

    @staticmethod
    def _url_output(url_sql, prefix=''):
        for url_row in url_sql:
            logger.info('%s', prefix + url_row.url)
            print(prefix + url_row.url)

    @staticmethod
    def _domain_output(domain_sql, prefix=''):
        for domain_row in domain_sql:
            logger.info('%s', prefix + domain_row.domain)
            print(prefix + domain_row.domain)

    @staticmethod
    def _ip_output(ip_sql, prefix=''):
        for ip_row in ip_sql:
            if ip_row.mask < 32:
                logger.info('%s', prefix + ip_row.ip + '/' + str(ip_row.mask))
                print(prefix + ip_row.ip + '/' + str(ip_row.mask))
            else:
                logger.info('%s', prefix + ip_row.ip)
                print(prefix + ip_row.ip)

    @staticmethod
    def history_show():
        history_sql = History.select()
        for history_row in history_sql:
            print(history_row.date, history_row.requestCode)


class BlrknCLI(object):
    def __init__(self):
        self.cfg = Config()
        choice_rb_diff = [i for i in range(self.cfg.DiffCount())]

        self.parser = argparse.ArgumentParser(add_help=True,
                                              description='Tool for list of restricted websites '
                                                          'http://vigruzki.rkn.gov.ru/')
        self.group = self.parser.add_mutually_exclusive_group()
        self.group.add_argument("--dump", action="store_true", required=False, default=False, help="Get new dump")
        self.group.add_argument("--diff", action="store", type=int, choices=choice_rb_diff, required=False,
                                default=None, help="difference dump")
        self.group.add_argument("--rollback", action="store", type=int, choices=choice_rb_diff, required=False,
                                default=None, help="rollback dump")
        self.group.add_argument("--stat", action="store", type=int, choices=choice_rb_diff, required=False,
                                default=None, help="dump statistics")
        self.parser.add_argument("--url", action="store_true", required=False, default=False, help="url list show")
        self.parser.add_argument("--ip", action="store_true", required=False, default=False, help="ip list show")
        self.parser.add_argument("--domain", action="store_true", required=False, default=False,
                                 help="domain list show")
        self.parser.add_argument("--history", action="store_true", required=False, default=False,
                                 help="history list show")
        self.parser.add_argument('--bt', action='store', default='ignore',
                                 choices=['default', 'ip', 'domain', 'domain-mask'], help='blockType')
        self.parser.add_argument("-v", "--version", action='version', version='version 2.0.0', help="show version")

        self.args = self.parser.parse_args()

        # self._peewee_debug()

        self.ip_print = self.args.ip
        self.url_print = self.args.url
        self.domain_print = self.args.domain
        self.history_print = self.args.history
        self.block_type = self.args.bt
        self.dump = self.args.dump
        self.diff = self.args.diff
        self.rollback = self.args.rollback
        self.stat = self.args.stat

        self._cfg_logging()
        logger.info('Starting script.')

        self.ctl_transact = init_db(self.cfg)

        self.report = Reporter(self.cfg)
        if self.diff is None and self.rollback is None:
                self.rollback = 0
        if self.ip_print:
            self.report.ip_show(bt=self.block_type, diff=self.diff, rollback=self.rollback)
        elif self.url_print:
            self.report.url_show(bt=self.block_type, diff=self.diff, rollback=self.rollback)
        elif self.domain_print:
            self.report.domain_show(bt=self.block_type, diff=self.diff, rollback=self.rollback)
        elif self.history_print:
            self.report.history_show()
        elif self.stat is not None:
            self.report.statistics_show(diff=self.stat, stdout=True)
        elif self.dump:
            # self._peewee_debug()
            # self._parse_dump_only()
            self._get_dump()
        else:
            self.parser.print_help()

        logger.info('Script stopped.')

    def _get_dump(self):
        self.dump = Core(self.ctl_transact, self.cfg)
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
            if self.dump.send_request():
                if self.dump.get_request():
                    result_bool = self.dump.parse_dump()
                    if result_bool == 1:
                        if self.cfg.Notify():
                            message = self.report.statistics_show()
                            self.notice.send_mail(message)
                    elif result_bool == 0:
                        if self.cfg.Notify():
                            message = 'Houston, we have a problem'
                            self.notice.send_mail(message)
                        logger.info('parse_dump error')

    def _parse_dump_only(self):
        self.dump = Core(self.ctl_transact, self.cfg)
        self.dump.code = 'test_' + ''.join(random.SystemRandom().
                                           choice('abcdefgijklmnoprstuvwxyz1234567890') for _ in range(8))
        History.create(requestCode=self.dump.code, date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.dump.code_id = History.get(History.requestCode == self.dump.code).id
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

    @staticmethod
    def _peewee_debug():
        log = logging.getLogger('peewee')
        log.setLevel(logging.DEBUG)
        log.addHandler(logging.StreamHandler())


def main():
    BlrknCLI()

if __name__ == '__main__':
    main()

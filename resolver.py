#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# __author__ = 'maximus'

import dns.resolver
import logging
from db import History, DNSResolver
from peewee import fn

logger = logging.getLogger(__name__)


class Resolver:
    def __init__(self, cfg, transact, reporter, code_id):
        logger.info('Resolver init')
        self.code_id = code_id
        self.transact = transact
        self.cfg = cfg
        self.reporter = reporter
        self.domain_sql = self.reporter.domain_rollback_sql(0, 'ignore')

        self.dns_servers = str(cfg.DNS()).split(' ')
        self.resolvers = [dns.resolver.Resolver(configure=False) for i in range(len(self.dns_servers))]
        for resolver, dns_server in zip(self.resolvers, self.dns_servers):
            resolver.nameservers = [dns_server]
            resolver.timeout = self.cfg.QueryTimeout()
            resolver.lifetime = self.cfg.QueryTimeout()

    def query(self):
        logger.info('Resolver run')
        self.query_v4()
        if self.cfg.IPv6():
            self.query_v6()
        dns_sql_new = DNSResolver.select(fn.Distinct(DNSResolver.ip)).where(DNSResolver.purge >> None,
                                                                            DNSResolver.add == self.code_id)

        dns_sql_last = DNSResolver.select(fn.Distinct(DNSResolver.ip)).where(DNSResolver.purge >> None,
                                                                             DNSResolver.add != self.code_id)

        # dns_sql_add = DNSResolver.select(fn.Distinct(DNSResolver.ip)).where(DNSResolver.purge >> None,
        #                                                                     DNSResolver.add == self.code_id,
        #                                                                     ~(DNSResolver.ip << dns_sql_last))

        dns_sql_purge = DNSResolver.select(fn.Distinct(DNSResolver.ip)).where(DNSResolver.purge >> None,
                                                                              DNSResolver.add != self.code_id,
                                                                              ~(DNSResolver.ip << dns_sql_new))

        count_purge = DNSResolver.update(purge=self.code_id).where(DNSResolver.purge >> None,
                                                                   DNSResolver.ip << dns_sql_purge).execute()

        logger.info('Resolver mark ip as old in table DNSResolver: %d', count_purge)

        count_dup = DNSResolver.delete().where(DNSResolver.purge >> None, DNSResolver.add == self.code_id,
                                               DNSResolver.ip << dns_sql_last).execute()

        logger.info('Resolver delete dup ip in table DNSResolver: %d', count_dup)

    def query_v4(self):
        all_replies = set()
        with self.transact.atomic():
            for domain in self.domain_sql:
                for resolver in self.resolvers:
                    try:
                        replies = resolver.query(str(domain.domain).replace('*.', ''), 'A')
                        for reply in replies:
                            all_replies.add(reply.address)
                    except dns.exception.DNSException:
                        pass
                if len(all_replies):
                    for ip in all_replies:
                        logger.info('Resolver add domain: %s, ip: %s', domain.domain, ip)
                        DNSResolver.create(domain=domain.domain, ip=ip, add=self.code_id)
                    all_replies.clear()

    def query_v6(self):
        logger.info('Resolver ipv6 run')
        all_replies = set()
        with self.transact.atomic():
            for domain in self.domain_sql:
                for resolver in self.resolvers:
                    try:
                        replies = resolver.query(domain.domain, 'AAAA')
                        for reply in replies:
                            all_replies.add(reply.address)
                    except dns.exception.DNSException:
                        pass
                if len(all_replies):
                    for ipv6 in all_replies:
                        logger.info('Resolver add domain: %s, ipv6: %s', domain.domain, ipv6)
                        DNSResolver.create(domain=domain.domain, ip=ipv6, mask=128, version=6, add=self.code_id)
                    all_replies.clear()

    def cleaner(self):
        private_nets = ['0.%', '127.%', '192.168.%', '10.%', '172.16.%', '172.17.%', '172.18.%', '172.19.%', '172.20.%',
                        '172.21.%', '172.22.%', '172.23.%', '172.24.%', '172.25.%', '172.26.%', '172.27.%', '172.28.%',
                        '172.29.%', '172.30.%', '172.31.%']
        logger.info('Resolver cleaner run')
        history_del = History.select(History.id).order_by(History.id.desc()).offset(self.cfg.DiffCount())
        count = DNSResolver.delete().where(DNSResolver.purge << history_del).execute()
        logger.info('History cleaner Table DNSResolver delete row %d', count)
        for net in private_nets:
            ip_count = DNSResolver.delete().where(DNSResolver.ip % net).execute()
            if ip_count:
                logger.info('IP error LIKE %s, count %d', net, ip_count)

        History.update(resolver=True).where(History.id == self.code_id).execute()
        history_inconsist_sql = History.select().where(History.resolver == False)
        reslov_inconsist_count = DNSResolver.delete().where(DNSResolver.add << history_inconsist_sql).execute()
        DNSResolver.update(purge=None).where(DNSResolver.purge << history_inconsist_sql).execute()
        logger.info('Delete rows incomplete resolving process %d', reslov_inconsist_count)

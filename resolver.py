#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# __author__ = 'maximus'

import dns.resolver
import logging
from db import History, IP, DNSResolver
from peewee import fn

logger = logging.getLogger(__name__)


class Resolver:
    def __init__(self, cfg, reporter, code_id):
        self.code_id = code_id
        self.cfg = cfg
        self.reporter = reporter
        self.domain_sql = self.reporter.domain_rollback_sql(0, 'ignore')

        self.dns_servers = str(cfg.DNS()).split(' ')
        self.resolvers = [dns.resolver.Resolver(configure=False) for i in range(len(self.dns_servers))]
        for resolver, dns_server in zip(self.resolvers, self.dns_servers):
            resolver.nameservers = [dns_server]

    def query(self):
        self.query_v4()
        if self.cfg.IPv6():
            self.query_v6()
        DNSResolver.update(purge=self.code_id).where(DNSResolver.add != self.code_id,
                                                     DNSResolver.purge >> None).execute()

    def query_v4(self):
        all_replies = set()
        for domain in self.domain_sql:
            for resolver in self.resolvers:
                try:
                    replies = resolver.query(domain.domain, 'A')
                    for reply in replies:
                        all_replies.add(reply)
                except dns.exception.DNSException:
                    pass
            ip_sql = IP.select(fn.Distinct(IP.ip), IP.mask).where(IP.mask == 32, IP.ip << list(all_replies))
            for ip in ip_sql:
                all_replies.remove(ip.ip)
            if len(all_replies):
                for ip in all_replies:
                    DNSResolver.create(domain=domain.domain, ip=ip, add=self.code_id)
                all_replies.clear()

    def query_v6(self):
        all_replies = set()
        for domain in self.domain_sql:
            for resolver in self.resolvers:
                try:
                    replies = resolver.query(domain.domain, 'AAAA')
                    for reply in replies:
                        all_replies.add(reply)
                except dns.exception.DNSException:
                    pass
            if len(all_replies):
                for ipv6 in all_replies:
                    DNSResolver.create(domain=domain.domain, ip=ipv6, mask=128, version=6, add=self.code_id)
                all_replies.clear()

    def cleaner(self):
        logger.info('Resolver cleaner run')
        history_del = History.select(History.id).order_by(History.id.desc()).offset(self.cfg.DiffCount())
        DNSResolver.delete().where(DNSResolver.purge << history_del).execute()

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
        logger.info('Resolver init')
        self.code_id = code_id
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
        DNSResolver.update(purge=self.code_id).where(DNSResolver.add != self.code_id,
                                                     DNSResolver.purge >> None).execute()

    def query_v4(self):
        logger.info('Resolver ipv4 run')
        all_replies = set()
        for domain in self.domain_sql:
            for resolver in self.resolvers:
                try:
                    replies = resolver.query(domain.domain, 'A')
                    for reply in replies:
                        all_replies.add(reply.address)
                except dns.exception.DNSException:
                    pass
            ip_sql = IP.select(fn.Distinct(IP.ip), IP.mask).where(IP.mask == 32, IP.ip << list(all_replies))
            for ip in ip_sql:
                all_replies.remove(ip.ip)
            if len(all_replies):
                for ip in all_replies:
                    logger.info('Resolver add domain: %s, ip: %s', domain.domain, ip)
                    DNSResolver.create(domain=domain.domain, ip=ip, add=self.code_id)
                all_replies.clear()

    def query_v6(self):
        logger.info('Resolver ipv6 run')
        all_replies = set()
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
        logger.info('Table DNSResolver delete row %d', count)
        for net in private_nets:
            ip_count = IP.delete().where(IP.ip % net).execute()
            if ip_count:
                logger.info('IP error LIKE %s, count %d', net, ip_count)


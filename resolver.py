#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# __author__ = 'maximus'

import dns.resolver
from db import Domain, IP
from peewee import fn
from config import Config


class Resolve:
    def __init__(self, cfg):
        self.cfg = cfg
        self.resolver = dns.resolver.Resolver()
        self.resolver.nameservers = str(cfg.DNS()).strip()

    def get_domain(self):
        pass

    def query(self):
        pass

    def check_ip(self):
        pass

    def write_ip_db(self):
        pass
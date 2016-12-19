#!/usr/bin/env python3
# -*- coding: utf-8 -*-


__author__ = 'Prototype-X'

import configparser
import os


class ConfigException(RuntimeError):
    pass


class Config(object):
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.optionxform = str
        path_cfg = str(os.path.dirname(os.path.abspath(__file__)))
        if os.path.exists(path_cfg + '/bl-rkn.cfg'):
            try:
                self.config.read(path_cfg + '/bl-rkn.cfg')
            except configparser.ParsingError:
                print('Config bl-rkn.cfg syntax error')
                exit()
        elif not os.path.exists(path_cfg + '/bl-rkn.cfg'):
            self.config.add_section('DataBase')
            self.config.set('DataBase', 'Type', '0')
            self.config.set('DataBase', 'Name', 'blacklist')
            self.config.set('DataBase', 'Host', 'localhost')
            self.config.set('DataBase', 'Port', '5432')
            self.config.set('DataBase', 'User', 'User')
            self.config.set('DataBase', 'Password', 'Password')
            self.config.add_section('Log')
            self.config.set('Log', 'LogRewrite', '1')
            self.config.set('Log', 'LogPathFName', 'bl-rkn.log')
            self.config.add_section('Notify')
            self.config.set('Notify', 'Notify', '0')
            self.config.set('Notify', 'Auth', '0')
            self.config.set('Notify', 'StartTLS', '0')
            self.config.set('Notify', 'Server', 'localhost')
            self.config.set('Notify', 'Port', '25')
            self.config.set('Notify', 'Subject', 'vigruzki.rkn.gov.ru ver. 2.2 update')
            self.config.set('Notify', 'From', 'zapret-info@rsoc.ru')
            self.config.set('Notify', 'To', '1@mail.ru')
            self.config.add_section('Request')
            self.config.set('Request', 'GenerateRequest', '0')
            self.config.set('Request', 'OperatorName', 'ООО "телеком"')
            self.config.set('Request', 'inn', '1234567890')
            self.config.set('Request', 'ogrn', '1234567891234')
            self.config.set('Request', 'email', '1@ru')
            self.config.set('Request', 'XMLPathFName', 'request.xml')
            self.config.set('Request', 'P7SPathFName', 'request.xml.p7s')
            self.config.set('Request', 'PEMPathFName', 'cert.pem')
            self.config.set('Request', 'ID', '123456789abcdef00000000000000001')
            self.config.add_section('History')
            self.config.set('History', 'HistoryCount', '0')
            self.config.set('History', 'DiffCount', '1')
            self.config.add_section('Dump')
            self.config.set('Dump', 'DumpFileSave', '1')
            self.config.set('Dump', 'DumpPath', '')
            self.config.set('Dump', 'GetResultMaxCount', '10')
            self.config.add_section('Resolver')
            self.config.set('Resolver', 'Resolver', '0')
            self.config.set('Resolver', 'QueryTimeout', '0.5')
            self.config.set('Resolver', 'IPv6', '0')
            self.config.set('Resolver', 'DNS', '8.8.8.8 8.8.4.4 77.88.8.8 77.88.8.1')
            self.config.add_section('OpenSSL')
            self.config.set('OpenSSL', 'Path', '')
            with open(path_cfg + '/bl-rkn.cfg', 'w') as configfile:
                self.config.write(configfile)

    def Type(self):
        try:
            dbtype = self.config.getint('DataBase', 'Type')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section DataBase or option Type in config file')
            dbtype = 0
            exit()
        return dbtype

    def Name(self):
        try:
            name = self.config.get('DataBase', 'Name')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section DataBase or option Name in config file')
            name = 'blacklist'
            exit()
        return name

    def Host(self):
        try:
            host = self.config.get('DataBase', 'Host')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section DataBase or option Host in config file')
            host = 'localhost'
            exit()
        return host

    def Port(self):
        try:
            port = self.config.getint('DataBase', 'Port')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section DataBase or option MySQLPort in config file')
            port = '5432'
            exit()
        return port

    def User(self):
        try:
            user = self.config.get('DataBase', 'User')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section DataBase or option MySQLUser in config file')
            user = 'User'
            exit()
        return user

    def Password(self):
        try:
            pwd = self.config.get('DataBase', 'Password')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section DataBase or option Password in config file')
            pwd = 'Password'
            exit()
        return pwd

    def LogRewrite(self):
        try:
            log = self.config.getboolean('Log', 'LogRewrite')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Log or option Log in config file')
            log = True
            exit()
        return log

    def LogPathFName(self):
        try:
            log_path = self.config.get('Log', 'LogPathFName')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Log or option LogPathFName in config file')
            log_path = 'bl-rkn.log'
            exit()
        return log_path

    def Notify(self):
        try:
            notify = self.config.getboolean('Notify', 'Notify')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Notify or option Notify in config file')
            notify = False
            exit()
        return notify

    def MailServer(self):
        try:
            mail_server = self.config.get('Notify', 'Server')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Notify or option Server in config file')
            mail_server = 'localhost'
            exit()
        return mail_server

    def MailPort(self):
        try:
            mail_port = self.config.get('Notify', 'Port')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Notify or option Port in config file')
            mail_port = '25'
            exit()
        return mail_port

    def MailAuth(self):
        try:
            mail_auth = self.config.getboolean('Notify', 'Auth')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Notify or option Auth in config file')
            mail_auth = False
            exit()
        return mail_auth

    def StartTLS(self):
        try:
            starttls = self.config.getboolean('Notify', 'StartTLS')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Notify or option StartTLS in config file')
            starttls = False
            exit()
        return starttls

    def MailLogin(self):
        try:
            mail_login = self.config.get('Notify', 'Login')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Notify or option Login in config file')
            mail_login = ''
            exit()
        return mail_login

    def MailPassword(self):
        try:
            mail_password = self.config.get('Notify', 'Password')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Notify or option Password in config file')
            mail_password = ''
            exit()
        return mail_password

    def MailSubject(self):
        try:
            mail_subject = self.config.get('Notify', 'Subject')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Notify or option Subject in config file')
            mail_subject = 'vigruzki.rkn.gov.ru ver. 2.2 update'
            exit()
        return mail_subject

    def MailFrom(self):
        try:
            from_mail = self.config.get('Notify', 'From')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Notify or option From in config file')
            from_mail = 'zapret-info@rsoc.ru'
            exit()
        return from_mail

    def MailTo(self):
        try:
            to_mail = self.config.get('Notify', 'To')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Notify or option To in config file')
            to_mail = '1@mail.ru'
            exit()
        return to_mail

    def GenRequest(self):
        try:
            gen_request = self.config.getboolean('Request', 'GenerateRequest')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Request or option GenerateRequest in config file')
            gen_request = False
            exit()
        return gen_request

    def OperatorName(self):
        try:
            operator = self.config.get('Request', 'OperatorName')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Request or option OperatorName in config file')
            operator = 'ООО "Телеком"'
            exit()
        return operator

    def inn(self):
        try:
            inn = self.config.getint('Request', 'inn')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Request or option inn in config file')
            inn = '1234567890'
            exit()
        return inn

    def ogrn(self):
        try:
            ogrn = self.config.getint('Request', 'ogrn')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Request or option Request in config file')
            ogrn = '1234567891234'
            exit()
        return ogrn

    def email(self):
        try:
            email = self.config.get('Request', 'email')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Request or option email in config file')
            email = '1@ru'
            exit()
        return email

    def XMLPathFName(self):
        try:
            xml_path = self.config.get('Request', 'XMLPathFName')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Request or option XMLPathFName in config file')
            xml_path = 'request.xml'
            exit()
        return xml_path

    def P7SPathFName(self):
        try:
            p7s_path = self.config.get('Request', 'P7SPathFName')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Request or option P7SPathFName in config file')
            p7s_path = 'request.xml.p7s'
            exit()
        return p7s_path

    def PEMPathFName(self):
        try:
            pem_path = self.config.get('Request', 'PEMPathFName')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Request or option PEMPathFName in config file')
            pem_path = 'cert.pem'
            exit()
        return pem_path

    def ID(self):
        try:
            id_path = self.config.get('Request', 'ID')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Request or option ID in config file')
            id_path = '123456789abcdef00000000000000001'
            exit()
        return id_path

    def HistoryCount(self):
        try:
            history_count = self.config.get('History', 'HistoryCount')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section History or option HistoryCount in config file')
            history_count = '0'
            exit()
        return int(history_count)

    def DiffCount(self):
        try:
            diff_count = self.config.get('History', 'DiffCount')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section History or option DiffCount in config file')
            diff_count = '1'
            exit()
        return int(diff_count)

    def DumpFileSave(self):
        try:
            file_save = self.config.getboolean('Dump', 'DumpFileSave')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Dump or option DumpFileSave in config file')
            file_save = True
            exit()
        return file_save

    def DumpPath(self):
        try:
            dump_path = self.config.get('Dump', 'DumpPath')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Dump or option DumpPath in config file')
            dump_path = ''
            exit()
        return dump_path

    def GetResultMaxCount(self):
        try:
            result_count = self.config.getint('Dump', 'GetResultMaxCount')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Dump or option GetResultMaxCount in config file')
            result_count = 3
            exit()
        return result_count

    def OpenSSL(self):
        try:
            path = self.config.get('OpenSSL', 'Path')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section OpenSSL or option Path in config file')
            path = ''
            exit()
        return path

    def Resolver(self):
        try:
            res = self.config.getboolean('Resolver', 'Resolver')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Resolver or option Resolver in config file')
            res = False
            exit()
        return res

    def QueryTimeout(self):
        try:
            timeout = self.config.getfloat('Resolver', 'QueryTimeout')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Resolver or option QueryTimeout in config file')
            timeout = 0.5
            exit()
        return timeout

    def IPv6(self):
        try:
            ipv6 = self.config.getboolean('Resolver', 'IPv6')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Resolver or option IPv6 in config file')
            ipv6 = False
            exit()
        return ipv6

    def DNS(self):
        try:
            dns = self.config.get('Resolver', 'DNS')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Resolver or option DNS in config file')
            dns = '8.8.8.8 77.88.8.1'
            exit()
        return dns

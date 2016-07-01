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
            self.config.set('DataBase', 'MySQL', '0')
            self.config.set('DataBase', 'MySQLUser', 'User')
            self.config.set('DataBase', 'MySQLPassword', 'Password')
            self.config.set('DataBase', 'MySQLHost', 'localhost')
            self.config.set('DataBase', 'MySQLPort', '3306')
            self.config.set('DataBase', 'DBName', 'blacklist')
            self.config.add_section('Log')
            self.config.set('Log', 'LogRewrite', '1')
            self.config.set('Log', 'LogPathFName', 'bl-rkn.log')
            self.config.add_section('Notify')
            self.config.set('Notify', 'Notify', '0')
            self.config.set('Notify', 'FromMailAddress', 'zapret-info@rsoc.ru')
            self.config.set('Notify', 'ToMailAddress', '1@mail.ru')
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
            self.config.add_section('Dump')
            self.config.set('Dump', 'DumpFileSave', '1')
            self.config.set('Dump', 'GetResultMaxCount', '10')
            with open(path_cfg + '/bl-rkn.cfg', 'w') as configfile:
                self.config.write(configfile)

    def MySQL(self):
        try:
            mysql = self.config.getboolean('DataBase', 'MySQL')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section DataBase or option MySQL in config file')
            mysql = 0
            exit()
        return mysql

    def MySQLUser(self):
        try:
            mysql_user = self.config.get('DataBase', 'MySQLUser')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section DataBase or option MySQLUser in config file')
            mysql_user = 'User'
            exit()
        return mysql_user

    def MySQLPassword(self):
        try:
            mysql_pwd = self.config.get('DataBase', 'MySQLPassword')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section DataBase or option MySQLPassword in config file')
            mysql_pwd = 'Password'
            exit()
        return mysql_pwd

    def MySQLHost(self):
        try:
            mysql_host = self.config.get('DataBase', 'MySQLHost')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section DataBase or option MySQLHost in config file')
            mysql_host = 'localhost'
            exit()
        return mysql_host

    def MySQLPort(self):
        try:
            mysql_port = self.config.getint('DataBase', 'MySQLPort')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section DataBase or option MySQLPort in config file')
            mysql_port = '3306'
            exit()
        return mysql_port

    def DBName(self):
        try:
            db_name = self.config.get('DataBase', 'DBName')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section DataBase or option DBName in config file')
            db_name = 'blacklist'
            exit()
        return db_name

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

    def Auth(self):
        try:
            auth = self.config.getboolean('Notify', 'Auth')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Notify or option Auth in config file')
            auth = False
            exit()
        return auth

    def FromMail(self):
        try:
            from_mail = self.config.get('Notify', 'FromMailAddress')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Notify or option FromMailAddress in config file')
            from_mail = 'zapret-info@rsoc.ru'
            exit()
        return from_mail

    def ToMail(self):
        try:
            to_mail = self.config.get('Notify', 'ToMailAddress')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Notify or option ToMailAddress in config file')
            to_mail = '1@mail.ru'
            exit()
        return to_mail

    def MailServer(self):
        try:
            mail_server = self.config.get('Notify', 'Server')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Notify or option Server in config file')
            mail_server = 'localhost'
            exit()
        return mail_server

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
            operator = 'ООО "телеком"'
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
        return history_count

    def DumpFileSave(self):
        try:
            file_save = self.config.getboolean('Dump', 'DumpFileSave')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Dump or option DumpFileSave in config file')
            file_save = True
            exit()
        return file_save

    def GetResultMaxCount(self):
        try:
            result_count = self.config.getint('Dump', 'GetResultMaxCount')
        except (configparser.NoOptionError, configparser.NoSectionError):
            print('Error section Dump or option GetResultMaxCount in config file')
            result_count = '10'
            exit()
        return result_count

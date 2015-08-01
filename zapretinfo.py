#!/usr/bin/env python3
# -*- coding: utf-8 -*-


__version__ = "0.0.9"
__author__ = "yegorov.p@gmail.com, https://github.com/yegorov-p/python-zapret-info"

import suds.client
from base64 import b64encode
import os

API_URL = "http://vigruzki.rkn.gov.ru/services/OperatorRequest/?wsdl"
# API_URL = "http://vigruzki.rkn.gov.ru/services/OperatorRequestTest/?wsdl"


class ZapretInfoException(RuntimeError):
    pass


class ZapretInfo(object):

    def __init__(self):
        self.client = suds.client.Client(API_URL)

    def getLastDumpDateEx(self):
        """
        Метод предназначен для получения временной метки последнего обновления выгрузки из реестра,
        а также для получения информации о версиях веб-сервиса, памятки и текущего формата выгрузки.
        """
        result = self.client.service.getLastDumpDateEx()
        return result

    def getLastDumpDate(self):
        """
        Оставлен для совместимости. Аналогичен getLastDumpDateEx, но возвращает только один
        параметр lastDumpDate.
        """
        result = self.client.service.getLastDumpDate()
        return result

    def sendRequest(self, requestFile, signatureFile, versionNum='2.2'):
        """
        Метод предназначен для направления запроса на получение выгрузки из реестра.
        """
        if not os.path.exists(requestFile):
            raise ZapretInfoException('No request file')
        if not os.path.exists(signatureFile):
            raise ZapretInfoException('No signature file')

        with open(requestFile, "rb") as f:
            data = f.read()

        xml = b64encode(data)
        xml = xml.decode('utf-8')

        with open(signatureFile, "rb") as f:
            data = f.read()

        sert = b64encode(data)
        sert = sert.decode('utf-8')

        result = self.client.service.sendRequest(xml, sert, versionNum)
        return dict((k, v) for (k, v) in result)

    def getResult(self, code):
        """
        Метод предназначен для получения результата обработки запроса - выгрузки из реестра
        """
        result = self.client.service.getResult(code)
        return dict((k, v) for (k, v) in result)

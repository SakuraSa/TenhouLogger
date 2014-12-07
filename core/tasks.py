#!/usr/bin/env python
# coding = utf-8

"""
core.tasks
"""

__author__ = 'Rnd495'

import re
import os
import json

import requests
from celery import exceptions as celery_exceptions
from celery import Celery

from configs import Configs, ConfigsError

configs = Configs.instance()

if not configs.celery_backend_url or not configs.celery_broker_url:
    raise ConfigsError(message="ConfigsError: celery setting was null")

module_name = os.path.splitext(os.path.split(__file__)[1])[0]
celery = Celery(module_name, backend=configs.celery_backend_url, broker=configs.celery_broker_url)


@celery.task
def celery_test():
    return "ok"


# test celery service
if not configs.is_celery_server_side:
    try:
        celery_test.delay().get(timeout=1)
    except celery_exceptions.TimeoutError:
        raise ConfigsError("ConfigsError: celery server timeout. maybe server is down.")


class FetchError(Exception):
    """
    FetchError
    this exception can be raised when fetching data from other website
    this exception can carry an inner exception
    """

    def __init__(self, message='Fetch Log Error', inner_exception=None):
        Exception.__init__(self)
        self.message = message
        self.inner_exception = inner_exception

    def __str__(self):
        return self.message

    def __repr__(self):
        return "%s(%s)" % (type(self).__name__, self.message)


REF_REGEX = re.compile(configs.tenhou_ref_regex)


@celery.task
def fetch_tenhou_log_string(ref):
    """
    fetch Tenhou log's json string
    can raise FetchError

    :type ref: str|unicode
    :rtype: unicode
    :param ref: ref of the Tenhou log
    :return: log's json string(unicode)
    """
    matches = REF_REGEX.findall(ref)
    if not matches:
        raise FetchError("Illegal ref: %s" % ref)
    else:
        ref = matches[0]
    url = configs.tenhou_log_url
    headers = {
        "Host": url.split("/")[2],
        "Referer": url,
    }
    response = requests.get(url, params=ref, headers=headers)
    if response.status_code != 200:
        raise FetchError("Illegal status: [%d]%s" % (response.status_code, response.reason))
    try:
        if not response.text.startswith("{"):
            raise ValueError("ValueError: json string should begin with '{'")
        json.loads(response.text)
    except ValueError, _ex:
        raise FetchError("Illegal json string: %s" % response.text, _ex)
    return response.text


RECORDS_REG = re.compile(configs.tenhou_records_regex)


@celery.task
def fetch_tenhou_records(player_name):
    """
    fetch one Tenhou player's all records
    can raise FetchError

    :type player_name: str
    :param player_name: record's owner-player's name
    :return: records string
    """
    url = configs.tenhou_records_url
    params = {
        'name': player_name
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise FetchError("Illegal status: [%d]%s" % (response.status_code, response.reason))
    match = REF_REGEX.search(response.text)
    if not match:
        raise FetchError("Illegal response content: can not match with r\"%s\"" % configs.tenhou_records_regex)
    try:
        return match.group("records")
    except IndexError:
        raise FetchError("Illegal records regex string: do not contains \"records\" group")
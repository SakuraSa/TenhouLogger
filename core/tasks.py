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
try:
    celery_test.delay().get(timeout=1)
except celery_exceptions.TimeoutError:
    raise ConfigsError("ConfigsError: celery server timeout. maybe server is down.")


class FetchLogError(Exception):
    """
    FetchLogError
    """

    def __init__(self, message='Fetch Log Error', inner_exception=None):
        Exception.__init__(self)
        self.message = message
        self.inner_exception = inner_exception

    def __str__(self):
        return self.message

    def __repr__(self):
        return "FetchLogError(%s)" % self.message


REF_REGEX = re.compile(configs.tenhou_ref_regex)


@celery.task
def fetch_tenhou_log(ref):
    """
    fetch Tenhou log's json string
    can raise FetchLogError

    :type ref: str|unicode
    :rtype: unicode
    :param ref: ref of the Tenhou log
    :return: log's json string(unicode)
    """
    matches = REF_REGEX.findall(ref)
    if not matches:
        raise FetchLogError("Illegal ref: %s" % ref)
    else:
        ref = matches[0]
    base = "http://tenhou.net/5/mjlog2json.cgi?%(ref)s"
    url = base % {'ref': ref}
    headers = {
        "Host": "tenhou.net",
        "Referer": url,
    }
    rsp = requests.get(url, headers=headers)
    if rsp.status_code != 200:
        raise FetchLogError("Illegal status: [%d]%s" % (rsp.status_code, rsp.reason))
    try:
        if not rsp.text.startswith("{"):
            raise ValueError("ValueError: json string should begin with '{'")
        js = json.dumps(rsp.text)
    except ValueError, _ex:
        raise FetchLogError("Illegal json string: %s" % rsp.text, _ex)
    return js
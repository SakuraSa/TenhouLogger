#!/usr/bin/env python
# coding = utf-8

"""
Manager
"""

import os
import tornado.web
import Page
from core.configs import Configs

__author__ = 'Rnd495'

page_dict = dict()
module_dict = dict()
configs = Configs.instance()


def mapping(mapping_path):
    """
    map page or module to path
    :param mapping_path: path
    :return: page or module
    """
    def wrapper(target):
        if issubclass(target, Page.PageBase):
            if mapping_path in page_dict:
                raise KeyError("KeyError: page '%s' is already registered." % mapping_path)
            return page_dict.setdefault(mapping_path, target)
        elif issubclass(target, tornado.web.UIModule):
            if mapping_path in module_dict:
                raise KeyError("KeyError: module '%s' is already registered." % mapping_path)
            return module_dict.setdefault(mapping_path, target)
        else:
            raise TypeError("TypeError: unknown type '%s' registered." % repr(target))
    return wrapper


def create_app():
    return tornado.web.Application(
        handlers=[
            (path, page)
            for path, page in page_dict.iteritems()
        ],
        ui_modules=module_dict,
        gzip=configs.gzip,
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        cookie_secret=configs.cookie_secret
    )
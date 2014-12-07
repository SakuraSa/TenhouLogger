#!/usr/bin/env python
# coding = utf-8

"""
Page
"""

__author__ = 'Rnd495'

import tornado.web

import core.models
from core.models import User
from core.configs import Configs
from UI.Manager import mapping

configs = Configs.instance()


class PageBase(tornado.web.RequestHandler):
    """
    PageBase
    """
    def __init__(self, application, request, **kwargs):
        tornado.web.RequestHandler.__init__(self, application, request, **kwargs)
        self.db = core.models.get_global_session()
        self._current_user = None

    def get_current_user(self):
        user_id = self.get_secure_cookie("user_id", None)
        if user_id:
            self._current_user = self.db.query(User).filter(User.id == user_id).first()
        else:
            self._current_user = None
        return self._current_user

    def get_login_url(self):
        return '/login'

    def data_received(self, chunk):
        return tornado.web.RequestHandler.data_received(self, chunk)


@mapping('/login')
class PageLogin(PageBase):
    """
    PageLogin
    """
    def __init__(self, application, request, **kwargs):
        tornado.web.RequestHandler.__init__(self, application, request, **kwargs)

    def get(self):
        return self.render('login.html')


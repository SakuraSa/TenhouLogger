#!/usr/bin/env python
# coding = utf-8

"""
Page
"""

__author__ = 'Rnd495'

import tornado.web
import tornado.gen

import core.models
from core import verification
from core import tasks
from core.models import User, GameLog
from core.configs import Configs
from core.celeryIOLoop import CeleryIOLoop
from UI.Manager import mapping

configs = Configs.instance()
celery = CeleryIOLoop()


class PageBase(tornado.web.RequestHandler):
    """
    PageBase
    """
    def __init__(self, application, request, **kwargs):
        tornado.web.RequestHandler.__init__(self, application, request, **kwargs)
        self._current_user = None

    @property
    def db(self):
        return core.models.get_global_session()

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
        PageBase.__init__(self, application, request, **kwargs)

    def get(self):
        return self.render('login.html')

    @verification.check
    def post(self):
        username = self.get_body_argument('username')
        password = self.get_body_argument('password')
        password = User.password_hash(password)
        remember = self.get_body_argument('remember-me', None)
        expire = 30 if remember else 1
        user = self.db.query(User).filter(User.name == username, User.pwd == password).first()
        if not user:
            redirect = self.get_argument('next', '/')
            self.redirect('/login?next=%s' % redirect)
        else:
            self.set_secure_cookie("user_id", str(user.id), expire)
            redirect = self.get_argument('next', '/user/dashboard?user_id=%d' % user.id)
            self.redirect(redirect)


@mapping('/logout')
class PageLogout(PageBase):
    """
    PageLogout
    """
    def __init__(self, application, request, **kwargs):
        PageBase.__init__(self, application, request, **kwargs)

    def get(self):
        self.clear_cookie('user_id')
        redirect = self.get_argument('next', '/')
        self.redirect(redirect)


@mapping('/')
class PageHome(PageBase):
    """
    PageHome
    """
    def __init__(self, application, request, **kwargs):
        PageBase.__init__(self, application, request, **kwargs)

    def get(self):
        user = self.current_user
        if user:
            self.redirect('/user/dashboard?user_id=%d' % user.id)
        else:
            return self.render('home.html')


@mapping('/api/get_username_availability')
class APIGetUsernameAvailability(PageBase):
    """
    APIGetUsernameAvailability
    """
    def get(self):
        name = self.get_query_argument('username')
        user_count = self.db.query(User).filter(User.name == name).count()
        self.write({'success': True, 'message': user_count == 0})


@mapping('/api/game_log_ref_upload')
class APIGameLogRefUpload(PageBase):
    """
    APIGameLogRefUpload
    """
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        ref = self.get_body_argument('ref')
        user_id_str = self.get_secure_cookie('user_id', None)
        user_id = int(user_id_str) if user_id_str else None
        try:
            message = yield celery.async(tasks.fetch_and_save_tenhou_log, ref=ref, upload_user_id=user_id)
            self.write({'success': True, 'message': message})
        except tasks.FetchError, _ex:
            self.write({'success': False, 'message': repr(_ex)})
        finally:
            self.finish()


@mapping('/api/player_name_check')
class APIPlayerNameCheck(PageBase):
    """
    APIPlayerNameCheck
    """
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        player_name = self.get_body_argument('name')
        try:
            message = yield celery.async(tasks.fetch_and_save_tenhou_records, player_name=player_name)
            self.write({'success': True, 'message': message})
        except tasks.FetchError, _ex:
            self.write({'success': False, 'message': repr(_ex)})
        finally:
            self.finish()
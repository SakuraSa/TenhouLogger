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


@mapping('/register')
class PageRegister(PageBase):
    """
    PageRegister
    """
    def __init__(self, application, request, **kwargs):
        PageBase.__init__(self, application, request, **kwargs)

    def get(self):
        self.render('register.html')

    @verification.check
    def post(self):
        username = self.get_body_argument('username')
        password = self.get_body_argument('password')
        password_confirm = self.get_body_argument('password_confirm')

        # register param check
        # password confirm
        if password != password_confirm:
            raise tornado.web.HTTPError(400, log_message='password dismatch with password confirm.')
        # username availability check
        result = APIGetUsernameAvailability.check(username=username, check_exists=True)
        if not result['availability']:
            raise tornado.web.HTTPError(400, log_message=result['reason'])
        # username availability check
        if not password:
            raise tornado.web.HTTPError(400, log_message='password can not be empty')

        # register new user
        user = core.models.User(name=username, pwd=password, role_id=3, calculate_point=1000)
        self.db.add(user)
        self.db.commit()

        # redirect to login page
        self.redirect('/login')

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
    def __init__(self, application, request, **kwargs):
        PageBase.__init__(self, application, request, **kwargs)

    def get(self):
        username = self.get_query_argument('username')
        self.write(APIGetUsernameAvailability.check(username=username, check_exists=True))

    @classmethod
    def check(cls, username, check_exists=True):
        if not username:
            return dict(availability=False, reason='username can not be empty.')
        if len(username) > 16:
            return dict(availability=False, reason='username "%s" is too long.' % username)
        if check_exists and core.models.get_global_session().query(User).filter(User.name == username).count() > 0:
            return dict(availability=False, reason='username "%s" is already exists.' % username)
        return dict(availability=True, reason='ok')


@mapping('/api/create_verification_code')
class APICreateVerificationCode(PageBase):
    """
    APICreateVerificationCode
    """
    def __init__(self, application, request, **kwargs):
        PageBase.__init__(self, application, request, **kwargs)

    def get(self):
        code = verification.Verification.instance().new()
        self.write({'uuid': code.uuid, 'image': code.image})


@mapping('/api/game_log_ref_upload')
class APIGameLogRefUpload(PageBase):
    """
    APIGameLogRefUpload
    """
    def __init__(self, application, request, **kwargs):
        PageBase.__init__(self, application, request, **kwargs)

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
    def __init__(self, application, request, **kwargs):
        PageBase.__init__(self, application, request, **kwargs)

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
#!/usr/bin/env python
# coding = utf-8

"""
core.models
"""

__author__ = 'Rnd495'

import datetime

import hashlib
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from configs import Configs

configs = Configs.instance()
Base = declarative_base()


class User(Base):
    __tablename__ = 'T_User'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(length=64), nullable=False)
    pwd = Column(String(length=128), nullable=False)
    role_id = Column(Integer, nullable=False, index=Index('index_role_id'))
    register_time = Column(DateTime, nullable=False)
    calculate_point = Column(Integer, nullable=False)

    def __init__(self, name, pwd, role_id=0, calculate_point=1000):
        self.name = name
        self.pwd = User.password_hash(pwd)
        self.register_time = datetime.datetime.now()
        self.role_id = role_id
        self.calculate_point = calculate_point

    def __repr__(self):
        return "<%s[%s]: %s>" % (type(self).__name__, self.id, self.name)

    def get_is_same_password(self, password):
        return User.password_hash(password) == self.pwd

    def set_password(self, password):
        self.pwd = User.password_hash(password)

    @staticmethod
    def password_hash(text):
        return hashlib.sha256(text + configs.user_password_hash_salt).hexdigest()


class Role(Base):
    __tablename__ = 'T_Role'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(length=64), nullable=False)

    def __init__(self, name, id=None):
        self.name = name
        if id is not None:
            self.id = id

    def __repr__(self):
        return "<%s[%s]: %s>" % (type(self).__name__, self.id, self.name)


class Model(Base):
    __tablename__ = 'T_Model'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(length=64), nullable=False)
    url = Column(String(length=128), nullable=False)
    parent_model_id = Column(Integer, default=None)

    def __init__(self, name, url, parent_model_id=None):
        self.name = name
        self.url = url
        self.parent_model_id = parent_model_id

    def __repr__(self):
        return "<%s[%s]: \"%s\" %s>" % (type(self).__name__, self.id, self.name, self.parent_model_id)


class RoleAndModel(Base):
    __tablename__ = 'T_RoleAndModel'

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, nullable=False, index=Index('index_role_id'))
    model_id = Column(Integer, nullable=False, index=Index('index_model_id'))

    def __init__(self, role_id, model_id):
        self.role_id = role_id
        self.model_id = model_id

    def __repr__(self):
        return "<%s[%s]: %s - %s>" % (type(self).__name__, self.id, self.role_id, self.model_id)


class Player(Base):
    __tablename__ = 'T_Player'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(length=64), nullable=False, index=Index('index_name'))
    owner_user_id = Column(Integer, default=None, index=Index('index_owner_user_id'))
    last_check_records_time = Column(DateTime, default=None)

    def __init__(self, name, owner_user_id=None):
        self.name = name
        self.owner_user_id = owner_user_id

    def __repr__(self):
        return "<%s[%s]: %s>" % (type(self).__name__, self.id, self.name)


class GameLog(Base):
    __tablename__ = 'T_GameLog'

    id = Column(Integer, primary_key=True, autoincrement=True)
    upload_time = Column(DateTime, nullable=False, index=Index('index_upload_time'))
    upload_user_id = Column(Integer, default=None, index=Index('index_upload_user_id'))
    play_time = Column(DateTime, nullable=False, index=Index('index_play_time'))
    lobby = Column(String(length=32), nullable=False, index=Index('index_lobby'))
    rule_cole = Column(String(length=8), nullable=False, index=Index('index_rule_cole'))
    ref_code = Column(String(length=32), nullable=False, index=Index('index_ref_cole'))
    json = Column(Text, nullable=False)

    def __repr__(self):
        return "<%s[%s]: %s>" % (type(self).__name__, self.id, self.ref_code)


class GameLogAndPlayer(Base):
    __tablename__ = 'T_GameLogAndPlayer'

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_log_id = Column(Integer, nullable=False, index=Index('index_game_log_id'))
    player_id = Column(Integer, nullable=False, index=Index('index_player_id'))

    def __repr__(self):
        return "<%s[%s]: %s->%s>" % (type(self).__name__, self.id, self.game_log_id, self.player_id)


class GameRecord(Base):
    __tablename__ = 'T_GameRecord'

    id = Column(Integer, primary_key=True, autoincrement=True)
    lobby = Column(String(length=32), nullable=False, index=Index('index_lobby'))
    play_time = Column(DateTime, nullable=False, index=Index('index_play_time'))
    rule_name = Column(String(length=32), nullable=False, index=Index('index_rule_name'))
    ref_code = Column(String(length=32), nullable=False, index=Index('index_ref_cole'))
    result_text = Column(String(length=300), nullable=False)

    def __repr__(self):
        return "<%s[%s]>" % (type(self).__name__, self.id)


class StatisticCache(Base):
    __tablename__ = 'T_StatisticCache'

    id = Column(Integer, primary_key=True, autoincrement=True)
    query_hash = Column(String(length=64), nullable=False, index=Index('index_ref_cole'))
    json = Column(Text, nullable=False)


_engine = None
_session_maker = None
_session = None


def get_engine():
    global _engine
    if not _engine:
        _engine = create_engine(configs.database_url, echo=False)
        Base.metadata.create_all(_engine)
    return _engine


def get_session_maker():
    global _session_maker
    if not _session_maker:
        _session_maker = sessionmaker(bind=get_engine())
    return _session_maker


def get_global_session():
    global _session
    if not _session:
        _session = _session_maker()
    return _session


def get_new_session():
    return get_session_maker()()

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
    role_id = Column(Integer, nullable=False)
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

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<%s[%s]: %s>" % (type(self).__name__, self.id, self.name)


class Model(Base):
    __tablename__ = 'T_Model'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(length=64), nullable=False)
    url = Column(String(length=128), nullable=False)
    parent_model_id = Column(Integer, default=None)

    def __init__(self, name, parent_model_id):
        self.name = name
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
    owner_user_id = Column(Integer, default=None)

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


class StatisticCache(Base):
    __tablename__ = 'T_StatisticCache'

    id = Column(Integer, primary_key=True, autoincrement=True)
    query_hash = Column(String(length=64), nullable=False, index=Index('index_ref_cole'))
    json = Column(Text, nullable=False)


def init():
    engine = create_engine(configs.database_url, echo=False)
    Base.metadata.create_all(engine)
    return engine

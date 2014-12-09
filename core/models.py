#!/usr/bin/env python
# coding = utf-8

"""
core.models
"""
import json

__author__ = 'Rnd495'

import re
import datetime

import hashlib
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, Float, String, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from configs import Configs

configs = Configs.instance()
Base = declarative_base()

REF_REGEX = re.compile(configs.tenhou_ref_regex)
RESULT_PT_REGEX = re.compile(configs.tenhou_result_pt_regex)
RECORDS_REGEX = re.compile(configs.tenhou_records_regex)


class User(Base):
    __tablename__ = 'T_User'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(length=64), nullable=False)
    pwd = Column(String(length=128), nullable=False)
    role_id = Column(Integer, nullable=False, index=Index('User_index_role_id'))
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
    role_id = Column(Integer, nullable=False, index=Index('RoleAndModel_index_role_id'))
    model_id = Column(Integer, nullable=False, index=Index('RoleAndModel_index_model_id'))

    def __init__(self, role_id, model_id):
        self.role_id = role_id
        self.model_id = model_id

    def __repr__(self):
        return "<%s[%s]: %s - %s>" % (type(self).__name__, self.id, self.role_id, self.model_id)


class Player(Base):
    __tablename__ = 'T_Player'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(length=64), nullable=False, index=Index('Player_index_name'))
    owner_user_id = Column(Integer, default=None, index=Index('Player_index_owner_user_id'))
    last_check_records_time = Column(DateTime, default=None)

    def __init__(self, name, owner_user_id=None):
        self.name = name
        self.owner_user_id = owner_user_id

    def __repr__(self):
        return "<%s[%s]: %s>" % (type(self).__name__, self.id, self.name)


class GameLog(Base):
    __tablename__ = 'T_GameLog'

    id = Column(Integer, primary_key=True, autoincrement=True)
    upload_time = Column(DateTime, nullable=False, index=Index('GameLog_index_upload_time'))
    upload_user_id = Column(Integer, default=None, index=Index('GameLog_index_upload_user_id'))
    play_time = Column(DateTime, nullable=False, index=Index('GameLog_index_play_time'))
    lobby = Column(String(length=32), nullable=False, index=Index('GameLog_index_lobby'))
    rule_cole = Column(String(length=8), nullable=False, index=Index('GameLog_index_rule_cole'))
    ref_code = Column(String(length=32), nullable=False, index=Index('GameLog_index_ref_cole'))
    json = Column(Text, nullable=False)

    def __init__(self, upload_user_id, json_string):
        self.upload_user_id = upload_user_id
        self.upload_time = datetime.datetime.now()
        self.json = json_string
        self.extract_info_from_json()
        self.player_names = None

    def extract_info_from_json(self):
        js = json.loads(self.json)
        self.ref_code = js['ref']
        time_str, self.rule_cole, self.lobby, uuid = js['ref'].split('-')
        self.play_time = datetime.datetime.strptime(time_str, '%Y%m%d%Hgm')
        self.player_names = js['name']

    def __repr__(self):
        return "<%s[%s]: %s>" % (type(self).__name__, self.id, self.ref_code)


class GameLogAndPlayer(Base):
    __tablename__ = 'T_GameLogAndPlayer'

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_log_id = Column(Integer, nullable=False, index=Index('GameLogAndPlayer_index_game_log_id'))
    player_id = Column(Integer, nullable=False, index=Index('GameLogAndPlayer_index_player_id'))

    def __init__(self, game_log_id, player_id):
        self.game_log_id = game_log_id
        self.player_id = player_id

    def __repr__(self):
        return "<%s[%s]: %s->%s>" % (type(self).__name__, self.id, self.game_log_id, self.player_id)


class GameRecord(Base):
    __tablename__ = 'T_GameRecord'

    id = Column(Integer, primary_key=True, autoincrement=True)
    hash = Column(String(length=32), nullable=False, unique=True)
    lobby = Column(String(length=32), nullable=False, index=Index('GameRecord_index_lobby'))
    play_time = Column(DateTime, nullable=False, index=Index('GameRecord_index_play_time'))
    time_cost = Column(Integer, nullable=False)
    rule_name = Column(String(length=32), nullable=False, index=Index('GameRecord_index_rule_name'))
    ref_code = Column(String(length=32), nullable=False, index=Index('GameRecord_index_ref_cole'))
    record_line = Column(String(length=300), nullable=False)

    def __init__(self, record_line):
        self.hash = GameRecord.get_record_line_hash(record_line)
        info = GameRecord.extract_info_from_record_line(record_line)
        self.lobby = info['lobby']
        self.play_time = info['play_time']
        self.time_cost = info['time_cost']
        self.rule_name = info['rule_name']
        self.ref_code = info['ref_code']
        self.result = info['result']
        self.record_line = record_line.strip()

    def __repr__(self):
        return "<%s[%s]>" % (type(self).__name__, self.id)

    @classmethod
    def get_record_line_hash(cls, record_line):
        return hashlib.md5(record_line.strip()).hexdigest()

    # noinspection PyTypeChecker
    @staticmethod
    def extract_info_from_record_line(record_line):
        record_line = [part.strip() for part in record_line.strip().split('|', 6)]
        lobby = record_line[0].lstrip('L')
        time_cost = int(record_line[1]) if record_line[1].isalnum() else None
        play_time = datetime.datetime.strptime(' '.join(record_line[2:4]), '%Y-%m-%d %H:%M')
        rule_name = record_line[4]
        ref_code = next(REF_REGEX.finditer(record_line[5])) if record_line[5] != '---' else None
        result = record_line[6]
        pts = RESULT_PT_REGEX.findall(result)
        names = [name.strip() for name in RESULT_PT_REGEX.split(result)]
        result = zip(names, pts)
        result.sort(key=lambda pair: pair[1], reverse=True)
        return {
            'lobby': lobby,
            'time_cost': time_cost,
            'play_time': play_time,
            'rule_name': rule_name,
            'ref_code': ref_code,
            'result': result
        }


class GameRecordAndPlayer(Base):
    __tablename = 'T_GameRecordAndPlayer'

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_record_id = Column(Integer, nullable=False, index=Index('GameRecordAndPlayer_index_game_record_id'))
    player_id = Column(Integer, nullable=False, index=Index('GameLogAndPlayer_index_player_id'))
    point_delta = Column(Float, nullable=False)
    rank = Column(Integer, nullable=False)

    def __init__(self, game_record_id, player_id, point_delta, rank):
        self.game_record_id = game_record_id
        self.player_id = player_id
        self.point_delta = point_delta
        self.rank = rank

    def __repr__(self):
        return "<%s[%s]>" % (type(self).__name__, self.id)


class StatisticCache(Base):
    __tablename__ = 'T_StatisticCache'

    id = Column(Integer, primary_key=True, autoincrement=True)
    query_hash = Column(String(length=64), nullable=False, index=Index('StatisticCache_index_ref_cole'))
    json = Column(Text, nullable=False)

    def __init__(self, query_hash, json_string):
        self.query_hash = query_hash
        self.json = json_string

    def __repr__(self):
        return "<%s[%s]>" % (type(self).__name__, self.id)


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
        _session = get_session_maker()()
    return _session


def get_new_session():
    return get_session_maker()()

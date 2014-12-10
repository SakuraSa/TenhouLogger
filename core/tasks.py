#!/usr/bin/env python
# coding = utf-8

"""
core.tasks
"""
import datetime

__author__ = 'Rnd495'

import re
import os
import json
import time
import urllib

import requests
from celery import exceptions as celery_exceptions
from celery import Celery

from models import get_global_session
from models import GameLog, GameLogAndPlayer, Player, GameRecord, GameRecordAndPlayer
from configs import Configs, ConfigsError

configs = Configs.instance()

if not configs.celery_backend_url or not configs.celery_broker_url:
    raise ConfigsError(message="ConfigsError: celery setting was null")

module_name = os.path.splitext(os.path.split(__file__)[1])[0]
celery = Celery(module_name, backend=configs.celery_backend_url, broker=configs.celery_broker_url)

REF_REGEX = re.compile(configs.tenhou_ref_regex)
RESULT_PT_REGEX = re.compile(configs.tenhou_result_pt_regex)
RECORDS_REGEX = re.compile(configs.tenhou_records_regex)


@celery.task(name='task.celery_test')
def celery_test():
    return "ok"


# test celery service
if not configs.is_celery_server_side:
    try:
        begin = time.time()
        celery_test.delay().get(timeout=1)
        cost = (time.time() - begin) * 1000
        print "celery server is online with %dms lag" % cost
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


def check_ref(ref):
    matches = REF_REGEX.findall(ref)
    if not matches:
        raise FetchError("Illegal ref: %s" % ref)
    else:
        ref = matches[0]
    return ref


@celery.task(name='task.fetch_tenhou_log_string')
def fetch_tenhou_log_string(ref):
    """
    fetch Tenhou log's json string
    can raise FetchError

    :type ref: str|unicode
    :rtype: unicode
    :param ref: ref of the Tenhou log
    :return: log's json string(unicode)
    """
    ref = check_ref(ref)
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


def get_player_id_by_name(name, auto_create=False, auto_commit=False):
    session = get_global_session()
    player = session.query(Player).filter(Player.name == name).first()
    if not player and auto_create:
        player = Player(name)
        session.add(player)
        if auto_commit:
            session.commit()
    return player


@celery.task(name='task.fetch_and_save_tenhou_log')
def fetch_and_save_tenhou_log(ref, upload_user_id=None):
    session = get_global_session()
    ref = check_ref(ref)
    game_log = session.query(GameLog).filter(GameLog.ref_code == ref).first()
    if not game_log:
        json_string = fetch_tenhou_log_string(ref)
        game_log = GameLog(upload_user_id, json_string)
        session.add(game_log)
        # create GameLogAndPlayer
        for name in game_log.player_names:
            player = get_player_id_by_name(name, auto_create=True)
            session.add(GameLogAndPlayer(game_log.id, player.id))
        session.commit()
        return 'ok'
    else:
        return 'already uploaded'


@celery.task(name='task.fetch_tenhou_records')
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
    match = RECORDS_REGEX.search(response.text)
    if not match:
        raise FetchError("Illegal response content: can not match with r\"%s\"" % configs.tenhou_records_regex)
    try:
        return match.group("records")
    except IndexError:
        raise FetchError("Illegal records regex string: do not contains \"records\" group")


@celery.task(name='task.fetch_and_save_tenhou_records')
def fetch_and_save_tenhou_records(player_name):
    session = get_global_session()
    records_text = fetch_tenhou_records(player_name)
    records_lines = [line.strip() for line in records_text.split("<br>") if line.strip()]

    # check query target player
    player = session.query(Player).filter(Player.name == player_name).first()
    if not player:
        player = Player(player_name)
        session.add(player)
        session.commit()

    # check frequency
    now = datetime.datetime.now()
    check_point = now + datetime.timedelta(days=1)
    if not player.last_check_records_time or player.last_check_records_time > check_point:
        player.last_check_records_time = now
        session.commit()
    else:
        return "player was checked in %s, please wait for 1 day" % player.last_check_records_time

    # create all game_record
    game_record_list = []
    player_id_name_dict = dict()
    for line in records_lines:
        hash_string = GameRecord.get_record_line_hash(line)
        if session.query(GameRecord).filter(GameRecord.hash == hash_string).count() > 0:
            continue
        try:
            game_record = GameRecord(line)
        except IndexError, _ex:
            print _ex
            continue
        game_record_list.append(game_record)

    if len(game_record_list) == 0:
        return "player \"%s\" is not found" % player_name

    # get all player name
    for game_record in game_record_list:
        for name, pt in game_record.result:
            if name in player_id_name_dict:
                continue
            else:
                player_id_name_dict[name] = None

    # check all player name
    new_player_list = []
    for name in player_id_name_dict.keys():
        player = session.query(Player).filter(Player.name == name).first()
        if player:
            player_id_name_dict[name] = player.id
        else:
            new_player_list.append(Player(name))

    # add new player
    for player in new_player_list:
        session.add(player)

    # add new game_record
    for game_record in game_record_list:
        session.add(game_record)

    # create player.id and game_record.id
    session.commit()

    # get new player id
    for player in new_player_list:
        player_id_name_dict[player.name] = player.id

    # create game_record_and_player
    for game_record in game_record_list:
        for rank, (name, pt) in enumerate(game_record.result):
            player_id = player_id_name_dict[name]
            game_record_and_player = GameRecordAndPlayer(game_record.id, player_id, pt, rank + 1)
            session.add(game_record_and_player)

    # save all
    session.commit()

    return '%d line records saved.' % len(records_lines)


def kick_player_from_tenhou_room(room_id, player_name):
    url = configs.tenhou_kick_api_url
    data = {
        "L": room_id,
        "UN": player_name
    }
    rsp = requests.post(url, data=data)
    return urllib.unquote(rsp.url[54:]).strip() == "OK"
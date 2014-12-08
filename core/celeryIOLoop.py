#!/usr/bin/env python
# coding = utf-8

"""
celeryIOLoop
"""

__author__ = 'Rnd495'

from tornado.concurrent import TracebackFuture
from tornado.ioloop import IOLoop


class CeleryIOLoop(object):
    """
    celeryIOLoop
    """

    def __init__(self, io_loop=None):
        object.__init__(self)
        self.io_loop = io_loop if io_loop else IOLoop.instance()

    def async(self, task, *args, **kwargs):
        future = TracebackFuture()
        if 'callback' in kwargs:
            callback = kwargs.pop('callback')
            self.io_loop.add_future(future, lambda _future: callback(_future.result()))
        result = task.delay(*args, **kwargs)
        self.io_loop.add_callback(self._on_result, result, future)
        return future

    def _on_result(self, result, future):
        # if result is not ready, add callback function to next loop,
        if result.ready():
            future.set_result(result.result)
        else:
            self.io_loop.add_callback(self._on_result, result, future)
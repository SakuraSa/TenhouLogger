#!/usr/bin/env python
# coding = utf-8

"""
UIModule
"""

__author__ = 'Rnd495'

import tornado.web
from Manager import mapping


@mapping(r'title')
class UITitle(tornado.web.UIModule):
    def render(self, title, subtitle=''):
        return self.render_string('ui/title.html', title=title, subtitle=subtitle)



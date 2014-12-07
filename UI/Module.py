#!/usr/bin/env python
# coding = utf-8

"""
UIModule
"""

__author__ = 'Rnd495'

import tornado.web

import core.verification
from Manager import mapping


@mapping(r'verification')
class UIVerification(tornado.web.UIModule):

    def render(self):
        code = core.verification.Verification.instance().new()
        return self.render_string('ui/verification.html', code=code)

    def javascript_files(self):
        return "/static/js/verification-img-modal-popup.js"


@mapping(r'title')
class UITitle(tornado.web.UIModule):
    def render(self, title, subtitle=''):
        return self.render_string('ui/title.html', title=title, subtitle=subtitle)



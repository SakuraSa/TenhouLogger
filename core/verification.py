#!/usr/bin/env python
# coding=utf-8

"""
core.verification
"""
import functools
import tornado.web

__author__ = 'Rnd495'

import time
import hashlib
import random
from cStringIO import StringIO
try:
    # import from pillow
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    # import from PIL
    import Image
    import ImageDraw
    import ImageFont


class Verification(object):
    def __init__(self, available_count=10, available_time=60):
        object.__init__(self)
        self.available_count = available_count
        self.available_time = available_time
        self.code_length = 4
        self.code_alpha = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        self.code_alike = {'O': '0', 'o': '0', 'I': '1', 'l': '1'}
        self.code_color = ((20, 15, 50), (50, 15, 20), (15, 20, 50))
        self.image_size = (100, 40)
        self.image_background_color = (200, 200, 200, 200)
        self.image_font = ImageFont.truetype(filename="consola.ttf", size=int(self.image_size[1] * 0.8))
        self.image_rotation = 60.0
        self.image_offset = 10
        self.image_scalar = (0.8, 1.3)
        self.image_sample = Image.BICUBIC
        self.case_sensitive = False
        self.random = random.Random()
        self.container = {}
        self.drop_size = 100
        self.char_image = {}
        self.init_char_images()

    def create_code(self):
        buf = []
        for _ in range(self.code_length):
            buf.append(self.code_alpha[self.random.randint(0, len(self.code_alpha) - 1)])
        return "".join(buf)

    def init_char_images(self):
        for c in self.code_alpha:
            color = self.code_color[self.random.randint(0, len(self.code_color) - 1)]
            size = self.image_font.getsize(c)
            image = Image.new("RGBA", size, (0, 0, 0, 0))
            draw = ImageDraw.ImageDraw(image)
            draw.text((0, 0), c, color, self.image_font)
            self.char_image[c] = image

    def create_image(self, code):
        image = Image.new("RGBA", self.image_size, self.image_background_color)
        for i, c in enumerate(code):
            px = self.image_size[0] / 5 * i + self.image_offset * self.random.random() - self.image_offset / 2.0
            py = self.image_offset * self.random.random() - self.image_offset / 2.0
            pos = (int(px), int(py))
            rotation = self.random.random() * self.image_rotation - self.image_rotation / 2.0
            scalar = self.image_scalar[0] + self.random.random() * (self.image_scalar[1] - self.image_scalar[0])
            resize = (int(self.char_image[c].size[0] * scalar), int(self.char_image[c].size[1] * scalar))
            cm = self.char_image[c].resize(resize, self.image_sample).rotate(rotation, self.image_sample, True)
            image.paste(cm, (pos[0], pos[1]), cm)
        stream = StringIO()
        image.save(stream, 'png')
        return "data:image/png;base64," + stream.getvalue().encode("base64")

    def new(self):
        code = self.create_code()
        image = self.create_image(code)
        vc = VerificationCode(code,
                              image,
                              self.available_count,
                              self.available_time,
                              self.case_sensitive,
                              self.code_alike)
        self.container[vc.uuid] = vc
        return vc

    def check(self, uuid, code):
        if len(self.container) > self.drop_size:
            self.drop()
        verification_code = self.container.get(uuid, None)
        if verification_code is None:
            return False
        if verification_code.check(code):
            return True
        if not verification_code.is_available():
            del self.container[verification_code.uuid]
        return False

    def drop(self):
        count = 0
        for verification_code in self.container.values():
            if not verification_code.is_available():
                count += 1
                del self.container[verification_code.uuid]
        return count

    @classmethod
    def instance(cls):
        if not hasattr(cls, '__instance__'):
            cls.__instance__ = cls()
        return cls.__instance__


class VerificationCode(object):
    def __init__(self, code, image, available_count, available_time, case_sensitive, code_alike):
        object.__init__(self)
        self.uuid = hashlib.sha256("%s-%s" % (hex(id(self)), hex(int(time.time() * 1000)))).hexdigest()
        self.begin_timestamp = time.time()
        self.count = 0
        self.code = ''.join(code_alike.get(c, c) for c in code)
        self.image = image
        self.available_count = available_count
        self.available_time = available_time
        self.case_sensitive = case_sensitive
        self.code_alike = code_alike

    def is_time_available(self):
        return (time.time() - self.begin_timestamp) <= self.available_time

    def is_count_available(self):
        return self.count <= self.available_count

    def is_available(self):
        return self.is_time_available() and self.is_count_available()

    def check(self, code):
        code = ''.join(self.code_alike.get(c, c) for c in code)
        self.count += 1
        if self.is_available():
            if self.case_sensitive:
                if code == self.code:
                    return True
            else:
                if code.lower() == self.code.lower():
                    return True
        return False


def check(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        code = self.get_argument("ver_code")
        uuid = self.get_argument("ver_uuid")
        success = Verification.instance().check(uuid, code)
        if not success:
            raise tornado.web.HTTPError(400, log_message="verification check failed.")
        else:
            return method(self, *args, **kwargs)
    return wrapper

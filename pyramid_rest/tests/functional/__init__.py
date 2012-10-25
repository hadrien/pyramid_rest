# -*- coding: utf-8 -*-
import unittest

import webtest

from pyramid.decorator import reify


class TestController(unittest.TestCase):

    @reify
    def config(self):
        from pyramid.config import Configurator
        from pyramid_rest import includeme
        config = Configurator(settings=None)
        config.include(includeme)
        return config


class TestExampleController(TestController):

    @reify
    def app(self):
        from pyramid_rest.tests.functional import example
        reload(example) # :-Q
        self.config.scan(example)
        self.config.commit()
        return webtest.TestApp(self.config.make_wsgi_app())

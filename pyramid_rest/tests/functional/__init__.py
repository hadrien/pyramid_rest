# -*- coding: utf-8 -*-
import unittest

import webtest

from pyramid.config import Configurator
from pyramid.decorator import reify
from pyramid.exceptions import ConfigurationConflictError


class TestExampleController(unittest.TestCase):

    _config = None

    @reify
    def app(self):
        return webtest.TestApp(self.config.make_wsgi_app())

    @property
    def config(self):
        if TestExampleController._config is None:
            _config = Configurator(settings={})
            _config.include('example')
            TestExampleController._config = _config
        return TestExampleController._config

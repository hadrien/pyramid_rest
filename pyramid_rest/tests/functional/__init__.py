# -*- coding: utf-8 -*-
from __future__ import absolute_import
import sys
import unittest

import webtest

from pyramid import testing


class TestExampleController(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('example')
        self.config.commit()
        self.app = webtest.TestApp(self.config.make_wsgi_app())

    @property
    def mongo_db(self):
        from pyramid_rest.mongo import IMongoConnection, DATABASE_NAME
        return getattr(
            self.app.app.registry.getUtility(IMongoConnection),
            DATABASE_NAME
            )

    def tearDown(self):
        testing.tearDown()
        for m in list(sys.modules):
            if 'example' in m:
                del sys.modules[m]

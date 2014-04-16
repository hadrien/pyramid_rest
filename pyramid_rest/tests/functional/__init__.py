import os
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
        from pyramid_mongokit import IMongoConnection
        return getattr(
            self.app.app.registry.getUtility(
                IMongoConnection,
                'mongo_connection',
                ),
            os.environ['MONGO_DB_NAME']
            )

    def tearDown(self):
        testing.tearDown()
        for m in list(sys.modules):
            if 'example' in m:
                del sys.modules[m]

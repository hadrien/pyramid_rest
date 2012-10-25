# -*- coding: utf-8 -*-
from pyramid_rest.tests.functional import TestExampleController



class TestResource(TestExampleController):

    def test_method_not_allowed(self):
        result = self.app.put('/users/123', status=405)


class TestResource2(TestExampleController):

    def test_method_not_allowed(self):
        result = self.app.put('/users/123', status=405)

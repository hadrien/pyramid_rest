# -*- coding: utf-8 -*-
from pyramid_rest.tests.functional import TestExampleController


class TestRenderer(TestExampleController):

    def test_bson_renderer(self):
        from pyramid_rest.renderer import json_loads, bson_loads

        result1 = self.app.get(
            '/applications',
            headers={'Accept': 'application/bson'},
            )
        result1 = bson_loads(result1.body)

        result2 = self.app.get(
            '/applications',
            headers={'Accept': 'application/json'},
            )
        result2 = json_loads(result2.body)

        self.assertEqual(result1, result2)

        expected = {
            u'data': [
                {u'id': 1, u'name': u'App 1'},
                {u'id': 2, u'name': u'App 2'},
                {u'id': 3, u'name': u'App 3'},
                {u'id': 4, u'name': u'App 4'},
                ]
            }

        self.assertEqual(expected, result1)

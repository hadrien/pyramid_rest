# -*- coding: utf-8 -*-
import unittest
from decimal import Decimal
from bson.objectid import ObjectId


class TestJsonDump(unittest.TestCase):

    def test_dumps(self):
        from pyramid_rest.renderer import json_dumps
        result = json_dumps({'key': Decimal('0.2')})

        self.assertEqual(
            '{"key": 0.2}',
            result
            )


class TestBson(unittest.TestCase):

    def test_encode_decode(self):
        from pyramid_rest.renderer import bson_dumps, bson_loads

        o = {
            '_id': ObjectId('50aab36b9978d001f3be41b6'),
            'unicode': u"yéééé",
            'float': 1.2,
            }

        result = bson_loads(bson_dumps(o))

        self.assertEqual(o, result)


class TestRestFactory(unittest.TestCase):

    def test_call(self):
        from pyramid_rest.renderer import Factory

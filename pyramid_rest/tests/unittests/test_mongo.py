# -*- coding: utf-8 -*-
import unittest


class TestMongo(unittest.TestCase):

    def test_no_document(self):
        from pyramid_rest.mongo import CollectionView
        with self.assertRaises(Exception):
            CollectionView(None, None)

# -*- coding: utf-8 -*-
from bson.objectid import ObjectId

from pyramid.httpexceptions import HTTPBadRequest

from pyramid_rest.tests.functional import TestExampleController


class TestCollectionView(TestExampleController):

    def setUp(self):
        super(TestCollectionView, self).setUp()

        app = self.mongo_db.Application()
        app.name = u'An Application?'
        app.secret_key = u'secret'

        app.save()

        user = self.mongo_db.User()
        user.name = u'Bob Marley'
        user.application_id = app._id
        user.save()

        self.app_id = str(app._id)
        self.user_id = str(user._id)

    def tearDown(self):
        self.mongo_db.application.drop()
        self.mongo_db.user.drop()
        self.mongo_db.message.drop()

        super(TestCollectionView, self).tearDown()

    def test_create(self):
        result = self.app.post(
            '/applications/%s/users/%s/messages' % (self.app_id, self.user_id),
            {u'from': u'Peter Tosh', u'content': u'yo man'}
            )

        json_body = self.app.get(result.location).json

        message = self.mongo_db.Message.find_one(
            {'_id': ObjectId(json_body['_id'])}
            )
        self.assertTrue(message)
        self.assertEqual(u'Peter Tosh', message['from'])
        self.assertEqual(u'yo man', message.content)
        self.assertEqual(self.app_id, str(message.application_id))
        self.assertEqual(self.user_id, str(message.user_id))

        expected = 'http://localhost/applications/%s/users/%s/messages/%s' % (
            self.app_id,
            self.user_id,
            message['_id'],
            )
        self.assertEqual(expected, result.location)

    def test_create_missing_required(self):
        with self.assertRaises(HTTPBadRequest):
            self.app.post(
                '/applications/%s/users/%s/messages' % (
                    self.app_id,
                    self.user_id,
                    ),
                {u'from': u'Peter Tosh'},
                status=400
                )

    def test_update(self):
        message = self.mongo_db.Message(doc={
            'application_id': ObjectId(self.app_id),
            'user_id': ObjectId(self.user_id),
            'from': u'Peter Tosh',
            'content': u'yo man',
            })
        message.save()

        self.app.put(
            '/applications/%s/users/%s/messages/%s' % (
                self.app_id, self.user_id, str(message._id)
                ),
            {u'content': u'yo man 2'}
            )

        result = self.mongo_db.Message.find_one({'_id': message._id})

        self.assertEqual(u'yo man 2', result.content)

    def test_delete(self):
        pass

# -*- coding: utf-8 -*-
from pyramid_rest.tests.functional import TestExampleController


class TestResource(TestExampleController):

    def test_method_not_allowed(self):
        result = self.app.put('/users/123', status=405)
        pass

    def test_application(self):
        self.app.get('/applications/1', status=405)
        self.app.get('/applications/1/edit', status=405)
        self.app.get('/applications/new', status=405)
        self.app.post('/applications', status=405)

        self.assertEqual([
            dict(id=1, name='App 1'),
            dict(id=2, name='App 2'),
            dict(id=3, name='App 3'),
            dict(id=4, name='App 4'),
            ],
            self.app.get('/applications').json,
            )

        self.assertEqual({}, self.app.put('/applications/1').json)
        self.assertEqual({}, self.app.post('/applications/1?_method=PUT').json)

        self.assertEqual({}, self.app.delete('/applications/1').json)
        self.assertEqual({}, self.app.delete('/applications/1?_method=DELETE').json)

    def test_application_users(self):
        self.assertEqual(
            [dict(id='1', name='User 1'),
            dict(id='2', name='User 2'),
            dict(id='3', name='User 3'),
            dict(id='4', name='User 4'),
            ],
            self.app.get('/applications/1/users').json
            )

        self.assertEqual(
            dict(id='1', name= 'User 1'),
            self.app.get('/applications/1/users/1').json,
            )

        self.app.post('/applications/1/users', status=405)
        self.app.put('/applications/1/users/1', status=405)
        self.app.get('/applications/1/users/1/edit', status=405)
        self.app.get('/applications/1/users/new', status=405)
        self.app.post('/applications/1/users', status=405)

    def test_application_media(self):
        self.app.get('/applications/1/media', status=405)
        self.app.get('/applications/1/media/1', status=405)
        self.app.get('/applications/1/media/new', status=405)
        self.app.get('/applications/1/media/edit', status=405)

        self.app.post('/applications/1/media', status=405)
        self.app.put('/applications/1/media/1', status=405)
        self.app.delete('/applications/1/media/1', status=405)

        self.app.post('/applications/1/media/1?_method=DELETE', status=405)


    def test_view_not_found(self):
        self.assertRaises(ImportError, self.config.add_resource, 'no.such.resource')


# -*- coding: utf-8 -*-
import unittest

import mock


class TestIncludeme(unittest.TestCase):

    @mock.patch('pyramid_rest.ResourceUtility')
    def test_includeme(self, m_utility):
        from pyramid_rest import (
            includeme,
            RequestMethodEventPredicate,
            override_request_method,
            NewRequest,
            )

        config = mock.Mock()
        config.registry.settings.get.return_value = 'true'

        includeme(config)

        config.registry.registerUtility.assert_called_once_with(
            m_utility.return_value
            )

        config.registry.settings.get.assert_called_once_with(
            'pyramid_rest.tunneling',
            'true',
            )

        config.add_subscriber_predicate.assert_called_once_with(
            'request_methods',
            RequestMethodEventPredicate
            )


        config.add_subscriber.assert_called_once_with(
            override_request_method,
            NewRequest,
            request_methods=['POST'],
            )

    def test_includeme_no_tunnelling(self):
        from pyramid_rest import includeme

        config = mock.Mock()
        config.registry.settings.get.return_value = 'false'

        includeme(config)

        self.assertFalse(config.add_subscriber_predicate.called)
        self.assertFalse(config.add_subscriber.called)


class TestRequestMethodEventPredicate(unittest.TestCase):

    def test_predicate(self):
        from pyramid_rest import RequestMethodEventPredicate

        pred = RequestMethodEventPredicate(['PUT', 'DELETE',], None)

        self.assertEqual(
            'request_method in %s' % ['PUT', 'DELETE'],
            pred.text()
            )

        self.assertEqual(['PUT', 'DELETE',], pred.methods)

        event = mock.Mock()
        event.request.method = 'PUT'

        self.assertTrue(pred(event))

        event.request.method = 'DELETE'
        self.assertTrue(pred(event))

        event.request.method = 'POST'
        self.assertFalse(pred(event))


class TestOverridRequestMethod(unittest.TestCase):

    def test_override_with_header(self):
        from pyramid_rest import override_request_method

        event = mock.Mock()
        event.request.headers.get.return_value = 'PUT'

        override_request_method(event)

        self.assertEqual('PUT', event.request.method)

    def test_override_with_query_param(self):
        from pyramid_rest import override_request_method

        event = mock.Mock()
        event.request.headers.get.return_value = None
        event.request.GET.get.return_value = 'DELETE'

        override_request_method(event)

        self.assertEqual('DELETE', event.request.method)

    def test_wrong_override(self):
        from pyramid_rest import override_request_method

        event = mock.Mock()
        event.request.headers.get.return_value = 'POST'
        event.request.method = 'GET'

        override_request_method(event)

        self.assertEqual('GET', event.request.method)

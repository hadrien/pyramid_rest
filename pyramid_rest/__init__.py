# -*- coding: utf-8 -*-
import functools
import logging

from pyramid.events import NewRequest
from pyramid.settings import asbool

from pyramid_rest.resource import (
    ResourceConfigurator,
    rest_resource_url,
    rest_resource_path,
    )

log = logging.getLogger(__name__)


class RequestMethodEventPredicate(object):

    def __init__(self, methods, config):
        self.methods = methods
        self.phash = self.text

    def __call__(self, event):
        return event.request.method in self.methods

    def text(self):
        return 'request_method in %s' % self.methods


def override_request_method(event):
    methods = ['PUT', 'DELETE']
    override = (
        event.request.headers.get('X-HTTP-Method-Override') or
        event.request.GET.get('_method', '').upper()
        )

    if override in methods:
        event.request.method = override


def includeme(config):
    log.info('Including pyramid_rest')

    utility = ResourceConfigurator()

    config.registry.registerUtility(utility)

    config.add_renderer(
        'pyramid_rest_renderer',
        'pyramid_rest.renderer.Factory'
        )

    config.add_directive('add_resource', utility.add_resource)
    config.add_directive(
        'add_singular_resource',
        functools.partial(utility.add_resource, singular=True),
        )
    config.add_request_method(rest_resource_url, 'rest_resource_url')
    config.add_request_method(rest_resource_path, 'rest_resource_path')

    if asbool(config.registry.settings.get('pyramid_rest.tunneling', 'true')):
        config.add_subscriber_predicate(
            'request_methods',
            RequestMethodEventPredicate
            )

        config.add_subscriber(
            override_request_method,
            NewRequest,
            request_methods=['POST'],
            )

    if asbool(config.registry.settings.get('pyramid_rest.mongo', 'true')):
        config.include('pyramid_rest.mongo')

    config.commit()

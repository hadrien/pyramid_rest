# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import logging

import mongokit
from bson.objectid import ObjectId

from pyramid.decorator import reify
from pyramid.events import NewRequest

from zope.interface import implementer
from zope.interface import Interface

from pyramid_rest.resource import ResourceAdded

log = logging.getLogger(__name__)

DATABASE_NAME = os.environ['MONGO_DB_NAME']

__all__ = ['register_document', 'CollectionView', ]


def includeme(config):
    log.info('Configure mongo...')
    connection = MongoConnection(
        os.environ['MONGO_URI'],
        auto_start_request=False,
        tz_aware=True,
        )
    config.registry.registerUtility(connection)
    config.add_request_method(
        mongo_connection,
        'mongo_connection',
        reify=True,
        )
    config.add_request_method(mongo_db, 'mongo_db', reify=True)
    config.add_subscriber(begin_request, NewRequest)
    config.add_subscriber(resource_added, ResourceAdded)
    log.info('Mongo configured...')


def resource_added(event):
    resource = event.resource
    cls = getattr(resource, 'view_class', None)
    if cls is None or (not issubclass(cls, CollectionView)):
        return
    collection = getattr(cls, 'model_class', None)
    if collection is None:
        return

    mongo_conn = event.config.registry.getUtility(IMongoConnection)
    mongo_conn.register(collection)
    log.info('Registered collection %s on mongokit connection.', collection)


def register_document(registry, document_cls):
    registry.getUtility(IMongoConnection).register(document_cls)


class IMongoConnection(Interface):
    pass


@implementer(IMongoConnection)
class MongoConnection(mongokit.Connection):
    pass


def mongo_connection(request):
    return request.registry.getUtility(IMongoConnection)


def mongo_db(request):
    return getattr(request.mongo_connection, DATABASE_NAME)


def begin_request(event):
    """"""
    event.request.mongo_connection.start_request()
    event.request.add_finished_callback(end_request)


def end_request(request):
    request.mongo_connection.end_request()


class CollectionView(object):

    model_class = None

    def __init__(self, context, request):
        self.context = context
        self.request = request
        if self.model_class is None:
            raise Exception('model_class cannot be None')

    @reify
    def collection(self):
        # model_class.__collection__ or model_class.__name__ as collection name
        collection_name = getattr(
            self.model_class,
            '__collection__',
            self.model_class.__name__,
            )
        return getattr(self.request.mongo_db, collection_name)

    def index(self, **identifiers):
        parent_ids = {id_name: ObjectId(identifier)
                      for id_name, identifier in identifiers.items()}
        return {'data': list(self.collection.find(parent_ids))}

    def show(self, **identifiers):
        ids = {id_name: ObjectId(identifier)
               for id_name, identifier in identifiers.items()}
        ids['_id'] = ids.pop('id')
        return self.collection.find_one(ids)

# -*- coding: utf-8 -*-
import os
import logging
from urlparse import urlparse

from bson.objectid import ObjectId, InvalidId
import mongokit

from pyramid.decorator import reify
from pyramid.events import NewRequest
from pyramid.httpexceptions import (
    HTTPBadRequest,
    HTTPCreated,
    HTTPNotFound,
    HTTPOk,
    )

from zope.interface import implementer
from zope.interface import Interface

from pyramid_rest.resource import ResourceAdded

log = logging.getLogger(__name__)

__all__ = ['register_document', 'CollectionView', ]


def includeme(config):
    log.info('Configure mongo...')
    os.environ['MONGO_URL_NAME'] = urlparse(os.environ['MONGO_URI']).path[1:]
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
    return getattr(request.mongo_connection, os.environ['MONGO_DB_NAME'])


def begin_request(event):
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

    def _get_ids_dict(self, identifiers):
        """Convert ``str`` identifiers to ``ObjectId``"""
        try:
            ids = {id_name: ObjectId(identifier)
                   for id_name, identifier in identifiers.items()}
        except InvalidId:
            raise HTTPBadRequest('Invalid id in: %r' % identifiers)
        if 'id' in ids:
            ids['_id'] = ids.pop('id')
        return ids

    def _get_document_or_404(self, identifiers):
        document = self.document_cls.find_one(self._get_ids_dict(identifiers))
        if document is None:
            raise HTTPNotFound()
        return document

    @reify
    def collection(self):
        # model_class.__collection__ or model_class.__name__ as collection name
        collection_name = getattr(self.model_class, '__collection__')
        return getattr(self.request.mongo_db, collection_name)

    @reify
    def document_cls(self):
        return getattr(self.request.mongo_db, self.model_class.__name__)

    def index(self, **identifiers):
        parent_ids = self._get_ids_dict(identifiers)
        return {'data': list(self.collection.find(parent_ids))}

    def create(self, **identifiers):
        document = self.document_cls()
        document.update(self.request.POST)
        for k, v in self._get_ids_dict(identifiers).iteritems():
            document[k] = v
        try:
            document.save()
        except (mongokit.StructureError, mongokit.RequireFieldError):
            log.exception(
                'error while creating %s, POST: %s, ids: %s',
                self.context.resource,
                self.request.POST,
                identifiers,
                )
            raise HTTPBadRequest()

        ids = [identifiers[name]
               for name in self.context.resource.ids[:-1]]
        ids.append(document._id)

        location = self.request.rest_resource_url(
            self.context.resource.name,
            *ids
            )
        return HTTPCreated(location=location)

    def update(self, **identifiers):
        # XXX: full replace + etag + last-modified
        document = self._get_document_or_404(identifiers)
        for field, value in self.request.POST.iteritems():
            if field in identifiers or field not in document:
                continue
            document[field] = value
        document.save()
        return HTTPOk()

    def show(self, **identifiers):
        return self._get_document_or_404(identifiers)

    def delete(self, **identifiers):
        """No delete cascade on sub resources."""
        self._get_document_or_404(identifiers).delete()
        return HTTPOk()

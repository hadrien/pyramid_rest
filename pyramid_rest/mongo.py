# -*- coding: utf-8 -*-
import logging

from bson.objectid import ObjectId, InvalidId
import mongokit

from pyramid.decorator import reify
from pyramid.httpexceptions import (
    HTTPBadRequest,
    HTTPCreated,
    HTTPNotFound,
    HTTPOk,
    )

from pyramid_mongokit import register_document, IMongoConnection


from pyramid_rest.resource import ResourceAdded


log = logging.getLogger(__name__)

__all__ = ['register_document', 'CollectionView', ]


def includeme(config):
    config.include('pyramid_mongokit')
    config.add_subscriber(resource_added, ResourceAdded)


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


class CollectionView(object):

    model_class = None

    def __init__(self, context, request):
        self.context = context
        self.request = request
        if self.model_class is None:
            raise Exception('model_class cannot be None')

    def _get_ids_dict(self, identifiers):
        """Convert ``str`` identifiers to ``ObjectId``"""
        ids = identifiers.copy()
        if 'id' in ids:
            ids['_id'] = ids.pop('id')
        try:
            for key, value in ids.iteritems():
                try:
                    cls = self.model_class.structure[key]
                except KeyError:
                    cls = ObjectId
                ids[key] = cls(value)
        except (InvalidId, ValueError):
            log.debug('Invalid id in %r', identifiers, exc_info=True)
            raise HTTPBadRequest('Invalid id in: %r' % identifiers)

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
        ids.append(document['_id'])

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

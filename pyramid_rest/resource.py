# -*- coding: utf-8 -*-
import logging
import functools

from pyramid.httpexceptions import HTTPMethodNotAllowed

import venusian

from zope.interface import implementer
from zope.interface import Interface

log = logging.getLogger(__name__)


class ResourceViewMapper(object):

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, view):

        def wrapper(context, request):
            return view(
                context,
                request,
                *self._ordered_ids(request.matchdict)
                )

        return wrapper

    def _ordered_ids(self, matchdict):
        return [matchdict[_] for _ in sorted(matchdict.keys())]


class IResourceUtility(Interface):
    pass


@implementer(IResourceUtility)
class ResourceUtility(object):

    methods = dict(
        index='GET',
        create='POST',
        show='GET',
        update='PUT',
        delete='DELETE',
        )

    def __init__(self, config, separator='.'):
        self.config = config
        self.resources = dict()
        self.parent_resources = dict()
        self.deferred = dict()
        self.separator = separator

    def add_resource(self, resource):
        try:
            parent, child = resource.name.rsplit(self.separator, 1)
            if parent not in self.resources:
                self.deferred[resource.name] = resource
                return
        except ValueError:
            # no separator in resource name: it is a root resource
            parent = None
            child = resource.name

        if parent is None:
            self.parent_resources[resource.name] = resource
            resource.parent = None
            resource.depth = 0
            parent_pattern = ''
        else:
            # resource knows about parent
            resource.parent = self.resources[parent]
            # parent knows about new child
            resource.parent.children[resource.name] = resource
            resource.depth = resource.parent.depth + 1
            parent_pattern = resource.parent.pattern

        resource.route_name = "%s" % resource.name
        resource.item_route_name = "%s_item" % resource.name

        resource.collection_pattern = '%s/%s' % (
            parent_pattern,
            child,
            )
        # XXX: provides a way to specify id pattern
        resource.pattern = '%s/%s/{id%s}' % (
            parent_pattern,
            child,
            resource.depth
            )
        self._add_resource_routes(resource)
        self._add_resource_views(resource)

        log.info(
            'Add REST resource: %s, views: %s, parent: %s',
            resource.name,
            resource.views.keys(),
            resource.parent
            )
        self.resources[resource.name] = resource

        self._add_deferred_children_resource(resource)

    def _add_deferred_children_resource(self, parent_resource):
        for name, child_resource in self.deferred.items():
            parent_name, child_name = name.rsplit(self.separator, 1)
            if parent_name == parent_resource.name:
                self.deferred.pop(name)
                self.add_resource(child_resource)

    def _add_resource_routes(self, resource):
        self.config.add_route(
            pattern=resource.pattern,
            name=resource.item_route_name,
            factory=functools.partial(ResourceContext, resource),
            )
        self.config.add_route(
            pattern=resource.collection_pattern,
            name=resource.route_name,
            factory=functools.partial(ResourceContext, resource),
            )

    def _add_resource_views(self, resource):
        for method, (view, info) in resource.views.iteritems():
            self.config.add_view(
                view=view,
                mapper=ResourceViewMapper,
                attr=method,
                **self._get_view_predicates(resource, method)
                )

        not_allowed = [m for m in self.methods if m not in resource.views]

        def not_allowed_view(request):
            raise HTTPMethodNotAllowed()

        for method in not_allowed:
            self.config.add_view(
                view=not_allowed_view,
                **self._get_view_predicates(resource, method)
                )

    def _get_view_predicates(self, resource, method):
        predicates = dict()

        if method in ('index', 'create'):
            predicates.update(route_name=resource.route_name)
        else:
            predicates.update(route_name=resource.item_route_name)

        predicates.update(request_method=self.methods[method])

        return predicates


class Resource(object):
    "A REST resource"

    def __init__(self, resource_name):
        self.name = resource_name
        self.info = venusian.attach(self, self.callback)
        self.views = dict()
        self.children = dict()

        # define REST decorators
        for method in ('index', 'show', 'create', 'update', 'delete'):
            setattr(self, method, functools.partial(self.decorator, method))

    def __repr__(self):
        return "<%s_%s>" % (self.__class__.__name__, self.name)

    def decorator(self, method, **kwargs):
        def wrapper(view):
            info = venusian.attach(view, lambda x, y, z: None)
            if method in self.views:
                # XXX - Raise a conflict error
                pass
            self.views[method] = (view, info)
            return view
        return wrapper

    def view_class(self, **kwargs):
        def wrapper(cls):
            self.info = venusian.attach(self, self.callback)
            return cls
        return wrapper

    def callback(self, context, name, ob):
        registry = context.config.registry
        registry.getUtility(IResourceUtility).add_resource(self)


class ResourceContext(object):

    def __init__(self, resource, request):
        self.resource = resource
        self.request = request

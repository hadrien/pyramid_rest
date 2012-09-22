# -*- coding: utf-8 -*-
import logging
import functools

from pyramid.httpexceptions import HTTPMethodNotAllowed
from pyramid.config.util import ActionInfo, action_method

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


def not_allowed_view(request):
    raise HTTPMethodNotAllowed()


@implementer(IResourceUtility)
class ResourceUtility(object):

    methods = dict(
        index='GET',
        create='POST',
        show='GET',
        update='PUT',
        delete='DELETE',
        new='GET',
        edit='GET',
        )

    def __init__(self, separator='.'):
        self.resources = dict()
        self.parent_resources = dict()
        self.deferred = dict()
        self.separator = separator

    def add(self, config, resource):
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
            parent_pattern = resource.parent.item_pattern

        # routes names:
        resource.route_name = "%s" % resource.name
        resource.item_route_name = "%s_item" % resource.name
        resource.new_route_name = '%s_new' % resource.name
        resource.edit_route_name = '%s_edit' % resource.name


        # routes patterns
        resource.pattern = '%s/%s' % (parent_pattern, child)
        # XXX: provides a way to specify id pattern
        resource.item_pattern = '%s/%s/{id%s}' % (
            parent_pattern,
            child,
            resource.depth
            )
        resource.new_pattern = '%s/new' % resource.pattern
        resource.edit_pattern = '%s/edit' % resource.item_pattern
        # modify the stack info for accurate source code info in introspection.
        config._ainfo.append(ActionInfo(*resource.info.codeinfo))
        self._add_routes(config, resource)
        self._add_views(config, resource)
        self._add_introspection(config, resource)
        config._ainfo.pop()

        log.info(
            'Add REST resource: %s, views: %s, parent: %s',
            resource.name,
            resource.views.keys(),
            resource.parent
            )
        self.resources[resource.name] = resource

        self._add_deferred_children(config, resource)

    def _add_deferred_children(self, config, parent_resource):
        for name, child_resource in self.deferred.items():
            parent_name, child_name = name.rsplit(self.separator, 1)
            if parent_name == parent_resource.name:
                self.deferred.pop(name)
                self.add(config, child_resource)

    def _add_routes(self, config, resource):
        config.add_route(
            pattern=resource.item_pattern,
            name=resource.item_route_name,
            factory=functools.partial(ResourceContext, resource),
            )
        config.add_route(
            pattern=resource.pattern,
            name=resource.route_name,
            factory=functools.partial(ResourceContext, resource),
            )
        config.add_route(
            pattern='%s' % resource.new_pattern,
            name='%s' % resource.new_route_name,
            factory=functools.partial(ResourceContext, resource),
            )
        config.add_route(
            pattern='%s' % resource.edit_pattern,
            name='%s' % resource.edit_route_name,
            factory=functools.partial(ResourceContext, resource),
            )

    def _add_views(self, config, resource):
        for method, (view, info) in resource.views.iteritems():
            config.add_view(
                view=view,
                mapper=ResourceViewMapper,
                **self._get_view_predicates(resource, method)
                )

        not_allowed = [m for m in self.methods if m not in resource.views]

        for method in not_allowed:
            config.add_view(
                view=not_allowed_view,
                **self._get_view_predicates(resource, method)
                )

    def _add_introspection(self, config, resource):
        cat_name = 'pyramid_rest resources'
        intr = config.introspectable(
            category_name=cat_name,
            discriminator=resource.discriminator,
            title=resource.name,
            type_name='resource',
            )
        intr['resource'] = resource
        intr.relate('routes', resource.route_name)
        intr.relate('routes', resource.item_route_name)
        intr.relate('routes', resource.new_route_name)
        intr.relate('routes', resource.edit_route_name)

        if resource.parent:
            intr.relate(cat_name, resource.parent.discriminator)

        config.action(resource.discriminator, introspectables=(intr,))

    def _get_view_predicates(self, resource, method):
        return dict(
            route_name={
                'index':  resource.route_name,
                'create': resource.route_name,
                'show':   resource.item_route_name,
                'delete': resource.item_route_name,
                'update': resource.item_route_name,
                'edit':   resource.edit_route_name,
                'new':    resource.new_route_name,
                }[method],
            request_method=self.methods[method],
            )


class Resource(object):
    "A REST resource"

    def __init__(self, resource_name):
        self.name = resource_name
        self.info = venusian.attach(self, self.callback)
        self.views = dict()
        self.children = dict()

        # define REST decorators
        for method in ('index', 'show', 'create', 'update', 'delete', 'new', 'edit'):
            setattr(self, method, functools.partial(self.decorator, method))

    def __repr__(self):
        return "<%s '%s'>" % (self.__class__.__name__, self.name)

    @property
    def discriminator(self):
        return ('pyramid_rest', self.name)

    def decorator(self, method, **kwargs):
        def wrapper(view):
            info = venusian.attach(view, lambda x, y, z: None)
            if method in self.views: # pragma: no cover
                # XXX - Raise a conflict error
                pass
            self.views[method] = (view, info)
            return view
        return wrapper

    def callback(self, context, name, ob):
        registry = context.config.registry
        registry.getUtility(IResourceUtility).add(context.config, self)


class ResourceContext(object):

    def __init__(self, resource, request):
        self.resource = resource
        self.request = request

    def is_item(self): # pragma: no cover
        pass

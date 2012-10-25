# -*- coding: utf-8 -*-
import functools
import inspect
import logging
import json

from pyramid.httpexceptions import HTTPMethodNotAllowed
from pyramid.config.util import ActionInfo, action_method

import venusian

from zope.interface import implementer
from zope.interface import Interface

log = logging.getLogger(__name__)


class ViewMapper(object):

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def _ordered_ids(self, matchdict):
        return [matchdict[i] for i in sorted(matchdict.keys())]


class FunctionViewMapper(ViewMapper):

    def __call__(self, view):

        def wrapper(context, request):

            return view(
                context,
                request,
                *self._ordered_ids(request.matchdict)
                )

        return wrapper


class ClassViewMapper(ViewMapper):

    def __call__(self, view):

        def wrapper(context, request):
            return view(
                view.im_class(context, request),
                *self._ordered_ids(request.matchdict)
                )

        return wrapper


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
        self.methods_configs = dict()

    def add_resource(self, config, resource_name, *args, **kwargs):
        class_name = ''.join([a.title() for a in resource_name.split(".")])
        module_name = resource_name.replace('.', '_')
        dotted_module = '%s.views.%s' % (config.package_name, module_name)
        dotted_class = '%s:%s' % (dotted_module, class_name)
        try:
            cls = config.maybe_dotted(dotted_class)
        except ImportError:
            # Make message is more explicit
            raise ImportError('No class %s found.' % dotted_class)
        config.scan(dotted_module)
        the_resource = resource_config(resource_name)
        the_resource(cls) # decorate class to register config
        the_resource.update_views_settings(self.methods_configs.get(cls, {}))
        self.add(config, the_resource)

    def add_method_config(self, cls, method, settings):
        if 'cls' not in self.methods_configs:
            self.methods_configs[cls] = dict()
        self.methods_configs[cls][method] = settings

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

        if config._ainfo is None:
            config._ainfo = []

        self._add_routes(config, resource)
        self._add_views(config, resource)
        self._add_introspectable(config, resource)
        self.resources[resource.name] = resource
        log.info(
            'Add REST resource="%s" parent="%s" views=%s',
            resource.name,
            resource.parent.name if resource.parent else None,
            resource.views.keys(),
            )
        self._add_deferred_children(config, resource)

    def _add_deferred_children(self, config, parent_resource):
        for name, child_resource in self.deferred.items():
            parent_name, child_name = name.rsplit(self.separator, 1)
            if parent_name == parent_resource.name:
                self.deferred.pop(name)
                self.add(config, child_resource)

    def _add_routes(self, config, resource):
        config._ainfo.append(ActionInfo(*resource.info.codeinfo))
        factory = functools.partial(ResourceContext, resource)
        config.add_route(
            pattern=resource.item_pattern,
            name=resource.item_route_name,
            factory=factory,
            )
        config.add_route(
            pattern=resource.pattern,
            name=resource.route_name,
            factory=factory,
            )
        config.add_route(
            pattern='%s' % resource.new_pattern,
            name='%s' % resource.new_route_name,
            factory=factory,
            )
        config.add_route(
            pattern='%s' % resource.edit_pattern,
            name='%s' % resource.edit_route_name,
            factory=factory,
            )
        config._ainfo.pop()

    def _add_views(self, config, resource):
        config._ainfo.append(ActionInfo(*resource.info.codeinfo))
        for view_info in resource.views.itervalues():
            if inspect.isfunction(view_info.view):
                mapper = FunctionViewMapper
                attr = None
            else:
                mapper = ClassViewMapper
                attr = view_info.view.__name__
            settings = view_info.settings.copy()
            settings.update(self._get_view_predicates(resource, view_info.method))
            settings.setdefault('renderer', 'json') # XXX: code a custom renderer
            config.add_view(
                view=view_info.view,
                mapper=mapper,
                attr=attr,
                **settings
                )

        not_allowed = [m for m in self.methods if m not in resource.views]

        for method in not_allowed:
            config.add_view(
                view=not_allowed_view,
                **self._get_view_predicates(resource, method)
                )
        config._ainfo.pop()

    def _add_introspectable(self, config, resource):
        cat_name = 'pyramid_rest resources'
        intr = config.introspectable(
            category_name=cat_name,
            discriminator=resource.discriminator,
            title=resource.name,
            type_name='resource',
            )
        intr['resource'] = resource
        intr['documentation'] = resource.__doc__
        intr.relate('routes', resource.route_name)
        intr.relate('routes', resource.item_route_name)
        intr.relate('routes', resource.new_route_name)
        intr.relate('routes', resource.edit_route_name)

        if resource.parent:
            intr.relate(cat_name, resource.parent.discriminator)

        config._ainfo.append(ActionInfo(*resource.info.codeinfo))
        config.action(resource.discriminator, introspectables=(intr,))
        config._ainfo.pop()

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
            permission=method,
            request_method=self.methods[method],
            )


class ViewInfo(object):

    def __init__(self, view, info, method, settings):
        self.view = view
        self.info = info
        self.method = method
        self.settings = settings


class BaseResource(object):

    methods = ('index', 'show', 'create', 'update', 'delete', 'new', 'edit')

    def __init__(self, resource_name, documentation="", acl=None):
        self.parent = None
        self.acl = acl
        self.name = resource_name
        self.views = dict()
        self._conflicts = dict()
        self.children = dict()
        self.__doc__ = documentation


    def __repr__(self):
        return "<%s '%s'>" % (self.__class__.__name__, self.name)

    @property
    def discriminator(self):
        return ('pyramid_rest', self.__repr__())

    def callback(self, context, name, ob):
        config = context.config.with_package(self.info.module)
        config.registry.getUtility(IResourceUtility).add(config, self)


class Resource(BaseResource):
    """Resource class"""

    def __init__(self, resource_name, documentation="", acl=None):
        super(Resource, self).__init__(resource_name, documentation, acl)
        self.info = venusian.attach(self, self.callback)

        # define REST decorators
        for method in self.methods:
            setattr(self, method, functools.partial(self.decorator, method))

    def decorator(self, method, **kwargs):
        def wrapper(view):
            info = venusian.attach(view, self.callback_view)
            view_info = ViewInfo(view, info, method, kwargs)
            self.views[method] = view_info
            self._conflicts[view] = view_info
            return view
        return wrapper

    def callback_view(self, context, name, view):
        view_info = self._conflicts[view]
        config = context.config
        config._ainfo.append(ActionInfo(*view_info.info.codeinfo))
        config.action((self.name, view_info.method))
        config._ainfo.pop()
        self._conflicts.pop(view)


class resource_config(BaseResource):
    """Resource decorator"""

    def __call__(self, cls):
        self.info = venusian.attach(cls, self.callback, category='pyramid')
        self.__doc__ = cls.__doc__

        views = inspect.getmembers(
            cls,
            lambda m: inspect.ismethod(m) and m.__name__ in self.methods
            )
        for name, view in views:
            self.views[name] = ViewInfo(view, self.info, name, {})
        return cls

    def update_views_settings(self, method_configs):
        for method_name, settings in method_configs.iteritems():
            self.views[method_name].settings.update(settings)

    def callback(self, context, name, ob):
        config = context.config.with_package(self.info.module)
        utility = config.registry.getUtility(IResourceUtility)
        method_configs = utility.methods_configs.get(ob, {})
        self.update_views_settings(method_configs)
        super(resource_config, self).callback(context, name, ob)


class method_config(object):

    def __init__(self, **settings):
        self.settings = settings

    def __call__(self, method):
        self.info = venusian.attach(method, self.callback)
        self.method = method
        return method

    def callback(self, context, name, ob):
        # callback may be called twice as 2 scans might be done:
        ## 1st is done when in ResourceUtility.add_resource
        ## 2nd might be done by the end user
        if self.method is not None:
            config = context.config.with_package(self.info.module)
            utility = config.registry.getUtility(IResourceUtility)
            utility.add_method_config(ob, self.method.func_name, self.settings)
            self.method = None


class ResourceContext(object):

    def __init__(self, resource, request):
        self.__parent__ = resource.parent
        self.__name__ = resource.name
        self.__acl__ = resource.acl if resource.acl else tuple()
        self.resource = resource
        self.request = request

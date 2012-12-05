# -*- coding: utf-8 -*-
import functools
import inspect
import logging

from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPMethodNotAllowed
from pyramid.config.util import ActionInfo

import venusian

from zope.interface import implementer
from zope.interface import Interface

log = logging.getLogger(__name__)


class ViewMapper(object):

    def __init__(self, **kwargs):
        self.kwargs = kwargs


class FunctionViewMapper(ViewMapper):

    def __call__(self, view):

        def wrapper(context, request):

            return view(
                context,
                request,
                **request.matchdict
                )

        return wrapper


class ClassViewMapper(ViewMapper):

    def __call__(self, view):

        def wrapper(context, request):
            return view(
                view.im_class(context, request),
                **request.matchdict
                )

        return wrapper


class IResourceConfigurator(Interface):
    pass


class ResourceAdded(object):
    """Event notified after a resource is added and configured."""
    def __init__(self, config, resource):
        self.config = config
        self.resource = resource


def not_allowed_view(request):
    # FIXME using raise makes tests fail
    return HTTPMethodNotAllowed()


@implementer(IResourceConfigurator)
class ResourceConfigurator(object):
    """Internal configurator of all REST resources. It is responsible for:

    # Registering to pyramid routes and views associated to resources.
    # . . .

    """

    methods = dict(
        index='GET',
        create='POST',
        show='GET',
        update='PUT',
        delete='DELETE',
        new='GET',
        edit='GET',
        )

    singular_methods = dict(
        show='GET',
        update='PUT',
        edit='GET',
        )

    def __init__(self):
        self.resources = dict()
        self.parent_resources = dict()
        self.deferred = dict()
        self.methods_configs = dict()

    def add_resource(
        self,
        config,
        resource_name,
        plural_name=None,
        singular=False,
        documentation="",
        acl=None,
        ):
        res = resource_config(
            resource_name,
            plural_name,
            singular,
            documentation,
            acl,
            )

        class_name = ''.join(a.title() for a in res.collection_name.split("."))
        module_name = res.collection_name.replace('.', '_')
        dotted_module = '%s.views.%s' % (config.package_name, module_name)
        dotted_class = '%s:%sView' % (dotted_module, class_name)
        try:
            cls = config.maybe_dotted(dotted_class)
        except ImportError:
            log.error('No class %s found.', dotted_class)
            raise
        config.scan(dotted_module)

        res(cls)  # decorate class to register config
        res.update_views_settings(self.methods_configs.get(cls, {}))
        self._add(config, res)

    def add_method_config(self, cls, method, settings):
        if 'cls' not in self.methods_configs:
            self.methods_configs[cls] = dict()
        self.methods_configs[cls][method] = settings

    def _add(self, config, resource):
        # XXX detect resource name duplicates
        try:
            parent, child = resource.collection_name.rsplit('.', 1)
            if parent not in self.resources:
                self.deferred[resource.name] = resource
                return
        except ValueError:
            # no separator in resource name: it is a root resource
            parent = None
            child = resource.collection_name

        if parent is None:
            self.parent_resources[resource.name] = resource
            resource.parent = None
            resource.depth = 0
        else:
            # resource knows about parent
            resource.parent = self.resources[parent]
            # parent knows about new child
            resource.parent.children[resource.name] = resource
            resource.depth = resource.parent.depth + 1

        if resource.parent:
            parent_pattern = resource.parent.lineage_route_pattern
        else:
            parent_pattern = ''

        if resource.singular:
            # route names
            resource.route_name = resource.name
            resource.edit_route_name = '%s_edit' % resource.name
            resource.item_route_name = None
            resource.new_route_name = None

            # routes patterns
            resource.pattern = '%s/%s' % (parent_pattern, child)
            resource.edit_pattern = '%s/edit' % resource.pattern
            resource.item_pattern = None
            resource.new_pattern = None

        else:
            # routes names:
            resource.route_name = "%s_collection" % resource.name
            resource.item_route_name = "%s_item" % resource.name
            resource.new_route_name = '%s_new' % resource.name
            resource.edit_route_name = '%s_edit' % resource.name

            # routes patterns
            resource.pattern = '%s/%s' % (parent_pattern, child)
            resource.item_pattern = '%s/{id}' % resource.pattern
            resource.new_pattern = '%s/new' % resource.pattern
            resource.edit_pattern = '%s/edit' % resource.item_pattern

        if config._ainfo is None:
            config._ainfo = []

        # XXX: to be refactored
        # self._validate_views_args_name(resource)
        self._add_routes(config, resource)
        self._add_views(config, resource)
        self._add_introspectable(config, resource)
        self.resources[resource.name] = resource
        log.info(
            'Add REST resource="%s" parent="%s" views=%s patterns=[%s, %s]',
            resource.name,
            resource.parent.name if resource.parent else None,
            resource.views.keys(),
            resource.pattern,
            resource.item_pattern,
            )
        config.registry.notify(ResourceAdded(config, resource))
        self._add_deferred_children(config, resource)

    def _add_deferred_children(self, config, parent_resource):
        for name, child_resource in self.deferred.items():
            parent_name, child_name = name.rsplit('.', 1)
            if parent_name == parent_resource.name:
                self.deferred.pop(name)
                self._add(config, child_resource)

    def _validate_views_args_name(self, resource):
        # XXX seems ugly: need refacto.
        not_last = resource.ids[:-1]

        expectation = {
            'index': not_last,
            'create': not_last,
            'show': resource.ids,
            'update': resource.ids,
            'delete': resource.ids,
            'new': not_last,
            'edit': resource.ids,
            }

        for view_info in resource.views.itervalues():
            spec = inspect.getargspec(view_info.view)
            if inspect.isfunction(view_info.view):
                expected = (
                    ['context', 'request']
                    + expectation[view_info.method]
                    )
            else:
                expected = ['self'] + expectation[view_info.method]
            nb_args = len(spec.args) - (
                len(spec.defaults) if spec.defaults else 0
                )
            received = spec.args[:nb_args]
            if expected != received:
                raise TypeError(
                    'resource=%s, view=%s, expected %s - got %s' % (
                    resource,
                    view_info.method,
                    expected,
                    received,
                    ))

    def _add_routes(self, config, resource):
        config._ainfo.append(ActionInfo(*resource.info.codeinfo))
        factory = functools.partial(ResourceContext, resource)
        if not resource.singular:
            config.add_route(
                pattern='%s' % resource.new_pattern,
                name='%s' % resource.new_route_name,
                factory=factory,
                )
            config.add_route(
                pattern=resource.item_pattern,
                name=resource.item_route_name,
                factory=factory,
                )
        config.add_route(
            pattern='%s' % resource.edit_pattern,
            name='%s' % resource.edit_route_name,
            factory=factory,
            )
        config.add_route(
            pattern=resource.pattern,
            name=resource.route_name,
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
            settings.update(
                self._get_view_predicates(resource, view_info.method)
                )
            settings.setdefault('renderer', 'pyramid_rest_renderer')
            config.add_view(
                view=view_info.view,
                mapper=mapper,
                attr=attr,
                **settings
                )

        if not resource.singular:
            not_allowed = [m for m in self.methods if m not in resource.views]
        if resource.singular:
            not_allowed = [m for m in self.singular_methods if (
                m not in resource.views)
                ]

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
        intr.relate('routes', resource.edit_route_name)
        if not resource.singular:
            intr.relate('routes', resource.item_route_name)
            intr.relate('routes', resource.new_route_name)

        if resource.parent:
            intr.relate(cat_name, resource.parent.discriminator)

        config._ainfo.append(ActionInfo(*resource.info.codeinfo))
        config.action(resource.discriminator, introspectables=(intr,))
        config._ainfo.pop()

    def _get_view_predicates(self, resource, method):
        if not resource.singular:
            route_name = {
                'index': resource.route_name,
                'create': resource.route_name,
                'show': resource.item_route_name,
                'delete': resource.item_route_name,
                'update': resource.item_route_name,
                'edit': resource.edit_route_name,
                'new': resource.new_route_name,
                }[method]
        if resource.singular:
            route_name = {
                'show': resource.route_name,
                'update': resource.route_name,
                'edit': resource.edit_route_name,
                }[method]
        return dict(
            route_name=route_name,
            permission=method,
            request_method=self.methods[method],
            )

    def resource_path(self, request, resource_name, *args):
        """Returns route name for ``resource_name`` with args"""
        resource = self.resources[resource_name]
        route_name = resource.get_route_name(*args)
        ids = dict(zip(
            resource.ids[:len(args)],
            args,
            ))
        return request.route_path(route_name, **ids)


def rest_resource_url(request, resource_name, *args):
    utility = request.registry.getUtility(IResourceConfigurator)
    path = utility.resource_path(request, resource_name, *args)
    return request.host_url + path


def rest_resource_path(request, resource_name, *args):
    utility = request.registry.getUtility(IResourceConfigurator)
    return utility.resource_path(request, resource_name, *args)


class ViewInfo(object):

    def __init__(self, view, info, method, settings):
        self.view = view
        self.info = info
        self.method = method
        self.settings = settings


class BaseResource(object):
    """
        :param resource_name: Resource name in singular form.
        :param plural_name: Resource collection name: a *s* is appended to
                                *resource_name* if it's not provided.
    """

    methods = tuple(ResourceConfigurator.methods.keys())
    singular_methods = tuple(ResourceConfigurator.singular_methods.keys())

    def __init__(
        self,
        resource_name,
        plural_name=None,
        singular=False,
        documentation="",
        acl=None,
        ):

        self.parent = None
        self.acl = acl
        self.name = resource_name
        self.singular = singular
        self.short_name = self.name.rpartition('.')[-1]

        if not self.singular and plural_name:
            name = list(resource_name.rpartition('.'))
            name[-1] = plural_name
            self.collection_name = ''.join(name)

        if not self.singular and not plural_name:
            self.collection_name = '%ss' % resource_name

        if self.singular:
            self.collection_name = self.name

        self.views = dict()
        self._conflicts = dict()
        self.children = dict()
        self.__doc__ = documentation

    def __repr__(self):
        return "<%s '%s'>" % (self.__class__.__name__, self.name)

    @reify
    def ids(self):
        """List of identifier names for this resource.

        Example::

            >>> resource = Resource('application.user')
            >>> resource.ids
            ['application_id', 'id']
        """
        my_id = [] if self.singular else ['id']
        if self.parent:
            return self.lineage_ids[:-1] + my_id
        return my_id

    @reify
    def lineage_ids(self):
        """List of identifier names a child resource needs for its route
        pattern. e.g.::

            >>> resource = Resource('application.user.message')
            >>> resource.parent.lineage_ids
            ['application_id', 'user_id']
        """
        id_name = self.short_name + '_id'
        if self.parent:
            return self.parent.lineage_ids + [id_name]
        return [id_name]

    @reify
    def lineage_route_pattern(self):
        child = self.collection_name.rpartition('.')[2]
        pattern = '/%s/{%s_id}' % (child, self.short_name)
        if self.parent:
            return self.parent.lineage_route_pattern + pattern
        return pattern

    @property
    def discriminator(self):
        return ('pyramid_rest', repr(self))

    def callback(self, context, name, ob):
        config = context.config.with_package(self.info.module)
        config.registry.getUtility(IResourceConfigurator)._add(config, self)

    def get_route_name(self, *args):
        """Returns route name associated with that resource and the arguments
        for url generation

        :param args: List of ids.
        """
        if (len(args) < self.depth
            or len(args) > self.depth + 1
            or (self.singular and len(args) != self.depth)
            ):
            raise ValueError('Need between %s and %s ids, received %s' % (
                self.depth,
                self.depth + 1,
                len(args),
                ))
        if self.singular:
            return self.route_name

        is_collection_path = (len(args) == self.depth)
        is_item_path = (len(args) == self.depth + 1)

        if is_collection_path:
            return self.route_name

        if is_item_path:
            return self.item_route_name


class Resource(BaseResource):
    """Resource class"""

    def __init__(
        self,
        resource_name,
        plural_name=None,
        singular=False,
        documentation="",
        acl=None,
        ):
        super(Resource, self).__init__(
            resource_name,
            plural_name,
            singular,
            documentation,
            acl,
            )
        self.info = venusian.attach(self, self.callback)

        # define REST decorators
        if not self.singular:
            iter_methods = iter(self.methods)

        if self.singular:
            iter_methods = iter(self.singular_methods)

        for method in iter_methods:
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
        self.view_class = cls
        self.__doc__ = cls.__doc__
        methods = self.singular_methods if self.singular else self.methods
        views = inspect.getmembers(
            cls,
            lambda m: inspect.ismethod(m) and m.__name__ in methods
            )
        for name, view in views:
            self.views[name] = ViewInfo(view, self.info, name, {})
        return cls

    def update_views_settings(self, method_configs):
        for method_name, settings in method_configs.iteritems():
            self.views[method_name].settings.update(settings)

    def callback(self, context, name, ob):
        config = context.config.with_package(self.info.module)
        utility = config.registry.getUtility(IResourceConfigurator)
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
        ## 1st is done when in ResourceConfigurator.add_resource
        ## 2nd might be done by the end user
        if self.method is not None:
            config = context.config.with_package(self.info.module)
            utility = config.registry.getUtility(IResourceConfigurator)
            utility.add_method_config(ob, self.method.func_name, self.settings)
            self.method = None


class ResourceContext(object):

    def __init__(self, resource, request):
        self.__parent__ = resource.parent
        self.__name__ = resource.name
        self.__acl__ = resource.acl if resource.acl else tuple()
        self.resource = resource
        self.request = request

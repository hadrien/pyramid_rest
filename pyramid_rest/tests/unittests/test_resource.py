import unittest

import mock


class TestFunctionViewMapper(unittest.TestCase):

    def test_init_and_call(self):
        from pyramid_rest.resource import FunctionViewMapper

        kwargs = dict()
        view = mock.Mock()
        ctx = mock.Mock()
        req = mock.MagicMock()
        req.matchdict.__iter__.return_value = ('id1', 'id0', 'id3', 'id2')

        fvm = FunctionViewMapper(**kwargs)
        wrapped = fvm(view)
        result = wrapped(ctx, req)

        self.assertEqual(kwargs, fvm.kwargs)
        self.assertEqual(view.return_value, result)

        view.assert_called_once_with(ctx, req, **req.matchdict)


class TestResourceConfigurator(unittest.TestCase):

    def _get_config(self):
        from pyramid.config import Introspectable, Configurator, Registry
        config = mock.Mock(spec=Configurator)
        config.introspectable.return_value = mock.MagicMock(
            spec=Introspectable
            )
        config.registry = mock.MagicMock(spec=Registry)
        return config

    def test_init(self):
        from pyramid_rest.resource import ResourceConfigurator

        ru = ResourceConfigurator()

        self.assertEqual(
            dict(
                index='GET',
                create='POST',
                show='GET',
                update='PUT',
                delete='DELETE',
                new='GET',
                edit='GET',
                ),
            ru.methods,
            )

    def test_add_sub_resource(self):
        from pyramid_rest.resource import ResourceConfigurator, Resource

        dad = Resource('dad')
        kid = Resource('dad.kid')

        config = self._get_config()

        # kid is a sub resource:
        # Resource utility must defer processing until parent resource is added
        ru = ResourceConfigurator()
        ru._add(config, kid)

        self.assertEqual({'dad.kid': kid}, ru.deferred)

        ru._add(config, dad)

    @mock.patch('pyramid_rest.resource.functools')
    def test_add_resources_route(self, m_functools):
        from pyramid_rest.resource import ResourceConfigurator, Resource

        kid = Resource('dad.kid')
        dad = Resource('dad')

        config = self._get_config()

        ru = ResourceConfigurator()

        ru._add(config, dad)

        self.assertEqual({'dad': dad}, ru.resources)
        self.assertEqual({'dad': dad}, ru.parent_resources)

        self.assertEqual(
            mock.call(
                pattern='/dads/new',
                name='dad_new',
                factory=m_functools.partial.return_value,
                ),
            config.add_route.call_args_list[0]
            )
        self.assertEqual(
            mock.call(
                pattern='/dads/{id}',
                name='dad_item',
                factory=m_functools.partial.return_value,
                ),
            config.add_route.call_args_list[1]
            )
        self.assertEqual(
            mock.call(
                pattern='/dads/{id}/edit',
                name='dad_edit',
                factory=m_functools.partial.return_value,
                ),
            config.add_route.call_args_list[2]
            )
        self.assertEqual(
            mock.call(
                pattern='/dads',
                name='dad_collection',
                factory=m_functools.partial.return_value,
                ),
            config.add_route.call_args_list[3]
            )
        ru._add(config, kid)
        self.assertEqual({'dad': dad, 'dad.kid': kid}, ru.resources)
        self.assertEqual({'dad': dad}, ru.parent_resources)

        self.assertEqual(
            mock.call(
                pattern='/dads/{dad_id}/kids/new',
                name='dad.kid_new',
                factory=m_functools.partial.return_value,
                ),
            config.add_route.call_args_list[4]
            )
        self.assertEqual(
            mock.call(
                pattern='/dads/{dad_id}/kids/{id}',
                name='dad.kid_item',
                factory=m_functools.partial.return_value,
                ),
            config.add_route.call_args_list[5]
            )
        self.assertEqual(
            mock.call(
                pattern='/dads/{dad_id}/kids/{id}/edit',
                name='dad.kid_edit',
                factory=m_functools.partial.return_value,
                ),
            config.add_route.call_args_list[6]
            )
        self.assertEqual(
            mock.call(
                pattern='/dads/{dad_id}/kids',
                name='dad.kid_collection',
                factory=m_functools.partial.return_value,
                ),
            config.add_route.call_args_list[7]
            )

    def test_add_resources_add_views(self):
        from pyramid_rest.resource import (
            ResourceConfigurator,
            Resource,
            not_allowed_view,
            )

        dad_index = mock.Mock(spec=not_allowed_view)
        dad_show = mock.Mock(spec=not_allowed_view)

        kid_index = mock.Mock(spec=not_allowed_view)
        kid_show = mock.Mock(spec=not_allowed_view)

        kid = Resource('dad.kid')
        dad = Resource('dad')

        config = self._get_config()

        ru = ResourceConfigurator()
        ru._validate_views_args_name = lambda a: a

        # simulate decorating methods:
        dad.index()(dad_index)
        dad.show()(dad_show)
        kid.index()(kid_index)
        kid.show()(kid_show)

        ru._add(config, dad)
        ru._add(config, kid)

        self.assertEqual(14, config.add_view.call_count)

        # check dad views:

        self._check_add_view(dad_index, 'index', 'GET', 'dad_collection', config.add_view.call_args_list[0])
        self._check_add_view(dad_show, 'show', 'GET', 'dad_item', config.add_view.call_args_list[1])

        self._check_add_not_allowed(not_allowed_view, 'edit', 'GET', 'dad_edit', config.add_view.call_args_list[2])
        self._check_add_not_allowed(not_allowed_view, 'new', 'GET', 'dad_new', config.add_view.call_args_list[3])
        self._check_add_not_allowed(not_allowed_view, 'create', 'POST', 'dad_collection', config.add_view.call_args_list[4])
        self._check_add_not_allowed(not_allowed_view, 'update', 'PUT', 'dad_item', config.add_view.call_args_list[5])
        self._check_add_not_allowed(not_allowed_view, 'delete', 'DELETE', 'dad_item', config.add_view.call_args_list[6])

        # check kid views:

        self._check_add_view(kid_index, 'index', 'GET', 'dad.kid_collection', config.add_view.call_args_list[7])
        self._check_add_view(kid_show, 'show', 'GET', 'dad.kid_item', config.add_view.call_args_list[8])

        self._check_add_not_allowed(not_allowed_view, 'edit', 'GET', 'dad.kid_edit', config.add_view.call_args_list[9])
        self._check_add_not_allowed(not_allowed_view, 'new', 'GET', 'dad.kid_new', config.add_view.call_args_list[10])
        self._check_add_not_allowed(not_allowed_view, 'create', 'POST', 'dad.kid_collection', config.add_view.call_args_list[11])
        self._check_add_not_allowed(not_allowed_view, 'update', 'PUT', 'dad.kid_item', config.add_view.call_args_list[12])
        self._check_add_not_allowed(not_allowed_view, 'delete', 'DELETE', 'dad.kid_item', config.add_view.call_args_list[13])

    def _check_add_view(self, view, permission, request_method, route_name, real_call):
        from pyramid_rest.resource import FunctionViewMapper
        self.assertEqual(
            mock.call(
                view=view,
                mapper=FunctionViewMapper,
                attr=None,
                renderer='pyramid_rest_renderer',
                permission=permission,
                request_method=request_method,
                route_name=route_name
                ),
            real_call,
            )

    def _check_add_not_allowed(self, view, permission, request_method, route_name, real_call):
        self.assertEqual(
            mock.call(
                view=view,
                permission=permission,
                request_method=request_method,
                route_name=route_name
                ),
            real_call,
            )


class TestNotAllowedView(unittest.TestCase):

    def test_raising_http_not_allowed(self):
        from pyramid_rest.resource import not_allowed_view, HTTPMethodNotAllowed
        self.assertIsInstance(not_allowed_view(None), HTTPMethodNotAllowed, )


class TestResource(unittest.TestCase):

    @mock.patch('pyramid_rest.resource.functools')
    def test_init(self, m_functools):
        from pyramid_rest.resource import Resource

        r = Resource('dad')

        self.assertEqual(m_functools.partial.return_value, r.index)
        self.assertEqual(m_functools.partial.return_value, r.show)
        self.assertEqual(m_functools.partial.return_value, r.create)
        self.assertEqual(m_functools.partial.return_value, r.update)
        self.assertEqual(m_functools.partial.return_value, r.delete)
        self.assertEqual(m_functools.partial.return_value, r.new)
        self.assertEqual(m_functools.partial.return_value, r.edit)

        self.assertEqual('<Resource \'dad\'>', r.__repr__())

    @mock.patch('pyramid_rest.resource.ViewInfo')
    @mock.patch('pyramid_rest.resource.venusian')
    def test_decorator(self, m_venusian, m_ViewInfo):
        from pyramid_rest.resource import Resource

        r = Resource('dad')

        view_index = mock.Mock()

        wrapper = r.decorator('index')
        result = wrapper(view_index)

        self.assertEqual(view_index, result)
        self.assertEqual(
            {'index': m_ViewInfo.return_value},
            r.views
            )

        self.assertEqual(
            mock.call(r, r.callback),
            m_venusian.attach.call_args_list[0]
            )
        self.assertEqual(
            mock.call(view_index, mock.ANY),
            m_venusian.attach.call_args_list[1]
            )

    def test_callback(self):
        from pyramid_rest.resource import Resource, IResourceConfigurator

        context = mock.Mock()

        r = Resource('dad')

        r.callback(context, None, None)

        context.config.with_package.assert_called_once_with(
            r.info.module
            )
        config = context.config.with_package.return_value

        (config
            .registry
            .getUtility
            .assert_called_once_with(IResourceConfigurator)
            )

        (config
            .registry
            .getUtility
            .return_value
            ._add
            .assert_called_once_with(config, r)
            )

    @mock.patch('pyramid_rest.resource.ActionInfo')
    def test_callback_view(self, m_action_info):
        from pyramid_rest.resource import Resource

        context = mock.Mock()
        view = mock.Mock()

        r = Resource('dad')
        r.decorator('index')(view)

        view_info = r._conflicts[view]

        r.callback_view(context, None, view)

        context.config._ainfo.append.assert_called_once_with(
            m_action_info.return_value,
            )
        context.config.action.assert_called_once_with(('dad', 'index'))
        context.config._ainfo.pop.assert_called_once_with()

        m_action_info.assert_called_once_with(*view_info.info.codeinfo)

    def test_lineage_ids(self):
        from pyramid.config import Configurator
        from pyramid_rest.resource import Resource, ResourceConfigurator

        config = Configurator(settings={})
        ru = ResourceConfigurator()

        dad = Resource('dad')
        kid = Resource('dad.kid')
        grandchild = Resource('dad.kid.grandchild')

        ru._add(config, dad)
        ru._add(config, kid)
        ru._add(config, grandchild)

        self.assertEqual(['dad_id'], dad.lineage_ids)
        self.assertEqual(['dad_id', 'kid_id'], kid.lineage_ids)
        self.assertEqual(['dad_id', 'kid_id', 'grandchild_id'], grandchild.lineage_ids)

        self.assertEqual(['id'], dad.ids)
        self.assertEqual(['dad_id', 'id'], kid.ids)
        self.assertEqual(['dad_id', 'kid_id', 'id'], grandchild.ids)


class TestResourceContext(unittest.TestCase):

    def test_init(self):
        from pyramid_rest.resource import ResourceContext, Resource

        resource = Resource('dad')
        request = mock.Mock()

        rctx = ResourceContext(resource, request)

        self.assertEqual(resource, rctx.resource)
        self.assertEqual(request, rctx.request)

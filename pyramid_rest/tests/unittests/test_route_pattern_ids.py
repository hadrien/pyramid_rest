import unittest

import mock


def wrong_ids_show(context, request, app_id, u_id, id):
    "Should have been application_id, user_id, id"
    return {}


class TestRoutePatternIds(unittest.TestCase):

    def _get_config(self):
        from pyramid.config import Configurator, Registry
        config = mock.MagicMock(spec=Configurator)
        config.registry = mock.MagicMock(spec=Registry)
        return config

    @unittest.expectedFailure
    def test_wrong_parent_id_names(self):
        from pyramid_rest.resource import Resource, ResourceConfigurator

        config = self._get_config()
        ru = ResourceConfigurator()

        # add parents:
        ru._add(config, Resource('application'))
        ru._add(config, Resource('application.user'))

        res = Resource('application.user.message')
        # decorate view function
        res.show()(wrong_ids_show)

        with self.assertRaises(TypeError):
            # simulate venusian callback
            ru._add(config, res)

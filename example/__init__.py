"""
Just an example RESTfull app for documentating and testing purpose.
"""
from pyramid.config import Configurator
from wsgiref.simple_server import make_server


def includeme(config):
    config.include('pyramid_rest')
    config.include('pyramid_debugtoolbar')

    config.add_resource('application')
    config.add_resource('application.medium', plural_name='media')
    config.add_resource('application.user')
    config.add_resource('application.user.message')

    config.add_singular_resource('application.user.score')
    config.add_singular_resource('health')

    config.scan()


def get_app(settings=None):
    settings if settings else {}
    config = Configurator(settings=settings)
    config.include('example')
    return config.make_wsgi_app()


def main(global_config, **settings):
    return get_app(settings)


if __name__ == '__main__':
    server = make_server('0.0.0.0', 6543, get_app())
    server.serve_forever()

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
    config.add_singular_resource('application.user.score')
    config.add_singular_resource('health')

    config.scan()


if __name__ == '__main__':
    config = Configurator(settings={})
    config.include('example')
    app = config.make_wsgi_app()
    server = make_server('0.0.0.0', 6543, app)
    server.serve_forever()

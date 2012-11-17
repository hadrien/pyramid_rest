from pyramid_rest.resource import method_config

from example.views import BaseView


class ApplicationUsersView(BaseView):

    def index(self, application_id):
        return [
            dict(id='1', name='User 1'),
            dict(id='2', name='User 2'),
            dict(id='3', name='User 3'),
            dict(id='4', name='User 4'),
            ]

    @method_config(permission='admin')
    def show(self, application_id, id):
        return dict(id=id, name='User %s' % id)

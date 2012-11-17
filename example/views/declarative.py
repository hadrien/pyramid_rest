from pyramid_rest.resource import Resource, resource_config, method_config

_USERS = {}

users = Resource('user')


@users.index()
def list_users(context, request):
    return _USERS


@users.create()
def create_user(context, request):
    pass


@users.show()
def get_user(context, request, id):
    return {'id': 123}

messages = Resource('user.message')


@messages.index()
def get_user_messages(context, request, user_id):
    return


user_summary = Resource('user.summary', singular=True)


@user_summary.show()
def get_user_summary(context, request, user_id):
    return {'summary': {}}


@resource_config('user.score', singular=True)
class UserScore(object):

    def __init__(self, context, request):
        pass

    def show(self, user_id):
        return {}

    @method_config(renderer='example.mako')
    def edit(self, user_id):
        return {}

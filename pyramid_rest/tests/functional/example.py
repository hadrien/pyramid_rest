# -*- coding: utf-8 -*-
from pyramid_rest.resource import Resource, resource_config, method_config

_USERS = {}

users = Resource('users')

@users.index()
def list_users(context, request):
    return _USERS


@users.create()
def create_user(context, request):
    return



messages = Resource('users.messages')

@messages.index()
def get_user_messages(context, request, user_id):
    return



@resource_config('users.score')
class UserScore(object):

    def __init__(self, context, request):
        pass

    def show(self, user_id):
        return {}

    @method_config(renderer='example.mako')
    def edit(self, user_id):
        return {}

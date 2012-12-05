# -*- coding: utf-8 -*-

from bson.objectid import ObjectId

from mongokit import Document


class Message(Document):

    use_dot_notation = True

    __collection__ = 'example'

    structure = {
        'from': unicode,
        'content': unicode,
        'application_id': ObjectId,
        'user_id': ObjectId,
        }

    required_fields = ['from', 'content', 'application_id', 'user_id']

    indexes = [{'fields': ['application_id', 'user_id']}]

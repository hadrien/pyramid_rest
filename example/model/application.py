# -*- coding: utf-8 -*-

from mongokit import Document


class Application(Document):

    use_dot_notation = True

    __collection__ = 'example'

    structure = {
        'name': unicode,
        'secret_key': unicode,
        }

    required_fields = ['name', 'secret_key']

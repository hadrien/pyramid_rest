# -*- coding: utf-8 -*-
from __future__ import absolute_import

from mongokit import Document


class Application(Document):

    use_dot_notation = True

    __collection__ = 'example'

    structure = {
        'name': unicode,
        'secret_key': basestring,
        }

    required_fields = ['name', 'secret_key']

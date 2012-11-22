# -*- coding: utf-8 -*-
from __future__ import absolute_import

from mongokit import Document


class Message(Document):

    structure = {
        'from': unicode,
        'to': unicode,
        'content': unicode
        }

    required_fields = ['from', 'to', 'content', ]

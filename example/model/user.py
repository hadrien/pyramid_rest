
from bson.objectid import ObjectId

from mongokit import Document


class User(Document):

    use_dot_notation = True

    __collection__ = 'example'

    structure = {
        'name': unicode,
        'application_id': ObjectId,
        }

    required_fields = ['application_id', 'name']

    indexes = [{'fields': ['application_id']},
               {'fields': ['name'], 'unique': True},
               ]

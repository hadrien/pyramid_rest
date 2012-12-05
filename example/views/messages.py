# -*- coding: utf-8 -*-

from pyramid_rest.mongo import CollectionView

from example.model import Message


class ApplicationUserMessages(CollectionView):

    model_class = Message

# -*- coding: utf-8 -*-

from pyramid_rest.mongo import CollectionView

from example.model import Application


class ApplicationsView(CollectionView):

    model_class = Application

    def index(self):
        return {
            'data': [
                dict(id=1, name='App 1'),
                dict(id=2, name='App 2'),
                dict(id=3, name='App 3'),
                dict(id=4, name='App 4'),
                ],
            }

    def update(self, id):
        return {}

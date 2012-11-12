from example.views import BaseView


class ApplicationsView(BaseView):

    def index(self):
        return [
            dict(id=1, name='App 1'),
            dict(id=2, name='App 2'),
            dict(id=3, name='App 3'),
            dict(id=4, name='App 4'),
            ]

    def update(self, id):
        return {}

    def delete(self, id):
        return {}

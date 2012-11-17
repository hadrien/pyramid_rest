from example.views import BaseView


class HealthView(BaseView):

    def show(self):
        return {'health': []}

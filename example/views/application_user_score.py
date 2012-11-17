from example.views import BaseView


class ApplicationUserScoreView(BaseView):

    def update(self, application_id, user_id):
        pass

    def show(self, application_id, user_id):
        return {'user_id': user_id, 'score': 123}

    def edit(self, application_id, user_id):
        pass

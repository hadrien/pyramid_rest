

class BaseView(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request

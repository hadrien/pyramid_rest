
from pyramid_rest.mongo import CollectionView

from example.model import Message


class ApplicationUserMessagesView(CollectionView):

    model_class = Message

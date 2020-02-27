# chat profiles
class ChatSource(object):

    def __init__(self, user=None):
        if user is None:
            raise Exception('user or bot_key must not be null')
        if user:
            self.source_type = 1
            self.source_user = user

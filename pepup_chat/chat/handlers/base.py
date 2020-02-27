# -*- encoding: utf-8 -*-
import logging
from django.utils.translation import ugettext as _

logger = logging.getLogger(__name__)


#
# Exception classes
# FIXME: 현재 consumers.py와 handlers.py에 모두 exception handling logic이 존재한다. 괜찮을까?
#   (handlers.py 에서는 error 정보를 client에 전송하는 데 유리하기는 함.)
#
class ChatException(Exception):
    def __init__(self, error_message, user_message):
        super(ChatException, self).__init__()
        if not user_message:
            user_message = _('오류가 발생했어요.')
        self.error_message = error_message
        self.user_message = user_message


class InvalidActionCodeException(ChatException):
    def __init__(self, action_code='', chat_msg=None, user_message=None):
        error_message = 'Invalid action_code : {}'.format(action_code)
        super(InvalidActionCodeException, self).__init__(error_message=error_message, user_message=user_message)
        self.chat_msg = chat_msg


class MessageValidationException(ChatException):
    def __init__(self, error_message='', chat_msg=None, user_message=None):
        super(MessageValidationException, self).__init__(error_message=error_message, user_message=user_message)
        self.chat_msg = chat_msg


class MessageHandlingException(ChatException):
    def __init__(self, error_message='', chat_msg=None, user_message=None):
        super(MessageHandlingException, self).__init__(error_message=error_message, user_message=user_message)
        self.error_message = error_message
        self.chat_msg = chat_msg


class DoubleExecutionPreventedException(ChatException):
    def __init__(self, error_message='', chat_msg=None, user_message=None):
        super(DoubleExecutionPreventedException, self).__init__(error_message=error_message, user_message=user_message)
        self.error_message = error_message
        self.chat_msg = chat_msg


#
# Handler decorator & getter
#
_handler_dict = {}  # dict : handler_name -> handler_class


def register_handler(handler_name, handler_version):
    def decorator(handler_class):
        handler_class.name = handler_name
        handler_class.version = handler_version
        key = (handler_name, handler_version)
        if key in _handler_dict:
            raise Exception("Failed to register {}; "
                            "handler with name {} is already registered".format(handler_class.__name__,
                                                                                handler_name))
        _handler_dict[key] = handler_class
        return handler_class

    return decorator


def get_handler_class(handler_name, handler_version):
    key = (handler_name, handler_version)
    return _handler_dict.get(key, None)

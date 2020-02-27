# -*- encoding: utf-8 -*-
import base64
import logging

from django.core.exceptions import SuspiciousOperation
from django.utils.encoding import force_bytes, force_text
from redis_sessions.session import SessionStore as RedisSessionStore


class SessionStore(RedisSessionStore):
    """
    Hash validation을 제외한 SessionStore object입니다.
    이 구현이 없으면 "Session data corrupted" 오류가 발생하게 됩니다.
    (서로 다른 worker가 같은 session instance에 접근할 때, hash가 일치하지 않을 수 있음. 자세한 부분은 모름)
    """

    def decode(self, session_data):
        encoded_data = base64.b64decode(force_bytes(session_data))
        try:
            # could produce ValueError if there is no ':'
            hash, serialized = encoded_data.split(b':', 1)
            return self.serializer().loads(serialized)
        except Exception as e:
            # ValueError, SuspiciousOperation, unpickling exceptions. If any of
            # these happen, just return an empty dictionary (an empty session).
            if isinstance(e, SuspiciousOperation):
                logger = logging.getLogger('django.security.%s' % e.__class__.__name__)
                logger.warning(force_text(e))
            return {}

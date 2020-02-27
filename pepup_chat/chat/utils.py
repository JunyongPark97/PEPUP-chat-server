# -*- encoding: utf-8 -*-


def mbunchify(data):
    try:
        from bunch import bunchify
        return bunchify(data)
    except ImportError:
        from munch import munchify
        return munchify(data)


try:
    from bunch import Bunch as MBunch
except ImportError:
    from munch import Munch as MBunch


def get_mocked_serializer_context(user, room, client_handler_version):
    return mbunchify({'request': {'user': user},
                      'room_id': room.id,
                      'room': room,
                      'client_handler_version': client_handler_version})
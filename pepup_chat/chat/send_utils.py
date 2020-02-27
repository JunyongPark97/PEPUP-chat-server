# -*- encoding: utf-8 -*-
import json
import six
import time

from chat.models import ChatRoom
from chat.serializers import ChatMessageReadSerializer
from core.decorators import lazy_property

"""
채널 Group에 관한 Documentation!

현재 3종류의 Group을 사용하여 메세지를 전달하고 있습니다.
    - "room-{}" : 방에 참여한 모든 client에게 전송하는 경우
    - "room-{}-user-{}" : 특정 사용자에게 전송하는 경우
    - "room-{}-user-{}-handler-{}" : 특정 사용자에게, 특정 version으로 접속하였을 때에만 전송하는 경우

아래는 참고사항입니다.
- client가 접속하면, 사용자의 reply_channel이 3개의 Group에 동시에 추가됩니다. (ws_connect 함수 참고)
- target_user가 없는 message는 "room-{}"에 전송됩니다.
    - handler version 구분이 구현되어 있지 않으므로, handler version에 상관없이 보여줄 수 있는 메세지만 전송해 주세요.
- target_user가 있고 target_handler_version이 없는 message는 "room-{}-user-{}"에 전송됩니다.
- target_user가 있고 target_handler_version이 있는 message는 "room-{}-user-{}-handler-{}"에 전송됩니다.
"""

def get_group_names(room_id, user_id, handler_version):
    return ['room-{}'.format(room_id),
            'room-{}-user-{}'.format(room_id, user_id),
            'room-{}-user-{}-handler-{}'.format(room_id, user_id, handler_version)]


class DeliveryFailure(Exception):
    pass


def send_to_group(channel_layer, group, message, immediately):
    """
    channels.channel.Group.send 함수 및 asgi_redis.core.send_group 함수를 개선한 버전입니다.
    - immediately=True 일 때
        - retry-send 기능이 추가되었습니다.
        - n번의 시도 모두 실패한다면, ChannelFull exception을 발생시킵니다. (silently ignore하는 기존 구현과는 다름)
    :param group: Group instance
    :param message: data to send (in dict)
    :param immediately:
    """
    retry_count = 3
    if immediately:
        # re-implementation of asgi_redis.core.send_group
        assert channel_layer.valid_group_name(group.name), "Group name not valid"
        for channel in channel_layer.group_channels(group.name):
            for i in range(retry_count):  # retry for 3 times, in blocking manner
                try:
                    channel_layer.send(channel, message)
                    break
                except channel_layer.ChannelFull:
                    if i == retry_count - 1:
                        raise  # re-raise ChannelFull
                    time.sleep(0.2 * (2 ** i))  # exponential delay
                    continue
    else:
        # # add to pending
        # from channels.message import pending_message_store
        # pending_message_store.append(group, message)
        group.send(message)


class MessageSender(object):
    """
    Client에 메세지를 보낼 때 사용하는 함수들을 모아놓은 class입니다.
    """
    def __init__(self, channel_layer, room_id, reply_channel, session_data=None):
        self.channel_layer = channel_layer
        self.room_id = room_id
        self.reply_channel = reply_channel
        if not session_data:
            session_data = {}
        self.session_data = session_data

    @lazy_property
    def room(self):
        return ChatRoom.objects.get(id=self.room_id)

    #
    # Delivery functions
    #
    def _send_payload_to_group(self, payload, immediately):
        group = Group('room-{}'.format(self.room_id), channel_layer=self.channel_layer)
        send_to_group(channel_layer=self.channel_layer,
                      group=group,
                      message={'text': payload},
                      immediately=immediately)

    def _send_payload_to_user(self, payload, target_user, target_handler_version, immediately):
        if target_handler_version:
            group = Group('room-{}-user-{}-handler-{}'.format(self.room_id, target_user.id, target_handler_version),
                          channel_layer=self.channel_layer)
        else:
            group = Group('room-{}-user-{}'.format(self.room_id, target_user.id), channel_layer=self.channel_layer)
        send_to_group(channel_layer=self.channel_layer,
                      group=group,
                      message={'text': payload},
                      immediately=immediately)

    def _send_payload_to_reply_channel(self, payload, immediately):
        self.reply_channel.send({'text': payload}, immediately=immediately)

    def fetch_to_reply_channel(self, chat_msgs):
        # fetch 시 사용하는 함수입니다.
        # - fetch의 경우, user 단위가 아닌 session 단위로 메세지를 전송해야 합니다.
        #   따라서 reply_channel에 직접 메세지를 전송합니다.
        context = self.session_data.copy()
        context['role_dict'] = self.room.get_role_dict()
        payload = json.dumps({
            "type": "messages",
            "messages": ChatMessageReadSerializer(chat_msgs, context=context, many=True).data,
        })
        self._send_payload_to_reply_channel(payload, immediately=False)

    def deliver_messages(self, chat_msgs, immediately=False):
        context = self.session_data.copy()
        context['role_dict'] = self.room.get_role_dict()
        broadcast_messages = list(filter(lambda msg: not msg.target_user, chat_msgs))
        target_messages = list(filter(lambda msg: msg.target_user, chat_msgs))
        # broadcast message : send to room
        if broadcast_messages:
            payload = json.dumps({
                "type": "messages",
                "messages": ChatMessageReadSerializer(broadcast_messages, context=context, many=True).data,
            })
            self._send_payload_to_group(payload, immediately=immediately)
        # target message : send to (room-user)
        for message in target_messages:
            payload = json.dumps({
                "type": "messages",
                "messages": [ChatMessageReadSerializer(message, context=context).data],
            })
            self._send_payload_to_user(payload=payload,
                                       target_user=message.target_user,
                                       target_handler_version=message.target_handler_version,
                                       immediately=immediately)

    def deliver_message(self, chat_msg, immediately=False):
        self.deliver_messages([chat_msg], immediately=immediately)

    def send_room_states(self, room_states, target_user, immediately=False):
        payload = json.dumps({
            "type": "room_states",
            "room_states": room_states,
        })
        if target_user is not None:
            self._send_payload_to_user(payload, target_user=target_user,
                                       target_handler_version=None, immediately=immediately)
        else:
            self._send_payload_to_group(payload, immediately=immediately)

    def send_toast(self, text, immediately=False):
        payload = json.dumps({
            "type": "toast",
            "text": text,
        })
        self._send_payload_to_reply_channel(payload, immediately=immediately)

    def send_status_update(self, source, active, typing, immediately=False):
        payload = json.dumps({
            "type": "status_update",
            "status": {
                "active": active,
                "typing": typing,
            },
        })
        self._send_payload_to_group(payload, immediately=immediately)

    def send_error(self, text):
        # client 개발자 console에 출력할 수 있는 오류를 보냅니다.
        payload = json.dumps({
            "type": "error",
            "error": text,
        })
        self._send_payload_to_reply_channel(payload, immediately=False)

    def send_ping(self, identifier, immediately=False):
        assert type(identifier) in six.string_types
        payload = json.dumps({
            "type": "ping",
            "identifier": identifier,
        })
        self._send_payload_to_reply_channel(payload, immediately=immediately)

    def send_pong(self, identifier, immediately=False):
        payload = json.dumps({
            "type": "pong",
            "identifier": identifier,
        })
        self._send_payload_to_reply_channel(payload, immediately=immediately)

    def send_close(self, immediately=False):
        self.reply_channel.send({'close': True}, immediately=immediately)

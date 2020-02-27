# -*- encoding: utf-8 -*-
from rest_framework import serializers

from chat.message_models import (
    TextChatMessageTmpl,
    ImageChatMessageTmpl,
    UserPostbackChatMessageTmpl,
)
from chat.models import ChatMessage
from chat.profile_models import ChatSource
from core.aws.fields import URLResolvableUUIDField
from core.serializer_fields import NullToBlankCharField


class ChatMessageUserDataSerializer(serializers.Serializer):
    """
    Input fields :
        - ['code', 'text', 'image_key', 'reply_token', 'postback_value', 'extras']
    Output fields :
        - ['code', 'text', 'image_key', 'postback_parent', 'postback_value', 'extras']
    Usage :
        input_data = {"text": ...}
        output_data = ChatMessageUserDataSerializer(data=input_data).data
    """
    code = NullToBlankCharField()
    text = NullToBlankCharField()
    image_key = URLResolvableUUIDField(allow_null=True, required=False)
    reply_token = serializers.UUIDField(write_only=True, allow_null=True, required=False)
    postback_parent = serializers.SerializerMethodField()
    # postback_value = serializers.CharField(allow_null=True, required=False)
    extras = serializers.DictField(write_only=True, allow_null=True, required=False)
    source = serializers.SerializerMethodField()

    def __init__(self, **kwargs):
        if 'many' in kwargs:
            raise Exception('ChatMessageUserDataSerializer(many=True) is not yet supported! sorry.')
        super(ChatMessageUserDataSerializer, self).__init__(**kwargs)

    def get_postback_parent(self, data):
        reply_token = data.get('reply_token', None)
        if reply_token:
            return ChatMessage.objects.get(token=reply_token)
        return None

    def get_source(self, data):
        return ChatSource(user=self.context['request'].user)

    def convert(self):
        """
        :return: ChatMessage instance
        :raises: serializers.ValidationError
        (현재는 many=False일 때에만 변환가능)
        # FIXME: x.data, x.validated_data 생각없이 막 쓰고 있음
        """
        self.is_valid(raise_exception=True)
        chat_source = self.data['source']
        text = self.data.get('text', '')
        image_key = self.data.get('image_key', None)
        code = self.data.get('code', '')
        postback_parent = self.data.get('postback_parent', None)
        postback_parent_id = None if postback_parent is None else postback_parent.id
        extras = self.validated_data.get('extras', {})

        room = self.context['room']
        client_handler_version = self.context['client_handler_version']

        # 1. "chat$info" message
        if not code:
            if text:
                message_tmpl = TextChatMessageTmpl(source=chat_source, text=text)
            elif image_key:
                message_tmpl = ImageChatMessageTmpl(source=chat_source, image_key=image_key)
            else:
                raise serializers.ValidationError(
                    'cannot convert user data to message; neither text nor image_key given')
            message_tmpl = message_tmpl.with_handler_name(room.room_type)
        # 2. postback message (if msg has code, it's considered as postback)
        # FIXME: code가 있는 경우 postback이거나 predefined 인데, 딱히 predefined를 별도 처리하고 있지 않음.
        else:
            message_tmpl = UserPostbackChatMessageTmpl(source=chat_source, code=code,
                                                       text=text, image_key=image_key, extras=extras)
        chat_msg_instance = (message_tmpl
                             .with_room_id(room_id=room.id)
                             .with_postback_parent_id(postback_parent_id)
                             .with_client_handler_version(client_handler_version)
                             .save())
        return chat_msg_instance

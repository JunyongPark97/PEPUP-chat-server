# -*- encoding: utf-8 -*-

import re

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from rest_framework import serializers

User = get_user_model()

from chat.models import ChatRoom, ChatMessage
from core.aws.fields import URLResolvableUUIDField


class ChatRoomSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())
    websocket_url = serializers.SerializerMethodField()
    another_selves = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ('id', 'room_type', 'owner', 'websocket_url', 'another_selves')

    def get_websocket_url(self, instance):
        domain = Site.objects.get(name='chat').domain
        return 'ws://{domain}/chat/{pk}/'.format(domain=domain, pk=instance.id)

    def get_another_selves(self, instance):
        return []


#
# Message serializer
#
class ChatUserSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(source='social_default_nickname')
    profile_image_url = serializers.CharField(source='social_default_profile_image_url')
    role = serializers.SerializerMethodField()
    is_staff = serializers.BooleanField()

    class Meta:
        model = User
        fields = ('id', 'nickname', 'profile_image_url', 'role', 'is_staff')

    def get_role(self, user):
        role_dict = self.context.get('role_dict', None)
        if not role_dict:
            return 'none'
        return role_dict.get(user.id, 'none')


class ChatMessageReadSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='get_message_type_display')
    code = serializers.CharField()
    template = serializers.JSONField()
    text = serializers.CharField()
    preview_image_url = serializers.SerializerMethodField()
    original_content_url = serializers.SerializerMethodField()
    lottie_emoji_url = serializers.SerializerMethodField()
    caption = serializers.CharField()
    duration = serializers.IntegerField()
    uri = serializers.CharField()
    token = serializers.CharField()
    extras = serializers.JSONField()
    is_hidden = serializers.BooleanField()  # 메세지를 visible -> invisible로 변경 시, hide후 deliver하기 때문에 필요
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    def to_representation(self, instance):
        """
        Copy-paste of rest_framework.serializers.Serializer.to_representation
        """
        from collections import OrderedDict
        from rest_framework.relations import PKOnlyObject

        ret = OrderedDict()
        fields = self._readable_fields

        for field in fields:
            try:
                attribute = field.get_attribute(instance)
            except Exception:
                # (MODIFIED) skip field if any exception (including AttributeError) occurs
                continue

            check_for_none = attribute.pk if isinstance(attribute, PKOnlyObject) else attribute
            # (MODIFIED) skip serializing "None" and blank values
            if check_for_none is None:
                # ret[field.field_name] = None
                pass
            else:
                # ret[field.field_name] = field.to_representation(attribute)
                val = field.to_representation(attribute)
                if val:
                    ret[field.field_name] = val

        return ret

    class Meta:
        model = ChatMessage
        fields = (
            'id',
            'type',
            'room_id',
            'text',
            'code',
            'preview_image_url',
            'original_content_url',
            'lottie_emoji_url',
            'caption',
            'uri',
            'duration',

            'source',

            'template',

            'token',
            'extras',
            'command',
            'is_hidden',

            'object_id',

            'created_at',
            'updated_at',
        )

    def get_preview_image_url(self, chat_msg):
        original_content_url = chat_msg.original_content_url
        if original_content_url:
            pattern = r'http://pepup-storage.s3.amazonaws.com/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}).jpg'
            result = re.match(pattern, original_content_url)
            if result:
                width = self.context.get('screen_width', 1080)
                resized_url = 'http://pepup-redirect.mathpresso.co.kr/image/{image_key}/?width={width}'.format(
                    image_key=result.groups()[0], width=width)
                return resized_url
        return original_content_url

    def get_original_content_url(self, chat_msg):
        original_content_url = chat_msg.original_content_url
        if original_content_url:
            pattern = r'http://pepup-storage.s3.amazonaws.com/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}).jpg'
            result = re.match(pattern, original_content_url)
            if result:
                width = self.context.get('screen_width', 1080) * 2
                resized_url = 'http://pepup-redirect.mathpresso.co.kr/image/{image_key}/?width={width}'.format(
                    image_key=result.groups()[0], width=width)
                return resized_url
        return original_content_url

    def get_lottie_emoji_url(self, chat_msg):
        if not chat_msg.lottie_emoji_key:
            return ''
        return 'https://qanda.co.kr/api/v3/emoji/lottie/json/?key={}'.format(chat_msg.lottie_emoji_key)


class ChatMessageWriteSerializer(serializers.ModelSerializer):
    """
    ChatMessage object를 생성할 때 사용합니다. (ex: ChatMessageTmpl.save)
    """
    text = serializers.CharField(allow_blank=True, required=False)
    code = serializers.CharField(allow_blank=True, required=False)
    image_key = URLResolvableUUIDField(allow_null=True, required=False)
    content_url = serializers.CharField(allow_blank=True, required=False)
    lottie_emoji_key = serializers.CharField(allow_blank=True, required=False)
    caption = serializers.CharField(allow_blank=True, required=False)
    uri = serializers.CharField(allow_blank=True, required=False)
    version = serializers.HiddenField(default=1)

    source_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(),
                                                     allow_null=True, required=False)
    source_bot_key = serializers.CharField(allow_blank=True, required=False)

    template = serializers.JSONField(allow_null=True, required=False)

    target_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(),
                                                     allow_null=True, required=False)
    is_hidden = serializers.BooleanField(default=False)

    postback_parent = serializers.PrimaryKeyRelatedField(queryset=ChatMessage.objects.all(),
                                                         allow_null=True, required=False)
    postback_value = serializers.CharField(allow_blank=True, required=False)
    extras = serializers.JSONField(allow_null=True, required=False)

    object_id = serializers.IntegerField(allow_null=True, required=False)

    client_handler_version = serializers.IntegerField(allow_null=True, required=False)
    target_handler_version = serializers.IntegerField(allow_null=True, required=False)

    class Meta:
        model = ChatMessage
        fields = (
            'message_type',
            'room',
            'text',
            'code',
            'image_key',
            'content_url',
            'lottie_emoji_key',
            'caption',
            'uri',
            'version',

            'source_type',
            'source_user',
            'source_bot_key',

            'template',

            'target_user',
            'is_hidden',

            'token',
            'postback_parent',
            'postback_value',
            'extras',

            'object_id',

            'client_handler_version',
            'target_handler_version',
        )


class UpdateStatusUserDataSerializer(serializers.Serializer):
    active = serializers.BooleanField()
    typing = serializers.BooleanField()

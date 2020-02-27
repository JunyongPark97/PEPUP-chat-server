from django.db import models
# Create your models here.
from django.conf import settings
import jsonfield
import six
import uuid


class ChatRoom(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chat_rooms', on_delete=models.CASCADE)
    active = models.BooleanField(default=True, help_text='웹소켓 채팅이 가능할 경우 True')
    created_at = models.DateTimeField(auto_now_add=True)


class ChatRoomTagValue(models.Model):
    """
    Chatting handler에서 필요한 값을 임시로 저장할 때 사용합니다.
    """
    room = models.ForeignKey(ChatRoom, related_name='tag_values', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chat_room_tag_values', on_delete=models.CASCADE)
    key = models.CharField(max_length=200, db_index=True)
    VALUE_TYPES = (
        (1, 'int'),
        (2, 'string'),
        (3, 'json'),
    )
    value_type = models.IntegerField(choices=VALUE_TYPES, db_index=True)
    int_value = models.IntegerField(blank=True, null=True, db_index=True)
    string_value = models.CharField(max_length=200, blank=True, db_index=True)
    json_value = jsonfield.JSONField(default=dict, null=True)

    def __repr__(self):
        return '"{}":"{}"'.format(self.key, self.value)

    @property
    def value(self):
        if self.value_type == 1:
            return self.int_value
        elif self.value_type == 2:
            return self.string_value
        elif self.value_type == 3:
            return self.json_value
        return None

    class Meta:
        index_together = (
            ('room', 'user', 'key'),
        )


class ChatMessage(models.Model):
    # normal fields
    MESSAGE_TYPES = (
        # DON'T CHANGE THOSE STRINGS!! (used with "get_message_type_display")
        (1, 'text'),
        (2, 'image'),
        (3, 'template'),
        (4, 'audio'),
        (5, 'video'),
        (6, 'postback'),
        (7, 'instant_command'),
        (8, 'lottie_emoji'),
    )
    message_type = models.IntegerField(choices=MESSAGE_TYPES, db_index=True)
    room = models.ForeignKey(ChatRoom, related_name='messages', on_delete=models.CASCADE)
    text = models.TextField()
    code = models.CharField(max_length=100, db_index=True)
    image = models.ImageField(blank=True, null=True)
    content_url = models.CharField(max_length=300, blank=True)
    lottie_emoji_key = models.CharField(max_length=30, blank=True)
    caption = models.CharField(max_length=30, blank=True)
    uri = models.CharField(max_length=300, blank=True)
    version = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    source_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chat_messages', blank=True, null=True, on_delete=models.CASCADE)

    # template data fields
    template = jsonfield.JSONField(default=dict)

    # target fields
    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='targeted_chat_messages',
                                    blank=True, null=True, on_delete=models.CASCADE)
    is_hidden = models.BooleanField(default=True)

    # action & postback fields
    token = models.UUIDField(unique=True, db_index=True, default=uuid.uuid4)
    # postback_parent = models.ForeignKey('self', related_name='postback_children', blank=True, null=True)
    # postback_value = models.CharField(max_length=100, blank=True, db_index=True)  # DEPRECATED?
    extras = jsonfield.JSONField(default=dict)

    # generic foreign key field
    object_id = models.PositiveIntegerField(blank=True, null=True, db_index=True)

    # invalidated
    invalidated = models.BooleanField(default=False)

    # client_handler_version : 메세지를 생성한 client의 버전 (bot 및 user 메세지 모두 포함)
    client_handler_version = models.IntegerField(blank=True, null=True, db_index=True)
    # target_handler_version : 특정 버전 handler를 사용하는 client에게만 메세지를 보낼 경우 사용
    target_handler_version = models.IntegerField(blank=True, null=True, db_index=True)

    @property
    def handler_name(self):
        return self.code.split('$')[0]

    @property
    def action_code(self):
        return self.code.split('$')[1]

    @property
    def original_content_url(self):
        if self.image:
            return self.image.url
        elif self.content_url:
            return self.content_url
        return None

    @property
    def command(self):
        if self.message_type == 7 and \
                        'command_code' in self.extras and \
                        'postback_message_code' in self.extras and \
                        'params' in self.extras:
            return {
                'code': self.extras['command_code'],
                'postback_message_code': self.extras['postback_message_code'],
                'params': self.extras['params'],
            }
        return None


class ChatRoomParticipant(models.Model):
    """
    채팅방 참여자 정보를 관리하기 위한 모델
    """
    room = models.ForeignKey(ChatRoom, related_name='participants', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chat_room_participants', on_delete=models.CASCADE)
    role = models.CharField(max_length=100, blank=True, db_index=True)

    class Meta:
        unique_together = (
            ('room', 'user'),
        )
        index_together = (
            ('room', 'user'),
        )

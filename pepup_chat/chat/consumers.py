from channels.generic.websocket import AsyncWebsocketConsumer
import json

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name
        print('connect!!!!')
        user = self.scope['user']
        print('scope: ', user)
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        print('join group!!!')
        await self.accept()
        print('accepted!!!!')

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print('disconnected!!!')

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        print('receive-----message')
        print(message)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )
        print('send!!')

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        print('chat!!_-----messafgea')
        print(message)
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))
        print('chat sended!!!')

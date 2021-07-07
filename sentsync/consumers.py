import json
from channels.generic.websocket import AsyncWebsocketConsumer


class RoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name
        self.user = 'user'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)

        if (message := text_data_json.get('message')) is not None:
            await self.group_send({
                'type': 'chat_message',
                'sender': self.user,
                'message': message
            })

        if (action := text_data_json.get('action')) is not None:
            await self.group_send({
                'type': 'room_action',
                'sender': self.user,
                'action': action
            })

        if (user := text_data_json.get('user')) is not None:
            self.user = user

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']

        await self.send(text_data=json.dumps({
            'message': message,
            'sender': event['sender']
        }))

    async def room_action(self, event):
        action = event['action']

        if event['sender'] == self.user:
            return

        await self.send(text_data=json.dumps({
            'action': {
                **action,
                'from': 'server'
            },
            'sender': event['sender']
        }))

    async def group_send(self, data):
        return await self.channel_layer.group_send(
            self.room_group_name,
            data
        )

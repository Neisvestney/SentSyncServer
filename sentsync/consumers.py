import json
import traceback

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from rooms.models import Room, RoomUser


class RoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % room_name

        self.room, _ = await database_sync_to_async(lambda: Room.objects.get_or_create(code=room_name))()
        self.user: RoomUser = await database_sync_to_async(
            lambda: RoomUser.objects.create(host=len(self.room.users.all()) == 0, room=self.room)
        )()

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        await self.sent_data_to_everyone(exclude=self.user.id)

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # Deleting user and room from db
        await self.cleanup_db()

        await self.sent_data_to_everyone()

    @database_sync_to_async
    def cleanup_db(self):
        self.user.delete()
        if len(self.room.users.all()) == 0:
            self.room.delete()
        elif self.user.host:
            new_host = self.room.users.first()
            new_host.host = True
            new_host.save()

    # Receive message from WebSocket
    async def receive(self, text_data=None, bytes_data=None):
        try:
            text_data_json = json.loads(text_data)

            if (message := text_data_json.get('message')) is not None:
                await self.group_send({
                    'type': 'chat_message',
                    'sender': self.user.to_dict(),
                    'message': message
                })

            if (action := text_data_json.get('action')) is not None:
                await self.group_send({
                    'type': 'room_action',
                    'sender': self.user.to_dict(),
                    'action': action
                })

            if (cmd := text_data_json.get('cmd')) is not None:
                if cmd['action'] == 'getData':
                    await self.send_data()
                elif cmd['action'] == 'setData':
                    if username := cmd.get('username'):
                        self.user.username = username
                        await database_sync_to_async(lambda: self.user.save())()
                    if self.user.host and (tab_url := cmd.get('tabUrl')):
                        self.room.tab_url = tab_url
                        await database_sync_to_async(lambda: self.room.save())()

                    await self.sent_data_to_everyone()

        except:
            traceback.print_exc()
            await self.close()

    async def sent_data_to_everyone(self, exclude=None):
        await self.group_send({
            'type': 'data_updated',
            'exclude': exclude
        })

    async def send_data(self):
        self.room = await database_sync_to_async(lambda: Room.objects.get(id=self.room.id))() #  Refresh room object
        await self.send(text_data=json.dumps({
            'data': {
                'you': self.user.to_dict(),
                'room': await database_sync_to_async(lambda: self.room.to_dict())()
            }
        }))

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']

        await self.send(text_data=json.dumps({
            'message': message,
            'sender': event['sender']
        }))

    async def room_action(self, event):
        action = event['action']

        await self.send(text_data=json.dumps({
            'action': {
                **action,
                'from': 'server'
            },
            'sender': event['sender']
        }))

    async def data_updated(self, event):
        self.user = await database_sync_to_async(lambda: RoomUser.objects.get(id=self.user.id))()
        if self.user.id != event.get('exclude'):
            await self.send_data()

    async def group_send(self, data):
        return await self.channel_layer.group_send(
            self.room_group_name,
            data
        )

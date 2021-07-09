from django.db import models


class Room(models.Model):
    code = models.CharField('Code', max_length=128)

    def to_dict(self):
        return {
            'users': [u.to_dict() for u in self.users.all()]
        }

    def __str__(self):
        return f'Room {self.code}'


class RoomUser(models.Model):
    room = models.ForeignKey(Room, related_name='users', on_delete=models.CASCADE)

    username = models.CharField('Username', max_length=128, default="user")
    host = models.BooleanField('Is host')

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'isHost': self.host,
        }

    def __str__(self):
        return f'{self.username} ({self.id})'

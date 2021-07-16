from django.apps import AppConfig
from django.db import OperationalError


class RoomsAppConfig(AppConfig):
    name = 'rooms'

    def ready(self):
        try:
            from rooms.models import Room
            Room.objects.all().delete()
        except OperationalError:
            pass

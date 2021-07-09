from django.apps import AppConfig


class RoomsAppConfig(AppConfig):
    name = 'rooms'

    def ready(self):
        from rooms.models import Room
        Room.objects.all().delete()

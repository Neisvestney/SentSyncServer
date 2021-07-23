from django.shortcuts import render, redirect

from rooms.models import Room


def index(request):
    return redirect('https://github.com/Neisvestney/SentSync')


def invite(request, code):
    room = None
    try:
        room = Room.objects.get(code=code)
    except Room.DoesNotExist:
        pass

    return render(request, 'invite.html', {'room': room, **({'host': room.users.get(host=True)} if room else {})})

from django.urls import path

from rooms.views import index, invite

urlpatterns = [
    path('', index, name='index'),
    path('invite/<str:code>/', invite, name='invite'),
]

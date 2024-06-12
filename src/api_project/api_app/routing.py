from django.urls import path

from . import monitor

websocket_urlpatterns = [
    path('ws/monitor/', monitor.ChatConsumer.as_asgi()),
]
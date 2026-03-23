"""
ASGI config for dalia project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""






import os
import django
from django.core.asgi import get_asgi_application
import socketio

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dalia.settings')
django.setup()

# Import our socket server (I'll create this next)
from agent.socket_server import sio

django_app = get_asgi_application()

# Mount Socket.IO on top of Django
# /socket.io/ handles WebSocket traffic
# Everything else goes to Django
application = socketio.ASGIApp(
    socketio_server=sio,
    other_asgi_app=django_app,
    socketio_path='socket.io'
)
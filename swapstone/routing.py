# chat/routing.py
#from django.conf.urls import url
from django.urls import path
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import OriginValidator
from . import consumers


websocket_urlpatterns = [
    #url(r'^ws/profile/friends/chat/(?P<room_name>[^/]+)/$', consumers.ChatConsumer),
    path("profile/friends/chat/<str:roomName>", consumers.ChatConsumer, name="chat"),
]

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    "websocket": OriginValidator(
	    AuthMiddlewareStack(
	        URLRouter(
	            websocket_urlpatterns
	        )
	    ),
	    ["http://127.0.0.1:8000"]
	),
})
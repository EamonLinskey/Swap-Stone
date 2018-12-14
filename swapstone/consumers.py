# from channels.generic.websocket import WebsocketConsumer
# import json

# class ChatConsumer(WebsocketConsumer):
#     def connect(self):
#         self.accept()

#     def disconnect(self, close_code):
#         pass

#     def receive(self, text_data):
#         text_data_json = json.loads(text_data)
#         message = text_data_json['message']
#         print(message)
#         print(text_data)

#         self.send(text_data=json.dumps({
#             'message': message
#         }))

# chat/consumers.py
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        print(self.scope)
        self.chatroom = self.scope['path'].split("/")[-1]
        self.room_group_name = 'chat_%s' % self.chatroom
        print("connected")
        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        print("disconnected")
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        timeStamp = text_data_json['timeStamp']
        print(f"recieved message from Websocket: {message}")
        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'timeStamp': timeStamp,
            }
        )

    # Receive message from room group
    def chat_message(self, event):
        message = event['message']
        print(event)
        timeStamp = event['timeStamp']

        print(f"recieved message from GroupRoom: {message}")

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message,
            'timeStamp': timeStamp
        }))
        print(f"sent message: {message}")
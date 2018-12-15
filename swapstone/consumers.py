from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
from deckShare.models import Profile, Message


def addMessageToDB(data):
    print(f"the data is {data}")
    print(data['sender'])
    sender = Profile.objects.get(blizzTag=data['sender'])
    reciever = Profile.objects.get(blizzTag=data['reciever'])
    message = data['message']
    timeStamp = data['timeStamp']
    print(type(timeStamp))
    timeStamp = 10
    message = Message(sender=sender, reciever=reciever, message=message, timeOfMessage=timeStamp)
    message.save()


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
        sender = text_data_json['sender']
        username = text_data_json['username']
        
        if(username != self.chatroom):
            addMessageToDB(text_data_json)

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
        #print(event)
        timeStamp = event['timeStamp']

        print(f"recieved message from GroupRoom: {message}")

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message,
            'timeStamp': timeStamp
        }))
        print(f"sent message: {message}")
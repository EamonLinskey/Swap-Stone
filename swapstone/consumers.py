from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
from deckShare.models import Profile, Message
from django.contrib.auth.models import User



def addMessageToDB(data):
    sender = Profile.objects.get(blizzTag=data['senderBlizzTag'])
    reciever = Profile.objects.get(blizzTag=data['recieverBlizzTag'])
    message = data['message']
    timeStamp = data['timeStamp']
    message = Message(sender=sender, reciever=reciever, message=message, timeOfMessage=timeStamp)
    message.save()

def validateMessage(sender, senderUsername, reciever, recieverUsername):
    # This validates that the sender and reciever exist and that their blizzTag as well as user name are both accurate.
    # It also makes sure that the sender is friends with the reciever.
    if User.objects.filter(username=senderUsername).exists() and User.objects.filter(username=recieverUsername).exists():
        userSender = User.objects.get(username=senderUsername)
        userReciever = User.objects.get(username=recieverUsername)
        if Profile.objects.filter(user=userSender).exists() and Profile.objects.filter(user=userReciever).exists():
            senderProfileFromUser = Profile.objects.get(user=userSender)
            recieverProfileFromUser = Profile.objects.get(user=userReciever)
            if Profile.objects.filter(blizzTag=sender).exists() == Profile.objects.filter(blizzTag=reciever).exists():
                senderProfileFromBlizzTag = Profile.objects.get(blizzTag=sender)
                recieverProfileFromBlizzTag = Profile.objects.get(blizzTag=reciever)
                if senderProfileFromBlizzTag == senderProfileFromUser and recieverProfileFromBlizzTag == recieverProfileFromUser:
                    if recieverProfileFromBlizzTag in senderProfileFromBlizzTag.friends.all():
                        #print("these messages were valid")
                        return True
    #print("INVALID MESSAGE")
    return False

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        if User.objects.filter(username=self.scope["user"]).exists():
            self.chatroom = self.scope['path'].split("/")[-1]
            self.room_group_name = 'chat_%s' % self.chatroom
            
            # Join room group
            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name,
                self.channel_name
            )

            #messages = getMessages(self.scope["user"])
            self.accept()
        else:
            print("user doesnt exist")

    def disconnect(self, close_code):
        # Leave room group
        #print("disconnected")
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        print(text_data)
        print(text_data_json)
        message = text_data_json['message']
        timeStamp = text_data_json['timeStamp']
        sender = text_data_json['senderBlizzTag']
        senderUsername = text_data_json['senderUsername']
        reciever = text_data_json['recieverBlizzTag']
        recieverUsername = text_data_json['recieverUsername']
        
        #if(senderUsername != self.chatroom):
        addMessageToDB(text_data_json)


        if validateMessage(sender, senderUsername, reciever, recieverUsername):
            # Send message to target
            target_channel = f'chat_{recieverUsername}'
            async_to_sync(self.channel_layer.group_send)(
                target_channel,
                {
                    'type': 'chat_message',
                    'message': message,
                    'timeStamp': timeStamp,
                }
            )

            # Send message to self
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'timeStamp': timeStamp,
                }
            )
        else:
            print("Invalid Message")

        

    # Receive message from room group
    def chat_message(self, event):
        message = event['message']
        #print(event)
        timeStamp = event['timeStamp']

        #print(f"recieved message from GroupRoom: {message}")

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message,
            'timeStamp': timeStamp
        }))
        #print(f"sent message: {message}")
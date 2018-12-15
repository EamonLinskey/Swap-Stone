// Minified Reconnecitng Web Socket frunction
function ReconnectingWebSocket(a){function f(g){c=new WebSocket(a);if(b.debug||ReconnectingWebSocket.debugAll){console.debug("ReconnectingWebSocket","attempt-connect",a)}var h=c;var i=setTimeout(function(){if(b.debug||ReconnectingWebSocket.debugAll){console.debug("ReconnectingWebSocket","connection-timeout",a)}e=true;h.close();e=false},b.timeoutInterval);c.onopen=function(c){clearTimeout(i);if(b.debug||ReconnectingWebSocket.debugAll){console.debug("ReconnectingWebSocket","onopen",a)}b.readyState=WebSocket.OPEN;g=false;b.onopen(c)};c.onclose=function(h){clearTimeout(i);c=null;if(d){b.readyState=WebSocket.CLOSED;b.onclose(h)}else{b.readyState=WebSocket.CONNECTING;if(!g&&!e){if(b.debug||ReconnectingWebSocket.debugAll){console.debug("ReconnectingWebSocket","onclose",a)}b.onclose(h)}setTimeout(function(){f(true)},b.reconnectInterval)}};c.onmessage=function(c){if(b.debug||ReconnectingWebSocket.debugAll){console.debug("ReconnectingWebSocket","onmessage",a,c.data)}b.onmessage(c)};c.onerror=function(c){if(b.debug||ReconnectingWebSocket.debugAll){console.debug("ReconnectingWebSocket","onerror",a,c)}b.onerror(c)}}this.debug=false;this.reconnectInterval=1e3;this.timeoutInterval=2e3;var b=this;var c;var d=false;var e=false;this.url=a;this.readyState=WebSocket.CONNECTING;this.URL=a;this.onopen=function(a){};this.onclose=function(a){};this.onmessage=function(a){};this.onerror=function(a){};f(a);this.send=function(d){if(c){if(b.debug||ReconnectingWebSocket.debugAll){console.debug("ReconnectingWebSocket","send",a,d)}return c.send(d)}else{throw"INVALID_STATE_ERR : Pausing to reconnect websocket"}};this.close=function(){if(c){d=true;c.close()}};this.refresh=function(){if(c){c.close()}}}ReconnectingWebSocket.debugAll=false

function showTime(message){
    timeStamp = moment(parseInt(message.id)).fromNow()
    document.querySelector(".timeStamp").innerHTML = timeStamp
}

document.addEventListener('DOMContentLoaded', function(event) {
    let ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";

    // This is a socket which listens for messages from other users. It should always be open while on the chat page
    let listererSocket = new ReconnectingWebSocket(`${ws_scheme}://${window.location.host}/profile/friends/chat/${user}`);

    listererSocket.onmessage = function(message) {
        var data = JSON.parse(message.data);
        console.log("message recieved")
        console.log(`the data is ${data["message"]}`)

        var messageArea = document.querySelector(".messageArea")
        
        messageArea.innerHTML += `<div onmouseover="showTime(this)" id='${data['timeStamp']}' class='message'>${data['message']} \n </div>`
    };


    // This is the socket which sends chats to other users. It will change depending on which caht is open
    let senderSocket = null

    let friend = ""

    function setChatroom(username){
        if(senderSocket){
            senderSocket.close()
        }
        newSenderSocket = new ReconnectingWebSocket(`${ws_scheme}://${window.location.host}/profile/friends/chat/${username}`);

        newSenderSocket.onclose = function(e) {
            console.error('Chat was closed');
        };
        
        return newSenderSocket
    }


    let msgBtns = document.querySelectorAll(".messageFriends");

    for(let btn of msgBtns){
        btn.onclick = function () {
            friend = btn.getAttribute('id');
            senderSocket = setChatroom(friend)
            document.querySelector(".chatbox").value = '';
        }
    }

    let sendBtn = document.querySelector(".send-message-button");

    sendBtn.onclick = function ()  {
        console.log("clicked me")
        let message = {
            username: user,
            sender: blizzTag,
            reciever: friend,
            message: document.querySelector(".pendingMessage").value,
            timeStamp: + new Date()
        }
        console.log(message)
        senderSocket.send(JSON.stringify(message));
        // sending on the listener keeps current chat updated
        listererSocket.send(JSON.stringify(message));
        document.querySelector(".pendingMessage").value = ""

    }
});



// Minified Reconnecitng Web Socket frunction
function ReconnectingWebSocket(a){function f(g){c=new WebSocket(a);if(b.debug||ReconnectingWebSocket.debugAll){console.debug("ReconnectingWebSocket","attempt-connect",a)}var h=c;var i=setTimeout(function(){if(b.debug||ReconnectingWebSocket.debugAll){console.debug("ReconnectingWebSocket","connection-timeout",a)}e=true;h.close();e=false},b.timeoutInterval);c.onopen=function(c){clearTimeout(i);if(b.debug||ReconnectingWebSocket.debugAll){console.debug("ReconnectingWebSocket","onopen",a)}b.readyState=WebSocket.OPEN;g=false;b.onopen(c)};c.onclose=function(h){clearTimeout(i);c=null;if(d){b.readyState=WebSocket.CLOSED;b.onclose(h)}else{b.readyState=WebSocket.CONNECTING;if(!g&&!e){if(b.debug||ReconnectingWebSocket.debugAll){console.debug("ReconnectingWebSocket","onclose",a)}b.onclose(h)}setTimeout(function(){f(true)},b.reconnectInterval)}};c.onmessage=function(c){if(b.debug||ReconnectingWebSocket.debugAll){console.debug("ReconnectingWebSocket","onmessage",a,c.data)}b.onmessage(c)};c.onerror=function(c){if(b.debug||ReconnectingWebSocket.debugAll){console.debug("ReconnectingWebSocket","onerror",a,c)}b.onerror(c)}}this.debug=false;this.reconnectInterval=1e3;this.timeoutInterval=2e3;var b=this;var c;var d=false;var e=false;this.url=a;this.readyState=WebSocket.CONNECTING;this.URL=a;this.onopen=function(a){};this.onclose=function(a){};this.onmessage=function(a){};this.onerror=function(a){};f(a);this.send=function(d){if(c){if(b.debug||ReconnectingWebSocket.debugAll){console.debug("ReconnectingWebSocket","send",a,d)}return c.send(d)}else{throw"INVALID_STATE_ERR : Pausing to reconnect websocket"}};this.close=function(){if(c){d=true;c.close()}};this.refresh=function(){if(c){c.close()}}}ReconnectingWebSocket.debugAll=false

function showTime(message){
    timeStamp = moment(parseInt(message.id)).fromNow()
    document.querySelector(".timeStamp").innerHTML = timeStamp
}



document.addEventListener('DOMContentLoaded', function(event) {
    // console.log(messages)
    // console.log(Object.keys(messages))
    // console.log(messages["bulktest0"]);
        
    for(let key of Object.keys(messages) ){
        console.log(key)
        console.log(messages[key])
    }

    let ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";

    // This is a socket which listens for messages from other users. It should always be open while on the chat page
    let socket = new ReconnectingWebSocket(`${ws_scheme}://${window.location.host}/profile/friends/chat/${user}`);

    socket.onmessage = function(message) {
        let data = JSON.parse(message.data);
        let messageArea = document.querySelector(".messageArea")
        messageArea.innerHTML += `<div onmouseover="showTime(this)" id='${data['timeStamp']}' class='message'>${data['message']} \n </div>`
    };

    let friend = ""
    let recieverTag = ""


    let msgBtns = document.querySelectorAll(".messageFriends");

    for(let btn of msgBtns){
        btn.onclick = function () {
            console.log("clicked message btn")
            friend = btn.getAttribute('username');
            recieverTag = btn.getAttribute('blizztag');
            let messageArea = document.querySelector(".messageArea")
            messageArea.innerHTML = ""
            document.querySelector(".chatbox").value = '';
            document.querySelector(".chatboxTitle").innerHTML = `${friend} (${recieverTag})`;
            for(let message of messages[recieverTag]){
                messageArea.innerHTML += `<div onmouseover="showTime(this)" id='${message['timeStamp']}' class='message'>${message['message']} \n </div>`
            }
        }
    }

    let sendBtn = document.querySelector(".send-message-button");

    sendBtn.onclick = function ()  {
        console.log("clicked me")
        let message = {
            senderUsername: user,
            senderBlizzTag: blizzTag,
            recieverUsername: friend,
            recieverBlizzTag: recieverTag, 
            message: document.querySelector(".pendingMessage").value,
            timeStamp: + new Date()
        }
        console.log(message)
        socket.send(JSON.stringify(message));
        document.querySelector(".pendingMessage").value = ""

    }
});



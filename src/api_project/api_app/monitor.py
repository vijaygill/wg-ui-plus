import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.generic.websocket import WebsocketConsumer
from .wireguardhelper import WireGuardHelper


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        #self.close()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        cmd = text_data if text_data else ""
        cmd = cmd.strip().lower()
        res = '*** Unknown command ***'
        print(f'>>>>>>>>>>>>>> {cmd}')

        if cmd == "monitor_iptables_log":
            wg = WireGuardHelper()
            res = wg.get_iptables_log()['output']

        self.send(text_data=res)
        self.close()

# sample code for client side.
# const chatSocket = new WebSocket('ws://orangepi5-plus:8000/ws/monitor/');
# chatSocket.onopen = function() {
#   console.log('WebSocket connection established.');
#   chatSocket.send('monitor_iptables_log');
# };
# chatSocket.onmessage = function(event) {
#   console.log('WebSocket data received.');
#   const message = event.data;
#   console.log('Received message:', message);
# };
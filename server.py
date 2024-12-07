import socket
import threading
import json
import time

# Server Code
class GameServer:
    def __init__(self, host, port):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((host, port))
        self.clients = []
        self.state = {
            'asteroids': [],
            'ships': {},
            'lasers': []
        }
        self.running = True
        self.start_time = time.time()  # Время старта игры
        self.game_duration = 30  # Продолжительность игры в секундах (например, 30 секунд)

    def start(self):
        threading.Thread(target=self.receive_messages).start()
        self.game_loop()

    def receive_messages(self):
        while self.running:
            message, address = self.server_socket.recvfrom(1024)
            if address not in self.clients:
                self.clients.append(address)
            data = json.loads(message.decode())
            self.handle_message(data, address)

    def handle_message(self, data, address):
        action = data.get('action')
        if action == 'connect':
            self.handle_connect(data.get('payload'), address)

    def handle_connect(self, payload, address):
        self.state['ships'][payload['client_id']] = {
            'position': [400, 300],  # Центральная позиция на экране
            'hp': 3,
            'angle': 0
        }
        response = {
            'status': 'success',
            'payload': {
                'message': 'Connection established',
                'session_id': payload['client_id']
            }
        }
        self.send_response(response, address)

    def send_response(self, response, address):
        self.server_socket.sendto(json.dumps(response).encode(), address)

    def broadcast_state(self):
        state_update = {
            'event': 'update_state',
            'payload': self.state
        }
        for client in self.clients:
            self.server_socket.sendto(json.dumps(state_update).encode(), client)

    def game_loop(self):
        while self.running:
            # Broadcast state to clients
            self.broadcast_state()
            time.sleep(1 / 30)  # Частота обновления 30 FPS

if __name__ == '__main__':
    server = GameServer('172.20.10.11', 12345)
    server.start()

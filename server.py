import socket
import threading
import json
import time
import math

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
        self.game_duration = 30  # Продолжительность игры в секундах

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
        payload = data.get('payload')

        if action == 'connect':
            self.handle_connect(payload, address)
        elif action == 'update_position':
            self.handle_update_position(payload, address)
        elif action == 'shoot':
            self.handle_shoot(payload, address)

    def handle_connect(self, payload, address):
        self.state['ships'][payload['client_id']] = {
            'position': [400, 300],  # Центральная позиция на экране
            'hp': 3,
            'angle': 0,
            'shots': 10,  # Максимальное количество выстрелов
            'is_reloading': False
        }
        response = {
            'status': 'success',
            'payload': {
                'message': 'Connection established',
                'session_id': payload['client_id']
            }
        }
        self.send_response(response, address)

    def handle_update_position(self, payload, address):
        client_id = payload['client_id']
        if client_id in self.state['ships']:
            self.state['ships'][client_id]['position'] = payload['position']
            self.state['ships'][client_id]['angle'] = payload['angle']

    def handle_shoot(self, payload, address):
        ship_id = payload['ship_id']
        if ship_id in self.state['ships']:
            ship = self.state['ships'][ship_id]
            if ship['shots'] > 0:
                laser = self.create_laser(ship)
                self.state['lasers'].append(laser)
                ship['shots'] -= 1

    def create_laser(self, ship):
        ship_x, ship_y = ship['position']
        ship_angle = ship['angle']
        return {
            "pos": [
                ship_x + 25 * math.cos(math.radians(ship_angle)),
                ship_y + 25 * math.sin(math.radians(ship_angle))
            ],
            "direction": ship_angle,
            "vel": [10 * math.cos(math.radians(ship_angle)), 10 * math.sin(math.radians(ship_angle))]
        }

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

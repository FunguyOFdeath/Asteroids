import socket
import threading
import json
import pygame
import time

# Client Code
class GameClient:
    def __init__(self, server_host, server_port, client_id):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_address = (server_host, server_port)
        self.client_id = client_id
        self.running = True
        self.state = {
            'asteroids': [],
            'ships': {},
            'lasers': []
        }

    def connect(self):
        connect_message = {
            'action': 'connect',
            'payload': {
                'client_id': self.client_id
            }
        }
        self.client_socket.sendto(json.dumps(connect_message).encode(), self.server_address)
        threading.Thread(target=self.receive_messages).start()

    def receive_messages(self):
        while self.running:
            try:
                message, _ = self.client_socket.recvfrom(4096)
                data = json.loads(message.decode())
                self.handle_message(data)
            except Exception as e:
                print(f"Error receiving message: {e}")

    def handle_message(self, data):
        if data.get('event') == 'update_state':
            self.state = data.get('payload')
            # Print received state information
            print(f"Received state update: {self.state}")

    def game_loop(self):
        pygame.init()
        screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Asteroids")
        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    self.running = False
                    break
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                        self.running = False
                        break
                    elif event.key == pygame.K_SPACE:  # Example shoot key
                        self.send_shoot()

            keys = pygame.key.get_pressed()
            position = [400, 300]  # This is just an example, needs ship update logic
            angle = 0  # Example angle, needs real-time update
            self.send_position_update(position, angle)

            screen.fill((0, 0, 0))
            pygame.display.flip()
            clock.tick(30)

    def send_position_update(self, position, angle):
        position_data = {
            'action': 'update_position',
            'payload': {
                'client_id': self.client_id,
                'position': position,
                'angle': angle
            }
        }
        self.client_socket.sendto(json.dumps(position_data).encode(), self.server_address)

    def send_shoot(self):
        shoot_message = {
            'action': 'shoot',
            'payload': {
                'ship_id': self.client_id
            }
        }
        self.client_socket.sendto(json.dumps(shoot_message).encode(), self.server_address)

if __name__ == '__main__':
    client = GameClient('10.162.68.4', 12345, 'player_1')
    client.connect()
    threading.Thread(target=client.game_loop).start()

import socket
import threading
import json
import time
from asteroid import AsteroidManager
from laser import LaserManager
from ship import Ship
from utils import FPS, MAX_ASTEROIDS, WIDTH, HEIGHT

class GameServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()

        # Игровые объекты
        self.asteroid_manager = AsteroidManager(MAX_ASTEROIDS)
        self.laser_manager = LaserManager()
        self.ships = [
            Ship(None, 0),
            Ship(None, 1)
        ]
        self.players = [
            {"conn": None, "addr": None, "connected": False, "ship_id": 0},
            {"conn": None, "addr": None, "connected": False, "ship_id": 1}
        ]

        self.running = True

    def start(self):
        threading.Thread(target=self.game_loop, daemon=True).start()

        while self.running:
            conn, addr = self.server_socket.accept()
            threading.Thread(target=self.handle_raw_connection, args=(conn, addr), daemon=True).start()

    def handle_raw_connection(self, conn, addr):
        """
        Обрабатывает подключение игрока. Назначает слот, если свободен.
        """
        try:
            data = conn.recv(1024).decode()
            msg = json.loads(data)
            if msg.get('action') == 'hello':
                player_id = msg['payload']['player_id']
                if 0 <= player_id < 2 and not self.players[player_id]['connected']:
                    self.players[player_id]['conn'] = conn
                    self.players[player_id]['addr'] = addr
                    self.players[player_id]['connected'] = True
                    print(f"Player {player_id} connected from {addr}")
                    response = {
                        "status": "success",
                        "message": f"Player {player_id} connected"
                    }
                    conn.send(json.dumps(response).encode())
                else:
                    response = {
                        "status": "failed",
                        "message": "Slot already taken or invalid player_id"
                    }
                    conn.send(json.dumps(response).encode())
                    conn.close()
            else:
                conn.close()
        except Exception as e:
            print(f"Error handling connection: {e}")
    def game_loop(self):
        while self.running:
            # Update game state
            self.update_lasers_state()
            self.check_collisions()
            self.check_collision_ships()
            self.handle_respawn()
            # Broadcast state to clients
            self.broadcast_state()
            time.sleep(1 / FPS)

            # Проверка времени игры и завершение, если время истекло
            elapsed_time = time.time() - self.start_time
            if elapsed_time >= self.game_duration:
                self.running = False
                final_state = {
                    'event': 'game_over',
                    'payload': {
                        'scores': self.scores
                    }
                }
                for client in self.clients:
                    self.server_socket.sendto(json.dumps(final_state).encode(), client)
                print("Game over. Final scores:", self.scores)

                # Отключение клиентов и ожидание перед перезапуском
                self.disconnect_clients()
                time.sleep(10)  # Ожидание 10 секунд перед перезапуском

                # Сброс состояния игры и перезапуск
                self.reset_game()
                threading.Thread(target=self.receive_messages).start()
                self.game_loop()
                return

    def broadcast_state(self):
        current_time = time.time()
        elapsed_time = int(current_time - self.start_time)
        time_left = max(0, self.game_duration - elapsed_time)

        state_update = {
            'event': 'update_state',
            'payload': {
                'asteroids': self.state['asteroids'],
                'ships': self.state['ships'],
                'lasers': self.state['lasers'],
                'time_left': time_left,
                'scores': self.scores
            }
        }
        for client in self.clients:
            self.server_socket.sendto(json.dumps(state_update).encode(), client)

        # Вывод текущих позиций всех кораблей
        for ship_id, ship in self.state['ships'].items():
            print(f"Ship {ship_id} position: {ship['position']}, angle: {ship['angle']}, shots left: {ship['shots']}")
        for laser in self.state['lasers']:
            print(f"Laser position: {laser['pos']}, direction: {laser['direction']}")
        for asteroid in self.state['asteroids']:
            print(f"Asteroid position: {asteroid['pos']}, radius: {asteroid['radius']}")

    def stop(self):
        self.running = False
        self.server_socket.close()


if __name__ == '__main__':
    server = GameServer('172.20.10.11', 12345)
    server.start()

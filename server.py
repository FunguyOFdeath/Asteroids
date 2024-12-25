import socket
import threading
import json
import time
import math
from asteroid import AsteroidManager
from laser import LaserManager
from utils import FPS, MAX_ASTEROIDS, WIDTH, HEIGHT
from ship import Ship
import os

PLAYERS_FILE = "players.json"  # Путь к файлу с игроками


# Server Code
class GameServer:
    def load_players(self):
        """Загружает данные игроков из файла."""
        if os.path.exists(PLAYERS_FILE):
            with open(PLAYERS_FILE, 'r') as f:
                return json.load(f)
        return {}

    def save_players(self):
        """Сохраняет данные игроков в файл."""
        with open(PLAYERS_FILE, 'w') as f:
            json.dump(self.players, f, indent=4)

    def __init__(self, host, port):
        self.start_time = time.time()  # Время старта игры
        self.game_duration = 30  # Продолжительность игры в секундах
        self.scores = {'player_0': 0, 'player_1': 0}  # Счет игроков
        self.players = self.load_players()  # Загружаем данные игроков

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((host, port))
        self.clients = []
        self.state = {
            'asteroids': [],
            'ships': {},
            'lasers': []
        }
        self.running = True

        # Создание игровых объектов
        self.asteroid_manager = AsteroidManager(MAX_ASTEROIDS)
        self.laser_manager = LaserManager()
        self.ships = {
            "player_0": Ship(None, 0),
            "player_1": Ship(None, 1)
        }

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
        elif action == 'shoot':
            self.handle_shoot(payload, address)
        elif action == 'update_position':
            self.handle_update_position(payload, address)

    def handle_connect(self, payload, address):
        # Добавляем центральные координаты и начальную позицию корабля
        start_position = [WIDTH // 2, HEIGHT // 2]
        self.state['ships'][payload['client_id']] = {
            'position': start_position,
            'hp': 3,
            'angle': 0,
            'respawn_timer': 0,  # Таймер возрождения
            'start_position': start_position,  # Сохранение начальной позиции для респауна
            'width': 50,  # Ширина корабля
            'height': 40,  # Высота корабля
            'shots': 10,  # Максимальное количество выстрелов
            'is_reloading': False,  # Состояние перезарядки
            'reload_start_time': 0  # Время начала перезарядки
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
        print(f"Received position update from client {payload['client_id']}: {payload['position']}, angle: {payload['angle']}")
        client_id = payload['client_id']
        if client_id in self.state['ships']:
            self.state['ships'][client_id]['position'] = payload['position']
            self.state['ships'][client_id]['angle'] = payload['angle']
            response = {
                'status': 'success',
                'payload': {
                    'message': 'Position updated',
                    'position': self.state['ships'][client_id]['position'],
                    'angle': self.state['ships'][client_id]['angle']
                }
            }
            self.send_response(response, address)

    def handle_shoot(self, payload, address):
        ship_id = payload['ship_id']
        if ship_id in self.state['ships']:
            ship = self.state['ships'][ship_id]
            current_time = time.time()

            # Проверка на перезарядку и количество оставшихся выстрелов
            if ship['is_reloading']:
                if current_time - ship['reload_start_time'] >= 1.5:  # Время перезарядки в секундах
                    ship['is_reloading'] = False
                    ship['shots'] = 10
                else:
                    response = {
                        'status': 'failed',
                        'payload': {
                            'message': 'Reloading in progress'
                        }
                    }
                    self.send_response(response, address)
                    return

            if ship['shots'] > 0:
                laser = self.create_laser(ship)
                self.state['lasers'].append(laser)
                ship['shots'] -= 1
                if ship['shots'] == 0:
                    ship['is_reloading'] = True
                    ship['reload_start_time'] = current_time
                response = {
                    'status': 'success',
                    'payload': {
                        'message': 'Laser fired'
                    }
                }
            else:
                response = {
                    'status': 'failed',
                    'payload': {
                        'message': 'No shots left, reloading'
                    }
                }
                ship['is_reloading'] = True
                ship['reload_start_time'] = current_time

            self.send_response(response, address)

    def create_laser(self, ship):
        # Рассчитать положение передней части корабля для стрельбы
        ship_x, ship_y = ship['position']
        ship_angle = ship['angle']

        # Смещение для передней точки корабля
        ship_length = 25  # длина от центра до "носа" корабля (от угла)
        radius_triangle = 20  # нужно для радиуса носа корабля (откуда будет пуляться)
        tip_x = ship_x + radius_triangle + ship_length * math.cos(math.radians(ship_angle))
        tip_y = ship_y + radius_triangle - ship_length * math.sin(math.radians(ship_angle))

        return {
            "pos": [tip_x, tip_y],
            "direction": ship_angle,
            "vel": [10 * math.cos(math.radians(ship_angle)), -10 * math.sin(math.radians(ship_angle))]
        }

    def send_response(self, response, address):
        self.server_socket.sendto(json.dumps(response).encode(), address)

    def reset_game(self):
        self.start_time = time.time()  # Перезапуск времени старта игры
        self.scores = {'player_0': 0, 'player_1': 0}  # Обнуление счета игроков
        self.state = {
            'asteroids': [],
            'ships': {},
            'lasers': []
        }
        self.running = True
        print("Game has been reset and is ready to start again.")

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

    def disconnect_clients(self):
        disconnect_message = {
            'event': 'disconnect',
            'payload': {
                'message': 'The game is over, disconnecting from server.'
            }
        }
        for client in self.clients:
            self.server_socket.sendto(json.dumps(disconnect_message).encode(), client)
        self.clients = []  # Очистить список клиентов после отключения
        print("All clients have been disconnected.")

    def update_lasers_state(self):
        updated_lasers = []
        for laser in self.state['lasers']:
            laser['pos'][0] += laser['vel'][0]
            laser['pos'][1] += laser['vel'][1]
            if 0 <= laser['pos'][0] <= WIDTH and 0 <= laser['pos'][1] <= HEIGHT:
                updated_lasers.append(laser)
        self.state['lasers'] = updated_lasers

    def check_collisions(self):
        # Check collisions between asteroids and ships
        for asteroid in self.state['asteroids'][:]:
            for ship_id, ship in self.state['ships'].items():
                if ship['hp'] <= 0:
                    continue  # Skip destroyed ships

                ship_x, ship_y = ship['position']
                asteroid_x, asteroid_y = asteroid['pos']
                dist = math.hypot(ship_x - asteroid_x, ship_y - asteroid_y)

                if dist < asteroid['radius']:
                    ship['hp'] -= 1
                    print(f"Collision detected! Ship {ship_id} HP reduced to {ship['hp']}")
                    if ship['hp'] <= 0:
                        print(f"Ship {ship_id} has been destroyed!")
                        ship['respawn_timer'] = 3 * FPS  # Set respawn timer for 3 seconds
                    self.state['asteroids'].remove(asteroid)
                    break

        # Check collisions between lasers and asteroids
        for laser in self.state['lasers'][:]:
            for asteroid in self.state['asteroids'][:]:
                dist = math.hypot(laser['pos'][0] - asteroid['pos'][0], laser['pos'][1] - asteroid['pos'][1])
                if dist < asteroid['radius']:
                    asteroid['hp'] -= 1
                    print(f"Collision detected! Asteroid HP reduced to {asteroid['hp']}")
                    if asteroid['hp'] <= 0:
                        print("Asteroid destroyed!")
                        self.state['asteroids'].remove(asteroid)
                        # Найти, какой корабль выстрелил лазером и добавить ему очки
                        shooter_id = laser.get('ship_id')
                        if shooter_id and shooter_id in self.scores:
                            self.scores[shooter_id] += 1  # Увеличение очков игрока, уничтожившего астероид
                        self.state['lasers'].remove(laser)
                        break

    def check_collision_ships(self):
        # Check collisions between ships
        ship_ids = list(self.state['ships'].keys())
        for i in range(len(ship_ids)):
            for j in range(i + 1, len(ship_ids)):
                ship_1 = self.state['ships'][ship_ids[i]]
                ship_2 = self.state['ships'][ship_ids[j]]

                if ship_1['hp'] <= 0 or ship_2['hp'] <= 0:
                    continue  # Skip destroyed ships

                ship_1_x, ship_1_y = ship_1['position']
                ship_2_x, ship_2_y = ship_2['position']
                dist = math.hypot(ship_1_x - ship_2_x, ship_1_y - ship_2_y)

                if dist < (ship_1['width'] + ship_2['width']) / 2:
                    # Collision detected, reduce HP of both ships
                    ship_1['hp'] -= 1
                    ship_2['hp'] -= 1
                    print(
                        f"Collision detected between ships {ship_ids[i]} and {ship_ids[j]}. Ship {ship_ids[i]} HP: {ship_1['hp']}, Ship {ship_ids[j]} HP: {ship_2['hp']}")

                    # Увеличение очков противника, если корабль уничтожен
                    if ship_1['hp'] <= 0:
                        self.scores[f'player_{j}'] += 1
                    if ship_2['hp'] <= 0:
                        self.scores[f'player_{i}'] += 1

    def handle_respawn(self):
        for ship_id, ship in self.state['ships'].items():
            if ship['hp'] <= 0 and ship['respawn_timer'] > 0:
                ship['respawn_timer'] -= 1
                if ship['respawn_timer'] == 0:
                    ship['hp'] = 3
                    if ship_id == 'player_1':
                        ship['position'] = [WIDTH * 0.2, HEIGHT * 0.2]
                        ship['angle'] = 0
                    elif ship_id == 'player_0':
                        ship['position'] = [WIDTH * 0.8, HEIGHT * 0.8]
                        ship['angle'] = 180
                    ship['shots'] = 10  # Восстановление боезапаса после возрождения
                    print(f"Ship {ship_id} has respawned at position {ship['position']} with HP {ship['hp']}")
                    # Send immediate position update to the client after respawn
                    response = {
                        'status': 'success',
                        'payload': {
                            'message': 'Respawn completed',
                            'position': ship['position'],
                            'angle': ship['angle'],
                            'hp': ship['hp'],
                            'shots': ship['shots']
                        }
                    }
                    client_address = next((addr for addr, cid in zip(self.clients, [ship_id]) if cid == ship_id), None)
                    if client_address:
                        self.send_response(response, client_address)
                    # Broadcasting the updated state to ensure client receives the new position immediately
                    self.broadcast_state()

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

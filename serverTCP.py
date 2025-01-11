import socket
import threading
import json
import time
import random

# Импорт необходимых классов из ваших файлов
from utils import WIDTH, HEIGHT, FPS, MAX_ASTEROIDS, GAME_TIME
from ship import Ship
from asteroid import AsteroidManager
from laser import LaserManager
from gamelogic import GameLogic

HOST = "192.168.22.175"  # IP-адрес сервера (пропишите нужный)
PORT = 12355  # Порт сервера


class GameServer:
    """
    Сервер, хранящий ровно 2 слота игроков (единственная сессия).
    Когда оба подключены, идет игра.
    Если один отключился, сервер ждет его повторного подключения.
    Логика столкновений, стрельбы и т.д. осуществляется через классы:
      - GameLogic
      - AsteroidManager
      - LaserManager
      - Ship
    """

    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()

        # Сессия из 2 слотов (player_id = 0 или 1)
        self.players = [
            {
                'conn': None,
                'addr': None,
                'connected': False,
                'ship_id': 0,
            },
            {
                'conn': None,
                'addr': None,
                'connected': False,
                'ship_id': 1,
            }
        ]

        self.game_started = False

        # Инициализируем игровые объекты
        # (На сервере screen = None, чтобы не рисовать, но логика Ship все равно работает)
        self.ship1 = Ship(None, 0)
        self.ship2 = Ship(None, 1)
        self.ships = [self.ship1, self.ship2]

        self.asteroid_manager = AsteroidManager(MAX_ASTEROIDS)
        self.laser_manager = LaserManager()
        self.logic = GameLogic(self.ships, self.asteroid_manager, self.laser_manager, max_time=GAME_TIME)

        self.running = True
        self.game_ended = False  # Флаг, чтобы при завершении игры показать результат

    def start(self):
        print(f"[SERVER] Started on {self.host}:{self.port}")
        # Поток игрового цикла
        threading.Thread(target=self.game_loop, daemon=True).start()

        # Принимаем входящие подключения
        while self.running:
            conn, addr = self.server_socket.accept()
            print(f"[SERVER] New raw connection from {addr}")
            t = threading.Thread(target=self.handle_raw_connection, args=(conn, addr), daemon=True)
            t.start()

    def reset_game(self):
        """Сброс игрового состояния."""
        self.start_time = time.time()
        self.points = [0] * len(self.ships)
        self.asteroid_manager.asteroids.clear()
        self.laser_manager.lasers.clear()
        print("[SERVER] Game reset.")

    def handle_raw_connection(self, conn, addr):
        """
        1) Получаем первое сообщение: {action:'hello', payload:{player_id:0/1}}
        2) Если слот свободен, назначаем его и переходим к чтению сообщений.
        """
        buffer_str = ""
        try:
            # Ждём первое сообщение
            data = conn.recv(4096)
            if not data:
                conn.close()
                return
            buffer_str += data.decode('utf-8')
            # Берём первую строку
            line, _, remainder = buffer_str.partition('\n')
            buffer_str = remainder
            line = line.strip()
            if not line:
                print("[SERVER] No JSON on first line, closing.")
                conn.close()
                return

            try:
                msg = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"[SERVER] Invalid JSON on hello: {e}")
                conn.close()
                return

            if msg.get('action') != 'hello':
                print("[SERVER] First message not 'hello', closing connection.")
                conn.close()
                return

            wanted_id = msg.get('payload', {}).get('player_id')
            if wanted_id not in (0, 1):
                print("[SERVER] Invalid player_id in hello.")
                conn.close()
                return

            # Пытаемся занять слот
            player_slot = self.players[wanted_id]
            if player_slot['connected']:
                print(f"[SERVER] Slot {wanted_id} is already connected.")
                conn.close()
                return
            # Иначе занимаем
            player_slot['conn'] = conn
            player_slot['addr'] = addr
            player_slot['connected'] = True

            print(f"[SERVER] Player slot {wanted_id} connected from {addr}")

            # Проверяем, подключены ли оба игрока
            if all(player['connected'] for player in self.players):
                print("[SERVER] Both players connected. Starting the game...")
                self.logic.start_time = time.time()  # Устанавливаем стартовое время
                self.game_started = True

            # Переходим к циклу чтения остальных сообщений
            self.handle_client_loop(conn, wanted_id, buffer_str)

        except Exception as e:
            print(f"[SERVER] Exception in handle_raw_connection: {e}")
        finally:
            pass

    def handle_client_loop(self, conn, slot_id, buffer_str):
        """Построчный прием команд (update_position, shoot, и т.д.)"""
        while self.running:
            try:
                data = conn.recv(4096)
                if not data:
                    print(f"[SERVER] Slot {slot_id} disconnected (no data).")
                    break
                buffer_str += data.decode('utf-8')

                # Построчный парсинг
                while '\n' in buffer_str:
                    line, buffer_str = buffer_str.split('\n', 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        msg = json.loads(line)
                        self.process_message(msg, slot_id)
                    except json.JSONDecodeError as e:
                        print(f"[SERVER] JSON decode error: {e}, line={repr(line)}")
                        continue
            except ConnectionResetError:
                print(f"[SERVER] Slot {slot_id} - ConnectionResetError")
                break
            except Exception as e:
                print(f"[SERVER] Slot {slot_id} exception: {e}")
                break

        # Если дошли сюда — клиент отключился
        self.players[slot_id]['connected'] = False
        self.players[slot_id]['conn'] = None
        self.players[slot_id]['addr'] = None
        try:
            conn.close()
        except:
            pass
        print(f"[SERVER] Slot {slot_id} cleaned up.")

    def save_winner_info(self, winner, p1_score, p2_score):
        """
        Сохраняем информацию о победителе в текстовый файл.
        winner = 0 (ничья), 1 (player1), 2 (player2)
        """
        if winner == 1:
            winner_name = "Player1"
            winner_score = p1_score
        elif winner == 2:
            winner_name = "Player2"
            winner_score = p2_score
        else:
            winner_name = "Draw"
            winner_score = p1_score  # или p2_score, ведь они равны при ничьей

        # Простой вариант — дописывать в текстовый файл.
        # Можно заменить на SQLite/JSON и т.д.
        with open("winners.txt", "a", encoding="utf-8") as f:
            f.write(f"{winner_name} | Score: {winner_score} | (P1={p1_score}, P2={p2_score})\n")

        print(f"[SERVER] Winner saved: {winner_name}, score={winner_score}")

    def load_leaderboard():
        """
        Читает файл winners.txt и возвращает список строк (результаты игр).
        """
        leaderboard = []
        try:
            with open("winners.txt", "r", encoding="utf-8") as f:
                # Читаем все строки
                lines = f.readlines()
                # Можно просто сохранить строки как есть
                leaderboard = [line.strip() for line in lines]
        except FileNotFoundError:
            # Если файл не найден, значит, ещё не было ни одной игры
            leaderboard = []
        return leaderboard

    def process_message(self, msg, slot_id):
        """Обработка действий от клиента (update_position, shoot и т.д.)"""
        action = msg.get('action')
        payload = msg.get('payload', {})

        if action == 'update_position':
            pos = payload.get('pos', [0, 0])
            angle = payload.get('angle', 0)
            if 0 <= slot_id < len(self.ships):
                # Обновляем координаты конкретного корабля
                self.ships[slot_id].rect.center = pos
                self.ships[slot_id].angle = angle

        elif action == 'restart':
            print(f"[SERVER] Player {slot_id} requested a restart.")
            self.logic.reset_game()  # Сбрасываем состояние игры
            for ship in self.ships:
                ship.reset()

        elif action == 'shoot':
            if 0 <= slot_id < len(self.ships):
                can_shoot, (lx, ly) = self.ships[slot_id].try_shoot()
                if can_shoot:
                    self.laser_manager.shoot_laser(lx, ly, self.ships[slot_id].angle, slot_id)

        else:
            # Можно добавить ready, respawn, etc.
            print(f"[SERVER] Unknown action: {action}")

    def game_loop(self):
        """Основной игровой цикл на сервере."""
        last_time = time.time()
        while self.running:
            now = time.time()
            dt = now - last_time
            if dt < 1.0 / FPS:
                time.sleep(1.0 / FPS - dt)
            last_time = now

            # Если игра не началась, ждем подключения обоих игроков
            if not self.game_started:
                self.broadcast_state()  # Отправляем текущее состояние (например, "ждем второго игрока")
                continue

            # Иначе полноценная игровая логика
            if len(self.asteroid_manager.asteroids) < MAX_ASTEROIDS:
                self.asteroid_manager.spawn_asteroid()

            game_over = self.logic.update()

            if game_over and not self.game_ended:
                # Игра закончена, сообщаем результат
                self.game_ended = True
                p1_score = self.logic.points[0]
                p2_score = self.logic.points[1]
                if p1_score > p2_score:
                    winner = 1  # Player 1 (slot 0, но человек видит +1)
                elif p2_score > p1_score:
                    winner = 2
                else:
                    winner = 0  # ничья

                self.save_winner_info(winner, p1_score, p2_score)

                end_msg = {
                    'event': 'game_over',
                    'payload': {
                        'scores': [p1_score, p2_score],
                        'winner': winner  # 0=draw, 1=first ship, 2=second ship
                    }
                }
                self.broadcast_message(end_msg)

            self.broadcast_state()

        print("[SERVER] game_loop finished.")
        self.server_socket.close()


    def broadcast_state(self):
        """
        Отправка текущего состояния (корабли, астероиды, лазеры, время, очки).
        Вызывается каждый тик в game_loop.
        """
        # if (self.ship1.is_reloading or self.ship2.is_reloading): print(f"[SERVER] Broadcasting state. Ships: {len(self.ships)}, RELOADING: {self.ship1.is_reloading}, RELOAD_START_TIME: {self.ship1.reload_start_time}, RELOADING2: {self.ship2.is_reloading}, RELOAD_START_TIME2: {self.ship2.reload_start_time}")
        # if (self.ship1.is_respawning or self.ship2.is_respawning): print(f"[SERVER] Broadcasting state. Ships: {len(self.ships)}, RESSPAWNING: {self.ship1.is_respawning}, RESSPAWNING2: {self.ship2.is_respawning}")
        if not self.game_started:
            state = {
                'event': 'waiting_for_players',
                'payload': {
                    'message': 'Waiting for both players to connect...',
                    'connected': sum(player['connected'] for player in self.players)
                }
            }
            self.broadcast_message(state)
            return

        state = {
            'event': 'update_state',
            'payload': {
                'ships': [
                    {
                        'id': i,
                        'hp': s.hp,
                        'pos': [s.rect.centerx, s.rect.centery],
                        'angle': s.angle,
                        'shots': s.shots,
                        'is_respawning': s.is_respawning,
                        'is_reloading': s.is_reloading,
                    }
                    for i, s in enumerate(self.ships)
                ],
                'asteroids': [
                    {
                        'pos': ast['pos'],
                        'radius': ast['radius'],
                        'color': ast['color'],  # Дополнительно, если хотим
                    }
                    for ast in self.asteroid_manager.asteroids
                ],
                'lasers': [
                    {
                        'pos': l['pos'],
                        'owner': l['owner']
                    }
                    for l in self.laser_manager.lasers
                ],
                'score': self.logic.points,  # Текущие очки
                'time_left': self.logic.get_time_left(),
            }
        }
        self.broadcast_message(state)

    def broadcast_message(self, message):
        """Отправка одного JSON-сообщения всем подключённым слотам."""
        data = (json.dumps(message) + '\n').encode('utf-8')
        for p in self.players:
            if p['connected'] and p['conn'] is not None:
                try:
                    p['conn'].sendall(data)
                except Exception as e:
                    print(f"[SERVER] sendall to slot {p['ship_id']} failed: {e}")
                    p['connected'] = False
                    p['conn'] = None
                    p['addr'] = None


if __name__ == "__main__":
    server = GameServer()
    server.start()

import socket
import threading
import json
import pygame
import sys
import time
# Импорт классов/констант для отрисовки
from utils import WIDTH, HEIGHT, BLACK, FPS
from ship import Ship
from asteroid import AsteroidManager
from laser import LaserManager
from gamelogic import GameLogic

HOST = "192.168.22.175"
PORT = 12355


class GameClient:
    """
    Клиент отправляет 'hello' со своим player_id (0 или 1).
    Получает update_state, game_over и т.д. от сервера.
    Локально отрисовывает (ship, asteroids, lasers).
    При нажатии SPACE отправляет shoot, при движении - update_position.
    """

    def __init__(self, server_host=HOST, server_port=PORT, player_id=0):
        self.server_host = server_host
        self.server_port = server_port
        self.player_id = player_id

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(f"Asteroids Client {player_id}")

        # Локальный корабль (только для отрисовки и управления)
        self.ship = Ship(self.screen, player_id)
        self.enemy_ship = Ship(self.screen, abs(1 - player_id))  # Противоположный ID

        # Вспомогательные менеджеры для отрисовки (не для логики столкновений!)
        # Так как сервер сам ведёт "game logic", клиент лишь визуализирует.
        self.asteroid_manager = AsteroidManager()
        self.laser_manager = LaserManager()

        self.running = True
        self.game_state = {}
        self.clock = pygame.time.Clock()
        self.game_over = False

    def connect(self):
        self.client_socket.connect((self.server_host, self.server_port))
        # Первым делом шлём hello
        hello_msg = {
            'action': 'hello',
            'payload': {
                'player_id': self.player_id
            }
        }
        self.send_raw(hello_msg)

        # Поток получения
        t = threading.Thread(target=self.listen_server, daemon=True)
        t.start()

        # Игровой цикл
        self.game_loop()

    def listen_server(self):
        """Построчно читаем JSON от сервера."""
        buffer = ""
        while self.running:
            try:
                data = self.client_socket.recv(4096).decode('utf-8')
                if not data:
                    print("[CLIENT] Server closed connection.")
                    break
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        msg = json.loads(line)
                        self.handle_server_message(msg)
                    except json.JSONDecodeError as e:
                        print(f"[CLIENT] JSON error: {e}, line={repr(line)}")
            except Exception as e:
                print(f"[CLIENT] listen_server error: {e}")
                break
        self.running = False
        print("[CLIENT] listen_server ended")

    def handle_server_message(self, msg):
        event = msg.get('event')
        payload = msg.get('payload', {})

        if event == 'update_state':
            self.game_state = payload
            ships_data = payload.get('ships', [])

            # Обновляем локальный корабль
            for ship_data in ships_data:
                if ship_data['id'] == self.player_id:
                    self.ship.hp = ship_data['hp']
                    self.ship.shots = ship_data['shots']
                    self.ship.rect.center = ship_data['pos']
                    self.ship.angle = ship_data['angle']

                    # Синхронизация флагов респауна и перезарядки
                    self.ship.is_respawning = ship_data.get('is_respawning', False)
                    is_reloading = ship_data.get('is_reloading', False)
                    if is_reloading:
                        # Если началась новая перезарядка
                        if not self.ship.is_reloading:
                            self.ship.reload_start_time = time.time()
                        self.ship.is_reloading = True
                    else:
                        self.ship.is_reloading = False
                else:
                    # Обновляем вражеский корабль
                    self.enemy_ship.hp = ship_data['hp']
                    self.enemy_ship.shots = ship_data['shots']
                    self.enemy_ship.rect.center = ship_data['pos']
                    self.enemy_ship.angle = ship_data['angle']

                    # Синхронизация флагов респауна и перезарядки
                    self.enemy_ship.is_respawning = ship_data.get('is_respawning', False)
                    is_reloading = ship_data.get('is_reloading', False)
                    if is_reloading:
                        # Если началась новая перезарядка
                        if not self.enemy_ship.is_reloading:
                            self.enemy_ship.reload_start_time = time.time()
                        self.enemy_ship.is_reloading = True
                    else:
                        self.enemy_ship.is_reloading = False

        elif event == 'waiting_for_players':
            print("[CLIENT] Waiting for another player...")
            self.game_state = {'time_left': 0}  # Устанавливаем "пустое" состояние

        elif event == 'game_over':
            # Игра закончена, выводим результат
            self.game_over = True
            scores = payload.get('scores', [0, 0])
            winner = payload.get('winner', 0)
            # winner=0 -> ничья, 1 -> игрок1, 2 -> игрок2
            if winner == 1:
                print(f"[CLIENT] Game Over! Player1 wins! Score={scores}")
            elif winner == 2:
                print(f"[CLIENT] Game Over! Player2 wins! Score={scores}")
            else:
                print(f"[CLIENT] Game Over! DRAW! Score={scores}")
        else:
            print(f"[CLIENT] Unknown event: {event}")

    def send_raw(self, obj):
        data = (json.dumps(obj) + "\n").encode('utf-8')
        try:
            self.client_socket.sendall(data)
        except Exception as e:
            print(f"[CLIENT] sendall error: {e}")
            self.running = False

    def send_message(self, action, payload):
        msg = {
            'action': action,
            'payload': payload
        }
        self.send_raw(msg)

    def game_loop(self):
        while self.running:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if self.game_over:
                        # Обработка выбора на экране GAME OVER
                        if event.key == pygame.K_r:  # Нажатие 'R' для рестарта
                            self.restart_game()
                        elif event.key == pygame.K_l:  # Нажатие 'L' для таблицы лидеров
                            self.show_leaderboard()
                    else:
                        if event.key == pygame.K_SPACE:
                            self.send_message('shoot', {})

            if self.game_over:
                # Покажем на экране "Game Over" и ждем ввода
                self.draw_game_over()
                continue

            # Локально двигаем корабль (чисто для анимации)
            keys = pygame.key.get_pressed()
            self.ship.update(keys)

            # Отправляем координаты на сервер
            self.send_message('update_position', {
                'pos': [self.ship.rect.centerx, self.ship.rect.centery],
                'angle': self.ship.angle
            })

            self.draw()

        pygame.quit()
        self.client_socket.close()

    def restart_game(self):
        """Отправить запрос на перезапуск игры и перезапустить локальные объекты."""
        self.send_message('restart', {})
        self.game_over = False
        self.ship.reset()
        self.enemy_ship.reset()
        self.game_state = {}
        print("[CLIENT] Requesting game restart...")

    def show_leaderboard(self):
        """Отображает таблицу лидеров."""
        self.screen.fill(BLACK)
        font = pygame.font.Font(None, 36)

        # Заглушка: таблица лидеров (можно заменить на данные от сервера)
        leaderboard = [
            ("Player1", 120),
            ("Player2", 100),
            ("Player3", 80),
        ]

        title = font.render("LEADERBOARD", True, (255, 255, 255))
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))

        for idx, (name, score) in enumerate(leaderboard):
            entry = font.render(f"{idx + 1}. {name} - {score} pts", True, (255, 255, 255))
            self.screen.blit(entry, (WIDTH // 2 - entry.get_width() // 2, 100 + idx * 40))

        prompt = font.render("Press R to restart or Q to quit", True, (255, 255, 255))
        self.screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, HEIGHT - 100))

        pygame.display.flip()

        # Ожидание нажатия клавиш
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.restart_game()
                        return
                    elif event.key == pygame.K_q:
                        self.running = False
                        return

    def draw_game_over(self):
        """Отрисовка экрана завершения."""
        self.screen.fill(BLACK)
        font = pygame.font.Font(None, 60)
        text = font.render("GAME OVER!", True, (255, 0, 0))
        rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        self.screen.blit(text, rect)

        # Отрисовка счета
        scores = self.game_state.get('score', [0, 0])
        score_text = font.render(f"Final Score: P1={scores[0]} P2={scores[1]}", True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
        self.screen.blit(score_text, score_rect)

        # Отрисовка победителя
        winner = 0 if scores[0] == scores[1] else (1 if scores[0] > scores[1] else 2)
        winner_text = "DRAW!" if winner == 0 else f"Player {winner} Wins!"
        winner_surface = font.render(winner_text, True, (0, 255, 0))
        winner_rect = winner_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 80))
        self.screen.blit(winner_surface, winner_rect)

        # Добавьте подсказки для игроков
        prompt_font = pygame.font.Font(None, 36)
        restart_prompt = prompt_font.render("Press R to Restart or L for Leaderboard", True, (255, 255, 255))
        prompt_rect = restart_prompt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 140))
        self.screen.blit(restart_prompt, prompt_rect)

        pygame.display.flip()

    def draw(self):
        """Отрисовка текущего состояния: корабли, астероиды, лазеры, очки, время."""
        self.screen.fill(BLACK)

        # Проверка состояния ожидания
        if not self.game_state.get('time_left', 0):
            font = pygame.font.Font(None, 36)
            waiting_text = font.render("Waiting for another player...", True, (255, 255, 255))
            self.screen.blit(waiting_text, (WIDTH // 2 - 150, HEIGHT // 2))
            pygame.display.flip()
            return

        # 1) Рисуем локальный корабль (он у нас Ship(screen,...))
        self.ship.draw()
        # Рисуем вражеский корабль
        self.enemy_ship.draw()

        # 2) Рисуем пришедшее от сервера:
        #    asteroids, lasers, ships, score, time_left
        asteroids_data = self.game_state.get('asteroids', [])
        lasers_data = self.game_state.get('lasers', [])
        ships_data = self.game_state.get('ships', [])
        score = self.game_state.get('score', [0, 0])
        time_left = self.game_state.get('time_left', 0)

        # Астероиды
        # (у нас есть asteroid_manager, но логика появления/движения
        #  идёт на сервере, здесь мы только отображаем)
        self.asteroid_manager.asteroids = []
        for ast in asteroids_data:
            # Восстанавливаем словарь, чтобы использовать .draw()
            new_ast = {
                'pos': ast['pos'],
                'vel': [0, 0],  # нам не важно, сервер уже двигает
                'radius': ast['radius'],
                'hp': 1,
                'color': ast['color']
            }
            self.asteroid_manager.asteroids.append(new_ast)
        self.asteroid_manager.draw(self.screen)

        # Лазеры
        self.laser_manager.lasers = []
        for lz in lasers_data:
            laser = {
                'pos': lz['pos'],
                'vel': [0, 0],
                'owner': lz['owner']
            }
            self.laser_manager.lasers.append(laser)
        self.laser_manager.draw(self.screen)

        # Отрисуем счёт
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: P1={score[0]}  P2={score[1]}", True, (255, 255, 255))
        self.screen.blit(score_text, (20, 20))

        # Таймер
        time_text = font.render(f"Time Left: {time_left}", True, (255, 255, 255))
        self.screen.blit(time_text, (WIDTH // 2 - 50, 20))

        pygame.display.flip()


if __name__ == "__main__":
    # Аргумент 1: player_id
    if len(sys.argv) > 1:
        pid = int(sys.argv[1])
    else:
        pid = 0

    # Аргумент 3: Ник игрока (не обязательно, если не нужно — можно удалить)
    if len(sys.argv) > 3:
        nickname = sys.argv[3]
    else:
        nickname = "Player"

    # Теперь передаём host и nickname в конструктор (добавим в __init__ при необходимости)
    client = GameClient(server_host=HOST, server_port=12355, player_id=pid)
    # Если хотим и ник где-то использовать — тоже можно хранить:
    # client.nickname = nickname

    client.connect()

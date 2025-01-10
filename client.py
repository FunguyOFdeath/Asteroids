import socket  # Подключаем модуль для работы с TCP/IP сокетами
import threading  # Подключаем модуль для создания и управления потоками
import json  # Подключаем модуль JSON для сериализации и десериализации данных
import pygame  # Подключаем библиотеку Pygame для графического интерфейса и обработки событий
import sys  # Подключаем модуль sys для работы с системными вызовами и аргументами
import time  # Подключаем модуль time для измерения времени и задержек

from utils import WIDTH, HEIGHT, BLACK, FPS  # Из модуля utils импортируем константы: ширину, высоту, цвет и частоту кадров
from ship import Ship  # Из модуля ship импортируем класс Ship (управление кораблём)
from asteroid import AsteroidManager  # Из модуля asteroid импортируем класс AsteroidManager (работа с астероидами)
from laser import LaserManager  # Из модуля laser импортируем класс LaserManager (работа с лазерами)
from gamelogic import GameLogic  # Из модуля gamelogic импортируем класс GameLogic (здесь напрямую не используется)

HOST = "192.168.22.175"  # Указываем адрес сервера по умолчанию (IP)
PORT = 12355  # Указываем порт сервера по умолчанию

if WIDTH == 0 or HEIGHT == 0:  # Проверяем, не установлены ли размеры окна как 0
    screen_info = pygame.display.Info()  # Получаем информацию об экране (размеры дисплея)
    WIDTH, HEIGHT = screen_info.current_w, screen_info.current_h  # Присваиваем ширину/высоту текущего монитора

class GameClient:  # Объявляем класс GameClient, который будет клиентом игры
    """
    Клиент, который подключается к серверу, получает состояние игры,
    отрисовывает её и обрабатывает события, отправляя их на сервер.
    """  # Докстринг класса

    def __init__(self, server_host=HOST, server_port=PORT, player_id=0):  # Конструктор GameClient
        self.server_host = server_host  # Запоминаем хост сервера
        self.server_port = server_port  # Запоминаем порт сервера
        self.player_id = player_id  # Запоминаем идентификатор игрока (0 или 1)

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Создаём TCP-сокет

        pygame.init()  # Инициализируем Pygame
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)  # Создаём полноэкранное окно нужного размера
        pygame.display.set_caption(f"Asteroids Client {player_id}")  # Устанавливаем заголовок окна с ID игрока

        self.ship = Ship(self.screen, player_id)  # Создаём объект класса Ship для управления собственным кораблём
        self.enemy_ship = Ship(self.screen, abs(1 - player_id))  # Создаём Ship для вражеского корабля (ID противоположен нашему)

        self.asteroid_manager = AsteroidManager()  # Создаём менеджер астероидов для локальной отрисовки
        self.laser_manager = LaserManager()  # Создаём менеджер лазеров для локальной отрисовки

        self.running = True  # Флаг, сигнализирующий, что клиент запущен
        self.game_state = {}  # Словарь для хранения текущего состояния игры, полученного с сервера
        self.clock = pygame.time.Clock()  # Создаём объект Clock для ограничения FPS
        self.game_over = False  # Флаг, показывающий, что игра окончена

    def connect(self):  # Метод для установления соединения с сервером
        self.client_socket.connect((self.server_host, self.server_port))  # Подключаемся к серверу по хосту и порту
        hello_msg = {  # Формируем сообщение "hello"
            'action': 'hello',  # Действие: приветствие
            'payload': {  # Полезная нагрузка
                'player_id': self.player_id  # Указываем свой ID
            }
        }
        self.send_raw(hello_msg)  # Отправляем приветственное сообщение на сервер

        t = threading.Thread(target=self.listen_server, daemon=True)  # Создаём поток, слушающий ответы сервера
        t.start()  # Запускаем поток в фоновом режиме

        self.game_loop()  # Переходим к выполнению игрового цикла

    def listen_server(self):  # Метод, постоянно слушающий сообщения от сервера
        buffer = ""  # Создаём пустой буфер для накопления данных
        while self.running:  # Пока клиентский цикл не остановлен
            try:
                data = self.client_socket.recv(4096).decode('utf-8')  # Считываем данные из сокета и декодируем
                if not data:  # Если данные пусты, сервер закрыл соединение
                    print("[CLIENT] Server closed connection.")  # Печатаем сообщение о закрытии
                    break  # Прерываем цикл
                buffer += data  # Добавляем полученную порцию в буфер
                while '\n' in buffer:  # Пока в буфере есть символ новой строки
                    line, buffer = buffer.split('\n', 1)  # Отделяем одну строку
                    line = line.strip()  # Убираем лишние пробелы по краям
                    if not line:  # Если строка пуста, пропускаем
                        continue
                    try:
                        msg = json.loads(line)  # Пробуем распарсить строку как JSON
                        self.handle_server_message(msg)  # Обрабатываем полученное сообщение
                    except json.JSONDecodeError as e:  # Если ошибка в структуре JSON
                        print(f"[CLIENT] JSON error: {e}, line={repr(line)}")  # Печатаем ошибку
            except Exception as e:  # Если любая ошибка чтения сокета
                print(f"[CLIENT] listen_server error: {e}")  # Выводим сообщение об ошибке
                break  # Прерываем цикл
        self.running = False  # Ставим флаг, что клиентский цикл завершается
        print("[CLIENT] listen_server ended")  # Печатаем информацию о завершении потока

    def handle_server_message(self, msg):  # Метод, обрабатывающий входящие сообщения от сервера
        event = msg.get('event')  # Извлекаем тип события
        payload = msg.get('payload', {})  # Извлекаем полезную нагрузку (словарь с данными)

        if event == 'update_state':  # Если пришло обновление состояния игры
            self.game_state = payload  # Сохраняем состояние в локальную переменную
            ships_data = payload.get('ships', [])  # Извлекаем список кораблей из состояния

            for ship_data in ships_data:  # Перебираем все данные о кораблях
                if ship_data['id'] == self.player_id:  # Если это информация о нашем корабле
                    self.ship.hp = ship_data['hp']  # Синхронизируем здоровье
                    self.ship.shots = ship_data['shots']  # Синхронизируем запас выстрелов
                    self.ship.rect.center = ship_data['pos']  # Синхронизируем позицию корабля (x, y)
                    self.ship.angle = ship_data['angle']  # Синхронизируем угол поворота

                    self.ship.is_respawning = ship_data.get('is_respawning', False)  # Узнаём, идёт ли респаун
                    is_reloading = ship_data.get('is_reloading', False)  # Узнаём, идёт ли перезарядка
                    if is_reloading:  # Если перезарядка
                        if not self.ship.is_reloading:  # Если локально не стоял флаг перезарядки
                            self.ship.reload_start_time = time.time()  # Запоминаем время начала перезарядки
                        self.ship.is_reloading = True  # Ставим флаг перезарядки
                    else:
                        self.ship.is_reloading = False  # Снимаем флаг перезарядки
                else:  # Иначе это вражеский корабль
                    self.enemy_ship.hp = ship_data['hp']  # Синхронизируем здоровье вражеского корабля
                    self.enemy_ship.shots = ship_data['shots']  # Синхронизируем запас выстрелов
                    self.enemy_ship.rect.center = ship_data['pos']  # Синхронизируем позицию
                    self.enemy_ship.angle = ship_data['angle']  # Синхронизируем угол

                    self.enemy_ship.is_respawning = ship_data.get('is_respawning', False)  # Узнаём о респауне
                    is_reloading = ship_data.get('is_reloading', False)  # Проверяем, есть ли перезарядка
                    if is_reloading:  # Если идёт перезарядка
                        if not self.enemy_ship.is_reloading:  # Если локально у нас не стоял флаг
                            self.enemy_ship.reload_start_time = time.time()  # Запоминаем время старта перезарядки
                        self.enemy_ship.is_reloading = True  # Ставим флаг перезарядки
                    else:
                        self.enemy_ship.is_reloading = False  # Снимаем флаг перезарядки

        elif event == 'waiting_for_players':  # Если сервер сообщил, что ждёт подключение второго игрока
            print("[CLIENT] Waiting for another player...")  # Выводим уведомление
            self.game_state = {'time_left': 0}  # Сбрасываем время, чтобы игра не шла локально

        elif event == 'game_over':  # Если сервер сообщил о завершении игры
            self.game_over = True  # Ставим флаг конца игры
            scores = payload.get('scores', [0, 0])  # Извлекаем счёт
            winner = payload.get('winner', 0)  # Извлекаем ID победителя (0=ничья,1=первый игрок,2=второй игрок)
            if winner == 1:  # Если победил первый игрок
                print(f"[CLIENT] Game Over! Player1 wins! Score={scores}")
            elif winner == 2:  # Если победил второй игрок
                print(f"[CLIENT] Game Over! Player2 wins! Score={scores}")
            else:  # Иначе ничья
                print(f"[CLIENT] Game Over! DRAW! Score={scores}")

        else:  # Если событие не опознано
            print(f"[CLIENT] Unknown event: {event}")  # Печатаем предупреждение

    def send_raw(self, obj):  # Метод, отправляющий JSON-сообщение в сокет
        data = (json.dumps(obj) + "\n").encode('utf-8')  # Преобразуем obj в JSON-строку, добавляем перевод строки, кодируем в байты
        try:
            self.client_socket.sendall(data)  # Отправляем все данные на сервер
        except Exception as e:  # Если при отправке возникла ошибка
            print(f"[CLIENT] sendall error: {e}")  # Выводим в консоль
            self.running = False  # Ставим флаг остановки клиента

    def send_message(self, action, payload):  # Метод, упрощающий отправку сообщений (формирует JSON)
        msg = {  # Собираем словарь с полями action и payload
            'action': action,
            'payload': payload
        }
        self.send_raw(msg)  # Вызываем send_raw для фактической отправки

    def game_loop(self):  # Основной игровой цикл клиента
        while self.running:  # Пока клиент не выключен
            self.clock.tick(FPS)  # Делаем задержку, чтобы не превышать FPS кадров в секунду
            for event in pygame.event.get():  # Считываем все события из очереди
                if event.type == pygame.QUIT:  # Если пользователь закрыл окно
                    self.running = False  # Ставим флаг остановки
                elif event.type == pygame.KEYDOWN:  # Если нажата клавиша
                    if self.game_over:  # Если игра окончена
                        if event.key == pygame.K_r:  # Если нажата клавиша 'R'
                            self.restart_game()  # Запрашиваем рестарт у сервера
                        elif event.key == pygame.K_l:  # Если нажата клавиша 'L'
                            self.show_leaderboard()  # Показываем таблицу лидеров (локально)
                    else:  # Если игра не окончена
                        if event.key == pygame.K_SPACE:  # Если нажата клавиша 'Space'
                            self.send_message('shoot', {})  # Отправляем серверу команду "shoot"

            if self.game_over:  # Если флаг конца игры стоит
                self.draw_game_over()  # Рисуем экран "Game Over"
                continue  # Пропускаем оставшуюся часть цикла (без update)

            keys = pygame.key.get_pressed()  # Получаем текущий набор нажатых клавиш
            self.ship.update(keys)  # Локально двигаем свой корабль (для анимации)

            self.send_message('update_position', {  # Отправляем серверу новую позицию и угол
                'pos': [self.ship.rect.centerx, self.ship.rect.centery],
                'angle': self.ship.angle
            })

            self.draw()  # Отрисовываем текущее состояние

        pygame.quit()  # Вызываем выход из Pygame, останавливая графику
        self.client_socket.close()  # Закрываем сокет, завершая соединение

    def restart_game(self):  # Метод, запрашивающий перезапуск игры у сервера
        self.send_message('restart', {})  # Отправляем действие 'restart'
        self.game_over = False  # Снимаем флаг окончания игры
        self.ship.reset()  # Сбрасываем параметры нашего корабля
        self.enemy_ship.reset()  # Сбрасываем параметры вражеского корабля
        self.game_state = {}  # Очищаем локальное состояние
        print("[CLIENT] Requesting game restart...")  # Выводим в консоль

    def show_leaderboard(self):  # Метод, показывающий "заглушку" таблицы лидеров
        self.screen.fill(BLACK)  # Закрашиваем фон чёрным
        font = pygame.font.Font(None, 36)  # Создаём шрифт нужного размера

        leaderboard = [  # Заглушка, имитирующая список лидеров
            ("Player1", 120),
            ("Player2", 100),
            ("Player3", 80),
        ]

        title = font.render("LEADERBOARD", True, (255, 255, 255))  # Рендерим надпись "LEADERBOARD"
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))  # Помещаем её по центру сверху

        for idx, (name, score) in enumerate(leaderboard):  # Перебираем элементы из списка
            entry = font.render(f"{idx + 1}. {name} - {score} pts", True, (255, 255, 255))  # Формируем строку с местом, именем, очками
            self.screen.blit(entry, (WIDTH // 2 - entry.get_width() // 2, 100 + idx * 40))  # Рисуем каждую строчку

        prompt = font.render("Press R to restart or Q to quit", True, (255, 255, 255))  # Подсказка с командами
        self.screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, HEIGHT - 100))  # Размещаем подсказку ближе к низу

        pygame.display.flip()  # Обновляем экран, показывая все изменения

        while True:  # Входим в цикл ожидания действий от пользователя
            for event in pygame.event.get():  # Считываем события
                if event.type == pygame.QUIT:  # Если закрывают окно
                    self.running = False  # Прерываем игру
                    return
                elif event.type == pygame.KEYDOWN:  # Если нажата клавиша
                    if event.key == pygame.K_r:  # Нажали R
                        self.restart_game()  # Запрашиваем рестарт
                        return
                    elif event.key == pygame.K_q:  # Нажали Q
                        self.running = False  # Прерываем игру
                        return

    def draw_game_over(self):  # Метод, рисующий экран, сообщающий об окончании игры
        self.screen.fill(BLACK)  # Закрашиваем фон чёрным
        font = pygame.font.Font(None, 60)  # Создаём шрифт побольше (60)
        text = font.render("GAME OVER!", True, (255, 0, 0))  # Рисуем строку "GAME OVER!" красным цветом
        rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))  # Центрируем эту надпись чуть выше середины
        self.screen.blit(text, rect)  # Отображаем надпись на экране

        scores = self.game_state.get('score', [0, 0])  # Получаем счёт из состояния
        score_text = font.render(f"Final Score: P1={scores[0]} P2={scores[1]}", True, (255, 255, 255))  # Формируем строку с очками
        score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))  # Центрируем чуть ниже надписи
        self.screen.blit(score_text, score_rect)  # Отображаем счёт

        winner = 0 if scores[0] == scores[1] else (1 if scores[0] > scores[1] else 2)  # Определяем победителя (0=ничья,1=1й,2=2й)
        winner_text = "DRAW!" if winner == 0 else f"Player {winner} Wins!"  # Формируем текст победы или ничьей
        winner_surface = font.render(winner_text, True, (0, 255, 0))  # Рендерим надпись с результатом
        winner_rect = winner_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 80))  # Ставим чуть ниже счёта
        self.screen.blit(winner_surface, winner_rect)  # Рисуем надпись победителя

        prompt_font = pygame.font.Font(None, 36)  # Создаём шрифт для подсказок (36)
        restart_prompt = prompt_font.render("Press R to Restart or L for Leaderboard", True, (255, 255, 255))  # Текст подсказки
        prompt_rect = restart_prompt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 140))  # Размещаем ещё ниже
        self.screen.blit(restart_prompt, prompt_rect)  # Отображаем эту подсказку

        pygame.display.flip()  # Обновляем экран, чтобы всё отобразилось

    def draw(self):  # Метод, который рисует текущее состояние игры (корабли, астероиды, лазеры)
        self.screen.fill(BLACK)  # Заливаем фон чёрным

        if not self.game_state.get('time_left', 0):  # Если в состоянии нет поля time_left или оно равно 0 (ожидание)
            font = pygame.font.Font(None, 36)  # Создаём шрифт
            waiting_text = font.render("Waiting for another player...", True, (255, 255, 255))  # Рисуем текст ожидания
            self.screen.blit(waiting_text, (WIDTH // 2 - 150, HEIGHT // 2))  # Ставим примерно по центру
            pygame.display.flip()  # Обновляем экран
            return  # Выходим из метода, так как рисовать больше нечего

        self.ship.draw()  # Рисуем наш корабль
        self.enemy_ship.draw()  # Рисуем вражеский корабль

        asteroids_data = self.game_state.get('asteroids', [])  # Получаем список астероидов из состояния
        lasers_data = self.game_state.get('lasers', [])  # Получаем список лазеров из состояния
        ships_data = self.game_state.get('ships', [])  # (Не обязательно используем, но получаем данные о кораблях)
        score = self.game_state.get('score', [0, 0])  # Извлекаем счёт из состояния
        time_left = self.game_state.get('time_left', 0)  # Сколько осталось времени до конца матча

        self.asteroid_manager.asteroids = []  # Очищаем локальный список астероидов
        for ast in asteroids_data:  # Перебираем каждый астероид, присланный сервером
            new_ast = {
                'pos': ast['pos'],  # Позиция астероида
                'vel': [0, 0],  # Скорость неважна, так как движение на сервере
                'radius': ast['radius'],  # Радиус
                'hp': 1,  # Здесь захардкожено 1, просто для отрисовки
                'color': ast['color']  # Цвет
            }
            self.asteroid_manager.asteroids.append(new_ast)  # Добавляем его в локальный менеджер
        self.asteroid_manager.draw(self.screen)  # Рисуем все астероиды

        self.laser_manager.lasers = []  # Очищаем локальный список лазеров
        for lz in lasers_data:  # Перебираем каждый лазер, присланный сервером
            laser = {
                'pos': lz['pos'],  # Позиция лазера
                'vel': [0, 0],  # Скорость неважна, так как движение считает сервер
                'owner': lz['owner']  # Какому кораблю принадлежит
            }
            self.laser_manager.lasers.append(laser)  # Добавляем лазер в локальный менеджер
        self.laser_manager.draw(self.screen)  # Рисуем лазеры

        font = pygame.font.Font(None, 36)  # Создаём шрифт
        score_text = font.render(f"Score: P1={score[0]}  P2={score[1]}", True, (255, 255, 255))  # Формируем текст счёта
        self.screen.blit(score_text, (20, 20))  # Помещаем в левом верхнем углу

        time_text = font.render(f"Time Left: {time_left}", True, (255, 255, 255))  # Текст оставшегося времени
        self.screen.blit(time_text, (WIDTH // 2 - 50, 20))  # Размещаем ближе к центру по горизонтали

        pygame.display.flip()  # Обновляем экран, чтобы показать все отрисованные элементы

if __name__ == "__main__":  # Проверяем, запускают ли данный файл напрямую
    if len(sys.argv) > 1:  # Если в аргументах командной строки есть что-то ещё, кроме имени файла
        pid = int(sys.argv[1])  # Пытаемся преобразовать первый аргумент в число (номер игрока)
    else:
        pid = 0  # Если аргумент не задан, то назначаем player_id = 0
    client = GameClient(player_id=pid)  # Создаём объект клиента с нужным ID
    client.connect()  # Подключаемся к серверу и запускаем игру

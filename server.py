import socket  # Импортируем модуль для работы с TCP/IP-соединениями
import threading  # Импортируем модуль для многопоточности
import json  # Импортируем модуль для кодирования и декодирования JSON
import time  # Импортируем модуль для измерения времени и пауз
import random  # Импортируем модуль для генерации случайных чисел

from utils import FPS, MAX_ASTEROIDS, GAME_TIME  # Импортируем нужные константы из utils
from ship import Ship  # Импортируем класс Ship (логика корабля)
from asteroid import AsteroidManager  # Импортируем класс AsteroidManager (управление астероидами)
from laser import LaserManager  # Импортируем класс LaserManager (управление лазерами)
from gamelogic import GameLogic  # Импортируем класс GameLogic (общая логика столкновений)

HOST = "192.168.22.175"  # Задаём IP-адрес сервера по умолчанию
PORT = 12355  # Задаём порт сервера по умолчанию


class GameServer:  # Объявляем класс GameServer, представляющий серверную часть игры
    def __init__(self, host=HOST, port=PORT):  # Инициализатор сервера, принимает хост и порт
        self.host = host  # Сохраняем хост в поле экземпляра
        self.port = port  # Сохраняем порт в поле экземпляра

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Создаём TCP-сокет
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Разрешаем переиспользовать адрес
        self.server_socket.bind((self.host, self.port))  # Привязываем сокет к указанному хосту и порту
        self.server_socket.listen()  # Ставим сокет в режим прослушивания входящих подключений

        self.players = [  # Создаём список из двух слотов для игроков
            {
                'conn': None,  # Сокет игрока (отсутствует по умолчанию)
                'addr': None,  # Адрес игрока (отсутствует по умолчанию)
                'connected': False,  # Флаг подключения (False изначально)
                'ship_id': 0,  # Номер корабля = 0
            },
            {
                'conn': None,  # Сокет второго игрока
                'addr': None,  # Адрес второго игрока
                'connected': False,  # Флаг подключения для второго
                'ship_id': 1,  # Номер корабля = 1
            }
        ]

        self.game_started = False  # Флаг, указывающий, началась ли игра
        self.ship1 = Ship(None, 0)  # Создаём корабль №0 (без экрана, ведь это сервер)
        self.ship2 = Ship(None, 1)  # Создаём корабль №1 (без экрана)
        self.ships = [self.ship1, self.ship2]  # Собираем корабли в список для удобства

        self.asteroid_manager = AsteroidManager(MAX_ASTEROIDS)  # Создаём менеджер астероидов с лимитом
        self.laser_manager = LaserManager()  # Создаём менеджер лазеров
        self.logic = GameLogic(self.ships, self.asteroid_manager, self.laser_manager,
                               max_time=GAME_TIME)  # Инициализируем логику игры

        self.running = True  # Флаг, что сервер запущен
        self.game_ended = False  # Флаг, что игра завершена (для отправки результата)

    def start(self):  # Метод запуска сервера
        print(f"[SERVER] Started on {self.host}:{self.port}")  # Выводим сообщение о старте
        threading.Thread(target=self.game_loop, daemon=True).start()  # Стартуем поток игрового цикла

        while self.running:  # Пока сервер работает
            conn, addr = self.server_socket.accept()  # Принимаем новое соединение
            print(f"[SERVER] New raw connection from {addr}")  # Выводим инфу о новом подключении
            t = threading.Thread(target=self.handle_raw_connection, args=(conn, addr), daemon=True)  # Создаём поток
            t.start()  # Запускаем поток обработки

    def reset_game(self):  # Метод для сброса игрового состояния
        self.start_time = time.time()  # Запоминаем текущее время как стартовое
        self.points = [0] * len(self.ships)  # Обнуляем очки для всех кораблей
        self.asteroid_manager.asteroids.clear()  # Чистим список астероидов
        self.laser_manager.lasers.clear()  # Чистим список лазеров
        print("[SERVER] Game reset.")  # Выводим сообщение о сбросе

    def handle_raw_connection(self, conn, addr):  # Метод обработки нового соединения (первое сообщение)
        buffer_str = ""  # Создаём буфер для чтения
        try:
            data = conn.recv(4096)  # Читаем данные из сокета
            if not data:  # Если данные пусты
                conn.close()  # Закрываем соединение
                return  # Выходим из метода
            buffer_str += data.decode('utf-8')  # Декодируем данные и добавляем в буфер

            line, _, remainder = buffer_str.partition('\n')  # Ищем первую строку, отделяем её
            buffer_str = remainder  # Остальное сохраняем в buffer_str
            line = line.strip()  # Убираем пробелы
            if not line:  # Если строка пуста
                print("[SERVER] No JSON on first line, closing.")  # Выводим ошибку
                conn.close()  # Закрываем соединение
                return

            try:
                msg = json.loads(line)  # Пробуем интерпретировать строку как JSON
            except json.JSONDecodeError as e:  # Если ошибка декодирования JSON
                print(f"[SERVER] Invalid JSON on hello: {e}")  # Выводим лог
                conn.close()  # Закрываем соединение
                return

            if msg.get('action') != 'hello':  # Если действие не 'hello'
                print("[SERVER] First message not 'hello', closing connection.")  # Логируем
                conn.close()  # Закрываем соединение
                return

            wanted_id = msg.get('payload', {}).get('player_id')  # Извлекаем желаемый ID
            if wanted_id not in (0, 1):  # Проверяем ID
                print("[SERVER] Invalid player_id in hello.")  # Логируем
                conn.close()  # Закрываем
                return

            player_slot = self.players[wanted_id]  # Получаем слот, соответствующий ID
            if player_slot['connected']:  # Если этот слот уже занят
                print(f"[SERVER] Slot {wanted_id} is already connected.")  # Логируем
                conn.close()  # Закрываем
                return

            player_slot['conn'] = conn  # Назначаем сокет
            player_slot['addr'] = addr  # Назначаем адрес
            player_slot['connected'] = True  # Ставим флаг подключения

            print(f"[SERVER] Player slot {wanted_id} connected from {addr}")  # Лог

            if all(player['connected'] for player in self.players):  # Если оба слота заняты
                print("[SERVER] Both players connected. Starting the game...")  # Выводим
                self.logic.start_time = time.time()  # Устанавливаем время старта логики
                self.game_started = True  # Ставим флаг начала игры

            self.handle_client_loop(conn, wanted_id, buffer_str)  # Переходим к циклу чтения сообщений
        except Exception as e:  # Ловим любые исключения
            print(f"[SERVER] Exception in handle_raw_connection: {e}")  # Логируем
        finally:
            pass  # Заглушка

    def handle_client_loop(self, conn, slot_id, buffer_str):  # Метод для построчной обработки команд
        while self.running:  # Пока сервер работает
            try:
                data = conn.recv(4096)  # Считываем данные из сокета
                if not data:  # Если пусто
                    print(f"[SERVER] Slot {slot_id} disconnected (no data).")  # Лог
                    break  # Выходим из цикла
                buffer_str += data.decode('utf-8')  # Декодируем и добавляем к буферу

                while '\n' in buffer_str:  # Пока есть перевод строки
                    line, buffer_str = buffer_str.split('\n', 1)  # Отделяем строку
                    line = line.strip()  # Убираем пробелы
                    if not line:  # Если строка пуста
                        continue
                    try:
                        msg = json.loads(line)  # Пробуем распарсить JSON
                        self.process_message(msg, slot_id)  # Обрабатываем сообщение
                    except json.JSONDecodeError as e:  # Если ошибка JSON
                        print(f"[SERVER] JSON decode error: {e}, line={repr(line)}")  # Лог
                        continue
            except ConnectionResetError:  # Если соединение было резко закрыто
                print(f"[SERVER] Slot {slot_id} - ConnectionResetError")  # Логируем
                break  # Прерываем
            except Exception as e:  # Другие исключения
                print(f"[SERVER] Slot {slot_id} exception: {e}")  # Лог
                break  # Прерываем

        self.players[slot_id]['connected'] = False  # Ставим флаг, что слот теперь не подключён
        self.players[slot_id]['conn'] = None  # Убираем сокет
        self.players[slot_id]['addr'] = None  # Убираем адрес
        try:
            conn.close()  # Пробуем закрыть соединение
        except:
            pass  # Игнорируем любые ошибки тут
        print(f"[SERVER] Slot {slot_id} cleaned up.")  # Логируем, что слот очищен

    def process_message(self, msg, slot_id):  # Метод, который разбирает действия клиента
        action = msg.get('action')  # Получаем действие (строку)
        payload = msg.get('payload', {})  # Получаем данные (словарь)

        if action == 'update_position':  # Если действие "update_position"
            pos = payload.get('pos', [0, 0])  # Извлекаем позицию
            angle = payload.get('angle', 0)  # Извлекаем угол
            if 0 <= slot_id < len(self.ships):  # Если слот_id валиден
                self.ships[slot_id].rect.center = pos  # Присваиваем позицию кораблю
                self.ships[slot_id].angle = angle  # Присваиваем угол кораблю

        elif action == 'restart':  # Если действие "restart"
            print(f"[SERVER] Player {slot_id} requested a restart.")  # Логируем
            self.logic.reset_game()  # Сбрасываем игру в логике
            for ship in self.ships:  # Перебираем корабли
                ship.reset()  # Сбрасываем параметры каждого корабля

        elif action == 'shoot':  # Если действие "shoot"
            if 0 <= slot_id < len(self.ships):  # Если слот корректен
                can_shoot, (lx, ly) = self.ships[slot_id].try_shoot()  # Пытаемся выстрелить
                if can_shoot:  # Если выстрел возможен
                    self.laser_manager.shoot_laser(lx, ly, self.ships[slot_id].angle, slot_id)  # Добавляем лазер

        else:  # Если действие не распознано
            print(f"[SERVER] Unknown action: {action}")  # Логируем

    def game_loop(self):  # Основной игровой цикл сервера (периодический)
        last_time = time.time()  # Запоминаем время предыдущего шага
        while self.running:  # Пока сервер работает
            now = time.time()  # Текущее время
            dt = now - last_time  # Прошедшее время
            if dt < 1.0 / FPS:  # Если с момента прошлого шага прошло меньше времени, чем нужно
                time.sleep(1.0 / FPS - dt)  # Спим, чтобы выдержать FPS
            last_time = now  # Обновляем предыдущий шаг

            if not self.game_started:  # Если игра ещё не начата
                self.broadcast_state()  # Шлём состояние (ждём игроков)
                continue  # Переходим к следующему циклу

            if len(self.asteroid_manager.asteroids) < MAX_ASTEROIDS:  # Если астероидов меньше лимита
                self.asteroid_manager.spawn_asteroid()  # Добавляем новый

            game_over = self.logic.update()  # Обновляем общую логику (столкновения, таймер)

            if game_over and not self.game_ended:  # Если логика говорит, что пора закончить, и раньше не завершали
                self.game_ended = True  # Ставим флаг
                p1_score = self.logic.points[0]  # Считаем очки первого
                p2_score = self.logic.points[1]  # Считаем очки второго
                if p1_score > p2_score:  # Если у первого очков больше
                    winner = 1  # Победил первый
                elif p2_score > p1_score:  # Иначе если у второго больше
                    winner = 2  # Победил второй
                else:  # Иначе ничья
                    winner = 0  # Признак ничьи

                end_msg = {  # Формируем сообщение о конце игры
                    'event': 'game_over',
                    'payload': {
                        'scores': [p1_score, p2_score],
                        'winner': winner
                    }
                }
                self.broadcast_message(end_msg)  # Шлём всем игрокам

            self.broadcast_state()  # Шлём текущее состояние

        print("[SERVER] game_loop finished.")  # Логируем
        self.server_socket.close()  # Закрываем серверный сокет

    def broadcast_state(self):  # Метод, отсылающий всем текущее состояние игры
        if not self.game_started:  # Если игра не началась
            state = {  # Формируем состояние: ждём игроков
                'event': 'waiting_for_players',
                'payload': {
                    'message': 'Waiting for both players to connect...',
                    'connected': sum(player['connected'] for player in self.players)
                }
            }
            self.broadcast_message(state)  # Шлём
            return  # Выходим из метода

        state = {  # Формируем состояние "update_state"
            'event': 'update_state',
            'payload': {
                'ships': [  # Описание кораблей
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
                'asteroids': [  # Описание астероидов
                    {
                        'pos': ast['pos'],
                        'radius': ast['radius'],
                        'color': ast['color'],
                    }
                    for ast in self.asteroid_manager.asteroids
                ],
                'lasers': [  # Описание лазеров
                    {
                        'pos': l['pos'],
                        'owner': l['owner']
                    }
                    for l in self.laser_manager.lasers
                ],
                'score': self.logic.points,  # Текущие очки
                'time_left': self.logic.get_time_left(),  # Сколько секунд осталось
            }
        }
        self.broadcast_message(state)  # Вызываем рассылку сформированного состояния

    def broadcast_message(self, message):  # Метод, рассылающий сообщение всем игрокам
        data = (json.dumps(message) + '\n').encode('utf-8')  # Превращаем в JSON, добавляем перевод строки, кодируем
        for p in self.players:  # Перебираем оба слота
            if p['connected'] and p['conn'] is not None:  # Если слот подключён
                try:
                    p['conn'].sendall(data)  # Отправляем данные
                except Exception as e:  # Если ошибка
                    print(f"[SERVER] sendall to slot {p['ship_id']} failed: {e}")  # Логируем
                    p['connected'] = False  # Ставим флаг, что больше не подключён
                    p['conn'] = None  # Очищаем сокет
                    p['addr'] = None  # Очищаем адрес


if __name__ == "__main__":  # Точка входа, если запускаем этот файл
    server = GameServer()  # Создаём экземпляр сервера с настройками по умолчанию
    server.start()  # Запускаем сервер

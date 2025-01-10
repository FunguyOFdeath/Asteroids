import pygame  # Библиотека для работы с графикой и игровыми событиями
import time  # Для работы с таймингами
import math  # Для математических расчетов, например, вычисления расстояния
import sys  # Для управления завершением программы
import random  # Для генерации случайных чисел

from asteroid import AsteroidManager  # Управление астероидами
from laser import LaserManager  # Управление лазерами
from ship import Ship  # Логика кораблей
from utils import WIDTH, HEIGHT, FPS, BLACK, WHITE, MAX_ASTEROIDS, GAME_TIME  # Константы и настройки

if WIDTH == 0 or HEIGHT == 0:  # Проверяем, не равны ли размеры экрана нулю
    screen_info = pygame.display.Info()  # Получаем информацию о текущем экране
    WIDTH, HEIGHT = screen_info.current_w, screen_info.current_h  # Устанавливаем размеры экрана

class BotPlayer2:  # Класс для управления ботом в игре
    def __init__(self, ship, asteroid_manager, laser_manager):
        self.ship = ship  # Корабль бота
        self.asteroid_manager = asteroid_manager  # Менеджер астероидов
        self.laser_manager = laser_manager  # Менеджер лазеров
        self.evade_mode = False  # Флаг уклонения
        self.last_evade_time = 0  # Время последнего уклонения
        self.evade_duration = 1.0  # Длительность уклонения

    def update(self, player_ship):  # Обновление логики бота
        if self.ship.is_respawning:  # Если корабль бота перерождается, ничего не делаем
            return

        current_time = time.time()  # Текущее время

        if self.evade_mode:  # Если включен режим уклонения
            if current_time - self.last_evade_time > self.evade_duration:  # Проверяем, завершилось ли уклонение
                self.evade_mode = False
            else:
                self.random_evade()  # Выполняем уклонение
                return

        nearest_ast = self.find_nearest_asteroid()  # Ищем ближайший астероид
        if nearest_ast:  # Если найден астероид
            dist_ast = self.dist(self.ship.rect.center, nearest_ast['pos'])  # Вычисляем расстояние до него
            if dist_ast < (nearest_ast['radius'] + self.ship.radius + 60):  # Если астероид слишком близко
                self.evade_mode = True  # Включаем режим уклонения
                self.last_evade_time = current_time  # Запоминаем время уклонения
                return

        self.aim_and_attack(player_ship)  # Целимся и атакуем игрока

    def random_evade(self):  # Логика уклонения
        turn_dir = random.choice([-1, 1])  # Выбираем направление поворота
        move_dir = random.choice([-1, 1])  # Выбираем направление движения
        self.ship.angle += 5 * turn_dir  # Меняем угол корабля

        dx = int(self.ship.speed * math.cos(math.radians(self.ship.angle))) * move_dir  # Расчет движения по оси X
        dy = int(self.ship.speed * math.sin(math.radians(self.ship.angle))) * move_dir * (-1)  # Расчет движения по оси Y
        self.ship.rect.x += dx  # Изменяем координаты корабля по X
        self.ship.rect.y += dy  # Изменяем координаты корабля по Y
        self.ship.rect.x %= WIDTH  # Учитываем границы экрана по X
        self.ship.rect.y %= HEIGHT  # Учитываем границы экрана по Y

    def aim_and_attack(self, player_ship):  # Логика атаки игрока
        sx, sy = self.ship.rect.center  # Координаты центра корабля бота
        px, py = player_ship.rect.center  # Координаты центра корабля игрока

        desired_angle = math.degrees(math.atan2(sy - py, px - sx))  # Вычисляем угол до игрока
        angle_diff = (desired_angle - self.ship.angle) % 360  # Разница углов
        if angle_diff > 180:  # Выбираем направление поворота
            self.ship.angle -= 3
        else:
            self.ship.angle += 3

        dist_p = self.dist((sx, sy), (px, py))  # Расстояние до игрока
        if dist_p > 150:  # Если игрок далеко, приближаемся
            dx = int(self.ship.speed * math.cos(math.radians(self.ship.angle)))
            dy = int(self.ship.speed * math.sin(math.radians(self.ship.angle))) * (-1)
            self.ship.rect.x += dx
            self.ship.rect.y += dy
        elif dist_p < 80:  # Если игрок слишком близко, отходим
            dx = int(self.ship.speed * math.cos(math.radians(self.ship.angle)))
            dy = int(self.ship.speed * math.sin(math.radians(self.ship.angle))) * (-1)
            self.ship.rect.x -= dx
            self.ship.rect.y -= dy

        self.ship.rect.x %= WIDTH  # Учитываем границы экрана по X
        self.ship.rect.y %= HEIGHT  # Учитываем границы экрана по Y

        can_shoot, (lx, ly) = self.ship.try_shoot()  # Проверяем возможность стрельбы
        if can_shoot:  # Если стрельба возможна
            self.laser_manager.shoot_laser(lx, ly, self.ship.angle, self.ship.number)  # Стреляем

    def find_nearest_asteroid(self):  # Поиск ближайшего астероида
        if not self.asteroid_manager.asteroids:  # Если астероидов нет, возвращаем None
            return None
        sx, sy = self.ship.rect.center  # Координаты центра корабля бота
        min_dist = float('inf')  # Инициализируем минимальное расстояние
        nearest = None  # Инициализируем ближайший астероид
        for ast in self.asteroid_manager.asteroids:  # Перебираем все астероиды
            d = self.dist((sx, sy), ast['pos'])  # Вычисляем расстояние до астероида
            if d < min_dist:  # Если расстояние меньше минимального
                min_dist = d  # Обновляем минимальное расстояние
                nearest = ast  # Обновляем ближайший астероид
        return nearest  # Возвращаем ближайший астероид

    @staticmethod
    def dist(p1, p2):  # Статический метод для вычисления расстояния между двумя точками
        return math.hypot(p2[0] - p1[0], p2[1] - p1[1])  # Возвращаем гипотенузу (расстояние)

class LocalPvELogic:  # Локальная логика PvE режима
    def __init__(self, ship_player, ship_bot, asteroid_manager, laser_manager):
        self.ship_player = ship_player  # Корабль игрока
        self.ship_bot = ship_bot  # Корабль бота
        self.asteroid_manager = asteroid_manager  # Менеджер астероидов
        self.laser_manager = laser_manager  # Менеджер лазеров
        self.start_time = time.time()  # Время начала игры
        self.max_time = GAME_TIME  # Максимальное время игры
        self.game_over = False  # Флаг окончания игры

    def update(self):  # Обновление логики игры
        self.asteroid_manager.update()  # Обновление астероидов
        self.laser_manager.update()  # Обновление лазеров

        for ship in [self.ship_player, self.ship_bot]:  # Проверяем столкновения кораблей с астероидами
            if ship.is_respawning:  # Пропускаем корабли в состоянии респауна
                continue
            for ast in self.asteroid_manager.asteroids[:]:
                dist_ship_ast = math.hypot(ship.rect.centerx - ast['pos'][0], ship.rect.centery - ast['pos'][1])
                if dist_ship_ast < (ship.radius + ast['radius']):  # Если столкновение
                    ship.take_damage()  # Корабль получает урон
                    ast['hp'] -= 1  # Астероид теряет здоровье
                    if ast['hp'] <= 0:  # Если здоровье астероида на нуле
                        self.asteroid_manager.asteroids.remove(ast)  # Удаляем астероид

        for laser in self.laser_manager.lasers[:]:  # Проверяем столкновения лазеров с объектами
            lx, ly = laser['pos']
            for ship in [self.ship_player, self.ship_bot]:  # Проверяем столкновения с кораблями
                if ship.is_respawning:
                    continue
                dist_laser_ship = math.hypot(lx - ship.rect.centerx, ly - ship.rect.centery)
                if dist_laser_ship < ship.radius:  # Если столкновение
                    ship.take_damage()  # Корабль получает урон
                    if laser in self.laser_manager.lasers:
                        self.laser_manager.lasers.remove(laser)  # Удаляем лазер
                    break

            for ast in self.asteroid_manager.asteroids[:]:  # Проверяем столкновения с астероидами
                dist_laser_ast = math.hypot(lx - ast['pos'][0], ly - ast['pos'][1])
                if dist_laser_ast < ast['radius']:
                    ast['hp'] -= 1
                    if ast['hp'] <= 0:
                        self.asteroid_manager.asteroids.remove(ast)
                    if laser in self.laser_manager.lasers:
                        self.laser_manager.lasers.remove(laser)
                    break

        if len(self.asteroid_manager.asteroids) < MAX_ASTEROIDS:  # Добавляем новые астероиды, если их недостаточно
            self.asteroid_manager.spawn_asteroid()

        if time.time() - self.start_time >= self.max_time:  # Проверяем, истекло ли время игры
            self.game_over = True

    def is_game_over(self):  # Проверяем, завершена ли игра
        return self.game_over

def run_pve():  # Функция запуска PvE режима
    pygame.init()  # Инициализируем Pygame
    screen = pygame.display.set_mode((WIDTH, HEIGHT))  # Создаем окно игры
    pygame.display.set_caption("PvE Mode")  # Устанавливаем заголовок окна

    clock = pygame.time.Clock()  # Создаем объект для управления временем

    player_ship = Ship(screen, 0)  # Создаем корабль игрока
    bot_ship = Ship(screen, 1)  # Создаем корабль бота

    asteroid_manager = AsteroidManager(MAX_ASTEROIDS)  # Инициализируем менеджер астероидов
    laser_manager = LaserManager()  # Инициализируем менеджер лазеров

    bot_controller = BotPlayer2(bot_ship, asteroid_manager, laser_manager)  # Создаем объект бота
    logic = LocalPvELogic(player_ship, bot_ship, asteroid_manager, laser_manager)  # Создаем объект логики

    for _ in range(4):  # Добавляем несколько астероидов в начало игры
        asteroid_manager.spawn_asteroid()

    running = True  # Флаг запуска цикла игры
    while running:
        clock.tick(FPS)  # Ограничиваем FPS
        for event in pygame.event.get():  # Обрабатываем события
            if event.type == pygame.QUIT:  # Выход из игры
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:  # Выход в меню
                    running = False
                elif event.key == pygame.K_SPACE:  # Стрельба игрока
                    can_shoot, (lx, ly) = player_ship.try_shoot()
                    if can_shoot:
                        laser_manager.shoot_laser(lx, ly, player_ship.angle, player_ship.number)

        keys = pygame.key.get_pressed()  # Получаем нажатые клавиши
        player_ship.update(keys)  # Обновляем движение игрока
        bot_controller.update(player_ship)  # Обновляем логику бота
        logic.update()  # Обновляем логику игры

        if logic.is_game_over():  # Проверяем, завершилась ли игра
            running = False

        screen.fill(BLACK)  # Очищаем экран
        asteroid_manager.draw(screen)  # Отображаем астероиды
        laser_manager.draw(screen)  # Отображаем лазеры

        player_ship.draw()  # Отображаем корабль игрока
        bot_ship.draw()  # Отображаем корабль бота

        time_left = logic.max_time - int(time.time() - logic.start_time)  # Вычисляем оставшееся время
        font = pygame.font.Font(None, 36)  # Устанавливаем шрифт
        text = font.render(f"Time left: {time_left}", True, WHITE)  # Рендерим текст времени
        screen.blit(text, (WIDTH // 2 - 50, 10))  # Отображаем текст на экране

        pygame.display.flip()  # Обновляем экран
    return  # Явное завершение функции

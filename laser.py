import math  # Модуль для математических расчетов
import pygame  # Модуль для работы с графикой и игровыми событиями
from utils import WIDTH, HEIGHT, YELLOW  # Константы: размеры экрана и цвет лазера

if WIDTH == 0 or HEIGHT == 0:  # Если размеры экрана не заданы
    screen_info = pygame.display.Info()  # Получаем информацию о текущем экране
    WIDTH, HEIGHT = screen_info.current_w, screen_info.current_h  # Устанавливаем размеры экрана


class LaserManager:  # Класс для управления лазерами
    def __init__(self):  # Инициализация менеджера лазеров
        self.lasers = []  # Список всех активных лазеров

    def shoot_laser(self, x, y, angle, owner_id):  # Метод для добавления нового лазера
        speed = 10  # Скорость движения лазера
        dx = speed * math.cos(math.radians(angle))  # Горизонтальная скорость лазера
        dy = -speed * math.sin(
            math.radians(angle))  # Вертикальная скорость лазера (отрицательная для верхней части экрана)
        laser = {
            'pos': [x, y],  # Начальная позиция лазера
            'vel': [dx, dy],  # Скорость лазера
            'owner': owner_id,  # ID владельца лазера
        }
        self.lasers.append(laser)  # Добавляем лазер в список

    def update(self):  # Метод для обновления позиций лазеров
        for laser in self.lasers[:]:  # Перебираем копию списка лазеров
            laser['pos'][0] += laser['vel'][0]  # Обновляем координату X
            laser['pos'][1] += laser['vel'][1]  # Обновляем координату Y

            if not (0 <= laser['pos'][0] <= WIDTH and 0 <= laser['pos'][
                1] <= HEIGHT):  # Проверяем, вышел ли лазер за границы экрана
                self.lasers.remove(laser)  # Удаляем лазер, если он вышел за экран

    def draw(self, screen):  # Метод для отрисовки лазеров на экране
        for laser in self.lasers:  # Перебираем все активные лазеры
            x, y = laser['pos']  # Координаты лазера
            pygame.draw.circle(screen, YELLOW, (int(x), int(y)), 3)  # Рисуем лазер в виде жёлтого круга

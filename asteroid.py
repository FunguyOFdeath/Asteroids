import random  # Модуль для работы с генерацией случайных чисел
import pygame  # Модуль для работы с графикой и событиями
from utils import WIDTH, HEIGHT, GREY  # Импортируем размеры экрана и цвет астероидов

if WIDTH == 0 or HEIGHT == 0:  # Проверяем, установлены ли размеры экрана
    screen_info = pygame.display.Info()  # Получаем информацию о текущем экране
    WIDTH, HEIGHT = screen_info.current_w, screen_info.current_h  # Устанавливаем размеры экрана в соответствии с текущими настройками

class AsteroidManager:  # Класс для управления астероидами
    def __init__(self, max_asteroids=10):  # Инициализация менеджера астероидов
        self.max_asteroids = max_asteroids  # Максимальное количество астероидов
        self.asteroids = []  # Список для хранения текущих астероидов

    def spawn_asteroid(self):  # Метод для создания нового астероида
        size = random.randint(20, 45)  # Случайный размер астероида
        speed = max(1, 3 - size // 7)  # Скорость астероида зависит от его размера
        new_ast = {
            'pos': [random.randint(0, WIDTH), random.randint(0, HEIGHT)],  # Случайное положение на экране
            'vel': [random.choice([-speed, speed]), random.choice([-speed, speed])],  # Случайное направление движения
            'radius': size,  # Радиус астероида
            'hp': 1,  # Здоровье астероида
            'color': GREY  # Цвет астероида
        }
        self.asteroids.append(new_ast)  # Добавляем новый астероид в список

    def update(self):  # Метод для обновления состояния астероидов
        for ast in self.asteroids:  # Перебираем все астероиды
            ast['pos'][0] += ast['vel'][0]  # Обновляем координату X
            ast['pos'][1] += ast['vel'][1]  # Обновляем координату Y
            ast['pos'][0] %= WIDTH  # Перемещаем астероид на противоположную сторону, если он выходит за границу по X
            ast['pos'][1] %= HEIGHT  # Перемещаем астероид на противоположную сторону, если он выходит за границу по Y

    def draw(self, screen):  # Метод для отрисовки астероидов на экране
        for ast in self.asteroids:  # Перебираем все астероиды
            x, y = ast['pos']  # Координаты астероида
            radius = ast['radius']  # Радиус астероида
            color = ast['color']  # Цвет астероида
            pygame.draw.circle(screen, color, (int(x), int(y)), radius)  # Рисуем основной круг астероида

            # Если астероид пересекает границы экрана, рисуем копии на противоположных сторонах
            if x < radius:  # Если астероид выходит за левую границу
                pygame.draw.circle(screen, color, (int(x + WIDTH), int(y)), radius)
            if (WIDTH - x) < radius:  # Если астероид выходит за правую границу
                pygame.draw.circle(screen, color, (int(x - WIDTH), int(y)), radius)
            if y < radius:  # Если астероид выходит за верхнюю границу
                pygame.draw.circle(screen, color, (int(x), int(y + HEIGHT)), radius)
            if (HEIGHT - y) < radius:  # Если астероид выходит за нижнюю границу
                pygame.draw.circle(screen, color, (int(x), int(y - HEIGHT)), radius)

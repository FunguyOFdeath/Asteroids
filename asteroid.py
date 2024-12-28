# asteroid.py
import random
import math
import pygame
from utils import WIDTH, HEIGHT, GREY

class AsteroidManager:
    """Класс-менеджер для хранения и управления всеми астероидами."""
    def __init__(self, max_asteroids=10):
        self.max_asteroids = max_asteroids
        self.asteroids = []

    def spawn_asteroid(self):
        """Создаёт и возвращает новый астероид."""
        size = random.randint(20, 45)
        speed = max(1, 3 - size // 7)
        new_ast = {
            'pos': [random.randint(0, WIDTH), random.randint(0, HEIGHT)],
            'vel': [random.choice([-speed, speed]), random.choice([-speed, speed])],
            'radius': size,
            'hp': 1,
            'color': GREY
        }
        self.asteroids.append(new_ast)

    def update(self):
        """Обновляет позиции астероидов и удаляет уничтоженные."""
        for ast in self.asteroids:
            ast['pos'][0] += ast['vel'][0]
            ast['pos'][1] += ast['vel'][1]
            ast['pos'][0] %= WIDTH
            ast['pos'][1] %= HEIGHT
        
        # Можно добавить любую дополнительную логику (разделение при попадании и т.д.)

    def draw(self, screen):
        """Рисуем астероиды, учитывая выход за края."""
        for ast in self.asteroids:
            x, y = ast['pos']
            radius = ast['radius']
            color = ast['color']
            pygame.draw.circle(screen, color, (int(x), int(y)), radius)
            
            # Если астероид пересекает границы, дорисуем "копию" с другой стороны
            if x < radius:
                pygame.draw.circle(screen, color, (int(x + WIDTH), int(y)), radius)
            if (WIDTH - x) < radius:
                pygame.draw.circle(screen, color, (int(x - WIDTH), int(y)), radius)
            if y < radius:
                pygame.draw.circle(screen, color, (int(x), int(y + HEIGHT)), radius)
            if (HEIGHT - y) < radius:
                pygame.draw.circle(screen, color, (int(x), int(y - HEIGHT)), radius)

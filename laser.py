# laser.py
import math
import pygame
from utils import WIDTH, HEIGHT, YELLOW

class LaserManager:
    """Класс-менеджер для хранения и управления всеми лазерами."""
    def __init__(self):
        self.lasers = []

    def shoot_laser(self, x, y, angle, owner_id):
        """Добавляет лазер в список."""
        speed = 10
        dx = speed * math.cos(math.radians(angle))
        dy = -speed * math.sin(math.radians(angle))
        laser = {
            'pos': [x, y],
            'vel': [dx, dy],
            'owner': owner_id,
        }
        self.lasers.append(laser)

    def update(self):
        """Обновляет позиции лазеров и удаляет вышедшие за экран."""
        for laser in self.lasers[:]:
            laser['pos'][0] += laser['vel'][0]
            laser['pos'][1] += laser['vel'][1]
            
            # Удаляем лазеры, вышедшие за границы
            if not (0 <= laser['pos'][0] <= WIDTH and 0 <= laser['pos'][1] <= HEIGHT):
                self.lasers.remove(laser)

    def draw(self, screen):
        """Отрисовка лазеров."""
        for laser in self.lasers:
            x, y = laser['pos']
            pygame.draw.circle(screen, YELLOW, (int(x), int(y)), 3)

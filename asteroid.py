import random
import pygame
import math
from utils import lasers, asteroids, WIDTH, HEIGHT, GREY


def spawn_asteroid():
    size = random.randint(20, 45)
    speed = max(1, 5 - size // 10)
    random_number = random.choice(range(1, 64))
    random_number -= 32
    asteroid = {
        'pos': [random.randint(0, WIDTH), random.randint(0, HEIGHT)],
        'vel': [random.choice([-speed, speed]), random.choice([-speed, speed])],
        'radius': size,
        'hp': 1,
        # 'hp': max(1, size // 20)
        'color': [GREY[0] - random_number, GREY[1] - random_number, GREY[2] - random_number]
    }
    asteroids.append(asteroid)


def update_asteroids():
    for asteroid in asteroids:
        asteroid['pos'][0] += asteroid['vel'][0]
        asteroid['pos'][1] += asteroid['vel'][1]
        asteroid['pos'][0] %= WIDTH
        asteroid['pos'][1] %= HEIGHT

        # Проверка столкновений с лазерами
        for laser in lasers:
            dist = math.hypot(laser['pos'][0] - asteroid['pos'][0], laser['pos'][1] - asteroid['pos'][1])
            if dist < asteroid['radius']:
                asteroid['hp'] -= 1  # Уменьшение ХП астероида
                if asteroid['hp'] <= 0:
                    asteroids.remove(asteroid)  # Удаление астероида, если ХП <= 0

                lasers.remove(laser)  # Удаление лазера после попадания
                break  # Астероид может поразить только один лазер


def draw_asteroids(screen):
    for asteroid in asteroids:

        radius = asteroid['radius']
        pos = asteroid['pos']
        color = asteroid['color']

        pygame.draw.circle(screen, color, pos, radius)  # реальное положение

        # Дорисовка при выходе за экран
        if pos[0] < radius:  # Справа
            pygame.draw.circle(screen, color, (pos[0] + WIDTH, pos[1]), radius)
        if WIDTH - pos[0] < radius:  # Слева
            pygame.draw.circle(screen, color, (pos[0] - WIDTH, pos[1]), radius)
        if pos[1] < radius:  # Справа
            pygame.draw.circle(screen, color, (pos[0], pos[1] + HEIGHT), radius)
        if HEIGHT - pos[1] < radius:  # Слева
            pygame.draw.circle(screen, color, (pos[0], pos[1] - HEIGHT), radius)

        # Отображение ХП астероида
        # hp_text = pygame.font.Font(None, 24).render(str(asteroid['hp']), True, WHITE)
        # screen.blit(hp_text, (asteroid['pos'][0] - 10, asteroid['pos'][1] - 10))

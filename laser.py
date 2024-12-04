import pygame
import math
from utils import lasers, points, WIDTH, HEIGHT, WHITE


def check_collision_asteroid(ship, asteroids, current_time):
    # Проверка на стрельбу
    if not ship.is_respawning:
        if pygame.key.get_pressed()[ship.keysPlayer[4]] and current_time - ship.last_laser_time > ship.laser_cooldown:
            ship.shoot_laser()

    # Дальшге идёт расчёт домага. Если у корабля пока неуязвимость - выходим
    if current_time < ship.invincible_until:
        return

    # Проверка столкновений с астероидами
    for asteroid in asteroids:
        dist = math.hypot(ship.rect.centerx - asteroid['pos'][0], ship.rect.centery - asteroid['pos'][1])
        if dist < asteroid['radius'] + ship.radius:
            ship.take_damage()

    for laser in lasers:
        if laser['num'] == ship.number:
            continue
        dist = math.hypot(laser['pos'][0] - ship.rect.centerx, laser['pos'][1] - ship.rect.centery)
        if dist < ship.radius:
            lasers.remove(laser)  # Удаление лазера после попадания
            ship.take_damage()


def check_collision_ships(ship1, ship2, current_time):
    if current_time > ship1.invincible_until and current_time > ship2.invincible_until:
        dist = math.hypot(ship1.rect.centerx - ship2.rect.centerx, ship1.rect.centery - ship2.rect.centery)
        if dist < ship1.radius + ship2.radius:
            ship1.take_damage()
            ship2.take_damage()


def update_lasers():
    for laser in lasers[:]:
        laser['pos'][0] += laser['vel'][0]
        laser['pos'][1] += laser['vel'][1]
        if not (0 <= laser['pos'][0] <= WIDTH and 0 <= laser['pos'][1] <= HEIGHT):
            lasers.remove(laser)


def shoot_laser(x, y, angle, number):
    speed = 10
    dx = speed * math.cos(math.radians(angle))
    dy = -speed * math.sin(math.radians(angle))
    lasers.append({'pos': [x, y], 'vel': [dx, dy], 'num': number})


def draw_lasers(screen):
    for laser in lasers:
        pygame.draw.circle(screen, (255, 255, 0), (int(laser['pos'][0]), int(laser['pos'][1])), 3)


def draw_hud(screen, ship1, ship2, current_time, end_time):
    # points
    point1_text = pygame.font.Font(None, 36).render(f"Игрок{ship1.number + 1} - {points[ship1.number]} оч", True, WHITE)
    text_rect = point1_text.get_rect(center=(100, 30))
    screen.blit(point1_text, text_rect)

    point2_text = pygame.font.Font(None, 36).render(f"Игрок{ship2.number + 1} - {points[ship2.number]} оч", True, WHITE)
    text_rect = point2_text.get_rect(center=(WIDTH - 100, 30))
    screen.blit(point2_text, text_rect)

    # time
    end_text = pygame.font.Font(None, 48).render(f"{round(end_time - current_time)}", True, WHITE)
    text_rect = end_text.get_rect(center=(WIDTH // 2, 40))
    screen.blit(end_text, text_rect)


def draw_end(screen, ship1, ship2):
    point1_text = pygame.font.Font(None, 72).render(f"Игрок{ship1.number + 1} - {points[ship1.number]} оч", True, WHITE)
    text_rect = point1_text.get_rect(center=(WIDTH // 2, HEIGHT * 0.45))
    screen.blit(point1_text, text_rect)

    point2_text = pygame.font.Font(None, 72).render(f"Игрок{ship2.number + 1} - {points[ship2.number]} оч", True, WHITE)
    text_rect = point2_text.get_rect(center=(WIDTH // 2, HEIGHT * 0.55))
    screen.blit(point2_text, text_rect)

import pygame
import time
from ship import Ship
from asteroid import spawn_asteroid, update_asteroids, draw_asteroids, asteroids
from laser import update_lasers, draw_lasers, draw_hud, draw_end, check_collision_ships, check_collision_asteroid
from utils import WIDTH, HEIGHT, BLACK, FPS, MAX_ASTEROIDS, clock, game_time


pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Asteroids")

# Создание корабля
ship1 = Ship(screen, 0)
ship2 = Ship(screen, 1)

end_time = time.time() + game_time

running = True
while running:
    # time
    current_time = time.time()
    clock.tick(FPS)
    if end_time < current_time:
        running = False

    # exit events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            # else:
            #     print(event.key)
    # keys
    keys = pygame.key.get_pressed()
    ship1.update(keys)
    ship2.update(keys)

    # proc
    update_lasers()
    if len(asteroids) < MAX_ASTEROIDS:
        spawn_asteroid()
    update_asteroids()
    check_collision_asteroid(ship1, asteroids, current_time)
    check_collision_asteroid(ship2, asteroids, current_time)
    check_collision_ships(ship1, ship2, current_time)

    # draw
    screen.fill(BLACK)
    draw_asteroids(screen)
    ship1.draw()
    ship2.draw()
    draw_lasers(screen)
    draw_hud(screen, ship1, ship2, current_time, end_time)

    pygame.display.flip()
pass  # while game


screen.fill(BLACK)
draw_end(screen, ship1, ship2)
pygame.display.flip()

running = True
while running:
    # exit events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
pass  # while end

pygame.quit()

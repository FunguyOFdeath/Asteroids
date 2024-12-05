import pygame

WIDTH = 800
HEIGHT = 600

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (101, 101, 101)
RED = (235, 15, 15)
ORANGE = (237, 118, 14)
BLUE = (15, 15, 235)
YELLOW = (255, 255, 0)

FPS = 60

clock = pygame.time.Clock()

# Глобальные переменные
lasers = []
asteroids = []
points = [0, 0]
MAX_ASTEROIDS = 10
game_time = 30

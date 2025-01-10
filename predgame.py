import pygame
import sys

pygame.init()

screen_info = pygame.display.Info()
WINDOW_WIDTH, WINDOW_HEIGHT = screen_info.current_w, screen_info.current_h
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Predgame Menu")

path = ""
bg_image = pygame.image.load(path + "PREDGAME.png")
ip_image = pygame.image.load(path + "IP.png")
nick_image = pygame.image.load(path + "NICK.png")
pole1_image = pygame.image.load(path + "POLE_1.png")
pole2_image = pygame.image.load(path + "POLE_2.png")
next_image = pygame.image.load(path + "NEXT.png")

WIDTH_SCALE, HEIGHT_SCALE = 0.2, 0.2
BUTTON_WIDTH, BUTTON_HEIGHT = WINDOW_WIDTH * WIDTH_SCALE, WINDOW_HEIGHT * HEIGHT_SCALE
FIELD_WIDTH, FIELD_HEIGHT = WINDOW_WIDTH * WIDTH_SCALE * 1.5, WINDOW_HEIGHT * HEIGHT_SCALE * 0.8

ip_image = pygame.transform.scale(ip_image, (int(BUTTON_WIDTH), int(BUTTON_HEIGHT)))
nick_image = pygame.transform.scale(nick_image, (int(BUTTON_WIDTH), int(BUTTON_HEIGHT)))
pole1_image = pygame.transform.scale(pole1_image, (int(FIELD_WIDTH), int(FIELD_HEIGHT)))
pole2_image = pygame.transform.scale(pole2_image, (int(FIELD_WIDTH), int(FIELD_HEIGHT)))
next_image = pygame.transform.scale(next_image, (int(BUTTON_WIDTH), int(BUTTON_HEIGHT)))

IP_RECT = ip_image.get_rect(center=(WINDOW_WIDTH // 3, WINDOW_HEIGHT // 3))
NICK_RECT = nick_image.get_rect(center=(2 * WINDOW_WIDTH // 3, WINDOW_HEIGHT // 3))
POLE1_RECT = pole1_image.get_rect(center=(WINDOW_WIDTH // 3, WINDOW_HEIGHT // 2))
POLE2_RECT = pole2_image.get_rect(center=(2 * WINDOW_WIDTH // 3, WINDOW_HEIGHT // 2))
NEXT_RECT = next_image.get_rect(center=(WINDOW_WIDTH // 2, 2 * WINDOW_HEIGHT // 3))

ip_input = ""
nick_input = ""
font = pygame.font.Font(None, int(WINDOW_HEIGHT * 0.07))
active_field = None
next_active = False

running = True
while running:
    screen.blit(pygame.transform.scale(bg_image, (WINDOW_WIDTH, WINDOW_HEIGHT)), (0, 0))
    screen.blit(ip_image, IP_RECT.topleft)
    screen.blit(nick_image, NICK_RECT.topleft)
    screen.blit(pole1_image, POLE1_RECT.topleft)
    screen.blit(pole2_image, POLE2_RECT.topleft)

    #Шрифт
    ip_surface = font.render(ip_input, True, (255, 255, 255))
    nick_surface = font.render(nick_input, True, (255, 255, 255))
    #get rect
    ip_surface_rect = ip_surface.get_rect()
    nick_surface_rect = nick_surface.get_rect()
    #set center
    ip_surface_rect.center = POLE1_RECT.center
    nick_surface_rect.center = POLE2_RECT.center
    #draw
    screen.blit(ip_surface, ip_surface_rect)
    screen.blit(nick_surface, nick_surface_rect)

    if ip_input.strip() and nick_input.strip():
        next_active = True
    screen.blit(next_image, NEXT_RECT.topleft if next_active else (NEXT_RECT.x, NEXT_RECT.y))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if active_field == "IP":
                if event.key == pygame.K_BACKSPACE:
                    ip_input = ip_input[:-1]
                else:
                    ip_input += event.unicode
            elif active_field == "NICK":
                if event.key == pygame.K_BACKSPACE:
                    nick_input = nick_input[:-1]
                else:
                    nick_input += event.unicode
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if POLE1_RECT.collidepoint(event.pos):
                active_field = "IP"
            elif POLE2_RECT.collidepoint(event.pos):
                active_field = "NICK"
            elif NEXT_RECT.collidepoint(event.pos) and next_active:
                print(f"Начало игры с IP: {ip_input} и Nick: {nick_input}")
                running = False

    pygame.display.flip()

pygame.quit()
sys.exit()

import pygame
import sys
import subprocess

pygame.init()

screen_info = pygame.display.Info()
WINDOW_WIDTH, WINDOW_HEIGHT = screen_info.current_w, screen_info.current_h
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Game Menu")

path = ""
bg_image = pygame.image.load(path + "MENU.png")
buttoms = {
    "PVP": {'img': pygame.image.load(path + "PVP.png")},
    "PVE": {'img': pygame.image.load(path + "PVE.png")},
    "LEADER": {'img': pygame.image.load(path + "LEADER.png")},
    "EXIT": {'img': pygame.image.load(path + "EXIT.png")}
}
count_buttoms = len(buttoms)

WIDTH_SCALE, HEIGHT_SCALE = 0.7, 0.7
BUTTON_WIDTH, BUTTON_HEIGHT = (WINDOW_WIDTH / len(buttoms)) * WIDTH_SCALE, WINDOW_HEIGHT * HEIGHT_SCALE
for key in buttoms:
    buttoms[key]['img'] = pygame.transform.scale(buttoms[key]['img'], (int(BUTTON_WIDTH), int(BUTTON_HEIGHT)))


for i, key in enumerate(buttoms):
    buttoms[key]['rect'] = pygame.Rect(i * WINDOW_WIDTH / len(buttoms) + WINDOW_WIDTH / len(buttoms) * (1.0 - WIDTH_SCALE) / 2,
                                       0 + WINDOW_HEIGHT * (1.0 - HEIGHT_SCALE) / 2,
                                       BUTTON_WIDTH, BUTTON_HEIGHT)


running = True
while running:
    screen.blit(pygame.transform.scale(bg_image, (WINDOW_WIDTH, WINDOW_HEIGHT)), (0, 0))
    for key, button in buttoms.items():
        screen.blit(button['img'], button['rect'].topleft)


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:  # Нажатие клавиши ESC
                running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Левая кнопка мыши
            mouse_pos = pygame.mouse.get_pos()
            for key, button in buttoms.items():
                if button['rect'].collidepoint(mouse_pos):
                    print(f"Клик по кнопке {key}")
                    if key == "PVP":
                        subprocess.run(["python", "predgame.py"])  # Используем subprocess для запуска
                        sys.exit()
                    if key == "EXIT":
                        running = False

    pygame.display.flip()

pygame.quit()
sys.exit()

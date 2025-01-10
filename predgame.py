import pygame  # Импортируем модуль Pygame для работы с графикой и событиями
import sys  # Импортируем модуль sys для управления завершением программы

pygame.init()  # Инициализируем все модули Pygame

screen_info = pygame.display.Info()  # Получаем информацию о текущем экране
WINDOW_WIDTH, WINDOW_HEIGHT = screen_info.current_w, screen_info.current_h  # Устанавливаем размеры окна равными размерам экрана
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN)  # Создаем окно в полноэкранном режиме
pygame.display.set_caption("Predgame Menu")  # Устанавливаем заголовок окна

path = ""  # Указываем путь к изображениям, оставляем пустым, если файлы находятся рядом
bg_image = pygame.image.load(path + "PREDGAME.png")  # Загружаем изображение фона меню
ip_image = pygame.image.load(path + "IP.png")  # Загружаем изображение для кнопки ввода IP
nick_image = pygame.image.load(path + "NICK.png")  # Загружаем изображение для кнопки ввода имени игрока
pole1_image = pygame.image.load(path + "POLE_1.png")  # Загружаем изображение для текстового поля IP
pole2_image = pygame.image.load(path + "POLE_2.png")  # Загружаем изображение для текстового поля имени
next_image = pygame.image.load(path + "NEXT.png")  # Загружаем изображение для кнопки "Далее"

WIDTH_SCALE, HEIGHT_SCALE = 0.2, 0.2  # Устанавливаем масштабирование для элементов интерфейса
BUTTON_WIDTH, BUTTON_HEIGHT = WINDOW_WIDTH * WIDTH_SCALE, WINDOW_HEIGHT * HEIGHT_SCALE  # Вычисляем размеры кнопок
FIELD_WIDTH, FIELD_HEIGHT = WINDOW_WIDTH * WIDTH_SCALE * 1.5, WINDOW_HEIGHT * HEIGHT_SCALE * 0.8  # Вычисляем размеры текстовых полей

ip_image = pygame.transform.scale(ip_image, (int(BUTTON_WIDTH), int(BUTTON_HEIGHT)))  # Масштабируем изображение для кнопки IP
nick_image = pygame.transform.scale(nick_image, (int(BUTTON_WIDTH), int(BUTTON_HEIGHT)))  # Масштабируем изображение для кнопки имени
pole1_image = pygame.transform.scale(pole1_image, (int(FIELD_WIDTH), int(FIELD_HEIGHT)))  # Масштабируем текстовое поле IP
pole2_image = pygame.transform.scale(pole2_image, (int(FIELD_WIDTH), int(FIELD_HEIGHT)))  # Масштабируем текстовое поле имени
next_image = pygame.transform.scale(next_image, (int(BUTTON_WIDTH), int(BUTTON_HEIGHT)))  # Масштабируем кнопку "Далее"

IP_RECT = ip_image.get_rect(center=(WINDOW_WIDTH // 3, WINDOW_HEIGHT // 3))  # Определяем позицию кнопки IP
NICK_RECT = nick_image.get_rect(center=(2 * WINDOW_WIDTH // 3, WINDOW_HEIGHT // 3))  # Определяем позицию кнопки имени
POLE1_RECT = pole1_image.get_rect(center=(WINDOW_WIDTH // 3, WINDOW_HEIGHT // 2))  # Определяем позицию текстового поля IP
POLE2_RECT = pole2_image.get_rect(center=(2 * WINDOW_WIDTH // 3, WINDOW_HEIGHT // 2))  # Определяем позицию текстового поля имени
NEXT_RECT = next_image.get_rect(center=(WINDOW_WIDTH // 2, 2 * WINDOW_HEIGHT // 3))  # Определяем позицию кнопки "Далее"

ip_input = ""  # Переменная для хранения введенного IP
nick_input = ""  # Переменная для хранения введенного имени игрока
font = pygame.font.Font(None, int(WINDOW_HEIGHT * 0.07))  # Устанавливаем шрифт и его размер в зависимости от высоты экрана
active_field = None  # Указывает, какое текстовое поле активно для ввода
next_active = False  # Флаг для активации кнопки "Далее"

running = True  # Флаг для работы игрового цикла
while running:  # Основной цикл программы
    screen.blit(pygame.transform.scale(bg_image, (WINDOW_WIDTH, WINDOW_HEIGHT)), (0, 0))  # Отображаем фон на экране
    screen.blit(ip_image, IP_RECT.topleft)  # Отображаем кнопку IP
    screen.blit(nick_image, NICK_RECT.topleft)  # Отображаем кнопку имени
    screen.blit(pole1_image, POLE1_RECT.topleft)  # Отображаем текстовое поле IP
    screen.blit(pole2_image, POLE2_RECT.topleft)  # Отображаем текстовое поле имени

    ip_surface = font.render(ip_input, True, (255, 255, 255))  # Рендерим текст IP в текстовое поле
    nick_surface = font.render(nick_input, True, (255, 255, 255))  # Рендерим текст имени в текстовое поле
    ip_surface_rect = ip_surface.get_rect()  # Получаем размеры рендера текста IP
    nick_surface_rect = nick_surface.get_rect()  # Получаем размеры рендера текста имени
    ip_surface_rect.center = POLE1_RECT.center  # Центрируем текст IP в текстовом поле
    nick_surface_rect.center = POLE2_RECT.center  # Центрируем текст имени в текстовом поле
    screen.blit(ip_surface, ip_surface_rect)  # Отображаем текст IP на экране
    screen.blit(nick_surface, nick_surface_rect)  # Отображаем текст имени на экране

    if ip_input.strip() and nick_input.strip():  # Проверяем, что оба текстовых поля не пустые
        next_active = True  # Активируем кнопку "Далее"
    screen.blit(next_image, NEXT_RECT.topleft if next_active else (NEXT_RECT.x, NEXT_RECT.y))  # Отображаем кнопку "Далее"

    for event in pygame.event.get():  # Обрабатываем события
        if event.type == pygame.QUIT:  # Если пользователь закрыл окно
            running = False  # Завершаем цикл
        elif event.type == pygame.KEYDOWN:  # Если была нажата клавиша
            if event.key == pygame.K_ESCAPE:  # Проверяем, нажата ли клавиша "ESC"
                running = False  # Завершаем цикл
            if active_field == "IP":  # Если активно поле IP
                if event.key == pygame.K_BACKSPACE:  # Если нажата клавиша Backspace
                    ip_input = ip_input[:-1]  # Удаляем последний символ
                else:
                    ip_input += event.unicode  # Добавляем символ в строку ввода IP
            elif active_field == "NICK":  # Если активно поле имени
                if event.key == pygame.K_BACKSPACE:  # Если нажата клавиша Backspace
                    nick_input = nick_input[:-1]  # Удаляем последний символ
                else:
                    nick_input += event.unicode  # Добавляем символ в строку ввода имени
        elif event.type == pygame.MOUSEBUTTONDOWN:  # Если была нажата кнопка мыши
            if POLE1_RECT.collidepoint(event.pos):  # Проверяем, нажато ли на поле IP
                active_field = "IP"  # Устанавливаем поле IP активным
            elif POLE2_RECT.collidepoint(event.pos):  # Проверяем, нажато ли на поле имени
                active_field = "NICK"  # Устанавливаем поле имени активным
            elif NEXT_RECT.collidepoint(event.pos) and next_active:  # Проверяем, нажата ли кнопка "Далее"
                print(f"Начало игры с IP: {ip_input} и Nick: {nick_input}")  # Выводим информацию о вводе в консоль
                running = False  # Завершаем цикл

    pygame.display.flip()  # Обновляем содержимое экрана

pygame.quit()  # Завершаем работу Pygame
sys.exit()  # Полностью завершаем программу

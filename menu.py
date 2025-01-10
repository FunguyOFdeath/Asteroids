import pygame  # Импортируем библиотеку для создания игр и графического интерфейса
import sys  # Импортируем модуль для управления параметрами и завершения программы
import subprocess  # Импортируем модуль для запуска внешних процессов

pygame.init()  # Инициализируем все модули Pygame

screen_info = pygame.display.Info()  # Получаем информацию о текущем экране
WINDOW_WIDTH, WINDOW_HEIGHT = screen_info.current_w, screen_info.current_h  # Устанавливаем ширину и высоту окна в соответствии с размерами экрана
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN)  # Создаем окно приложения в полноэкранном режиме
pygame.display.set_caption("Game Menu")  # Устанавливаем заголовок окна

path = ""  # Путь к файлам ресурсов, оставляем пустым, если они находятся рядом с кодом
bg_image = pygame.image.load(path + "MENU.png")  # Загружаем изображение для фона меню

buttoms = {  # Определяем кнопки и их изображения
    "PVP": {'img': pygame.image.load(path + "PVP.png")},  # Кнопка "PvP"
    "PVE": {'img': pygame.image.load(path + "PVE.png")},  # Кнопка "PvE"
    "LEADER": {'img': pygame.image.load(path + "LEADER.png")},  # Кнопка "Лидеры"
    "EXIT": {'img': pygame.image.load(path + "EXIT.png")}  # Кнопка "Выход"
}

count_buttoms = len(buttoms)  # Подсчитываем количество кнопок

WIDTH_SCALE, HEIGHT_SCALE = 0.7, 0.7  # Масштабирование размеров кнопок относительно их исходного размера
BUTTON_WIDTH = (WINDOW_WIDTH / len(buttoms)) * WIDTH_SCALE  # Вычисляем ширину кнопок
BUTTON_HEIGHT = WINDOW_HEIGHT * HEIGHT_SCALE  # Вычисляем высоту кнопок

for key in buttoms:  # Применяем масштабирование к каждой кнопке
    buttoms[key]['img'] = pygame.transform.scale(
        buttoms[key]['img'],  # Изображение кнопки
        (int(BUTTON_WIDTH), int(BUTTON_HEIGHT))  # Новый размер кнопки
    )

for i, key in enumerate(buttoms):  # Создаем прямоугольники для отслеживания позиций кнопок
    buttoms[key]['rect'] = pygame.Rect(
        i * WINDOW_WIDTH / count_buttoms + (WINDOW_WIDTH / count_buttoms) * (1.0 - WIDTH_SCALE) / 2,  # Горизонтальная позиция
        WINDOW_HEIGHT * (1.0 - HEIGHT_SCALE) / 2,  # Вертикальная позиция
        BUTTON_WIDTH,  # Ширина кнопки
        BUTTON_HEIGHT  # Высота кнопки
    )

running = True  # Флаг для управления циклом игры
while running:  # Главный цикл программы
    screen.blit(pygame.transform.scale(bg_image, (WINDOW_WIDTH, WINDOW_HEIGHT)), (0, 0))  # Отрисовываем фон

    for key, button in buttoms.items():  # Отображаем все кнопки на экране
        screen.blit(button['img'], button['rect'].topleft)

    for event in pygame.event.get():  # Обрабатываем события
        if event.type == pygame.QUIT:  # Если пользователь закрыл окно
            running = False  # Завершаем цикл

        elif event.type == pygame.KEYDOWN:  # Если нажата клавиша
            if event.key == pygame.K_ESCAPE:  # Проверяем, нажата ли клавиша "ESC"
                running = False  # Завершаем цикл

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Проверяем, была ли нажата левая кнопка мыши
            mouse_pos = pygame.mouse.get_pos()  # Получаем позицию курсора
            for key, button in buttoms.items():  # Проверяем, попал ли курсор на одну из кнопок
                if button['rect'].collidepoint(mouse_pos):  # Если курсор на кнопке
                    print(f"Клик по кнопке {key}")  # Выводим название кнопки в консоль

                    if key == "PVP":  # Если нажата кнопка "PvP"
                        subprocess.run(["python", "predgame.py"])  # Запускаем внешний процесс с предыгровым меню
                        sys.exit()  # Завершаем приложение

                    elif key == "PVE":  # Если нажата кнопка "PvE"
                        try:
                            import pve  # Импортируем модуль с логикой режима PvE

                            pve.run_pve()  # Запускаем режим "Игрок против бота"
                        except ImportError:  # Если модуль не найден
                            print("Модуль pve не найден! Убедитесь, что pve.py лежит рядом.")  # Выводим ошибку

                    elif key == "LEADER":  # Если нажата кнопка "Лидеры"
                        print("Здесь можно было бы отобразить таблицу лидеров.")  # Выводим сообщение-заглушку

                    elif key == "EXIT":  # Если нажата кнопка "Выход"
                        running = False  # Завершаем цикл

    pygame.display.flip()  # Обновляем содержимое экрана

pygame.quit()  # Завершаем работу Pygame
sys.exit()  # Полностью выходим из программы

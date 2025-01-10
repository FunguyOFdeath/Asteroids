import pygame  # Библиотека для работы с графикой и игровыми событиями
import math  # Библиотека для математических расчетов
import time  # Библиотека для работы с временными интервалами
from utils import WIDTH, HEIGHT, ORANGE, BLUE, WHITE, RED  # Импорт констант из утилит

if WIDTH == 0 or HEIGHT == 0:  # Если размеры экрана не заданы
    screen_info = pygame.display.Info()  # Получаем информацию о текущем экране
    WIDTH, HEIGHT = screen_info.current_w, screen_info.current_h  # Устанавливаем размеры экрана


class Ship:  # Класс для управления кораблем игрока
    def __init__(self, screen, number):  # Инициализация корабля
        self.screen = screen  # Экран для отрисовки корабля
        self.number = number  # Номер корабля (идентификатор)

        self.angle = 0  # Начальный угол поворота корабля
        self.speed = 5  # Скорость движения корабля
        self.radius = 20  # Радиус корабля

        self.start_hp = 3  # Начальное количество здоровья
        self.hp = self.start_hp  # Текущее здоровье
        self.start_shots = 10  # Начальное количество боезапаса
        self.shots = self.start_shots  # Текущий боезапас
        self.is_reloading = False  # Флаг состояния перезарядки
        self.reload_time = 1.5  # Время перезарядки
        self.reload_start_time = 0  # Время начала перезарядки
        self.laser_cooldown = 0.2  # Задержка между выстрелами
        self.last_laser_time = 0  # Время последнего выстрела

        self.is_respawning = False  # Флаг состояния респауна
        self.respawn_start_time = 0  # Время начала респауна
        self.invincible_time = 0.6  # Время неуязвимости после респауна
        self.invincible_until = time.time() + self.invincible_time  # Конец времени неуязвимости

        if number == 0:  # Настройки для первого игрока
            self.keys = {
                'left': pygame.K_a,
                'right': pygame.K_d,
                'up': pygame.K_w,
                'down': pygame.K_s,
                'shoot': pygame.K_e,
            }
            self.start_pos = (WIDTH * 0.2, HEIGHT * 0.2)  # Начальная позиция
            self.start_angle = 0  # Начальный угол
            self.color = ORANGE  # Цвет корабля
        else:  # Настройки для второго игрока
            self.keys = {
                'left': pygame.K_LEFT,
                'right': pygame.K_RIGHT,
                'up': pygame.K_UP,
                'down': pygame.K_DOWN,
                'shoot': pygame.K_RCTRL,
            }
            self.start_pos = (WIDTH * 0.8, HEIGHT * 0.8)  # Начальная позиция
            self.start_angle = 180  # Начальный угол
            self.color = BLUE  # Цвет корабля

        self.image = pygame.Surface((50, 40), pygame.SRCALPHA)  # Поверхность для изображения корабля
        pygame.draw.polygon(self.image, self.color, [(0, 40), (25, 0), (50, 40)])  # Рисуем треугольник для корпуса
        pygame.draw.circle(self.image, RED, (25, 8), 4)  # Рисуем круг для носа корабля
        pygame.draw.line(self.image, RED, (10, 30), (40, 30), width=4)  # Линия на корпусе

        self.rect = self.image.get_rect(center=self.start_pos)  # Определяем прямоугольник для позиции корабля
        self.angle = self.start_angle  # Устанавливаем начальный угол

    def set_hp(self, hp):  # Метод для установки здоровья
        self.hp = hp  # Устанавливаем новое значение здоровья

    def reset(self):  # Метод для сброса состояния корабля
        self.hp = self.start_hp  # Восстанавливаем здоровье
        self.shots = self.start_shots  # Восстанавливаем боезапас
        self.is_reloading = False  # Сбрасываем флаг перезарядки
        self.is_respawning = False  # Сбрасываем флаг респауна
        self.angle = self.start_angle  # Устанавливаем начальный угол
        self.rect.center = self.start_pos  # Возвращаем корабль в начальную позицию
        self.invincible_until = time.time() + self.invincible_time  # Обновляем время неуязвимости

    def take_damage(self):  # Метод для нанесения урона
        current_time = time.time()  # Текущее время
        if self.is_respawning or current_time < self.invincible_until:  # Проверяем неуязвимость
            return  # Урон не наносится
        self.hp -= 1  # Уменьшаем здоровье
        self.invincible_until = current_time + self.invincible_time  # Обновляем время неуязвимости
        if self.hp <= 0:  # Если здоровье закончилось
            self.is_respawning = True  # Активируем респаун
            self.respawn_start_time = current_time  # Запоминаем время начала респауна

    def update(self, keys):  # Метод для обновления движения корабля
        current_time = time.time()  # Текущее время
        if self.is_respawning:  # Проверяем состояние респауна
            elapsed = current_time - self.respawn_start_time  # Время с начала респауна
            if elapsed > 2:  # Если респаун завершен
                self.reset()  # Сбрасываем состояние корабля
            return  # Прекращаем обновление

        if keys[self.keys['left']]:  # Поворот влево
            self.angle += 5
        if keys[self.keys['right']]:  # Поворот вправо
            self.angle -= 5

        dx = int(self.speed * math.cos(math.radians(self.angle)))  # Смещение по X
        dy = int(self.speed * math.sin(math.radians(self.angle)))  # Смещение по Y
        if keys[self.keys['up']]:  # Движение вперёд
            self.rect.x += dx
            self.rect.y -= dy
        if keys[self.keys['down']]:  # Движение назад
            self.rect.x -= dx
            self.rect.y += dy

        self.rect.x %= WIDTH  # Перемещение по горизонтали с учётом границ экрана
        self.rect.y %= HEIGHT  # Перемещение по вертикали с учётом границ экрана

        if self.is_reloading:  # Проверка состояния перезарядки
            elapsed = current_time - self.reload_start_time  # Время с начала перезарядки
            if elapsed >= self.reload_time:  # Если перезарядка завершена
                self.is_reloading = False  # Сбрасываем флаг перезарядки
                self.shots = self.start_shots  # Восстанавливаем боезапас

    def try_shoot(self):  # Метод для проверки возможности выстрела
        current_time = time.time()  # Текущее время
        if (self.shots > 0 and not self.is_reloading and (
                current_time - self.last_laser_time) >= self.laser_cooldown and not self.is_respawning):  # Проверяем возможность стрельбы
            self.shots -= 1  # Уменьшаем количество боезапаса
            self.last_laser_time = current_time  # Обновляем время последнего выстрела
            if self.shots <= 0 and not self.is_reloading:  # Если боезапас закончился
                self.is_reloading = True  # Активируем перезарядку
                self.reload_start_time = current_time  # Запоминаем время начала перезарядки
            tip_x = self.rect.centerx + self.radius * math.cos(math.radians(self.angle))  # Координата X носа корабля
            tip_y = self.rect.centery - self.radius * math.sin(math.radians(self.angle))  # Координата Y носа корабля
            return True, (tip_x, tip_y)  # Возвращаем возможность стрельбы и координаты выстрела
        return False, (0, 0)  # Если стрельба невозможна

    def draw(self):  # Метод для отрисовки корабля
        if self.is_respawning:  # Если корабль находится в состоянии респауна
            dt = time.time() - self.respawn_start_time  # Время с начала респауна
            death_text = pygame.font.Font(None, 36).render(f"Player {self.number + 1} is respawning", True,
                                                           RED)  # Текст респауна
            self.screen.blit(death_text,
                             (WIDTH // 2 - 100, HEIGHT // 2 + 40 * self.number))  # Отображаем текст респауна
            return  # Завершаем отрисовку
        if self.is_reloading:  # Если идет перезарядка
            font = pygame.font.Font(None, 20)  # Устанавливаем шрифт
            text_reload = font.render("Reloading...", True, RED)  # Текст перезарядки
            self.screen.blit(text_reload,
                             (self.rect.centerx - 40, self.rect.centery + 60))  # Отображаем текст перезарядки
        current_time = time.time()  # Текущее время
        is_reloading = (current_time < self.invincible_until)  # Проверяем состояние неуязвимости
        if is_reloading and int(current_time * 10) % 2 == 0:  # Если неуязвимость активна и кадр "мигает"
            return  # Пропускаем кадр для эффекта мигания
        rotated_image = pygame.transform.rotate(self.image, self.angle - 90)  # Поворачиваем изображение корабля
        new_rect = rotated_image.get_rect(center=self.rect.center)  # Центрируем изображение после поворота
        self.screen.blit(rotated_image, new_rect.topleft)  # Отображаем изображение корабля
        font = pygame.font.Font(None, 20)  # Устанавливаем шрифт для отображения текста
        text_hp = font.render(f"HP: {self.hp}", True, WHITE)  # Текст здоровья
        text_shots = font.render(f"Shots: {self.shots}", True, WHITE)  # Текст боезапаса
        self.screen.blit(text_hp, (self.rect.centerx - 15, self.rect.centery + 25))  # Отображаем текст здоровья
        self.screen.blit(text_shots, (self.rect.centerx - 20, self.rect.centery + 45))  # Отображаем текст боезапаса

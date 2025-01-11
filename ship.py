# ship.py
import pygame
import math
import time
from utils import WIDTH, HEIGHT, ORANGE, BLUE, WHITE, RED


class Ship:
    """Класс корабля игрока: хранит логику движения, стрельбы и респауна."""

    def __init__(self, screen, number):
        self.screen = screen
        self.number = number

        # Параметры корабля
        self.angle = 0
        self.speed = 5
        self.radius = 20

        # Параметры здоровья и стрельбы
        self.start_hp = 3
        self.hp = self.start_hp
        self.start_shots = 10
        self.shots = self.start_shots
        self.is_reloading = False
        self.reload_time = 1.5
        self.reload_start_time = 0
        self.laser_cooldown = 0.2
        self.last_laser_time = 0

        # Респаун и неуязвимость
        self.is_respawning = False
        self.respawn_start_time = 0
        self.invincible_time = 0.6
        self.invincible_until = time.time() + self.invincible_time

        # Клавиши управления
        if number == 0:
            self.keys = {
                'left': pygame.K_a,
                'right': pygame.K_d,
                'up': pygame.K_w,
                'down': pygame.K_s,
                'shoot': pygame.K_e,
            }
            self.start_pos = (WIDTH * 0.2, HEIGHT * 0.2)
            self.start_angle = 0
            self.color = ORANGE
        else:
            self.keys = {
                'left': pygame.K_LEFT,
                'right': pygame.K_RIGHT,
                'up': pygame.K_UP,
                'down': pygame.K_DOWN,
                'shoot': pygame.K_RCTRL,
            }
            self.start_pos = (WIDTH * 0.8, HEIGHT * 0.8)
            self.start_angle = 180
            self.color = BLUE

        # Создаем surface с треугольником корабля
        self.image = pygame.Surface((50, 40), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, self.color, [(0, 40), (25, 0), (50, 40)])
        pygame.draw.circle(self.image, RED, (25, 8), 4)
        pygame.draw.line(self.image, RED, (10, 30), (40, 30), width=4)

        self.rect = self.image.get_rect(center=self.start_pos)
        self.angle = self.start_angle

    def set_hp(self, hp):
        """Устанавливает новое значение HP."""
        self.hp = hp

    def reset(self):
        """Сбрасывает состояние корабля после смерти."""
        self.hp = self.start_hp
        self.shots = self.start_shots
        self.is_reloading = False
        self.is_respawning = False
        self.angle = self.start_angle
        self.rect.center = self.start_pos
        self.invincible_until = time.time() + self.invincible_time

    def take_damage(self):
        """Уменьшает ХП при получении урона."""
        current_time = time.time()

        # Неуязвимы при респауне?
        if self.is_respawning or current_time < self.invincible_until:
            return

        self.hp -= 1
        self.invincible_until = current_time + self.invincible_time
        if self.hp <= 0:
            # Начинаем респаун
            self.is_respawning = True
            self.respawn_start_time = current_time
            print(f"[DEBUG] Ship {self.number} initiated respawn.")

    def update(self, keys):
        """Обновление движения корабля с учетом клавиш."""
        current_time = time.time()

        # Проверка, не в процессе ли корабль возрождения
        if self.is_respawning:
            # Обработка респауна (2 секунды)
            elapsed = current_time - self.respawn_start_time
            if elapsed > 2:  # 2 секунды респауна
                self.reset()
                print(f"[DEBUG] Ship {self.number} respawned.")
            return

        # Повороты
        if keys[self.keys['left']]:
            self.angle += 5
        if keys[self.keys['right']]:
            self.angle -= 5

        # Движение вперед/назад
        dx = int(self.speed * math.cos(math.radians(self.angle)))
        dy = int(self.speed * math.sin(math.radians(self.angle)))
        if keys[self.keys['up']]:
            self.rect.x += dx
            self.rect.y -= dy
        if keys[self.keys['down']]:
            self.rect.x -= dx
            self.rect.y += dy

        # Телепортируем за границами окна
        self.rect.x %= WIDTH
        self.rect.y %= HEIGHT

        # Перезарядка
        if self.is_reloading:
            elapsed = current_time - self.reload_start_time
            if elapsed >= self.reload_time:
                self.is_reloading = False
                self.shots = self.start_shots
                print(f"[DEBUG] ship_{self.number} finished reloading. Elapsed: {elapsed:.2f}s")

    def try_shoot(self):
        """Проверка возможности выстрела (для локальной игры).
           Возвращает (bool, (x, y)) - можно ли стрелять и координаты точки вылета лазера.
        """
        current_time = time.time()

        if (self.shots > 0 and
                not self.is_reloading and
                (current_time - self.last_laser_time) >= self.laser_cooldown and
                not self.is_respawning):
            self.shots -= 1
            self.last_laser_time = current_time

            # Если боезапас кончился — входим в стадию перезарядки
            if self.shots <= 0 and not self.is_reloading:
                self.is_reloading = True
                self.reload_start_time = current_time
                print(f"[DEBUG] Reloading started for ship_{self.number}")

            # Возвращаем координаты носа корабля
            tip_x = self.rect.centerx + self.radius * math.cos(math.radians(self.angle))
            tip_y = self.rect.centery - self.radius * math.sin(math.radians(self.angle))
            return True, (tip_x, tip_y)

        return False, (0, 0)

    def draw(self):
        """Отрисовка корабля на экране."""
        if self.is_respawning:
            # Эффект "мерцания" во время смерти или показать текст "умер" — на ваше усмотрение
            dt = time.time() - self.respawn_start_time
            death_text = pygame.font.Font(None, 36).render(f"Player {self.number + 1} is respawning", True, RED)
            self.screen.blit(death_text, (WIDTH // 2 - 100, HEIGHT // 2 + 40 * self.number))
            return
        # Проверяем, не идет ли перезарядка
        if self.is_reloading:
            font = pygame.font.Font(None, 20)
            text_reload = font.render("Reloading...", True, RED)
            self.screen.blit(text_reload, (self.rect.centerx - 40, self.rect.centery + 60))

        # Если корабль "мигает" при возрождении/инвул
        current_time = time.time()
        is_reloading = (current_time < self.invincible_until)
        if is_reloading and int(current_time * 10) % 2 == 0:
            return  # Пропускаем кадр, чтобы создать мерцание

        rotated_image = pygame.transform.rotate(self.image, self.angle - 90)
        new_rect = rotated_image.get_rect(center=self.rect.center)
        self.screen.blit(rotated_image, new_rect.topleft)

        # Отображение ХП и боезапаса
        font = pygame.font.Font(None, 20)
        text_hp = font.render(f"HP: {self.hp}", True, WHITE)
        text_shots = font.render(f"Shots: {self.shots}", True, WHITE)
        self.screen.blit(text_hp, (self.rect.centerx - 15, self.rect.centery + 25))
        self.screen.blit(text_shots, (self.rect.centerx - 20, self.rect.centery + 45))

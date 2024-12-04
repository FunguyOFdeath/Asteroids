import pygame
import math
import time
from utils import points, WIDTH, HEIGHT, ORANGE, BLUE, WHITE, RED
from laser import shoot_laser


class Ship:
    def __init__(self, screen, number):
        self.number = number
        self.screen = screen
        self.image = pygame.Surface((50, 40), pygame.SRCALPHA)

        if number == 0:
            pygame.draw.polygon(self.image, ORANGE, [(0, 40), (25, 0), (50, 40)])  # оранжевый
            self.start = WIDTH * 0.2, HEIGHT * 0.2
            self.keysPlayer = [pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s, pygame.K_e]
            self.start_angle = 0
        elif number == 1:
            pygame.draw.polygon(self.image, BLUE, [(0, 40), (25, 0), (50, 40)])  # синий
            self.start = WIDTH * 0.8, HEIGHT * 0.8
            self.rect = self.image.get_rect(center=self.start)
            self.keysPlayer = [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN, pygame.K_RCTRL]
            # self.keysPlayer = [pygame.K_k, pygame.K_SEMICOLON, pygame.K_o, pygame.K_l, pygame.K_p]
            self.start_angle = 180
        else:
            print(f'Ship unknown number{self.number}')
            exit(1)

        self.startHp = 3
        self.startShots = 10

        pygame.draw.circle(self.image, RED, (25, 8), 4)
        pygame.draw.line(self.image, RED, (10, 30), (40, 30), width=4)
        self.invincibleTime = 0.6
        self.angle = self.start_angle
        self.rect = self.image.get_rect(center=self.start)
        self.speed = 5
        self.radius = 20
        # self.lives = 3
        self.__hp = self.startHp
        self.invincible_until = time.time() + self.invincibleTime
        self.last_laser_time = 0
        self.laser_cooldown = 0.2
        self.shots = self.startShots  # Максимальное количество выстрелов
        self.reload_time = 1.5  # Время перезарядки в секундах (2 секунды)
        self.is_reloading = False
        self.reload_start_time = 0
        self.is_respawning = False
        self.respawn_start_time = 0

    def update(self, keys):
        # Если игрок возрождается
        current_time = time.time()
        if self.is_respawning:
            if self.respawn_start_time + 2 < current_time:
                self.is_respawning = False
            return  # Не выполняем дальнейшее обновление во время воскрешения

        # Управление игроком
        if keys[self.keysPlayer[0]]:
            self.angle += 5
        if keys[self.keysPlayer[1]]:
            self.angle -= 5
        if keys[self.keysPlayer[2]]:
            self.rect.x += int(self.speed * math.cos(math.radians(self.angle)))
            self.rect.y -= int(self.speed * math.sin(math.radians(self.angle)))
        if keys[self.keysPlayer[3]]:
            self.rect.x -= int(self.speed * math.cos(math.radians(self.angle)))
            self.rect.y += int(self.speed * math.sin(math.radians(self.angle)))

        self.rect.x %= WIDTH
        self.rect.y %= HEIGHT

        # Проверка на перезарядку
        if self.is_reloading:
            if current_time - self.reload_start_time >= self.reload_time:
                self.is_reloading = False
                self.shots = self.startShots

    def take_damage(self):
        """Уменьшает ХП при получении урона."""
        if self.is_respawning:
            return

        current_time = time.time()
        if current_time < self.invincible_until:
            return

        self.__hp -= 1
        self.invincible_until = current_time + self.invincibleTime

        if self.__hp <= 0:
            points[(self.number + 1) % 2] += 1
            self.reset()
            self.is_respawning = True
            self.respawn_start_time = current_time

    def shoot_laser(self):
        current_time = time.time()
        if self.shots > 0 and not self.is_reloading:
            # Стрельба из вершины треугольника
            tip_x = self.rect.centerx + self.radius * math.cos(math.radians(self.angle))
            tip_y = self.rect.centery - self.radius * math.sin(math.radians(self.angle))
            shoot_laser(tip_x, tip_y, self.angle, self.number)
            self.shots -= 1
            self.last_laser_time = current_time
        elif self.shots <= 0 and not self.is_reloading:
            self.is_reloading = True
            self.reload_start_time = current_time

    def draw(self):
        if not self.is_respawning:
            rotated_image = pygame.transform.rotate(self.image, self.angle - 90)
            new_rect = rotated_image.get_rect(center=self.rect.center)
            current_time = time.time()
            if current_time > self.invincible_until:
                self.screen.blit(rotated_image, new_rect.topleft)
            else:
                if int(current_time * 10) % 2 == 0:
                    self.screen.blit(rotated_image, new_rect.topleft)

            # Отображение оставшихся выстрелов
            shots_text = pygame.font.Font(None, 24).render(f"Shots: {self.shots}", True, WHITE)
            self.screen.blit(shots_text, (self.rect.centerx - 15, self.rect.centery + 50))

            # Отображение ХП корабля
            hp_text = pygame.font.Font(None, 24).render(f"HP: {self.__hp}", True, WHITE)
            self.screen.blit(hp_text, (self.rect.centerx - 15, self.rect.centery + 70))

        else:
            # Отображение экрана смерти
            death_text = pygame.font.Font(None, 72).render(f"Игрок {self.number + 1} умер!", True, RED)
            if self.number == 0:
                text_rect = death_text.get_rect(center=(WIDTH // 2, HEIGHT * 0.45))
                self.screen.blit(death_text, text_rect)
            elif self.number == 1:
                text_rect = death_text.get_rect(center=(WIDTH // 2, HEIGHT * 0.55))
                self.screen.blit(death_text, text_rect)
            else:
                print(f'Ship unknown number{self.number}')
                exit(1)

    def reset(self):
        """Сбрасывает состояние корабля после смерти."""
        self.__hp = self.startHp  # Восстановление полного запаса ХП
        self.rect = self.image.get_rect(center=self.start)  # Возвращение на стартовую позицию
        self.angle = self.start_angle  # Сброс угла поворота
        self.invincible_until = time.time() + self.invincibleTime  # Кратковременная неуязвимость
        self.is_reloading = False  # Сброс состояния перезарядки
        self.shots = self.startShots  # Полный боезапас

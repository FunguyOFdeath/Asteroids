import math  # Библиотека для математических расчетов
import time  # Библиотека для работы со временем


class GameLogic:  # Класс для управления логикой игры
    def __init__(self, ship_list, asteroid_manager, laser_manager, max_time=30):  # Инициализация логики игры
        self.ships = ship_list  # Список кораблей
        self.asteroid_manager = asteroid_manager  # Менеджер астероидов
        self.laser_manager = laser_manager  # Менеджер лазеров
        self.start_time = time.time()  # Время начала игры
        self.max_time = max_time  # Максимальное время игры
        self.points = [0] * len(ship_list)  # Очки для каждого корабля

    def update(self):  # Метод для обновления состояния игры
        current_time = time.time()  # Текущее время

        self.asteroid_manager.update()  # Обновляем состояние астероидов
        self.laser_manager.update()  # Обновляем состояние лазеров

        for i, ship in enumerate(self.ships):  # Обрабатываем каждый корабль
            if ship.is_reloading:  # Проверяем состояние перезарядки
                elapsed = current_time - ship.reload_start_time  # Время с начала перезарядки
                if elapsed >= ship.reload_time:  # Если перезарядка завершена
                    ship.is_reloading = False  # Сбрасываем флаг перезарядки
                    ship.shots = ship.start_shots  # Восстанавливаем боезапас
                    print(f"[SERVER] Ship {i} finished reloading.")

            if ship.is_respawning:  # Проверяем состояние респауна
                elapsed = current_time - ship.respawn_start_time  # Время с начала респауна
                if elapsed > 2:  # Если респаун завершён через 2 секунды
                    ship.reset()  # Сбрасываем состояние корабля
                    print(f"[SERVER] Ship {i} respawned.")
                continue  # Пропускаем дальнейшую обработку этого корабля

            for asteroid in self.asteroid_manager.asteroids:  # Проверяем столкновения с астероидами
                dist = math.hypot(ship.rect.centerx - asteroid['pos'][0],  # Расстояние до астероида по X
                                  ship.rect.centery - asteroid['pos'][1])  # Расстояние до астероида по Y
                if dist < (ship.radius + asteroid['radius']):  # Если произошло столкновение
                    ship.take_damage()  # Наносим урон кораблю
                    asteroid['hp'] -= 1  # Уменьшаем здоровье астероида
                    if asteroid['hp'] <= 0:  # Если здоровье астероида исчерпано
                        self.asteroid_manager.asteroids.remove(asteroid)  # Удаляем астероид

        for laser in self.laser_manager.lasers[:]:  # Проверяем столкновения лазеров
            lx, ly = laser['pos']  # Координаты лазера

            for i, ship in enumerate(self.ships):  # Проверяем столкновения с кораблями
                if ship.is_respawning:  # Пропускаем корабли в состоянии респауна
                    continue
                dist = math.hypot(lx - ship.rect.centerx, ly - ship.rect.centery)  # Расстояние до корабля
                if dist < ship.radius:  # Если произошло столкновение
                    ship.take_damage()  # Наносим урон кораблю
                    owner_id = laser['owner']  # Получаем ID владельца лазера
                    if owner_id != ship.number:  # Если лазер выпущен другим кораблём
                        self.points[owner_id] += 1  # Начисляем очки владельцу лазера
                    self.laser_manager.lasers.remove(laser)  # Удаляем лазер
                    break
            else:  # Если лазер не столкнулся с кораблём
                for ast in self.asteroid_manager.asteroids[:]:  # Проверяем столкновения с астероидами
                    dist_ast = math.hypot(lx - ast['pos'][0], ly - ast['pos'][1])  # Расстояние до астероида
                    if dist_ast < ast['radius']:  # Если произошло столкновение
                        self.asteroid_manager.asteroids.remove(ast)  # Удаляем астероид
                        if laser in self.laser_manager.lasers:  # Если лазер всё ещё существует
                            self.laser_manager.lasers.remove(laser)  # Удаляем лазер
                        break

        elapsed = current_time - self.start_time  # Вычисляем время с начала игры
        if elapsed >= self.max_time:  # Проверяем, истекло ли время игры
            return True  # Завершаем игру
        return False  # Игра продолжается

    def reset_game(self):  # Метод для сброса состояния игры
        self.start_time = time.time()  # Сбрасываем время начала игры
        self.points = [0] * len(self.ships)  # Сбрасываем очки всех игроков
        self.asteroid_manager.asteroids.clear()  # Удаляем все астероиды
        self.laser_manager.lasers.clear()  # Удаляем все лазеры
        print("[SERVER] GameLogic reset.")  # Лог сообщения о сбросе

    def get_time_left(self):  # Метод для получения оставшегося времени
        return max(0, self.max_time - int(time.time() - self.start_time))  # Возвращаем оставшееся время

# gamelogic.py
import math
import time


class GameLogic:
    """Класс, отвечающий за:
       - Столкновения
       - Подсчет очков
       - Общее управление длительностью игры и т.д.
    """

    def __init__(self, ship_list, asteroid_manager, laser_manager, max_time=30):
        self.ships = ship_list
        self.asteroid_manager = asteroid_manager
        self.laser_manager = laser_manager
        self.start_time = time.time()
        self.max_time = max_time
        self.points = [0] * len(ship_list)  # Для каждого корабля

    def update(self):
        """Общее обновление игры — вызывается каждый кадр."""
        current_time = time.time()

        # Обновляем астероиды и лазеры
        self.asteroid_manager.update()
        self.laser_manager.update()

        # Сталкиваем корабли с астероидами
        for i, ship in enumerate(self.ships):
            # Управление перезарядкой
            if ship.is_reloading:
                elapsed = current_time - ship.reload_start_time
                if elapsed >= ship.reload_time:
                    ship.is_reloading = False
                    ship.shots = ship.start_shots
                    print(f"[SERVER] Ship {i} finished reloading.")

            if ship.is_respawning:
                elapsed = current_time - ship.respawn_start_time
                if elapsed > 2:  # Завершение респауна через 2 секунды
                    ship.reset()
                    print(f"[SERVER] Ship {i} respawned.")
                continue

            for asteroid in self.asteroid_manager.asteroids:
                dist = math.hypot(ship.rect.centerx - asteroid['pos'][0],
                                  ship.rect.centery - asteroid['pos'][1])
                if dist < (ship.radius + asteroid['radius']):
                    ship.take_damage()
                    asteroid['hp'] -= 1
                    if asteroid['hp'] <= 0:
                        self.asteroid_manager.asteroids.remove(asteroid)

                        # Сталкиваем лазеры с астероидами и другими кораблями
        for laser in self.laser_manager.lasers[:]:
            lx, ly = laser['pos']

            # 1) Смотрим столкновение с кораблями
            for i, ship in enumerate(self.ships):
                if ship.is_respawning:
                    continue
                dist = math.hypot(lx - ship.rect.centerx, ly - ship.rect.centery)
                if dist < ship.radius:
                    # Урон кораблю
                    ship.take_damage()
                    # Если лазер выпущен другим кораблем — добавим очки
                    owner_id = laser['owner']
                    if owner_id != ship.number:
                        self.points[owner_id] += 1

                    self.laser_manager.lasers.remove(laser)
                    break

            else:
                # 2) Если не удалили лазер, проверяем на столкновение с астероидами
                for ast in self.asteroid_manager.asteroids[:]:
                    dist_ast = math.hypot(lx - ast['pos'][0], ly - ast['pos'][1])
                    if dist_ast < ast['radius']:
                        # Удаляем астероид
                        self.asteroid_manager.asteroids.remove(ast)
                        # Удаляем лазер
                        if laser in self.laser_manager.lasers:
                            self.laser_manager.lasers.remove(laser)
                        break

        # Проверяем, не истекло ли время игры
        elapsed = current_time - self.start_time
        if elapsed >= self.max_time:
            # Игра окончена — можно вернуть флаг, результат и т.д.
            return True  # Укажем, что пора завершать
        return False

    def reset_game(self):
        """Сброс игрового состояния для новой игры."""
        self.start_time = time.time()
        self.points = [0] * len(self.ships)
        self.asteroid_manager.asteroids.clear()
        self.laser_manager.lasers.clear()
        print("[SERVER] GameLogic reset.")

    def get_time_left(self):
        """Сколько осталось до конца игры."""
        return max(0, self.max_time - int(time.time() - self.start_time))

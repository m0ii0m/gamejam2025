import math
import random
import pygame as pg
from core import Scene, WIDTH, HEIGHT, GRAVITY, GRAY, BLUE, WHITE, GREEN, RED, YELLOW, draw_multiline_center, draw_text_center

class RunnerScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        # Ground and player
        self.ground_y = HEIGHT - 90
        self.player = pg.Rect(120, self.ground_y - 50, 34, 50)
        self.vel_y = 0.0
        self.on_ground = True

        # Arrows from castle side
        self.castle_x = WIDTH - 120
        self.arrows = []
        self.spawn_timer = 0.0
        self.spawn_interval = 1.0
        
        # Cooldown entre flèches individuelles (0.5 secondes)
        self.arrow_cooldown = 0.5
        self.last_arrow_time = 0.0

        # Progress towards the castle
        self.distance = 0.0
        self.target_distance = 800.0
        self.speed = 260.0

        # Game state
        self.alive = True
        self.win = False

    def reset(self):
        self.player.update(120, self.ground_y - 50, 34, 50)
        self.vel_y = 0
        self.on_ground = True
        self.arrows.clear()
        self.spawn_timer = 0
        self.distance = 0
        self.speed = 260.0
        self.alive = True
        self.win = False
        self.last_arrow_time = 0.0

    def spawn_arrow(self):
        x = self.castle_x + 100
        y = self.ground_y - random.randint(40, 140)
        target = (self.player.centerx + random.randint(-40, 40), self.player.centery + random.randint(-20, 10))
        vx, vy = target[0] - x, target[1] - y
        length = math.hypot(vx, vy) or 1.0
        speed = random.uniform(260, 340)
        vx, vy = vx / length * speed, vy / length * speed
        self.arrows.append({"x": x, "y": y, "vx": vx, "vy": vy})

    def handle_event(self, event):
        if event.type == pg.KEYDOWN:
            if event.key in (pg.K_SPACE, pg.K_UP, pg.K_w):
                if self.on_ground and self.alive and not self.win:
                    self.vel_y = -17.2
                    self.on_ground = False
            if event.key == pg.K_r and not self.alive:
                self.reset()
            if event.key == pg.K_ESCAPE:
                pg.event.post(pg.event.Event(pg.QUIT))
            if event.key == pg.K_RETURN and self.win:
                from scenes.defense import ArrowDefenseScene
                self.game.change_scene(ArrowDefenseScene(self.game))

    def update(self, dt):
        if not self.alive or self.win:
            return
        self.speed += 12.0 * dt
        self.vel_y += GRAVITY
        self.player.y += int(self.vel_y)
        if self.player.bottom >= self.ground_y:
            self.player.bottom = self.ground_y
            self.vel_y = 0
            self.on_ground = True

        # Mettre à jour le cooldown des flèches
        self.last_arrow_time += dt

        self.spawn_timer += dt
        min_interval = max(0.4, self.spawn_interval - (self.distance / self.target_distance) * 0.5)
        if self.spawn_timer >= min_interval:
            self.spawn_timer = 0.0
            count = 1 + (1 if random.random() < 0.25 else 0)
            arrows_spawned = 0
            for _ in range(count):
                # Vérifier le cooldown avant de spawner chaque flèche
                if self.last_arrow_time >= self.arrow_cooldown:
                    self.spawn_arrow()
                    self.last_arrow_time = 0.0  # Reset du cooldown
                    arrows_spawned += 1
                    break  # Une seule flèche par cycle pour respecter le cooldown

        for a in self.arrows:
            a["x"] += a["vx"] * dt
            a["y"] += a["vy"] * dt
        self.arrows = [a for a in self.arrows if -80 <= a["x"] <= WIDTH + 160 and -80 <= a["y"] <= HEIGHT + 80]

        self.distance += self.speed * dt * 0.4
        if self.distance >= self.target_distance:
            self.win = True

        player_hitbox = self.player.inflate(-6, -4)
        for a in self.arrows:
            pt_rect = pg.Rect(int(a["x"]) - 2, int(a["y"]) - 2, 4, 4)
            if player_hitbox.colliderect(pt_rect):
                self.alive = False
                break

    def draw_hud(self, surf):
        pg.draw.rect(surf, GRAY, (0, self.ground_y, WIDTH, HEIGHT - self.ground_y))
        bar_w, bar_h = 320, 12
        x, y = WIDTH // 2 - bar_w // 2, 24
        pg.draw.rect(surf, (60, 60, 60), (x, y, bar_w, bar_h), border_radius=4)
        p = max(0.0, min(1.0, self.distance / self.target_distance))
        pg.draw.rect(surf, BLUE, (x + 2, y + 2, int((bar_w - 4) * p), bar_h - 4), border_radius=4)
        draw_text_center(surf, "Messager -> Château", 18, WHITE, (WIDTH // 2, y + 28))

    def draw(self, surf):
        surf.fill((22, 22, 28))
        pg.draw.rect(surf, (35, 35, 55), (0, 0, WIDTH, self.ground_y))
        castle_w, castle_h = 80, 120
        castle_x = self.castle_x
        pg.draw.rect(surf, (110, 110, 140), (castle_x, self.ground_y - castle_h, castle_w, castle_h))
        for i in range(3):
            sx = castle_x + 12
            sy = self.ground_y - castle_h + 30 + i * 26
            pg.draw.rect(surf, (90, 90, 110), (sx, sy, 14, 6))

        for a in self.arrows:
            pg.draw.circle(surf, RED, (int(a["x"]), int(a["y"])), 3)
        pg.draw.rect(surf, GREEN if self.alive else RED, self.player)
        self.draw_hud(surf)

        if not self.alive:
            draw_multiline_center(
                surf,
                [
                    "Le messager est tombé...",
                    "Appuyez sur R pour recommencer",
                    "ESC pour quitter",
                ],
                26,
                WHITE,
                (WIDTH // 2, HEIGHT // 2),
            )
        elif self.win:
            draw_multiline_center(
                surf,
                [
                    "Le messager atteint le château !",
                    "Le prince apprend la mort du roi...",
                    "Appuyez sur ENTER pour défendre le prince (intérieur)",
                ],
                26,
                WHITE,
                (WIDTH // 2, HEIGHT // 2),
            )

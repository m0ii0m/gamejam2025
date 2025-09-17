import math
import random
import pygame as pg
from core import Scene, WIDTH, HEIGHT, GRAVITY, WHITE, BLUE, GREEN, YELLOW, RED, draw_text_center, draw_multiline_center

class ArrowDefenseScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.castle_x = WIDTH - 120
        self.wall_rect = pg.Rect(self.castle_x, 0, 120, HEIGHT)

        self.prince = pg.Rect(WIDTH - 280, HEIGHT - 80, 28, 48)
        self.prince_speed = 80.0
        self.exit_x = 40

        self.guard = pg.Rect(WIDTH // 2 - 20, 48, 40, 18)
        self.guard_speed = 320
        self.shields = []
        self.drop_cooldown = 0.45
        self.drop_timer = 0.0
        self.max_shields = 6
        self.shield_w = 18
        self.shield_top = 80

        self.arrows = []
        self.spawn_timer = 0.0
        self.base_spawn_interval = 0.9
        self.elapsed = 0.0
        self.win = False
        self.lose = False

    def reset(self):
        self.prince.x = WIDTH - 280
        self.guard.centerx = WIDTH // 2
        self.shields.clear()
        self.arrows.clear()
        self.spawn_timer = 0.0
        self.drop_timer = 0.0
        self.elapsed = 0.0
        self.win = False
        self.lose = False

    def handle_event(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_SPACE and not (self.win or self.lose):
                if self.drop_timer <= 0.0 and len(self.shields) < self.max_shields:
                    x = max(0, min(WIDTH - self.shield_w, self.guard.centerx - self.shield_w // 2))
                    shield_rect = pg.Rect(x, self.shield_top, self.shield_w, HEIGHT - 40 - self.shield_top)
                    self.shields.append(shield_rect)
                    self.drop_timer = self.drop_cooldown
            if event.key == pg.K_r and self.lose:
                self.reset()
            if event.key == pg.K_RETURN and self.win:
                from scenes.end import EndOfLevelScene
                self.game.change_scene(EndOfLevelScene(self.game))
            if event.key == pg.K_ESCAPE:
                pg.event.post(pg.event.Event(pg.QUIT))

    def spawn_arrow(self):
        x = self.castle_x + 40
        slit_offsets = [40, 80, 120, 160, 200, 240]
        y = 40 + random.choice(slit_offsets)
        target = (self.prince.centerx + random.randint(-20, 20), self.prince.centery + random.randint(-10, 10))
        vx, vy = target[0] - x, target[1] - y
        length = math.hypot(vx, vy) or 1.0
        speed = random.uniform(200, 280)
        vx, vy = vx / length * speed, vy / length * speed
        self.arrows.append({"x": x, "y": y, "vx": vx, "vy": vy})

    def update(self, dt):
        if self.win or self.lose:
            return
        self.elapsed += dt
        if self.drop_timer > 0:
            self.drop_timer -= dt

        keys = pg.key.get_pressed()
        if keys[pg.K_LEFT] or keys[pg.K_a]:
            self.guard.x -= int(self.guard_speed * dt)
        if keys[pg.K_RIGHT] or keys[pg.K_d]:
            self.guard.x += int(self.guard_speed * dt)
        self.guard.x = max(0, min(WIDTH - self.guard.width, self.guard.x))

        self.prince.x -= int(self.prince_speed * dt)
        if self.prince.left <= self.exit_x:
            self.win = True

        self.spawn_timer += dt
        interval = max(0.35, self.base_spawn_interval - min(0.5, self.elapsed * 0.03))
        if self.spawn_timer >= interval:
            self.spawn_timer = 0.0
            for _ in range(1 + (1 if self.elapsed > 8 else 0)):
                self.spawn_arrow()

        for a in self.arrows:
            a["x"] += a["vx"] * dt
            a["y"] += a["vy"] * dt
        self.arrows = [a for a in self.arrows if -60 <= a["x"] <= WIDTH + 100 and -60 <= a["y"] <= HEIGHT + 60]

        prince_hitbox = self.prince.inflate(6, 6)
        new_arrows = []
        for a in self.arrows:
            arrow_rect = pg.Rect(int(a["x"]) - 2, int(a["y"]) - 2, 4, 4)
            blocked = any(arrow_rect.colliderect(s) for s in self.shields)
            if blocked:
                continue
            if arrow_rect.colliderect(prince_hitbox):
                self.lose = True
                new_arrows = []
                break
            new_arrows.append(a)
        self.arrows = new_arrows

    def draw(self, surf):
        surf.fill((24, 24, 28))
        ground_rect = pg.Rect(0, HEIGHT - 40, WIDTH, 40)
        rampart_rect = pg.Rect(0, 32, WIDTH, 20)
        pg.draw.rect(surf, (60, 60, 70), ground_rect)
        pg.draw.rect(surf, (70, 70, 85), rampart_rect)

        pg.draw.rect(surf, (110, 110, 140), self.wall_rect)
        for i in range(6):
            sy = 40 + i * 40
            pg.draw.rect(surf, (90, 90, 110), (self.castle_x + 12, sy, 16, 8))

        pg.draw.rect(surf, (40, 40, 50), (0, HEIGHT - 100, 30, 60))
        draw_text_center(surf, "Sortie", 14, WHITE, (18, HEIGHT - 112))

        pg.draw.rect(surf, BLUE, self.prince)
        draw_text_center(surf, "Prince", 16, WHITE, (self.prince.centerx, self.prince.top - 14))
        pg.draw.rect(surf, GREEN, self.guard)
        draw_text_center(surf, "Soldat (← →) — ESPACE: rideau", 16, WHITE, (WIDTH // 2, 18))

        for srect in self.shields:
            pg.draw.rect(surf, YELLOW, srect)
        for a in self.arrows:
            pg.draw.circle(surf, RED, (int(a["x"]), int(a["y"])) , 3)

        total = (WIDTH - 280) - self.exit_x
        done = max(0, (WIDTH - 280) - self.prince.left)
        p = max(0.0, min(1.0, done / total if total > 0 else 1.0))
        bar_w, bar_h = 300, 10
        x, y = WIDTH // 2 - bar_w // 2, 24
        pg.draw.rect(surf, (60, 60, 60), (x, y, bar_w, bar_h), border_radius=3)
        pg.draw.rect(surf, (90, 180, 120), (x + 2, y + 2, int((bar_w - 4) * p), bar_h - 4), border_radius=3)
        draw_text_center(surf, "Prince → Sortie", 16, WHITE, (WIDTH // 2, y + 24))

        if self.lose:
            draw_multiline_center(
                surf,
                [
                    "Le prince a été touché...",
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
                    "Le prince a franchi la porte !",
                    "Niveau 1 terminé.",
                    "ENTER pour continuer",
                ],
                26,
                WHITE,
                (WIDTH // 2, HEIGHT // 2),
            )

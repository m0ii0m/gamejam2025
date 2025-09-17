import pygame as pg

# --------------------------
# Constants and config
# --------------------------
WIDTH, HEIGHT = 960, 540
FPS = 60
GRAVITY = 0.9
WHITE = (240, 240, 240)
BLACK = (15, 15, 20)
GRAY = (80, 80, 90)
RED = (200, 60, 60)
GREEN = (60, 180, 90)
BLUE = (80, 120, 200)
YELLOW = (230, 210, 80)


class Scene:
    def __init__(self, game):
        self.game = game

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surf):
        pass


def draw_text_center(surf, text, size, color, center, font_name=None):
    font = pg.font.SysFont(font_name or "consolas", size)
    s = font.render(text, True, color)
    r = s.get_rect(center=center)
    surf.blit(s, r)


def draw_multiline_center(surf, lines, color, center, line_gap=8, font=None):
    font = font or pg.font.SysFont("Consolas", 26)
    surfaces = [font.render(line, True, color) for line in lines]
    total_h = sum(s.get_height() for s in surfaces) + line_gap * (len(surfaces) - 1)
    top = center[1] - total_h // 2
    for s in surfaces:
        r = s.get_rect(center=(center[0], top + s.get_height() // 2))
        surf.blit(s, r)
        top += s.get_height() + line_gap


def draw_multiline_left(surf, lines, displayed_text, color, center, line_gap=8, font=None):
    font = font or pg.font.SysFont("Consolas", 26)
    surfaces = [font.render(line, True, color) for line in lines]
    total_h = sum(s.get_height() for s in surfaces) + line_gap * (len(surfaces) - 1)
    max_w = max(s.get_width() for s in surfaces)
    top = center[1] - total_h // 2
    left_x = center[0] - max_w // 2
    for i, line in enumerate(displayed_text):
        if line:  
            text_surf = font.render(line, True, color)
            surf.blit(text_surf, (left_x, top))
        top += surfaces[i].get_height() + line_gap


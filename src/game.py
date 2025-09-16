import sys
import pygame as pg
from core import WIDTH, HEIGHT, FPS, draw_text_center
from scenes.intro import IntroScene

class Game:
    def __init__(self):
        pg.init()
        pg.display.set_caption("GameJam 2025 — Retour du Prince")
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        self.clock = pg.time.Clock()
        self.scene = IntroScene(self)

    def change_scene(self, scene):
        self.scene = scene

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                else:
                    self.scene.handle_event(event)

            self.scene.update(dt)
            self.scene.draw(self.screen)

            draw_text_center(self.screen, "ESC: Quitter", 14, (200, 200, 210), (70, HEIGHT - 16))

            pg.display.flip()
        pg.quit()
        sys.exit(0)

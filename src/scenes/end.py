import pygame as pg
from core import Scene, WIDTH, HEIGHT, WHITE, BLACK, draw_multiline_center
from scenes.intro import IntroScene

class EndOfLevelScene(Scene):
    def handle_event(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_RETURN:
                self.game.change_scene(IntroScene(self.game))
            if event.key == pg.K_ESCAPE:
                pg.event.post(pg.event.Event(pg.QUIT))

    def draw(self, surf):
        surf.fill(BLACK)
        draw_multiline_center(
            surf,
            [
                "Niveau 1 terminé !",
                "Prochain: la forêt de nuit (QTE & cheval)",
                "ENTER pour revenir à l'intro — ESC pour quitter",
            ],
            26,
            WHITE,
            (WIDTH // 2, HEIGHT // 2),
        )

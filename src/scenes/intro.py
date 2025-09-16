import pygame as pg
from core import Scene, WIDTH, HEIGHT, WHITE, BLACK, draw_multiline_center

class IntroScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.lines = [
            "Deux royaumes en guerre...",
            "Le roi est mort. Le prince est loin, chez l'ennemi.",
            "Un messager doit atteindre le château pour prévenir le prince.",
            "",
            "Appuyez sur ENTER pour commencer (Niveau 1)",
        ]

    def handle_event(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_RETURN:
                # Lazy import to avoid circular imports
                from scenes.runner import RunnerScene
                self.game.change_scene(RunnerScene(self.game))
            elif event.key == pg.K_ESCAPE:
                pg.event.post(pg.event.Event(pg.QUIT))

    def draw(self, surf):
        surf.fill(BLACK)
        draw_multiline_center(surf, self.lines, 26, WHITE, (WIDTH // 2, HEIGHT // 2))

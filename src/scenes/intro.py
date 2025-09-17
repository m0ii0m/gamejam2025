import pygame as pg
from core import Scene, WIDTH, HEIGHT, WHITE, BLACK, draw_multiline_center

class IntroScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.typing_sound = pg.mixer.Sound("assets/sounds/Writing-Sound.wav")
        self.typing_sound.set_volume(1) 


        self.lines = [
            "Deux royaumes en guerre...",
            "Le roi est mort. Le prince est loin, chez l'ennemi.",
            "Un messager doit atteindre le château pour prévenir le prince.",
            "",
            "Appuyez sur ENTER pour commencer (Niveau 1)",
        ]

        self.displayed_text = [""] * len(self.lines)
        self.current_line = 0
        self.current_char = 0
        self.char_delay = 50  # ms entre chaque lettre
        self.last_update = pg.time.get_ticks()

    def handle_event(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_RETURN:
                # Lazy import to avoid circular imports
                from scenes.runner import RunnerScene
                self.game.change_scene(RunnerScene(self.game))
            elif event.key == pg.K_ESCAPE:
                pg.event.post(pg.event.Event(pg.QUIT))

    def draw(self, surf):
        if self.current_line == 0 and self.current_char == 0:
            self.typing_sound.play()
        surf.fill(BLACK)
        if self.current_line >= len(self.lines):
            self.typing_sound.stop()


        now = pg.time.get_ticks()
        if self.current_line < len(self.lines):
            if now - self.last_update > self.char_delay:
                line_text = self.lines[self.current_line]
                if self.current_char < len(line_text):
                    self.displayed_text[self.current_line] += line_text[self.current_char]
                    self.current_char += 1
                else:
                    self.current_line += 1
                    self.current_char = 0
                self.last_update = now

        draw_multiline_center(surf, self.displayed_text, 26, WHITE, (WIDTH // 2, HEIGHT // 2))


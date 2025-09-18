import pygame as pg
from ..core import Scene, WIDTH, HEIGHT, WHITE, BLACK, draw_multiline_left

class IntroScene(Scene):
    def __init__(self, game):
        

        self.font_bahiana = pg.font.Font("assets/fonts/Bahiana/Bahiana-Regular.ttf", 34)

        super().__init__(game)
        self.typing_sound = pg.mixer.Sound("assets/sounds/Writing-Sound.wav")
        self.typing_sound.set_volume(1) 
        self.typing_sound2 = pg.mixer.Sound("assets/sounds/Soft Wind.wav")
        self.typing_sound2.set_volume(0.5) 


        self.lines = [
            "Notre pays est en guerre, et le roi vient de mourir.",
            "Le prince, dernier espoir du royaume, doit être prévenu.",
            "Un messager courageux part alors accomplir sa mission :",
            "",
            "Avertir le prince, actuellement assiégé dans son château.",
            "",
            "",
            "Appuyez sur ENTER pour commencer (Niveau 1)",
        ]

        #   

        self.finished = False
        self.displayed_text = [""] * len(self.lines)
        self.current_line = 0
        self.current_char = 0
        self.char_delay = 50  # ms entre chaque lettre
        self.last_update = pg.time.get_ticks()

    def handle_event(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_RETURN:
                self.typing_sound2.stop()
                self.finished = True
            elif event.key == pg.K_ESCAPE:
                pg.event.post(pg.event.Event(pg.QUIT))


    def draw(self, surf):
        if self.current_line == 0 and self.current_char == 0:
            self.typing_sound.play()
            self.typing_sound2.play(loops=-1)
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







        draw_multiline_left(surf,self.lines,self.displayed_text, WHITE,(WIDTH//2, HEIGHT//2),line_gap=10,font=self.font_bahiana)


    def is_finished(self):
        return self.finished




import pygame


class Credits:
    def __init__(self, screen_size, return_callback, background):
        self.screen_size = screen_size
        self.return_callback = return_callback
        self.background = background

        self.title_font = pygame.font.Font("./assets/fonts/Bahiana-Regular.ttf", 64)
        self.text_font = pygame.font.Font("./assets/fonts/Bahiana-Regular.ttf", 48)

        self.credits_lines = [
            "Game by: Chazelle Etienne, Constant Théo, Graveleau Louidji, Leveque Lucas, Régnier Ludovic",
            "For: GameJam ESIEE 2025 edition",
            "Sprites: ...",
            "Music and sounds: ...",
        ]

        self.credits_texts = [
            self.text_font.render(line, True, (168, 11, 11))
            for line in self.credits_lines
        ]

        self.credits_texts_shadow = [
            self.text_font.render(line, True, (98, 10, 10))
            for line in self.credits_lines
        ]

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            self.return_callback()

    def draw(self, surface):
        self.background.update()
        self.background.draw(surface, 0)

        # Title
        title_surf = self.title_font.render("Credits", True, (168, 11, 11))
        title_surf_shadow = self.title_font.render("Credits", True, (98, 10, 10))
        title_rect = title_surf.get_rect(center=(self.screen_size[0] // 2, 60))
        title_rect_shadow = title_surf_shadow.get_rect(
            center=(self.screen_size[0] // 2 + 3, 60 + 3)
        )
        surface.blit(title_surf_shadow, title_rect_shadow)
        surface.blit(title_surf, title_rect)

        # Credits text with shadow
        for i, text_surf in enumerate(self.credits_texts_shadow):
            rect = text_surf.get_rect(
                center=(self.screen_size[0] // 2 + 2, 2 + 150 + i * 40)
            )
            surface.blit(text_surf, rect)
        for i, text_surf in enumerate(self.credits_texts):
            rect = text_surf.get_rect(center=(self.screen_size[0] // 2, 150 + i * 40))
            surface.blit(text_surf, rect)

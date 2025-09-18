import pygame


class Credits:
    def __init__(self, screen_size, return_callback, background):
        self.screen_size = screen_size
        self.return_callback = return_callback
        self.background = background

        self.title_font = pygame.font.Font("./assets/fonts/Bahiana-Regular.ttf", 56)  # Réduit de 64 à 56
        self.text_font = pygame.font.Font("./assets/fonts/Bahiana-Regular.ttf", 36)   # Réduit de 48 à 36
        self.header_font = pygame.font.Font("./assets/fonts/Bahiana-Regular.ttf", 42) # Nouvelle police pour les titres de section

        self.credits_lines = [
            ["Game by", "Chazelle Etienne", "Constant Théo", "Graveleau Louidji", "Leveque Lucas", "Régnier Ludovic"],
            ["Sprites", "Onfe", "LuizMelo", "aamatniekss"],
            ["Music and sounds", "Pixabay", "orangefreesounds"],
        ]

        # Créer les surfaces pour chaque ligne individuellement
        self.credits_texts = []
        
        for section in self.credits_lines:
            section_texts = []
            for i, line in enumerate(section):
                if i == 0:  # Premier élément = titre de section
                    # Couleur rouge foncé pour les titres
                    section_texts.append(self.header_font.render(line, True, (139, 0, 0)))  # Rouge foncé
                else:  # Autres éléments = texte normal
                    # Couleur rouge pour le texte normal
                    section_texts.append(self.text_font.render(line, True, (168, 11, 11)))
            self.credits_texts.append(section_texts)

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

        # Credits text sans ombres
        y_position = 140  # Commencer un peu plus haut
        line_spacing = 35  # Réduit de 50 à 35
        section_spacing = 50  # Réduit de 80 à 50
        
        for section_index, section_texts in enumerate(self.credits_texts):
            # Afficher les textes de cette section
            for line_index, text_surf in enumerate(section_texts):
                rect = text_surf.get_rect(center=(self.screen_size[0] // 2, y_position))
                surface.blit(text_surf, rect)
                y_position += line_spacing
            
            # Ajouter un espacement supplémentaire entre les sections
            y_position += section_spacing

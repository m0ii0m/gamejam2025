import pygame
from button import Button
from parallax_bg import ParallaxBg

class StartMenu:
    def __init__(self, screen_size, font_path, bg_image_path, button_image_path, callbacks):
        self.screen_width, self.screen_height = screen_size

        # Load assets
        self.background = ParallaxBg('./assets/backgrounds/start_menu/', screen_size, cloud_layers=[2,3,4])
        self.bg_image = pygame.image.load(bg_image_path).convert()
        self.bg_image = pygame.transform.scale(self.bg_image, screen_size)
        self.button_image = pygame.image.load(button_image_path).convert_alpha()

        # Callbacks
        self.callbacks = callbacks

        # Fonts
        self.title_font = pygame.font.Font('./assets/fonts/Bahiana-Regular.ttf', 256)
        self.button_font = pygame.font.Font(font_path, 40)

        # Title
        self.title_text = self.title_font.render("Plot Armor", True, (168, 11, 11))
        self.title_rect = self.title_text.get_rect()
        self.title_shadow_text = self.title_font.render("Plot Armor", True, (98, 10, 10))

        # Data
        title_margin = 150
        btn_count = 3
        btn_size = (600, 150)
        btn_gap = 50
        btn_text_color = (142, 78, 99)
        btn_labels = ["Start", "Credits", "Quit"]
        btn_callbacks = ["start", "credits", "quit"]

        # Compute dimensions of the container surface
        container_height = (
            self.title_rect.height +
            title_margin +
            btn_count * btn_size[1] +
            (btn_count - 1) * btn_gap
        )

        # Set title position
        screen_width_center = self.screen_width // 2
        screen_height_center = self.screen_height // 2
        title_position = screen_height_center - container_height // 2 + self.title_rect.height // 2
        self.title_rect.center = (screen_width_center, title_position)
        self.title_shadow_rect = self.title_shadow_text.get_rect().move(self.title_rect.x + 10, self.title_rect.y + 10)
        container_offset = title_position + title_margin 
        
        # Buttons
        self.buttons = []
        for i in range(btn_count):
            self.buttons.append(Button(self.button_image, btn_size, (screen_width_center - btn_size[0] // 2, container_offset), btn_labels[i], self.button_font, btn_text_color, self.callbacks[btn_callbacks[i]], hover_overlay_color=(112, 92, 13, 50)))
            container_offset += btn_size[1] + btn_gap

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()
        for button in self.buttons:
            button.update(mouse_pos, mouse_click)

    def draw(self, surface):
        self.background.update()
        self.background.draw(surface, 0)
        surface.blit(self.title_shadow_text, self.title_shadow_rect)
        surface.blit(self.title_text, self.title_rect)
        for button in self.buttons:
            button.draw(surface)

import pygame
from button import Button

class StartMenu:
    def __init__(self, screen_size, font_path, bg_image_path, button_image_path, callbacks):
        self.screen_width, self.screen_height = screen_size

        # Load assets
        self.bg_image = pygame.image.load(bg_image_path).convert()
        self.bg_image = pygame.transform.scale(self.bg_image, screen_size)
        self.button_image = pygame.image.load(button_image_path).convert_alpha()

        # Callbacks (dict with "start", "credits", "quit")
        self.callbacks = callbacks

        # Fonts
        self.title_font = pygame.font.Font(font_path, 80)
        self.button_font = pygame.font.Font(font_path, 40)

        # Title
        self.title_text = self.title_font.render("Plot Armor", True, (255, 255, 255))
        self.title_rect = self.title_text.get_rect()

        # Data
        title_margin = 100
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
        title_position = screen_height_center - container_height // 2 + self.title_rect.height
        self.title_rect.center = (screen_width_center, title_position)
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
        surface.blit(self.bg_image, (0, 0))
        surface.blit(self.title_text, self.title_rect)
        for button in self.buttons:
            button.draw(surface)

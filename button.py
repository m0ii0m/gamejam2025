
import pygame

class Button:
    def __init__(self, image, size, pos, text, font, text_color, callback, hover_overlay_color=(0,0,0,100)):
        self.image = image
        self.image = pygame.transform.scale(self.image, size)
        self.rect = self.image.get_rect(topleft=pos)
        self.text = font.render(text, True, text_color)
        self.text_rect = self.text.get_rect(center=self.rect.center)
        self.callback = callback
        self.hovered = False
        self.hover_overlay = self.image.copy()
        self.hover_overlay.fill(hover_overlay_color, special_flags=pygame.BLEND_RGBA_MULT)

    def update(self, mouse_pos, mouse_click):
        self.hovered = self.rect.collidepoint(mouse_pos)
        if self.hovered and mouse_click[0]:
            self.callback()

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        if self.hovered:
            surface.blit(self.hover_overlay, self.rect)
        surface.blit(self.text, self.text_rect)

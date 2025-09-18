import pygame
import os
import random

class Horse:
    def __init__(self, x, y, facing="right"):
        self.rect = pygame.Rect(x, y, 75, 75)  # Taille similaire au joueur
        self.facing = facing
        self.x = x
        self.y = y
        
        # Animation
        self.animation_timer = 0
        self.animation_speed = random.randint(6, 10)  # Vitesse d'animation variable
        self.current_animation = "idle"
        self.animation_frame = 0
        self.animation_finished = False
        
        # Chargement des sprites
        self.sprites = {}
        self.load_sprites()
        
    def load_sprites(self):
        """Charge tous les sprites de l'ennemi"""
        sprite_path = "assets/images/sprites/horse/"
        
        animations = {
            "idle": {"path": "idle", "count": 9, "loop": True},
            "jump": {"path": "jump", "count": 10, "loop": False},
            "run": {"path": "run", "count": 6, "loop": True},
        }
        
        for anim_name, anim_info in animations.items():
            folder_path = os.path.join(sprite_path, anim_info["path"])
            if os.path.exists(folder_path):
                self.sprites[anim_name] = []
                
                # Charger toutes les images du dossier
                files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                files.sort()  # Trier pour avoir le bon ordre
                
                for filename in files:
                    img_path = os.path.join(folder_path, filename)
                    try:
                        image = pygame.image.load(img_path).convert_alpha()
                        # Redimensionner l'image pour correspondre à la taille du joueur
                        scaled_image = pygame.transform.scale(image, (75, 75))
                        self.sprites[anim_name].append(scaled_image)
                    except pygame.error as e:
                        print(f"Erreur lors du chargement de {img_path}: {e}")
                    
    def update(self):
        # Animation
        self.update_animation()
                    
    def update_animation(self):
        """Met à jour l'animation"""
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            if self.current_animation in self.sprites and self.sprites[self.current_animation]:
                animation_frames = self.sprites[self.current_animation]
                max_frames = len(animation_frames)
                
                if self.animation_frame >= max_frames:
                    self.animation_frame = max_frames - 1
                
                should_loop = True
                if self.current_animation in ["jump"]:
                    should_loop = False
                
                if should_loop:
                    self.animation_frame = (self.animation_frame + 1) % max_frames
                else:
                    if self.animation_frame < max_frames - 1:
                        self.animation_frame += 1
                    else:
                        self.animation_finished = True
                        
    def draw(self, screen, camera_x, camera_y):
        if self.current_animation in self.sprites and self.sprites[self.current_animation]:
            animation_frames = self.sprites[self.current_animation]
            max_frame = len(animation_frames) - 1
            if self.animation_frame > max_frame:
                self.animation_frame = max_frame
                
            current_sprite = animation_frames[self.animation_frame].copy()
            
            # Inverser l'image si nécessaire
            if not self.facing == 'right':
                current_sprite = pygame.transform.flip(current_sprite, True, False)
            
            # Position à l'écran
            screen_x = self.rect.x - camera_x
            screen_y = self.rect.y - camera_y
            
            screen.blit(current_sprite, (screen_x, screen_y))

    def set_animation(self, animation_name):
        """Change l'animation actuelle"""
        if animation_name != self.current_animation:
            self.current_animation = animation_name
            self.animation_frame = 0
            self.animation_timer = 0
            self.animation_finished = False
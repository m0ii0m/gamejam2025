import pygame
import os

class Prince:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 100, 100)  # Agrandir de 75x75 à 100x100 pour une meilleure présence
        self.x = x  # Position fixe du prince
        self.y = y
        
        # Animation
        self.animation_timer = 0
        self.animation_speed = 8  # Animation plus lente pour le prince (statique)
        self.current_animation = "idle"
        self.animation_frame = 0
        
        # Le prince fait face à la droite par défaut (vers où arrive le joueur)
        self.facing_right = True
        
        # Chargement des sprites
        self.sprites = {}
        self.load_sprites()
        
    def load_sprites(self):
        """Charge les sprites du prince depuis le dossier prince"""
        sprite_path = "assets/Sprites/prince/"
        
        # Chargement uniquement de l'animation idle pour le prince statique
        animations = {
            "idle": {"type": "folder", "path": "idle", "count": 8, "loop": True}
        }
        
        for anim_name, anim_config in animations.items():
            try:
                frames = []
                
                if anim_config["type"] == "folder":
                    # Charger des fichiers individuels depuis un dossier
                    folder_path = os.path.join(sprite_path, anim_config["path"])
                    for i in range(1, anim_config["count"] + 1):
                        filename = f"{anim_name}{i}.png"
                        full_path = os.path.join(folder_path, filename)
                        if os.path.exists(full_path):
                            frame = pygame.image.load(full_path).convert_alpha()
                            # Redimensionner la frame à 100x100 pour correspondre à la hitbox
                            frame = pygame.transform.scale(frame, (100, 100))
                            frames.append(frame)
                        else:
                            # Si le fichier n'existe pas, essayer sans le numéro d'animation
                            alt_filename = f"{anim_config['path']}{i}.png"
                            alt_full_path = os.path.join(folder_path, alt_filename)
                            if os.path.exists(alt_full_path):
                                frame = pygame.image.load(alt_full_path).convert_alpha()
                                frame = pygame.transform.scale(frame, (100, 100))  # Agrandir à 100x100
                                frames.append(frame)
                
                self.sprites[anim_name] = frames if frames else [self.create_default_sprite()]
                
            except pygame.error as e:
                print(f"Erreur lors du chargement de l'animation du prince {anim_name}: {e}")
                # Créer un sprite par défaut pour le prince
                self.sprites[anim_name] = [self.create_default_sprite()]
    
    def create_default_sprite(self):
        """Crée un sprite par défaut pour le prince"""
        default_surface = pygame.Surface((100, 100), pygame.SRCALPHA)  # Agrandir à 100x100
        # Dessiner un prince simple (rectangle doré) - proportions ajustées
        pygame.draw.rect(default_surface, (255, 215, 0), (15, 15, 70, 85))  # Corps doré plus grand
        pygame.draw.circle(default_surface, (255, 220, 177), (50, 35), 16)  # Tête plus grande
        return default_surface
    
    def update(self):
        """Met à jour l'animation du prince"""
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            if self.current_animation in self.sprites and self.sprites[self.current_animation]:
                animation_frames = self.sprites[self.current_animation]
                max_frames = len(animation_frames)
                
                # Animation en boucle
                self.animation_frame = (self.animation_frame + 1) % max_frames
    
    def draw(self, screen, camera_x, camera_y):
        """Dessine le prince avec une aura dorée"""
        # Position à l'écran
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        if self.current_animation in self.sprites and self.sprites[self.current_animation]:
            # Protection contre l'index hors limites
            max_frame = len(self.sprites[self.current_animation]) - 1
            if self.animation_frame > max_frame:
                self.animation_frame = max_frame
            
            current_sprite = self.sprites[self.current_animation][self.animation_frame]
            
            # Flip horizontal si le prince regarde à gauche
            if not self.facing_right:
                current_sprite = pygame.transform.flip(current_sprite, True, False)
            
            # Dessiner le prince directement (sans aura)
            screen.blit(current_sprite, (screen_x, screen_y))
    
    def draw_golden_aura(self, screen, screen_x, screen_y, sprite):
        """Dessine une aura dorée animée autour du prince"""
        import math
        
        # Calculer l'animation de pulsation pour les rayons seulement (pas l'intensité)
        time_factor = self.animation_timer * 0.1  # Vitesse de pulsation
        aura_intensity = 60  # Intensité constante et visible
        
        # Couleurs dorées avec transparence constante
        golden_colors = [
            (255, 215, 0, aura_intensity),    # Or pur
            (255, 223, 0, aura_intensity//2), # Or plus clair
            (255, 140, 0, aura_intensity//3)  # Or-orange
        ]
        
        # Dessiner plusieurs cercles concentriques pour créer l'effet d'aura
        center_x = screen_x + sprite.get_width() // 2
        center_y = screen_y + sprite.get_height() // 2
        
        for i, color in enumerate(golden_colors):
            # Rayon qui pulse légèrement (animation douce)
            base_radius = 45 + i * 8
            radius_variation = int(3 * math.sin(time_factor + i))  # Pulsation plus douce
            radius = base_radius + radius_variation
            
            # Créer une surface temporaire pour dessiner l'aura avec transparence
            aura_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            
            # Dessiner le cercle doré avec dégradé
            for r in range(radius, 0, -2):
                alpha = int(color[3] * (radius - r) / radius)
                if alpha > 0:
                    pygame.draw.circle(aura_surface, (*color[:3], alpha), 
                                     (radius, radius), r)
            
            # Positionner l'aura centrée sur le prince
            aura_rect = aura_surface.get_rect(center=(center_x, center_y))
            screen.blit(aura_surface, aura_rect, special_flags=pygame.BLEND_ALPHA_SDL2)

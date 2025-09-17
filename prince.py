import pygame
import os

class Prince:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 75, 75)  # Même taille que le joueur
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
                            # Redimensionner la frame à 75x75 
                            frame = pygame.transform.scale(frame, (75, 75))
                            frames.append(frame)
                        else:
                            # Si le fichier n'existe pas, essayer sans le numéro d'animation
                            alt_filename = f"{anim_config['path']}{i}.png"
                            alt_full_path = os.path.join(folder_path, alt_filename)
                            if os.path.exists(alt_full_path):
                                frame = pygame.image.load(alt_full_path).convert_alpha()
                                frame = pygame.transform.scale(frame, (75, 75))
                                frames.append(frame)
                
                self.sprites[anim_name] = frames if frames else [self.create_default_sprite()]
                
            except pygame.error as e:
                print(f"Erreur lors du chargement de l'animation du prince {anim_name}: {e}")
                # Créer un sprite par défaut pour le prince
                self.sprites[anim_name] = [self.create_default_sprite()]
    
    def create_default_sprite(self):
        """Crée un sprite par défaut pour le prince"""
        default_surface = pygame.Surface((75, 75), pygame.SRCALPHA)
        # Dessiner un prince simple (rectangle doré)
        pygame.draw.rect(default_surface, (255, 215, 0), (10, 10, 55, 65))  # Corps doré
        pygame.draw.circle(default_surface, (255, 220, 177), (37, 25), 12)  # Tête
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
        """Dessine le prince"""
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
            
            screen.blit(current_sprite, (screen_x, screen_y))

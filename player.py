import pygame
import os

class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 75, 75)  # Taille du joueur ajustée pour scale 2.34 (75x75)
        self.speed = 5
        self.jump_speed = -15
        self.gravity = 0.8
        self.velocity_y = 0
        self.on_ground = False
        self.facing_right = True
        
        # Animation
        self.animation_timer = 0
        self.animation_speed = 6  # Plus rapide pour les animations individuelles du prince
        self.current_animation = "idle"
        self.animation_frame = 0
        self.animation_finished = False  # Pour les animations qui ne bouclent pas
        
        # États spéciaux
        self.is_taking_hit = False
        self.is_dead = False
        self.hit_timer = 0
        self.death_timer = 0
        
        # Système de vies pour les flèches
        self.health = 3  # 3 touches de flèches avant de mourir
        self.max_health = 3
        self.invulnerable = False  # Invulnérabilité temporaire après être touché
        self.invulnerable_timer = 0
        self.invulnerable_duration = 45  # Réduit à 0.75 seconde pour plus d'action
        
        # États de mort
        self.is_dying = False  # En train de mourir (chute)
        self.death_fall_complete = False  # Chute terminée
        self.is_alive = True  # Vivant ou mort définitivement
        
        # Chargement des sprites
        self.sprites = {}
        self.load_sprites()
        
    def load_sprites(self):
        """Charge tous les sprites du prince"""
        sprite_path = "assets/Sprites/prince/"
        
        # Chargement des différentes animations
        animations = {
            "idle": {"type": "folder", "path": "idle", "count": 8, "loop": True},
            "run": {"type": "folder", "path": "run", "count": 8, "loop": True},
            "jump": {"type": "folder", "path": "jump", "count": 2, "loop": False},
            "fall": {"type": "folder", "path": "fall", "count": 2, "loop": True},
            "takehit": {"type": "folder", "path": "takehit", "count": 4, "loop": False},
            "death": {"type": "folder", "path": "death", "count": 6, "loop": False}
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
                        frame = pygame.image.load(full_path).convert_alpha()
                        # Redimensionner la frame à 75x75 (ajusté pour scale 2.34)
                        frame = pygame.transform.scale(frame, (75, 75))
                        frames.append(frame)
                
                elif anim_config["type"] == "sheet":
                    # Charger depuis une sprite sheet
                    full_path = os.path.join(sprite_path, anim_config["file"])
                    sprite_sheet = pygame.image.load(full_path).convert_alpha()
                    frames = self.cut_sprite_sheet(sprite_sheet, anim_config["frames"], 1)
                
                elif anim_config["type"] == "single":
                    # Charger une seule image
                    full_path = os.path.join(sprite_path, anim_config["file"])
                    frame = pygame.image.load(full_path).convert_alpha()
                    # Redimensionner la frame à 75x75 (ajusté pour scale 2.34)
                    frame = pygame.transform.scale(frame, (75, 75))
                    frames = [frame]
                
                self.sprites[anim_name] = frames
                print(f"Animation '{anim_name}' chargée avec {len(frames)} frames")
                
            except pygame.error as e:
                print(f"Erreur lors du chargement de l'animation {anim_name}: {e}")
                # Créer un rectangle coloré par défaut
                default_surface = pygame.Surface((75, 75))  # Ajusté à 75x75
                default_surface.fill((0, 0, 255))  # Bleu pour le prince
                self.sprites[anim_name] = [default_surface]
    
    def cut_sprite_sheet(self, sprite_sheet, cols, rows):
        """Découpe une sprite sheet en frames individuelles"""
        frames = []
        frame_width = sprite_sheet.get_width() // cols
        frame_height = sprite_sheet.get_height() // rows
        
        for row in range(rows):
            for col in range(cols):
                x = col * frame_width
                y = row * frame_height
                frame = sprite_sheet.subsurface((x, y, frame_width, frame_height))
                # Redimensionner la frame à 75x75 (ajusté pour scale 2.34)
                frame = pygame.transform.scale(frame, (75, 75))
                frames.append(frame)
        
        return frames
    
    def update(self, keys, collision_tiles):
        """Met à jour le joueur"""
        # Gestion de l'invulnérabilité
        if self.invulnerable:
            self.invulnerable_timer += 1
            if self.invulnerable_timer >= self.invulnerable_duration:
                self.invulnerable = False
                self.invulnerable_timer = 0
        
        # Gestion des états spéciaux
        if self.is_dying:
            # Le joueur tombe jusqu'au sol puis reste mort
            self.velocity_y += self.gravity
            self.rect.y += self.velocity_y
            
            # Vérifier collision avec le sol
            for tile_rect in collision_tiles:
                if self.rect.colliderect(tile_rect) and self.velocity_y > 0:
                    self.rect.bottom = tile_rect.top
                    self.velocity_y = 0
                    self.on_ground = True
                    self.death_fall_complete = True
                    self.is_dead = True
                    self.is_dying = False
                    break
            
            self.update_animation()
            return  # Ne pas traiter d'autres inputs pendant la chute de mort
        
        if self.is_dead:
            self.death_timer += 1
            if self.current_animation != "death":
                self.current_animation = "death"
                self.animation_frame = 0
                self.animation_finished = False
            self.update_animation()
            return  # Ne pas traiter d'autres inputs si mort
        
        if self.is_taking_hit:
            self.hit_timer += 1
            if self.current_animation != "takehit":
                self.current_animation = "takehit"
                self.animation_frame = 0
                self.animation_finished = False
            if self.hit_timer > 30:  # 0.5 seconde à 60 FPS
                self.is_taking_hit = False
                self.hit_timer = 0
            self.update_animation()
            return  # Ne pas traiter d'autres inputs pendant hit
        
        # Mouvement horizontal
        dx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_q]:
            dx = -self.speed
            self.facing_right = False
            if self.on_ground:
                self.current_animation = "run"
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = self.speed
            self.facing_right = True
            if self.on_ground:
                self.current_animation = "run"
        else:
            if self.on_ground:
                self.current_animation = "idle"
        
        # Saut
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_z]) and self.on_ground:
            self.velocity_y = self.jump_speed
            self.on_ground = False
            self.current_animation = "jump"
            self.animation_frame = 0  # Recommencer l'animation de saut
        
        # Gravité
        self.velocity_y += self.gravity
        if self.velocity_y > 0 and not self.on_ground:
            self.current_animation = "fall"
        
        # Test pour déclencher l'animation de hit (touche H)
        if keys[pygame.K_h] and not self.is_taking_hit:
            self.take_hit()
        
        # Test pour déclencher l'animation de mort (touche K)
        if keys[pygame.K_k] and not self.is_dead:
            self.die()
        
        # Mouvement
        self.rect.x += dx
        self.rect.y += self.velocity_y
        
        # Collision avec les tiles
        self.handle_collisions(collision_tiles)
        
        # Animation
        self.update_animation()
    
    def handle_collisions(self, collision_tiles):
        """Gère les collisions avec les tiles"""
        # Collision verticale
        self.on_ground = False
        for tile_rect in collision_tiles:
            if self.rect.colliderect(tile_rect):
                if self.velocity_y > 0:  # Tombant
                    self.rect.bottom = tile_rect.top
                    self.velocity_y = 0
                    self.on_ground = True
                elif self.velocity_y < 0:  # Sautant
                    self.rect.top = tile_rect.bottom
                    self.velocity_y = 0
        
        # Limites de l'écran (ne pas sortir à gauche)
        if self.rect.left < 0:
            self.rect.left = 0
    
    def update_animation(self):
        """Met à jour l'animation"""
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            if self.current_animation in self.sprites and self.sprites[self.current_animation]:
                animation_frames = self.sprites[self.current_animation]
                max_frames = len(animation_frames)
                
                # Protection contre l'index invalide
                if self.animation_frame >= max_frames:
                    self.animation_frame = max_frames - 1
                
                # Déterminer si l'animation doit boucler
                should_loop = True
                if self.current_animation in ["takehit", "death", "jump"]:
                    should_loop = False
                
                if should_loop:
                    # Animation en boucle
                    self.animation_frame = (self.animation_frame + 1) % max_frames
                else:
                    # Animation qui ne boucle pas
                    if self.animation_frame < max_frames - 1:
                        self.animation_frame += 1
                    else:
                        self.animation_finished = True
    
    def take_hit(self):
        """Déclenche l'animation de prise de dégâts"""
        if not self.is_taking_hit and not self.is_dead:
            self.is_taking_hit = True
            self.hit_timer = 0
            self.current_animation = "takehit"
            self.animation_frame = 0
            self.animation_finished = False
    
    def take_arrow_hit(self):
        """Gère les dégâts des flèches"""
        if not self.invulnerable and not self.is_dead:
            self.health -= 1
            self.invulnerable = True
            self.invulnerable_timer = 0
            
            if self.health <= 0:
                self.die()
            else:
                self.take_hit()
            
            return True  # Indique qu'on a pris des dégâts
        return False
    
    def die(self):
        """Déclenche le processus de mort avec chute"""
        if not self.is_dead and not self.is_dying:
            self.is_dying = True
            self.is_alive = False
            self.death_timer = 0
            # Commencer par l'animation de death en tombant
            self.current_animation = "death"
            self.animation_frame = 0
            self.animation_finished = False
            # Ajouter une vélocité vers le bas si on est en l'air
            if not self.on_ground:
                self.velocity_y = max(self.velocity_y, 2)  # Force la chute
    
    def respawn(self, x, y):
        """Ressuscite le joueur à une position donnée"""
        self.is_dead = False
        self.is_taking_hit = False
        self.death_timer = 0
        self.hit_timer = 0
        self.health = self.max_health  # Restaurer la santé
        self.invulnerable = False
        self.invulnerable_timer = 0
        self.rect.x = x
        self.rect.y = y
        self.velocity_y = 0
        self.current_animation = "idle"
        self.animation_frame = 0
        self.animation_finished = False
    
    def draw(self, screen, x, y):
        """Dessine le joueur avec effet de clignotement si invulnérable"""
        if self.current_animation in self.sprites and self.sprites[self.current_animation]:
            # Protection contre l'index hors limites
            max_frame = len(self.sprites[self.current_animation]) - 1
            if self.animation_frame > max_frame:
                self.animation_frame = max_frame
            
            current_sprite = self.sprites[self.current_animation][self.animation_frame]
            
            # Flip horizontal si le joueur regarde à gauche
            if not self.facing_right:
                current_sprite = pygame.transform.flip(current_sprite, True, False)
            
            # Effet de clignotement pendant l'invulnérabilité
            if self.invulnerable:
                # Clignoter toutes les 10 frames
                if (self.invulnerable_timer // 5) % 2 == 0:
                    screen.blit(current_sprite, (x, y))
            else:
                screen.blit(current_sprite, (x, y))

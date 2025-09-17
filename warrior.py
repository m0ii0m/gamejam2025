import pygame
import os
import random

class Warrior:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 75, 75)  # Taille similaire au joueur
        self.speed = random.uniform(2, 4)  # Vitesse légèrement plus rapide que les ennemis
        self.jump_speed = -12
        self.gravity = 0.8
        self.velocity_y = 0
        self.velocity_x = 0
        self.on_ground = False
        self.facing_right = random.choice([True, False])
        
        # Animation
        self.animation_timer = 0
        self.animation_speed = random.randint(6, 10)  # Vitesse d'animation variable
        self.current_animation = "idle"
        self.animation_frame = 0
        self.animation_finished = False
        
        # États de combat - Plus résistant
        self.health = 8  # Beaucoup plus résistant
        self.max_health = 8
        self.is_attacking = False
        self.is_taking_hit = False
        self.is_dead = False
        self.attack_timer = 0
        self.hit_timer = 0
        self.death_timer = 0
        self.attack_cooldown = 0
        
        # IA comportementale - Plus statique
        self.behavior_timer = 0
        self.behavior_duration = random.randint(120, 300)  # Comportements plus longs
        self.current_behavior = "guard"  # Commence par garder sa position
        self.target = None
        self.aggro_range = 150  # Portée réduite pour être plus statique
        self.attack_range = 100  # Portée d'attaque
        
        # Chargement des sprites
        self.sprites = {}
        self.load_sprites()
        
    def load_sprites(self):
        """Charge tous les sprites du warrior"""
        sprite_path = "assets/Sprites/warrior/"
        
        animations = {
            "idle": {"path": "idle", "count": 10, "loop": True},
            "run": {"path": "run", "count": 8, "loop": True},
            "jump": {"path": "jump", "count": 2, "loop": False},
            "fall": {"path": "fall", "count": 2, "loop": True},
            "hit": {"path": "hit", "count": 3, "loop": False},
            "death": {"path": "death", "count": 10, "loop": False},
            "attack1": {"path": "attack1", "count": 4, "loop": False},
            "attack2": {"path": "attack2", "count": 4, "loop": False}
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
                
                if self.sprites[anim_name]:
                    print(f"Animation warrior '{anim_name}' chargée avec {len(self.sprites[anim_name])} frames")
                else:
                    print(f"Aucune image trouvée pour l'animation warrior '{anim_name}'")
                    
    def update(self, collision_tiles, allies, enemies):
        """Met à jour le warrior avec IA automatique"""
        if self.is_dead:
            self.death_timer += 1
            self.update_animation()
            return
            
        if self.is_taking_hit:
            self.hit_timer += 1
            if self.hit_timer > 30:
                self.is_taking_hit = False
                self.hit_timer = 0
            self.update_animation()
            return
            
        if self.is_attacking:
            self.attack_timer += 1
            if self.attack_timer > 35:  # Attaque légèrement plus rapide que les ennemis
                self.is_attacking = False
                self.attack_timer = 0
                self.attack_cooldown = 30  # Cooldown plus court pour plus d'action
            self.update_animation()
            return
        
        # Réduire le cooldown d'attaque
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
            
        # IA comportementale
        self.update_ai(allies, enemies)
        
        # Physique
        self.velocity_y += self.gravity
        self.rect.x += self.velocity_x
        self.rect.y += self.velocity_y
        
        # Collision avec les tiles
        self.handle_collisions(collision_tiles)
        
        # Animation
        self.update_animation()
        
    def update_ai(self, allies, enemies):
        """IA simple pour le warrior - cible les ennemis"""
        self.behavior_timer += 1
        
        # Chercher des cibles (ennemis) à proximité
        closest_enemy = None
        closest_distance = float('inf')
        
        for enemy in enemies:
            if not enemy.is_dead:
                distance = abs(enemy.rect.centerx - self.rect.centerx)
                if distance < self.aggro_range and distance < closest_distance:
                    closest_enemy = enemy
                    closest_distance = distance
        
        # Comportement basé sur la proximité des ennemis
        if closest_enemy and closest_distance < self.attack_range and self.attack_cooldown == 0:
            # Attaquer
            self.attack(closest_enemy)
        elif closest_enemy and closest_distance < self.aggro_range:
            # Poursuivre
            self.chase_target(closest_enemy)
        else:
            # Comportement aléatoire
            if self.behavior_timer >= self.behavior_duration:
                self.change_behavior()
                
    def chase_target(self, target):
        """Poursuit une cible"""
        if target.rect.centerx < self.rect.centerx:
            self.velocity_x = -self.speed
            self.facing_right = False
            self.current_animation = "run"
        elif target.rect.centerx > self.rect.centerx:
            self.velocity_x = self.speed
            self.facing_right = True
            self.current_animation = "run"
        else:
            self.velocity_x = 0
            self.current_animation = "idle"
            
    def attack(self, target):
        """Attaque une cible"""
        if not self.is_attacking:
            self.is_attacking = True
            self.attack_timer = 0
            self.current_animation = random.choice(["attack1", "attack2"])
            self.animation_frame = 0
            self.animation_finished = False
            self.velocity_x = 0
            
            # Infliger des dégâts à la cible si elle est assez proche
            if abs(target.rect.centerx - self.rect.centerx) < self.attack_range:
                target.take_damage()
            
    def change_behavior(self):
        """Change le comportement aléatoirement - Plus statique"""
        behaviors = ["guard", "idle", "patrol"]  # Comportements plus statiques
        self.current_behavior = random.choice(behaviors)
        self.behavior_timer = 0
        self.behavior_duration = random.randint(120, 300)  # Plus long
        
        if self.current_behavior == "guard":
            self.velocity_x = 0
            self.current_animation = "idle"
        elif self.current_behavior == "idle":
            self.velocity_x = 0
            self.current_animation = "idle"
        elif self.current_behavior == "patrol":
            # Mouvement de patrouille très lent
            if random.choice([True, False]):
                self.velocity_x = self.speed * 0.2
                self.facing_right = True
            else:
                self.velocity_x = -self.speed * 0.2
                self.facing_right = False
            self.current_animation = "run"
            
    def take_damage(self):
        """Reçoit des dégâts"""
        if not self.is_taking_hit and not self.is_dead:
            self.health -= 1
            if self.health <= 0:
                self.die()
            else:
                self.is_taking_hit = True
                self.hit_timer = 0
                self.current_animation = "hit"
                self.animation_frame = 0
                self.animation_finished = False
                
    def die(self):
        """Meurt"""
        if not self.is_dead:
            self.is_dead = True
            self.death_timer = 0
            self.current_animation = "death"
            self.animation_frame = 0
            self.animation_finished = False
            self.velocity_x = 0
            
    def handle_collisions(self, collision_tiles):
        """Gère les collisions avec les tiles"""
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
                if self.current_animation in ["hit", "death", "attack1", "attack2"]:
                    should_loop = False
                
                if should_loop:
                    self.animation_frame = (self.animation_frame + 1) % max_frames
                else:
                    if self.animation_frame < max_frames - 1:
                        self.animation_frame += 1
                    else:
                        self.animation_finished = True
                        
    def draw(self, screen, camera_x, camera_y):
        """Dessine le warrior"""
        if self.current_animation in self.sprites and self.sprites[self.current_animation]:
            animation_frames = self.sprites[self.current_animation]
            max_frame = len(animation_frames) - 1
            if self.animation_frame > max_frame:
                self.animation_frame = max_frame
                
            current_sprite = animation_frames[self.animation_frame]
            
            # Inverser l'image si nécessaire
            if not self.facing_right:
                current_sprite = pygame.transform.flip(current_sprite, True, False)
            
            # Position à l'écran
            screen_x = self.rect.x - camera_x
            screen_y = self.rect.y - camera_y
            
            screen.blit(current_sprite, (screen_x, screen_y))

import pygame
import os
import random

class Enemy:
    def __init__(self, x, y, team="red"):
        self.rect = pygame.Rect(x, y, 75, 75)  # Taille similaire au joueur
        self.speed = random.uniform(1, 3)  # Vitesse variable
        self.jump_speed = -12
        self.gravity = 0.8
        self.velocity_y = 0
        self.velocity_x = 0
        self.on_ground = False
        self.facing_right = random.choice([True, False])
        
        # Équipe et couleur
        self.team = team
        if team == "red":
            self.color_filter = (255, 150, 150)  # Teinte rouge
        else:  # blue
            self.color_filter = (150, 150, 255)  # Teinte bleue
        
        # PERMETTRE TRAVERSÉE ENTRE ENNEMIS - Plus petite hitbox pour éviter blocages
        self.collision_rect = pygame.Rect(x + 15, y + 15, 45, 60)  # Hitbox réduite
        
        # Animation
        self.animation_timer = 0
        self.animation_speed = random.randint(6, 10)  # Vitesse d'animation variable
        self.current_animation = "idle"
        self.animation_frame = 0
        self.animation_finished = False
        
        # États de combat - Plus résistant
        self.health = 6  # Plus résistant
        self.max_health = 6
        self.is_attacking = False
        self.is_taking_hit = False
        self.is_dead = False
        self.attack_timer = 0
        self.hit_timer = 0
        self.death_timer = 0
        self.attack_cooldown = 0
        
        # IA comportementale - COOLDOWN DE 5 SECONDES ENTRE ACTIONS
        self.behavior_timer = 0
        self.behavior_duration = random.randint(300, 600)  # 5-10 secondes à 60 FPS
        self.current_behavior = "guard"  # Commence par garder sa position
        self.target = None
        self.aggro_range = 120  # Portée réduite
        self.attack_range = 90   # Portée d'attaque
        
        # COOLDOWN GLOBAL POUR ACTIONS (5 secondes = 300 frames)
        self.action_cooldown = 0  # Timer pour empêcher actions fréquentes
        self.action_cooldown_duration = 120  # 2 secondes à 60 FPS
        
        # Chargement des sprites
        self.sprites = {}
        self.load_sprites()
        
    def load_sprites(self):
        """Charge tous les sprites de l'ennemi"""
        sprite_path = "assets/Sprites/ennemy/"
        
        animations = {
            "idle": {"path": "idle", "count": 4, "loop": True},
            "run": {"path": "run", "count": 8, "loop": True},
            "jump": {"path": "jump", "count": 2, "loop": False},
            "fall": {"path": "fall", "count": 2, "loop": True},
            "hit": {"path": "hit", "count": 4, "loop": False},
            "death": {"path": "death", "count": 4, "loop": False},
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
                    
    def update(self, collision_tiles, enemy_targets, ally_enemies, player=None):
        """Met à jour l'ennemi avec IA automatique"""
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
            if self.attack_timer > 40:
                self.is_attacking = False
                self.attack_timer = 0
                self.attack_cooldown = 40  # Cooldown réduit pour plus d'action
            self.update_animation()
            return
        
        # Réduire le cooldown d'attaque
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
            
        # Réduire le cooldown d'action globale
        if self.action_cooldown > 0:
            self.action_cooldown -= 1
            
        # IA comportementale - SEULEMENT SI PAS EN COOLDOWN
        if self.action_cooldown == 0:
            self.update_ai(enemy_targets, ally_enemies)
        else:
            # En cooldown : rester complètement immobile et idle
            self.velocity_x = 0
            if self.current_animation not in ["attack1", "attack2", "hit", "death"]:
                self.current_animation = "idle"
        
        # Physique
        self.velocity_y += self.gravity
        
        # Appliquer une friction pour éviter le glissement SEULEMENT SI PAS EN COOLDOWN
        if self.on_ground and not self.is_attacking:
            if self.action_cooldown > 0:
                # En cooldown : arrêt complet
                self.velocity_x = 0
            else:
                # Friction normale
                self.velocity_x *= 0.85
        
        self.rect.x += self.velocity_x
        self.rect.y += self.velocity_y
        
        # Mettre à jour la hitbox de collision réduite
        self.collision_rect.centerx = self.rect.centerx
        self.collision_rect.centery = self.rect.centery + 10
        
        # Collision avec les tiles
        self.handle_collisions(collision_tiles)
        
        # Animation
        self.update_animation()
        
    def update_ai(self, enemy_targets, ally_enemies):
        """IA simple pour l'ennemi - cible seulement les ennemis de l'équipe adverse"""
        self.behavior_timer += 1
        
        # Chercher des cibles (ennemis de l'équipe adverse) à proximité
        closest_target = None
        closest_distance = float('inf')
        
        # Vérifier les ennemis de l'équipe adverse
        for enemy in enemy_targets:
            if not enemy.is_dead:
                distance = abs(enemy.rect.centerx - self.rect.centerx)
                if distance < self.aggro_range and distance < closest_distance:
                    closest_target = enemy
                    closest_distance = distance
        
        # PAS DE CIBLAGE DU JOUEUR - Seuls les ennemis adverses sont ciblés
        
        # Vérifier s'il y a des alliés qui bloquent le chemin - ÉVITER LES BLOCAGES
        blocked_by_ally = False
        if closest_target:
            for ally in ally_enemies:
                if ally != self and not ally.is_dead:
                    # Si un allié est entre nous et la cible
                    ally_distance = abs(ally.rect.centerx - self.rect.centerx)
                    if ally_distance < 50:  # Très proche
                        target_direction = 1 if closest_target.rect.centerx > self.rect.centerx else -1
                        ally_direction = 1 if ally.rect.centerx > self.rect.centerx else -1
                        if target_direction == ally_direction:
                            blocked_by_ally = True
                            break
        
        # Comportement basé sur la proximité des cibles
        if closest_target and closest_distance < self.attack_range and self.attack_cooldown == 0 and not blocked_by_ally:
            # Attaquer
            self.attack(closest_target)
        elif closest_target and closest_distance < self.aggro_range and not blocked_by_ally:
            # Poursuivre
            self.chase_target(closest_target)
        elif blocked_by_ally:
            # Éviter le blocage - seulement si pas en cooldown
            if self.action_cooldown == 0:
                if random.choice([True, False]):
                    self.velocity_x = random.choice([-1, 1]) * self.speed * 0.5
                    self.current_animation = "run"
                    # DÉCLENCHER COOLDOWN APRÈS MOUVEMENT D'ÉVITEMENT
                    self.action_cooldown = self.action_cooldown_duration
                else:
                    self.velocity_x = 0
                    self.current_animation = "idle"
            else:
                # En cooldown : rester immobile
                self.velocity_x = 0
                self.current_animation = "idle"
        else:
            # Comportement aléatoire - SEULEMENT SI TEMPS ÉCOULÉ
            if self.behavior_timer >= self.behavior_duration:
                self.change_behavior()
                
    def chase_target(self, target):
        """Poursuit une cible"""
        if target.rect.centerx < self.rect.centerx:
            self.velocity_x = -self.speed * 1.5  # Vitesse de poursuite plus rapide
            self.facing_right = False
            self.current_animation = "run"
        elif target.rect.centerx > self.rect.centerx:
            self.velocity_x = self.speed * 1.5   # Vitesse de poursuite plus rapide
            self.facing_right = True
            self.current_animation = "run"
        else:
            self.velocity_x = 0
            self.current_animation = "idle"
        
        # DÉCLENCHER COOLDOWN DE 5 SECONDES APRÈS POURSUITE
        self.action_cooldown = self.action_cooldown_duration
            
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
                if hasattr(target, 'take_damage'):
                    target.take_damage()
                # PAS D'ATTAQUE DU JOUEUR - Les ennemis ne peuvent plus toucher le joueur
            
            # DÉCLENCHER COOLDOWN DE 5 SECONDES APRÈS ATTAQUE
            self.action_cooldown = self.action_cooldown_duration
            
    def change_behavior(self):
        """Change le comportement aléatoirement - Plus calme avec longues pauses"""
        behaviors = ["guard", "idle", "patrol"]  # Comportements plus statiques
        self.current_behavior = random.choice(behaviors)
        self.behavior_timer = 0
        self.behavior_duration = random.randint(300, 600)  # 5-10 secondes entre actions
        
        if self.current_behavior == "guard":
            self.velocity_x = 0
            self.current_animation = "idle"
        elif self.current_behavior == "idle":
            self.velocity_x = 0
            self.current_animation = "idle"
        elif self.current_behavior == "patrol":
            # Mouvement de patrouille très lent
            if random.choice([True, False]):
                self.velocity_x = self.speed * 0.3  # Encore plus lent
                self.facing_right = True
            else:
                self.velocity_x = -self.speed * 0.3  # Encore plus lent
                self.facing_right = False
            self.current_animation = "run"
            
        # DÉCLENCHER COOLDOWN DE 5 SECONDES APRÈS CHANGEMENT COMPORTEMENT
        self.action_cooldown = self.action_cooldown_duration
            
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
                    self.rect.y += 5  # BAISSER 5PX APRÈS COLLISION (réduit de 25px à 5px)
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
        """Dessine l'ennemi avec filtre de couleur selon l'équipe"""
        if self.current_animation in self.sprites and self.sprites[self.current_animation]:
            animation_frames = self.sprites[self.current_animation]
            max_frame = len(animation_frames) - 1
            if self.animation_frame > max_frame:
                self.animation_frame = max_frame
                
            current_sprite = animation_frames[self.animation_frame].copy()
            
            # Appliquer le filtre de couleur selon l'équipe
            color_surface = pygame.Surface(current_sprite.get_size())
            color_surface.fill(self.color_filter)
            current_sprite.blit(color_surface, (0, 0), special_flags=pygame.BLEND_MULT)
            
            # Inverser l'image si nécessaire
            if not self.facing_right:
                current_sprite = pygame.transform.flip(current_sprite, True, False)
            
            # Position à l'écran
            screen_x = self.rect.x - camera_x
            screen_y = self.rect.y - camera_y
            
            screen.blit(current_sprite, (screen_x, screen_y))
import pygame
import random
from enemy import Enemy
from arrow import Arrow

class ProtectorSoldier:
    """Soldat bleu (enemy) qui protège le prince en bloquant les flèches"""
    def __init__(self, x, y):
        # Créer un enemy bleu
        self.enemy = Enemy(x, y, team="blue")
        self.rect = self.enemy.rect
        self.speed = 4
        self.is_dead = False
        self.death_timer = 0
        self.target_x = 70 * 16 * 2.5  # Tile 70 en pixels (plus loin à droite que tile 62)
        
        # Synchroniser les positions
        self.enemy.rect.x = x
        self.enemy.rect.y = y

    def update(self):
        if not self.is_dead:
            # Courir vers la tile 70
            if self.rect.x < self.target_x:
                self.rect.x += self.speed
                # Synchroniser la position de l'enemy
                self.enemy.rect.x = self.rect.x
                self.enemy.rect.y = self.rect.y
                # Forcer l'animation de course
                self.enemy.current_animation = "run"
                self.enemy.facing_right = True
            else:
                # Il a atteint sa destination, rester immobile
                self.enemy.current_animation = "idle"
            
            # Mettre à jour l'animation de l'enemy
            self.enemy.update_animation()
        else:
            # Soldat mort : rester en place et continuer l'animation de mort
            self.death_timer += 1
            # Continuer l'animation de mort
            self.enemy.update_animation()
            
    def take_arrow_hit(self):
        """Le soldat se prend une flèche et meurt, bloquant la flèche"""
        if not self.is_dead:
            self.is_dead = True
            self.death_timer = 0
            # Déclencher l'animation de mort et arrêter le mouvement
            self.enemy.current_animation = "death"
            self.enemy.animation_frame = 0
            self.enemy.is_dying = True
            print("Un soldat protecteur a bloqué une flèche !")
            return True  # Flèche bloquée
        return False
    
    def draw(self, screen, camera_x, camera_y):
        # Utiliser le système de rendu de l'enemy
        # Les corps restent visibles indéfiniment - pas de condition sur death_timer
        screen_x = self.rect.x - camera_x
        screen_y = self.rect.y - camera_y
        
        # Fallback si l'enemy ne se dessine pas correctement
        try:
            self.enemy.draw(screen, camera_x, camera_y)
        except:
            # Dessiner un rectangle bleu en fallback
            color = (150, 150, 150) if self.is_dead else (100, 100, 255)
            pygame.draw.rect(screen, color, (screen_x, screen_y, 48, 64))

class PrinceProtectionManager:
    """Gestionnaire du mini-niveau de protection du prince"""
    def __init__(self, prince_x, prince_y, castle_door_x):
        self.prince_x = prince_x
        # Utiliser la même position Y que les ennemis pour une cohérence visuelle
        ground_level = 655  # Même valeur que battlefield_manager
        self.prince_y = ground_level - 100 + 2  # Même logique que game.py : comme les ennemis mais 2px plus bas
        self.castle_door_x = castle_door_x
        
        # États du mini-niveau
        self.state = "waiting"  # "waiting", "cinematic_slowdown", "player_death", "pause_after_death", "zooming_out", "protection", "zoom_on_prince", "dezoom_reveal_enemies", "final_sequence"
        self.state_timer = 0
        
        # Gestion du zoom sur le prince
        self.zoom_start_tile = 54  # Tile où commence le zoom (plus tôt)
        self.zoom_end_tile = 70   # Tile où se termine le zoom
        self.zoom_factor = 1.0    # Facteur de zoom actuel (1.0 = normal, 2.0 = zoomé x2)
        self.max_zoom_factor = 2.5  # Zoom maximum
        
        # Effet de fade
        self.fade_alpha = 0  # Pour le fade vers l'écran noir
        self.fade_speed = 3  # Vitesse du fade
        
        # Position du messager mort (sauvegardée pour le zoom)
        self.dead_messenger_x = 0
        self.dead_messenger_y = 0
        
        # Cinématique d'avancement du messager
        self.cinematic_start_x = 0  # Position de départ du messager
        self.cinematic_target_distance = 4 * 16 * 2.5  # 4 tiles en pixels
        self.cinematic_distance_covered = 0
        
        # Tile de zoom sur le prince
        self.zoom_tile = 56
        
        # Position actuelle du prince (il bougera vers la droite)
        self.current_prince_x = prince_x
        self.prince_base_speed = 1.5  # Plus rapide (était 0.5)
        self.prince_speed_variation = 0
        self.prince_speed_timer = 0
        
        # Animation du prince
        self.prince_animation_frame = 0
        self.prince_animation_timer = 0
        self.prince_animation_speed = 8
        
        # Santé du prince (invincible mais barre de vie qui descend)
        self.prince_health = 100
        self.prince_max_health = 100
        self.prince_invulnerable = False
        self.prince_invulnerable_timer = 0
        self.prince_invulnerable_duration = 60  # 1 seconde
        
        # Gestion du zoom
        self.target_zoom_tile = 62  # Tile 62 doit être visible à droite
        self.zoom_complete = False
        
        # Flèches qui visent le prince
        self.protection_arrows = []
        self.arrow_spawn_timer = 0
        self.arrow_spawn_interval = random.randint(30, 120)  # Intervalle réduit : 0.5 à 2 secondes (était 1-5s)
        
        # Soldats protecteurs
        self.protector_soldiers = []
        
        # Ennemis pour la séquence finale
        self.final_enemies = []
        self.enemy_fall_timer = 0
        self.enemy_fall_interval = 30  # 0.5 secondes entre chaque chute
        self.simultaneous_death_triggered = False  # Flag pour la mort simultanée
        
        # Sprites du prince
        self.prince_sprites = self.load_prince_sprites()
        
    def load_prince_sprites(self):
        """Charge les sprites du prince pour l'animation de course"""
        try:
            sprites = []
            sprite_path = "assets/Sprites/prince/"
            
            # Charger les 8 frames de course
            for i in range(1, 9):
                filename = f"run{i}.png"
                full_path = sprite_path + "run/" + filename
                sprite = pygame.image.load(full_path).convert_alpha()
                # Redimensionner pour correspondre à la taille du prince
                sprite = pygame.transform.scale(sprite, (48, 64))
                sprites.append(sprite)
                
            return sprites
        except pygame.error as e:
            print(f"Erreur lors du chargement des sprites du prince: {e}")
            # Créer un sprite par défaut
            default_sprite = pygame.Surface((48, 64))
            default_sprite.fill((255, 215, 0))  # Or
            return [default_sprite] * 8
        
    def is_player_near_prince(self, player_x):
        """Vérifie si le joueur est à 5 tiles du prince pour déclencher la cinématique"""
        tile_size = 16 * 2.5  # 40 pixels par tile
        distance_threshold = 5 * tile_size  # 5 tiles
        return abs(player_x - self.prince_x) <= distance_threshold
        
    def start_sequence(self, player_x):
        """Démarre la séquence quand le joueur est à 5 tiles du prince"""
        print("Cinématique démarrée : Le messager avance automatiquement de 4 tiles en ralentissant !")
        self.state = "cinematic_slowdown"
        self.state_timer = 0
        self.cinematic_start_x = player_x
        self.cinematic_distance_covered = 0
        
    def update(self, player_manager, arrow_manager, collision_tiles=None, keys=None):
        """Met à jour le mini-niveau"""
        self.state_timer += 1
        
        if self.state == "cinematic_slowdown":
            # Phase d'avancement automatique du messager avec ralentissement vers la gauche
            current_player = player_manager.get_current_player()
            
            # Calculer la vitesse basée sur la distance parcourue (ralentissement progressif)
            progress_ratio = self.cinematic_distance_covered / self.cinematic_target_distance
            # Vitesse qui diminue de 3 à 0.5 pixels/frame
            current_speed = 3.0 * (1.0 - progress_ratio * 0.8)  # Garde une vitesse minimum
            
            # Faire avancer le joueur automatiquement vers la GAUCHE
            current_player.rect.x -= current_speed  # Moins pour aller à gauche
            self.cinematic_distance_covered += current_speed
            
            # Forcer l'animation de course tant qu'il bouge
            if current_speed > 1.0:
                current_player.current_animation = "run"
            else:
                current_player.current_animation = "idle"
            
            current_player.facing_right = False  # Vers la gauche
            
            # Arrêter après 4 tiles et faire mourir le messager
            if self.cinematic_distance_covered >= self.cinematic_target_distance:
                print("Le messager a parcouru 4 tiles vers la gauche et s'effondre !")
                # Sauvegarder la position du messager mort pour le zoom
                self.dead_messenger_x = current_player.rect.x
                self.dead_messenger_y = current_player.rect.y
                current_player.die()
                self.state = "player_death"
                self.state_timer = 0
                
        elif self.state == "player_death":
            # Attendre que le joueur soit complètement mort
            current_player = player_manager.get_current_player()
            
            if current_player.is_dead or self.state_timer >= 180:  # 3 secondes max
                print("Le messager est mort, pause de 2 secondes...")
                self.state = "pause_after_death"
                self.state_timer = 0
                
        elif self.state == "pause_after_death":
            # Pause de 2 secondes après la mort du messager
            if self.state_timer >= 120:  # 2 secondes à 60 FPS
                print("Fin de la pause, le prince commence à marcher !")
                self.state = "zooming_out"
                self.state_timer = 0
                
        elif self.state == "zooming_out":
            # Phase de dézoomer (gérée dans game.py)
            # Faire commencer le prince à marcher pendant le panning
            if self.current_prince_x < self.castle_door_x:
                current_speed = max(0.1, self.prince_base_speed + 0.2)  # Vitesse fixe pendant le panning
                self.current_prince_x += current_speed
                
            # Mise à jour de l'animation du prince pendant le panning
            self.prince_animation_timer += 1
            if self.prince_animation_timer >= self.prince_animation_speed:
                self.prince_animation_timer = 0
                self.prince_animation_frame = (self.prince_animation_frame + 1) % 8  # 8 frames de course
                
            if self.zoom_complete:
                print("Dézoomer terminé, début de la protection du prince !")
                self.state = "protection"
                self.state_timer = 0
                self.setup_protection_phase()
                
        elif self.state == "protection":
            level_complete = self.update_protection_phase(collision_tiles, keys)
            if level_complete:
                return True
                
        elif self.state == "zoom_on_prince":
            # Phase de zoom sur le prince (tile 54 à 70)
            prince_tile = self.current_prince_x / (16 * 2.5)
            
            # Faire avancer le prince jusqu'à la tile 70
            if prince_tile < self.zoom_end_tile:
                current_speed = max(0.1, self.prince_base_speed)
                self.current_prince_x += current_speed
                
                # Mise à jour de l'animation du prince (course)
                self.prince_animation_timer += 1
                if self.prince_animation_timer >= self.prince_animation_speed:
                    self.prince_animation_timer = 0
                    self.prince_animation_frame = (self.prince_animation_frame + 1) % 8
            else:
                # Le prince a atteint la tile 70, il s'arrête et se met en idle
                self.prince_animation_timer = 0
                self.prince_animation_frame = 0  # Frame idle
                
            # Calculer le zoom basé sur la position du prince
            if prince_tile >= self.zoom_start_tile and prince_tile <= self.zoom_end_tile:
                # Zoom progressif de 1.0 à max_zoom_factor
                zoom_progress = (prince_tile - self.zoom_start_tile) / (self.zoom_end_tile - self.zoom_start_tile)
                self.zoom_factor = 1.0 + (self.max_zoom_factor - 1.0) * zoom_progress
                
            # Quand le prince atteint la tile 70, attendre 1 seconde puis dézoomer
            if prince_tile >= self.zoom_end_tile and self.state_timer >= 60:  # 1 seconde à 60 FPS
                print("Prince à la tile 70, pause terminée, dézoom et révélation des ennemis !")
                self.state = "dezoom_reveal_enemies"
                self.state_timer = 0
                self.setup_final_sequence()  # Créer les ennemis pendant le dézoom
                
        elif self.state == "dezoom_reveal_enemies":
            # Dézoom progressif symétrique au zoom (de tile 70 à 54)
            if self.state_timer == 1:  # Premier frame
                # Forcer le prince en animation idle
                self.prince_animation_timer = 0
                self.prince_animation_frame = 0
                # Commencer le nettoyage progressif du battlefield
                self.cleanup_battlefield()
                print("Début du dézoom progressif, nettoyage progressif commencé, ennemis créés !")
            
            # Continuer le nettoyage progressif si nécessaire
            self.continue_cleanup_battlefield()
            
            # Calculer le dézoom symétrique (mais plus rapide)
            # Distance de dézoom : de tile 70 à tile 54 (16 tiles de distance)
            zoom_distance = self.zoom_end_tile - self.zoom_start_tile  # 16 tiles
            frames_for_zoom = (zoom_distance / self.prince_base_speed * (16 * 2.5)) / 2  # 2x plus rapide
            
            if self.state_timer <= frames_for_zoom:
                # Dézoom progressif rapide
                dezoom_progress = self.state_timer / frames_for_zoom
                self.zoom_factor = self.max_zoom_factor - (self.max_zoom_factor - 1.0) * dezoom_progress
            else:
                # Dézoom terminé
                self.zoom_factor = 1.0
            
            # Pendant le dézoom : les ennemis attaquent puis meurent automatiquement après 3 secondes
            if self.state_timer >= 30:  # Commencer l'attaque 0.5s après le début du dézoom
                # Calculer le temps écoulé depuis la création des ennemis
                time_since_creation = self.state_timer - self.final_enemies_creation_time
                
                # Phase 1 : Les soldats se ruent vers le prince pendant 3 secondes
                if time_since_creation < 180:  # Pendant 3 secondes (180 frames)
                    for enemy in self.final_enemies:
                        if not enemy.is_dead:
                            # Faire avancer les soldats vers le prince (position fixe)
                            dx = self.current_prince_x - enemy.rect.x
                            dy = self.prince_y - enemy.rect.y  # Viser la position du prince directement
                            distance = (dx**2 + dy**2)**0.5
                            
                            if distance > 50:  # S'arrêter près du prince
                                enemy.rect.x += dx / distance * 3  # Vitesse 3
                                enemy.rect.y += dy / distance * 3
                                enemy.current_animation = "run"
                
                # Phase 2 : Tous les soldats meurent d'un coup simultanément après exactement 3 secondes (Plot Armor du prince)
                elif time_since_creation == 180:  # Exactement 3 secondes après création
                    print("PLOT ARMOR ACTIVÉ ! Tous les soldats meurent simultanément après 3 secondes !")
                    # Marquer le moment de mort simultanée
                    self.simultaneous_death_triggered = True
                    self.simultaneous_death_start_time = self.state_timer
                    
                    for enemy in self.final_enemies:
                        if not enemy.is_dead:
                            # Forcer la mort complète simultanée de tous les ennemis
                            enemy.is_dead = True
                            enemy.health = 0
                            enemy.death_timer = 0  # Même timer pour tous
                            enemy.current_animation = "death"
                            enemy.animation_frame = 0  # Même frame pour tous
                            enemy.animation_finished = False
                            enemy.velocity_x = 0
                            enemy.velocity_y = 0
                            # S'assurer que l'ennemi ne peut plus attaquer
                            enemy.is_attacking = False
                            enemy.attack_timer = 0
                            # Réinitialiser le timer d'animation pour synchroniser
                            enemy.animation_timer = 0
                    
                    print(f"Tous les {len([e for e in self.final_enemies if e.is_dead])} ennemis sont morts simultanément après 3 secondes !")
                
                # Mise à jour des animations des ennemis (synchronisées pour la mort simultanée)
                for enemy in self.final_enemies:
                    if enemy.is_dead:
                        # Mettre à jour le timer de mort de façon synchronisée
                        if hasattr(self, 'simultaneous_death_triggered') and self.simultaneous_death_triggered:
                            # Synchroniser les timers de mort pour tous les ennemis
                            enemy.death_timer = self.state_timer - self.simultaneous_death_start_time
                            # Forcer la mise à jour synchrone de l'animation de mort
                            if enemy.current_animation == "death":
                                # Calculer la frame d'animation basée sur le temps écoulé depuis la mort
                                time_since_death = enemy.death_timer
                                animation_speed = enemy.animation_speed
                                frame_progress = time_since_death // animation_speed
                                max_frames = len(enemy.sprites["death"]) if "death" in enemy.sprites else 4
                                enemy.animation_frame = min(frame_progress, max_frames - 1)
                        else:
                            enemy.death_timer += 1
                    
                    # Mettre à jour l'animation pour tous les ennemis
                    enemy.update_animation()
                
            if self.state_timer >= frames_for_zoom + 180:  # Attendre 3 secondes après le dézoom
                print("Dézoom et séquence finale terminés ! Victoire du prince !")
                return True  # Mini-niveau terminé
                
        elif self.state == "final_sequence":
            level_complete = self.update_final_sequence()
            if level_complete:
                return True
            
    def create_killing_arrow(self, player, arrow_manager):
        """Crée une flèche qui va viser le joueur depuis la tile 62"""
        # Position depuis la tile 62
        tile_62_x = 62 * 16 * 2.5  # Tile 62 en pixels
        arrow_x = tile_62_x
        arrow_y = 20 * 16 * 2.5  # Même hauteur que le joueur
        
        # Créer une flèche dirigée vers le joueur avec une vitesse plus lente mais sûre
        killing_arrow = Arrow(arrow_x, arrow_y, player.rect.centerx, player.rect.centery, "normal")
        killing_arrow.speed = 4  # Vitesse normale pour être visible
        killing_arrow.max_range = 2000  # Portée augmentée pour être sûr d'atteindre
        arrow_manager.arrows.append(killing_arrow)
        print(f"Flèche tueuse créée depuis tile 62 (x={arrow_x}) vers joueur (x={player.rect.centerx})")
        
    def setup_protection_phase(self):
        """Configure la phase de protection"""
        # Ne créer des ennemis que pour la séquence finale - ils seront créés plus tard
        pass
            
    def update_protection_phase(self, collision_tiles=None, keys=None):
        """Met à jour la phase de protection simplifiée"""
        # Spawner un soldat protecteur quand on appuie sur espace
        if keys and keys[pygame.K_SPACE]:
            # Éviter de spawner trop de soldats d'un coup
            if not hasattr(self, 'space_was_pressed') or not self.space_was_pressed:
                self.spawn_protector_soldier()
            self.space_was_pressed = True
        else:
            self.space_was_pressed = False
            
        # Mettre à jour les soldats protecteurs
        for soldier in self.protector_soldiers[:]:
            soldier.update()
            # Les corps ne disparaissent jamais - commenté pour garder les corps
            # if soldier.is_dead and soldier.death_timer > 300:  # 5 secondes au lieu de 2
            #     self.protector_soldiers.remove(soldier)
        # Faire avancer le prince vers la porte avec vitesse variable
        if self.current_prince_x < self.castle_door_x:
            # Variation de vitesse périodique
            self.prince_speed_timer += 1
            if self.prince_speed_timer >= 120:  # Changer de vitesse toutes les 2 secondes
                self.prince_speed_timer = 0
                self.prince_speed_variation = random.uniform(-0.2, 0.3)  # Variation plus petite
                
            current_speed = max(0.1, self.prince_base_speed + self.prince_speed_variation)  # Minimum très lent
            self.current_prince_x += current_speed
            
        # Mise à jour de l'animation du prince
        self.prince_animation_timer += 1
        if self.prince_animation_timer >= self.prince_animation_speed:
            self.prince_animation_timer = 0
            self.prince_animation_frame = (self.prince_animation_frame + 1) % 8  # 8 frames de course
            
        # Gestion de l'invulnérabilité du prince
        if self.prince_invulnerable:
            self.prince_invulnerable_timer += 1
            if self.prince_invulnerable_timer >= self.prince_invulnerable_duration:
                self.prince_invulnerable = False
                self.prince_invulnerable_timer = 0
                
        # Spawner des flèches qui visent le prince
        self.arrow_spawn_timer += 1
        if self.arrow_spawn_timer >= self.arrow_spawn_interval:
            self.arrow_spawn_timer = 0
            self.arrow_spawn_interval = random.randint(30, 120)  # Nouvel intervalle réduit (0.5-2s)
            self.spawn_protection_arrow()
            
        # Mettre à jour les flèches
        for arrow in self.protection_arrows[:]:
            arrow.update()
            
            # Vérifier collision avec les soldats protecteurs (priorité)
            arrow_blocked = False
            for soldier in self.protector_soldiers:
                if not arrow.is_stuck and arrow.rect.colliderect(soldier.rect):
                    if soldier.take_arrow_hit():
                        self.protection_arrows.remove(arrow)
                        arrow_blocked = True
                        break
                        
            if arrow_blocked:
                continue
            
            # Vérifier collision avec le sol (comme dans ArrowManager)
            if not arrow.is_stuck and collision_tiles:
                for tile_rect in collision_tiles:
                    if arrow.rect.colliderect(tile_rect):
                        # Planter la flèche au sol
                        arrow.stick_to_ground(tile_rect.top)
                        break
            
            # Vérifier collision avec le prince (seulement si la flèche n'est pas plantée)
            prince_rect = pygame.Rect(self.current_prince_x, self.prince_y, 48, 64)
            if not arrow.is_stuck and arrow.rect.colliderect(prince_rect) and not self.prince_invulnerable:
                # Le prince prend des dégâts mais ne peut pas descendre en dessous de 1 PV
                self.prince_health = max(1, self.prince_health - 10)
                self.prince_invulnerable = True
                self.prince_invulnerable_timer = 0
                self.protection_arrows.remove(arrow)
                print(f"Le prince prend une flèche ! Santé : {self.prince_health}/{self.prince_max_health}")
                continue
                    
            # Supprimer les flèches hors écran
            if arrow.rect.y > 800 or arrow.rect.x > self.castle_door_x + 200:
                if arrow in self.protection_arrows:
                    self.protection_arrows.remove(arrow)
                    
        # Vérifier si le prince a atteint la tile 54 pour déclencher le zoom
        zoom_tile_x = self.zoom_start_tile * 16 * 2.5  # Tile 54 en pixels
        if self.current_prince_x >= zoom_tile_x and self.state == "protection":
            print("Le prince a atteint la tile 54 ! Début du zoom sur le prince...")
            self.state = "zoom_on_prince"
            self.state_timer = 0
            # Nettoyer le battlefield avant le zoom
            self.cleanup_battlefield()
            return False  # Continuer pour la séquence de zoom
            
        # Vérifier si le prince a atteint la porte (après tile 58)
        if self.current_prince_x >= self.castle_door_x:
            print("Le prince a atteint la porte ! Début de la séquence finale - Plot Armor !")
            self.state = "final_sequence"
            self.state_timer = 0
            self.setup_final_sequence()  # Créer les 50 soldats
            return False  # Continuer le mini-jeu pour la séquence finale
            
        return False
            
    def spawn_protector_soldier(self):
        """Spawne un soldat protecteur à droite de l'écran, au milieu en hauteur"""
        soldier_x = 1200
        soldier_y = 360
        
        soldier = ProtectorSoldier(soldier_x, soldier_y)
        self.protector_soldiers.append(soldier)
        print(f"Soldat protecteur spawné à ({soldier_x}, {soldier_y}) ! Total: {len(self.protector_soldiers)}")
        
    def spawn_protection_arrow(self):
        """Spawne une flèche qui vise le prince depuis la tile 62 en haut de l'écran"""
        # Position fixe : tile 62 en X, haut de l'écran en Y (comme dans le jeu principal)
        tile_62_x = 62 * 16 * 2.5  # Tile 62 en pixels = 2480
        arrow_x = tile_62_x
        arrow_y = 0  # Haut de l'écran (hauteur max de l'affichage)
        
        # Cibler le prince avec un peu de variation (même logique que le jeu principal)
        target_x = self.current_prince_x + random.randint(-50, 50)
        target_y = self.prince_y + random.randint(-30, 30)
        
        arrow = Arrow(arrow_x, arrow_y, target_x, target_y, "normal")
        arrow.speed = 5  # Même vitesse que les flèches du jeu principal
        arrow.max_range = 3000  # Portée étendue pour atteindre le prince
        self.protection_arrows.append(arrow)
        print(f"Flèche tirée depuis tile 62 (x={arrow_x}, y={arrow_y}) vers prince (x={target_x}, y={target_y})")
        
    def cleanup_battlefield(self):
        """Nettoie progressivement le battlefield : supprime les soldats bleus et flèches par vagues"""
        print("Début du nettoyage progressif du battlefield...")
        
        # Diviser le nettoyage en plusieurs vagues
        total_soldiers = len(self.protector_soldiers)
        total_arrows = len(self.protection_arrows)
        
        # Nettoyage progressif des soldats (par tiers)
        soldiers_per_wave = max(1, total_soldiers // 3)  # Minimum 1 par vague
        arrows_per_wave = max(1, total_arrows // 2)      # Minimum 1 par vague
        
        # Vague 1 : Supprimer le premier tiers des soldats
        for i in range(min(soldiers_per_wave, len(self.protector_soldiers))):
            if self.protector_soldiers:
                soldier = self.protector_soldiers.pop(0)
                print(f"Soldat protecteur supprimé : {i+1}/{soldiers_per_wave}")
        
        # Vague 1 : Supprimer la moitié des flèches
        for i in range(min(arrows_per_wave, len(self.protection_arrows))):
            if self.protection_arrows:
                arrow = self.protection_arrows.pop(0)
                print(f"Flèche supprimée : {i+1}/{arrows_per_wave}")
        
        print(f"Première vague terminée. Soldats restants: {len(self.protector_soldiers)}, Flèches restantes: {len(self.protection_arrows)}")
        
        # Programmer les vagues suivantes (sera appelé par update)
        if not hasattr(self, 'cleanup_phase'):
            self.cleanup_phase = 1
            self.cleanup_timer = 0
    
    def continue_cleanup_battlefield(self):
        """Continue le nettoyage progressif du battlefield"""
        if hasattr(self, 'cleanup_phase'):
            self.cleanup_timer += 1
            
            # Vague 2 : après 20 frames (1/3 seconde)
            if self.cleanup_phase == 1 and self.cleanup_timer >= 20:
                soldiers_per_wave = max(1, len(self.protector_soldiers) // 2)
                for i in range(min(soldiers_per_wave, len(self.protector_soldiers))):
                    if self.protector_soldiers:
                        self.protector_soldiers.pop(0)
                        
                # Supprimer le reste des flèches
                remaining_arrows = len(self.protection_arrows)
                for i in range(remaining_arrows):
                    if self.protection_arrows:
                        self.protection_arrows.pop(0)
                        
                print(f"Deuxième vague terminée. Soldats restants: {len(self.protector_soldiers)}")
                self.cleanup_phase = 2
                self.cleanup_timer = 0
            
            # Vague 3 : après 40 frames (2/3 seconde)
            elif self.cleanup_phase == 2 and self.cleanup_timer >= 20:
                # Supprimer tous les soldats restants
                remaining_soldiers = len(self.protector_soldiers)
                self.protector_soldiers.clear()
                print(f"Troisième vague terminée. {remaining_soldiers} soldats finaux supprimés.")
                print("Nettoyage progressif du battlefield terminé !")
                
                # Nettoyer les variables de nettoyage
                delattr(self, 'cleanup_phase')
                delattr(self, 'cleanup_timer')
        
    def setup_final_sequence(self):
        """Configure la séquence finale avec 100 soldats qui se ruent sur le prince"""
        print("Création de 100 soldats pour la séquence finale Plot Armor !")
        
        # Utiliser le même positionnement en hauteur que battlefield_manager
        ground_level = 655  # Même valeur que dans battlefield_manager et game.py
        enemy_base_y = ground_level - 100 + 5  # Même formule que les autres ennemis
        
        # Créer 100 soldats rouges qui se ruent vers le prince
        for i in range(100):
            # Position en formation plus dispersée : lignes de 10 soldats
            row = i // 10  # Ligne (0 à 9)
            col = i % 10   # Colonne (0 à 9)
            
            # Formation étalée sur un plus grand espace
            x = self.current_prince_x + 300 + (col * 80) + (row * 30)  # Formation étalée avec décalage par ligne
            # TOUS LES ENNEMIS AU MÊME NIVEAU Y (pas de variation en hauteur)
            y = enemy_base_y  # Exactement la même hauteur pour tous
            
            enemy = Enemy(x, y, team="red")
            enemy.is_attacking = True
            enemy.current_behavior = "attack"
            # Faire courir tous les soldats vers le prince
            enemy.target_x = self.current_prince_x
            enemy.target_y = enemy_base_y  # Viser la même hauteur de base
            self.final_enemies.append(enemy)
        
        # Marquer le moment de création des ennemis pour déclencher la mort après 3 secondes
        self.final_enemies_creation_time = self.state_timer
            
    def update_final_sequence(self):
        """Met à jour la séquence finale (tous les ennemis sont déjà morts, juste attendre)"""
        # Le prince reste complètement immobile en idle pendant toute la séquence finale
        self.prince_animation_timer = 0
        self.prince_animation_frame = 0  # Frame idle constante
        
        # Continuer les animations de mort des soldats de manière synchronisée
        for enemy in self.final_enemies:
            if enemy.is_dead and hasattr(self, 'simultaneous_death_start_time'):
                # Maintenir la synchronisation des animations de mort
                time_since_death = self.state_timer - self.simultaneous_death_start_time
                enemy.death_timer = time_since_death
                
                # Forcer l'animation de mort avec synchronisation
                if enemy.current_animation == "death" and "death" in enemy.sprites:
                    max_frames = len(enemy.sprites["death"])
                    animation_speed = enemy.animation_speed
                    frame_progress = time_since_death // animation_speed
                    enemy.animation_frame = min(frame_progress, max_frames - 1)
                    
                    # Ne pas marquer l'animation comme terminée trop tôt
                    if frame_progress >= max_frames - 1:
                        enemy.animation_finished = True
            
            # Mettre à jour l'animation de l'ennemi
            enemy.update_animation()
        
        # Fin du mini-niveau après 3 secondes (les ennemis sont déjà morts)
        if self.state_timer > 180:  # 3 secondes
            print("Séquence finale terminée ! Victoire du prince !")
            return True  # Mini-niveau terminé
            
        return False
        
    def draw(self, screen, camera_x, camera_y):
        """Dessine les éléments du mini-niveau"""
        # Ne pas gérer l'écran noir ici - c'est géré dans game.py
        if self.state == "black_screen":
            return  # Ne rien dessiner, game.py gère l'écran noir
            
        if self.state == "protection":
            # Dessiner les flèches D'ABORD
            for arrow in self.protection_arrows:
                arrow.draw(screen, camera_x, camera_y)
                
        elif self.state in ["dezoom_reveal_enemies", "final_sequence"]:
            # Dessiner les 100 soldats qui se ruent sur le prince pendant le dézoom et après
            for enemy in self.final_enemies:
                enemy.draw(screen, camera_x, camera_y)
                
        # Dessiner le prince à sa position actuelle (sauf pendant disappearing et black_screen)
        if self.state in ["zooming_out", "protection", "zoom_on_prince", "dezoom_reveal_enemies", "final_sequence"]:
            screen_x = self.current_prince_x - camera_x
            screen_y = self.prince_y - camera_y
            
            # Utiliser le sprite animé du prince
            if self.prince_sprites and len(self.prince_sprites) > 0:
                current_sprite = self.prince_sprites[self.prince_animation_frame % len(self.prince_sprites)]
                
                # Effet de clignotement si invulnérable
                if self.prince_invulnerable and (self.prince_invulnerable_timer // 10) % 2 == 0:
                    pass  # Ne pas dessiner (clignotement)
                else:
                    screen.blit(current_sprite, (screen_x, screen_y))
            else:
                # Fallback : rectangle doré si les sprites ne sont pas chargés
                if not (self.prince_invulnerable and (self.prince_invulnerable_timer // 10) % 2 == 0):
                    pygame.draw.rect(screen, (255, 215, 0), (screen_x, screen_y, 48, 64))
        
        # Dessiner les soldats protecteurs EN DERNIER (premier plan) - sauf pendant fading_to_black et black_screen
        if self.state == "protection":
            for soldier in self.protector_soldiers:
                soldier.draw(screen, camera_x, camera_y)
                
        # Dessiner le fade vers l'écran noir
        if self.state == "fading_to_black" and self.fade_alpha > 0:
            fade_surface = pygame.Surface((screen.get_width(), screen.get_height()))
            fade_surface.set_alpha(self.fade_alpha)
            fade_surface.fill((0, 0, 0))  # Noir
            screen.blit(fade_surface, (0, 0))
                
    def draw_prince_health_bar(self, screen):
        """Dessine la barre de vie du prince en haut de l'écran"""
        if self.state == "protection":
            # Barre de fond
            bar_width = 300
            bar_height = 20
            bar_x = (screen.get_width() - bar_width) // 2
            bar_y = 20
            
            # Fond de la barre (rouge foncé)
            pygame.draw.rect(screen, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))
            
            # Barre de vie (vert/jaune/rouge selon les PV)
            health_ratio = self.prince_health / self.prince_max_health
            current_bar_width = int(bar_width * health_ratio)
            
            if health_ratio > 0.5:
                bar_color = (0, 200, 0)  # Vert
            elif health_ratio > 0.2:
                bar_color = (255, 255, 0)  # Jaune
            else:
                bar_color = (255, 100, 100)  # Rouge clair (ne devient jamais rouge foncé car min 1 PV)
                
            pygame.draw.rect(screen, bar_color, (bar_x, bar_y, current_bar_width, bar_height))
            
            # Bordure
            pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)
            
            # Texte de santé
            font = pygame.font.Font(None, 24)
            text = f"Prince: {self.prince_health}/{self.prince_max_health} PV"
            text_surface = font.render(text, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(bar_x + bar_width // 2, bar_y + bar_height + 15))
            screen.blit(text_surface, text_rect)
            
    def get_zoom_factor(self):
        """Retourne le facteur de zoom actuel pour game.py"""
        return self.zoom_factor
        
    def get_zoom_target_position(self):
        """Retourne la position de la caméra pour le zoom sur le prince"""
        if self.state == "zoom_on_prince":
            # Centrer sur le prince pendant le zoom
            return self.current_prince_x, self.prince_y
        elif self.state == "dezoom_reveal_enemies":
            # Pendant le dézoom, positionner le prince à 20px du bord gauche
            return self.current_prince_x - 20, self.prince_y
        elif self.state == "final_sequence":
            # Pendant la séquence finale, garder le prince à 20px du bord gauche
            return self.current_prince_x - 20, self.prince_y
        return None
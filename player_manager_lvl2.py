
import pygame
from player import Player
from prince import Prince
from horse import Horse
from QTE_manager import QTEManager

class PlayerManager2:
    """Gère le niveau 2"""
    def __init__(self, initial_x, initial_y):
        self.initial_spawn_x = initial_x
        self.initial_spawn_y = initial_y
        
        # Joueur actuel
        self.current_player = Player(initial_x, initial_y, play_sound=False)
        self.current_player.update_can_move(False)
        self.prince = Prince(initial_x, initial_y - 20)
        self.prince_is_walking = False
        self.prince_current_animation = "idle"
        
        # Liste des corps morts
        self.dead_bodies = []
        
        # État du respawn
        self.respawning = False
        self.new_player = None
        self.respawn_timer = 0
        self.respawn_duration = 120  # 2 secondes à 60 FPS

        self.is_in_QTE = False
        self.QTE_is_over = False
        self.QTE_manager = QTEManager(initial_x, initial_y, self.on_qte_end)
        self.QTE_manager.start_round()  # Démarrer immédiatement le QTE

        self.horse_x = 445  # Position du cheval
        self.horse = Horse(self.horse_x, initial_y)
        self.horse_trigger_zone_x = self.horse_x - 10  # Position du cheval
        self.horse_game_triggered = False
        self.horse_game_over = False
        self.horse_timer = 120 
        self.horse_score = 0

        # Position actuelle du prince (il bougera vers la droite)
        self.prince_base_speed = 0.5  # Plus rapide (était 0.5)
        self.prince_speed_variation = 0
        self.prince_speed_timer = 0
        
        # Animation du prince
        self.prince_animation_frame = 0
        self.prince_animation_timer = 0
        self.prince_animation_speed = 8
        self.prince_current_animation = "idle"  # Animation actuelle du prince ("idle" ou "run")
        
        # Sons de pas du prince
        self.prince_footstep_timer = 0
        self.prince_footstep_interval = 30  # 30 frames = 0.5 seconde entre chaque pas (lent)
        self.prince_is_walking = False
        self.sprites = {"campfire": []}
        self.init_campfire_frames()
        self.campfire_animation_frame = 0

        self.horse_footstep_timer = 0
        self.horse_footstep_interval = 15

        self.frame_count = 0
        self.frame_between_animation = 4
        self.campfire_sound_playing = False

        try:
            self.campfire_sound = pygame.mixer.Sound("assets/sounds/fire.mp3")
            self.campfire_sound.set_volume(0.7)
            
            self.footstep_sound = pygame.mixer.Sound("assets/sounds/footstep.wav")
            self.footstep_sound.set_volume(0.5) 
            self.horse_footstep_sound = pygame.mixer.Sound("assets/sounds/gallop.wav")
            self.horse_footstep_sound.set_volume(0.5) 

            
            self.horse_neigh_sound = pygame.mixer.Sound("assets/sounds/horse_neigh.mp3")
            self.horse_neigh_sound.set_volume(0.5)
            self.whip_sound = pygame.mixer.Sound("assets/sounds/whip.mp3")
            self.whip_sound.set_volume(0.7)
        except pygame.error as e:
            print(f"Erreur lors du chargement des sons: {e}")
            self.footstep_sound = None
            self.campfire_sound = None
            self.horse_footstep_sound = None
            self.horse_neigh_sound = None
            self.whip_sound = None
        
        
        # Agrandir la touche E (ex: 1.5x)
        key_e_raw = pygame.image.load("assets/images/sprites/key/e1.png").convert_alpha()
        scale_factor = 1.3
        new_size = (int(key_e_raw.get_width() * scale_factor), int(key_e_raw.get_height() * scale_factor))
        self.key_e_img = pygame.transform.scale(key_e_raw, new_size)
        
    def update(self, keys, collision_tiles):
        if not self.campfire_sound_playing:
            self.campfire_sound_playing=True
            self.campfire_sound.play(loops=-1)
        if hasattr(self, 'campfire_sound') and self.campfire_sound:
            campfire_x = self.initial_spawn_x - 30
            campfire_y = self.initial_spawn_y - 45
            player_x = self.current_player.rect.x
            player_y = self.current_player.rect.y
            dist = ((player_x - campfire_x) ** 2 + (player_y - campfire_y) ** 2) ** 0.5
            max_dist = 650
            volume = max(0.0, 1.0 - dist / max_dist)
            self.campfire_sound.set_volume(volume * 0.9)


        """Met à jour le gestionnaire de joueurs"""
        self.QTE_manager.update(keys)

        if self.QTE_is_over and not self.horse_game_triggered and self.prince.x < self.horse_trigger_zone_x:
            current_speed = max(0.1, self.prince_base_speed + 0.2)  # Vitesse fixe pendant le panning
            self.prince.x += current_speed
            self.current_player.rect.x  = self.prince.x + (self.prince.rect.width // 2) - (self.current_player.rect.width // 2)   # Déplacer le joueur avec le prince
            
            
            # Jouer les pas lents du prince
            self.prince_footstep_timer += 1
            if self.prince_footstep_timer >= self.prince_footstep_interval:
                self.prince_footstep_timer = 0
                if self.footstep_sound:
                    self.footstep_sound.play()

        if not self.horse_game_triggered and self.prince.x >= self.horse_trigger_zone_x:
            self.horse_game_triggered = True
            self.prince_current_animation = "idle"
            self.prince_is_walking = False

        if self.horse_game_triggered and not self.horse_game_over:
            self.horse_timer -= 1
            if keys[pygame.K_e]:
                self.horse_score += 1

        if not self.horse_game_over and self.horse_timer<=0:
            self.horse_game_over = True
            self.current_player.update_can_move(True)
            self.current_player.speed += self.current_player.speed * (self.horse_score / 100)  # Augmente la vitesse du joueur
            print(self.current_player.speed)
            self.prince_is_walking = False
            self.prince_current_animation = 'idle'
            self.horse_neigh_sound.play()
            self.whip_sound.play()
        else:
            # Mettre à jour le joueur actuel
            self.current_player.update(keys, collision_tiles)
            
            if self.current_player.can_move:
                horse_moving = False
                horse_jumping = False
                if keys[pygame.K_z] or keys[pygame.K_UP] or keys[pygame.K_SPACE]:
                    horse_jumping = True
                    self.horse.set_animation('jump')
                if keys[pygame.K_q] or keys[pygame.K_LEFT]:
                    self.horse.facing = 'left'
                    self.prince.facing_right = False
                    horse_moving = True
                elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:  
                    self.horse.facing = 'right'
                    self.prince.facing_right = True
                    horse_moving = True
                if horse_moving and not horse_jumping:
                    # Jouer le gallop
                    self.horse_footstep_timer += 1
                    if self.horse_footstep_timer >= self.horse_footstep_interval:
                        self.horse_footstep_timer = 0
                        if self.horse_footstep_sound:
                            self.horse_footstep_sound.play()
                    self.horse.set_animation('run')
                else:
                    self.horse.set_animation('idle')

                if self.horse_game_over and self.prince.x < 3300:
                    self.prince.x = self.current_player.rect.x - 10 - (self.prince.rect.width // 2) + (self.current_player.rect.width // 2)
                    if not self.prince.facing_right:
                        self.prince.x += 10
                    self.prince.y = self.current_player.rect.y - 55
                    self.horse.rect.x = self.current_player.rect.x  - (self.horse.rect.width // 2) + (self.current_player.rect.width // 2)
                    self.horse.rect.y = self.current_player.rect.y - 5
                else:
                    self.horse.facing = 'right'
                    self.prince.facing_right = True
                    self.current_player.speed = self.current_player.speed * 0.99
                    self.prince.x += self.current_player.speed
                    self.horse.rect.x += self.current_player.speed
            else:
                self.current_player.rect.x = self.prince.x + (self.prince.rect.width // 2) - (self.current_player.rect.width // 2)   # Déplacer le joueur avec le prince
        self.horse.update()
        self.prince.update()
    
    def get_current_player(self):
        """Retourne le joueur actuel (celui qu'on contrôle)"""
        return self.current_player
    
    def draw(self, screen, camera_x, camera_y):
        """Dessine tous les éléments"""
        # Dessiner tous les corps morts
        for body in self.dead_bodies:
            body.draw(screen, camera_x, camera_y)
        
        if self.horse_game_triggered and not self.horse_game_over:
            img = self.key_e_img
            pos = (self.horse_x-img.get_width()//2 + 30, self.initial_spawn_y - 30)
            screen.blit(img, pos)
        
        self.horse.draw(screen, camera_x, camera_y)
        self.QTE_manager.draw(screen,camera_x,camera_y)
        self.prince.draw(screen, camera_x, camera_y)
        self.draw_campfire(screen, camera_x, camera_y)
    
    def draw_health_bar(self, screen):
        """Dessine la barre de santé"""
        if not self.respawning:
            # Position de la barre de santé
            health_x = 20
            health_y = 20
            heart_size = 30
            
            for i in range(self.current_player.max_health):
                heart_x = health_x + i * (heart_size + 5)
                
                # Dessiner le cœur
                if i < self.current_player.health:
                    # Cœur plein (rouge)
                    pygame.draw.circle(screen, (255, 0, 0), (heart_x + heart_size//2, health_y + heart_size//2), heart_size//2)
                else:
                    # Cœur vide (gris)
                    pygame.draw.circle(screen, (100, 100, 100), (heart_x + heart_size//2, health_y + heart_size//2), heart_size//2)
                    pygame.draw.circle(screen, (50, 50, 50), (heart_x + heart_size//2, health_y + heart_size//2), heart_size//2, 2)

    def on_qte_end(self):
        """Appelé lorsque le QTE est terminé"""
        self.QTE_is_over = True
        self.prince_is_walking = True
        self.prince_current_animation = "run"
        # self.current_player.update_can_move(True)

    def draw_campfire(self, screen, camera_x, camera_y):
        # Affiche l'animation du feu de camp en boucle
        self.frame_count += 1
        if self.frame_count % self.frame_between_animation == 0:
            self.campfire_animation_frame += 1
        frames = self.sprites["campfire"]
        frame = frames[self.campfire_animation_frame % len(frames)]
        screen_x = self.initial_spawn_x - camera_x - 30
        screen_y = self.initial_spawn_y - camera_y + 45
        screen.blit(frame, (screen_x, screen_y))

    def init_campfire_frames(self):
        """Charge toutes les frames du feu de camp"""
        import os
        sprite_path = "assets/images/sprites/campfire/"
        frames = []
        files = [f for f in os.listdir(sprite_path) if f.lower().startswith("campfire") and f.lower().endswith('.png')]
        files.sort()  # Pour l'ordre d'animation
        for filename in files:
            img_path = os.path.join(sprite_path, filename)
            try:
                image = pygame.image.load(img_path).convert_alpha()
                frames.append(image)
            except pygame.error as e:
                print(f"Erreur lors du chargement de {img_path}: {e}")
        self.sprites["campfire"] = frames
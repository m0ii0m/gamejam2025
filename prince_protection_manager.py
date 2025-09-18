import pygame
import random
import math
from enemy import Enemy
from arrow import Arrow

class ProtectorSoldier:
    """Soldat bleu (enemy) qui protège le prince en bloquant les flèches"""
    
    # Sons partagés pour tous les protecteurs
    _sounds_loaded = False
    _man_dying_sound = None
    
    @classmethod
    def load_sounds(cls):
        """Charge les sons une seule fois"""
        if not cls._sounds_loaded:
            try:
                pygame.mixer.init()
                cls._man_dying_sound = pygame.mixer.Sound("assets/sons/manDying.wav")
                # Ajuster le volume si nécessaire
                cls._man_dying_sound.set_volume(0.7)
                cls._sounds_loaded = True
            except pygame.error as e:
                print(f"Erreur lors du chargement des sons protecteur: {e}")
                cls._man_dying_sound = None
                cls._sounds_loaded = True
    
    def __init__(self, x, y):
        # Charger les sons si pas déjà fait
        ProtectorSoldier.load_sounds()
        
        # Créer un enemy bleu
        self.enemy = Enemy(x, y, team="blue")
        self.rect = self.enemy.rect
        self.speed = 4
        self.is_dead = False
        self.death_timer = 0
        self.target_x = 70 * 16 * 2.5  # Tile 70 en pixels (plus loin à droite que tile 62)
        
        # Sons de mort
        self.death_sounds_played = False
        
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
            
            # Gérer les sons de mort
            if not self.death_sounds_played:
                # Jouer manDying immédiatement
                if ProtectorSoldier._man_dying_sound:
                    ProtectorSoldier._man_dying_sound.play()
                self.death_sounds_played = True
            
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
        # Charger les sons
        try:
            pygame.mixer.init()
            self.haki_sound = pygame.mixer.Sound("assets/sounds/haki.mp3")
            self.haki_sound.set_volume(1.0)  # Volume maximum
            self.battle_sound = pygame.mixer.Sound("assets/sounds/music/level1_battleSoundonly.mp3")
            self.battle_sound.set_volume(0.7)
            self.sneeze_sound = pygame.mixer.Sound("assets/sounds/sneeze.mp3")
            self.sneeze_sound.set_volume(1.0)  # Volume maximum
            self.gasp_sound = pygame.mixer.Sound("assets/sounds/gasp.mp3")
            self.gasp_sound.set_volume(1.0)  # Volume maximum
            self.paper_sound = pygame.mixer.Sound("assets/sounds/paper.mp3")
            self.paper_sound.set_volume(0.6)
            self.footstep_sound = pygame.mixer.Sound("assets/sounds/footstep.wav")
            self.footstep_sound.set_volume(0.5)  # Volume modéré pour les pas
        except pygame.error as e:
            print(f"Erreur lors du chargement des sons: {e}")
            self.haki_sound = None
            self.battle_sound = None
            self.sneeze_sound = None
            self.gasp_sound = None
            self.paper_sound = None
            self.footstep_sound = None
        
        # Variables pour la gestion audio séquencée
        self.footsteps_only_mode = False  # Pour couper la musique pendant le zoom
        self.battle_sound_playing = False  # Contrôle du son de bataille
        self.sneeze_played = False  # Pour ne jouer sneeze qu'une fois
        self.haki_played = False  # Pour ne jouer haki qu'une fois
        self.original_music_volume = 0.5  # Volume original de la musique
        self.silence_timer = 0  # Timer pour l'attente de 1 seconde après sneeze
        self.enemies_turned = False  # Pour savoir si les ennemis se sont tournés vers le prince
        
        # Système de séquences temporelles
        self.sequence_actions = []
        self.sequence_timer = 0
        
        # Variables pour les sons de mort du messager
        self.messenger_gasp_played = False
        self.messenger_gasp_timer = 0  # Délai de 1s avant gasp
        self.messenger_paper_timer = 0
        
        self.prince_x = prince_x
        # Utiliser la même position Y que les ennemis pour une cohérence visuelle
        ground_level = 655  # Même valeur que battlefield_manager
        self.prince_y = ground_level - 100 - 25  # Remonter le prince de 2px supplémentaires (était -23, maintenant -25)
        self.castle_door_x = castle_door_x
        
        # États du mini-niveau
        self.state = "waiting"  # "waiting", "cinematic_slowdown", "player_death", "pause_after_death", "zooming_out", "protection", "zoom_on_prince", "dezoom_reveal_enemies", "final_sequence"
        self.state_timer = 0
        
        # Gestion du zoom sur le prince
        self.zoom_start_tile = 54  # Tile où commence le zoom (plus tôt)
        self.zoom_end_tile = 70   # Tile où se termine le zoom
        self.zoom_factor = 1.0    # Facteur de zoom actuel (1.0 = normal, 2.0 = zoomé x2)
        self.max_zoom_factor = 2.5  # Zoom maximum
        self.min_zoom_factor = 2.1  # Zoom minimum après dézoom (moins de dézoom)
        
        # Effet de fade
        self.fade_alpha = 0  # Pour le fade vers l'écran noir
        self.fade_speed = 3  # Vitesse du fade
        
        # Effet d'onde de choc haki
        self.haki_shockwave_active = False
        self.haki_shockwave_radius = 0
        self.haki_shockwave_speed = 25  # Encore plus rapide
        self.haki_shockwave_max_radius = 2000  # Radius maximum pour couvrir tout l'écran
        self.haki_shockwave_center_x = 0  # Position du centre de l'onde
        self.haki_shockwave_center_y = 0
        self.haki_shockwave_alpha = 255  # Alpha pour le fade progressif
        self.haki_shockwave_fade_speed = 8  # Vitesse du fade
        
        # Position du messager mort (sauvegardée pour le zoom)
        self.dead_messenger_x = 0
        self.dead_messenger_y = 0
        
        # Cinématique d'avancement du messager
        self.cinematic_start_x = 0  # Position de départ du messager
        self.cinematic_target_distance = 2 * 16 * 2.5  # 2 tiles en pixels
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
        self.prince_current_animation = "idle"  # Animation actuelle du prince ("idle" ou "run")
        
        # Sons de pas du prince
        self.prince_footstep_timer = 0
        self.prince_footstep_interval = 30  # 30 frames = 0.5 seconde entre chaque pas (lent)
        self.prince_is_walking = False
        
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
        self.arrow_spawn_interval = random.randint(2, 8)  # Intervalle très réduit : 0.07 à 0.27 secondes pour commencer très intense
        self.initial_arrow_burst = 8  # Nombre de flèches à spawner immédiatement (doublé)
        self.initial_burst_spawned = False  # Flag pour savoir si le burst initial a été fait
        
        # Soldats protecteurs
        self.protector_soldiers = []
        
        # Ennemis pour la séquence finale
        self.final_enemies = []
        self.enemy_fall_timer = 0
        self.enemy_fall_interval = 30  # 0.5 secondes entre chaque chute
        self.simultaneous_death_triggered = False  # Flag pour la mort simultanée
        
        # Sprites du prince
        self.prince_sprites = self.load_prince_sprites()
        
    def create_sequence(self, actions):
        """Crée une séquence d'actions temporelles
        actions = [(delay_frames, action_function, description), ...]
        """
        self.sequence_actions = actions
        self.sequence_timer = 0
        
    def update_sequence(self):
        """Met à jour la séquence d'actions temporelles"""
        if not self.sequence_actions:
            return False  # Séquence terminée
            
        self.sequence_timer += 1
        
        # Vérifier si une action doit être exécutée
        while self.sequence_actions:
            delay, action, description = self.sequence_actions[0]
            
            if self.sequence_timer >= delay:
                print(f"Exécution action: {description}")
                result = action()
                self.sequence_actions.pop(0)
                self.sequence_timer = 0  # Reset timer pour la prochaine action
                
                # Si l'action retourne True, arrêter la séquence
                if result:
                    return True
            else:
                break
                
        return len(self.sequence_actions) == 0  # True si plus d'actions
        
    def setup_zoom_sequence(self):
        """Configure la séquence de zoom sur le prince"""
        actions = [
            (1, self.start_zoom_audio, "Couper musique pour zoom"),
            (0, self.start_prince_movement, "Démarrer mouvement prince"),
        ]
        self.create_sequence(actions)
        
    def setup_dezoom_sequence(self):
        """Configure la séquence de dézoom et actions finales"""
        frames_for_zoom = int((self.zoom_end_tile - self.zoom_start_tile) / self.prince_base_speed * (16 * 2.5) / 2)
        
        actions = [
            (1, self.start_dezoom, "Démarrer dézoom et nettoyage"),
            (frames_for_zoom, self.complete_dezoom, "Terminer dézoom"),
            (1, self.play_sneeze, "Jouer sneeze"),
            (60, self.turn_enemies, "Tourner ennemis vers prince"),
            (60, self.play_haki, "Jouer son haki"),
            (60, self.kill_all_enemies, "Mort simultanée des ennemis"),
            (180, self.complete_sequence, "Terminer séquence")
        ]
        self.create_sequence(actions)
        
    # Actions pour les séquences
    def start_zoom_audio(self):
        if not self.footsteps_only_mode:
            pygame.mixer.music.set_volume(0)
            self.footsteps_only_mode = True
        return False
        
    def start_prince_movement(self):
        return False  # Continue la séquence
        
    def start_dezoom(self):
        # Forcer complètement le prince en idle et réinitialiser l'animation
        self.prince_current_animation = "idle"  
        self.prince_animation_timer = 0
        self.prince_animation_frame = 0  # Commencer à la première frame d'idle
        self.cleanup_battlefield()
        return False
        
    def complete_dezoom(self):
        self.zoom_factor = self.min_zoom_factor  # 1.8x au lieu de 1.0x
        return False
        
    def play_sneeze(self):
        if self.sneeze_sound and not self.sneeze_played:
            self.sneeze_sound.play()
            self.sneeze_played = True
            pygame.mixer.music.set_volume(0.0)
        return False
        
    def turn_enemies(self):
        print("Arrêt des actions aléatoires et orientation vers le prince !")
        for enemy in self.final_enemies:
            if not enemy.is_dead:
                # Arrêter toutes les actions aléatoires
                enemy.facing_right = False  # Regarder vers la gauche (vers le prince)
                enemy.current_animation = "idle"
                enemy.velocity_x = 0
                enemy.velocity_y = 0
                enemy.current_behavior = "idle"  # Arrêter la patrouille
                enemy.turned_to_prince = True  # Marquer que cet ennemi a été tourné
        self.enemies_turned = True
        return False
        
    def play_haki(self):
        if not self.haki_played and self.haki_sound:
            self.haki_sound.play()
            self.haki_played = True
            
            # Déclencher l'onde de choc depuis la position du prince
            self.haki_shockwave_active = True
            self.haki_shockwave_radius = 0
            self.haki_shockwave_alpha = 255  # Commencer avec opacité maximale
            self.haki_shockwave_center_x = self.current_prince_x
            self.haki_shockwave_center_y = self.prince_y + 50  # Centre sur le prince
        return False
        
    def kill_all_enemies(self):
        self.simultaneous_death_triggered = True
        self.simultaneous_death_start_time = self.state_timer
        
        for enemy in self.final_enemies:
            if not enemy.is_dead:
                enemy.is_dead = True
                enemy.health = 0
                enemy.death_timer = 0
                enemy.current_animation = "death"
                enemy.animation_frame = 0
                enemy.animation_finished = False
                enemy.velocity_x = 0
                enemy.velocity_y = 0
                enemy.is_attacking = False
                enemy.attack_timer = 0
                enemy.animation_timer = 0
        return False
        
    def complete_sequence(self):
        print("Séquence finale terminée ! Victoire du prince !")
        return True
        
    def load_prince_sprites(self):
        """Charge les sprites du prince pour l'animation de course et idle"""
        try:
            sprites = {}
            sprite_path = "assets/images/sprites/prince/"
            
            # Charger les 8 frames de course
            run_sprites = []
            for i in range(1, 9):
                filename = f"run{i}.png"
                full_path = sprite_path + "run/" + filename
                sprite = pygame.image.load(full_path).convert_alpha()
                # Redimensionner pour correspondre à la taille du prince (plus grande)
                sprite = pygame.transform.scale(sprite, (80, 105))  # Agrandir encore de 72x95 à 80x105
                run_sprites.append(sprite)
            sprites["run"] = run_sprites
            print(f"Prince sprites - Run chargé: {len(run_sprites)} frames")
            
            # Charger les vraies sprites idle (8 frames également)
            idle_sprites = []
            for i in range(1, 9):
                filename = f"idle{i}.png"
                full_path = sprite_path + "idle/" + filename
                sprite = pygame.image.load(full_path).convert_alpha()
                # Redimensionner pour correspondre à la taille du prince
                sprite = pygame.transform.scale(sprite, (80, 105))
                idle_sprites.append(sprite)
            sprites["idle"] = idle_sprites
            print(f"Prince sprites - Idle chargé: {len(idle_sprites)} frames")
                
            return sprites
        except pygame.error as e:
            print(f"Erreur lors du chargement des sprites du prince: {e}")
            # Créer un sprite par défaut
            default_sprite = pygame.Surface((80, 105))  # Taille agrandie pour correspondre
            default_sprite.fill((255, 215, 0))  # Or
            return {"run": [default_sprite] * 8, "idle": [default_sprite]}
    
    def update_prince_animation(self):
        """Met à jour l'animation du prince de manière centralisée"""
        # Vérifier que l'animation actuelle existe et réinitialiser la frame si nécessaire
        if (self.prince_current_animation in self.prince_sprites and 
            len(self.prince_sprites[self.prince_current_animation]) > 0):
            # S'assurer que la frame actuelle est valide
            max_frames = len(self.prince_sprites[self.prince_current_animation])
            if self.prince_animation_frame >= max_frames:
                self.prince_animation_frame = 0
        else:
            # Animation inexistante - rester à la frame 0
            self.prince_animation_frame = 0
            return
        
        self.prince_animation_timer += 1
        if self.prince_animation_timer >= self.prince_animation_speed:
            self.prince_animation_timer = 0
            
            # Vérifier que l'animation actuelle existe
            if (self.prince_current_animation in self.prince_sprites and 
                len(self.prince_sprites[self.prince_current_animation]) > 0):
                current_animation_frames = self.prince_sprites[self.prince_current_animation]
                self.prince_animation_frame = (self.prince_animation_frame + 1) % len(current_animation_frames)
            else:
                # Fallback si l'animation n'existe pas
                self.prince_animation_frame = 0
        
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
                
                # Jouer le gasp immédiatement à la mort du messager
                if self.gasp_sound and not self.messenger_gasp_played:
                    self.gasp_sound.play()
                    self.messenger_gasp_played = True
                    self.messenger_paper_timer = 180  # 3 secondes après gasp pour le paper
                
                current_player.die()
                # Désactiver le respawn - le messager ne reviendra plus
                player_manager.disable_respawn()
                self.state = "player_death"
                self.state_timer = 0
                
        elif self.state == "player_death":
            # Attendre que le joueur soit complètement mort
            current_player = player_manager.get_current_player()
            
            # Gérer le timer pour le son paper (3 secondes après gasp)
            if self.messenger_paper_timer > 0:
                self.messenger_paper_timer -= 1
                if self.messenger_paper_timer == 0 and self.paper_sound:
                    self.paper_sound.play()
            
            if current_player.is_dead or self.state_timer >= 180:  # 3 secondes max
                print("Le messager est mort, pause de 2 secondes...")
                self.state = "pause_after_death"
                self.state_timer = 0
                
        elif self.state == "pause_after_death":
            # Pause de 2 secondes après la mort du messager
            if self.state_timer >= 180:  # 2 secondes à 60 FPS
                print("Pause terminée, début du zoom out vers le prince !")
                self.state = "zooming_out"
                self.state_timer = 0
                # Le zoom out sera géré par game.py
                
        elif self.state == "zooming_out":
            # Phase de dézoomer (gérée dans game.py)
            # Faire commencer le prince à marcher pendant le panning
            if self.current_prince_x < self.castle_door_x:
                current_speed = max(0.1, self.prince_base_speed + 0.2)  # Vitesse fixe pendant le panning
                self.current_prince_x += current_speed
                self.prince_is_walking = True
                self.prince_current_animation = "run"
                
                # Jouer les pas lents du prince
                self.prince_footstep_timer += 1
                if self.prince_footstep_timer >= self.prince_footstep_interval:
                    self.prince_footstep_timer = 0
                    if self.footstep_sound:
                        self.footstep_sound.play()
            else:
                self.prince_is_walking = False
                self.prince_current_animation = "idle"
                
            # Mise à jour de l'animation du prince pendant le panning
            self.prince_animation_timer += 1
            if self.prince_animation_timer >= self.prince_animation_speed:
                self.prince_animation_timer = 0
                if self.prince_current_animation == "run":
                    self.prince_animation_frame = (self.prince_animation_frame + 1) % len(self.prince_sprites["run"])
                else:  # idle
                    self.prince_animation_frame = 0  # Frame fixe pour idle
                
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
            # Utiliser le système de séquences pour le zoom
            if not hasattr(self, 'zoom_sequence_started'):
                self.setup_zoom_sequence()
                self.zoom_sequence_started = True
            
            # Exécuter les actions de la séquence
            self.update_sequence()
            
            # Logique de mouvement du prince et zoom (continue en parallèle)
            prince_tile = self.current_prince_x / (16 * 2.5)
            
            # Faire avancer le prince jusqu'à la tile 70
            if prince_tile < self.zoom_end_tile:
                current_speed = max(0.1, self.prince_base_speed)
                self.current_prince_x += current_speed
                self.prince_is_walking = True
                self.prince_current_animation = "run"
                
                # Jouer les pas lents du prince pendant le zoom
                self.prince_footstep_timer += 1
                if self.prince_footstep_timer >= self.prince_footstep_interval:
                    self.prince_footstep_timer = 0
                    if self.footstep_sound:
                        self.footstep_sound.play()
                
                # Mise à jour de l'animation du prince (course)
                self.update_prince_animation()
            else:
                # Le prince a atteint la tile 70, il s'arrête et se met en idle
                self.prince_is_walking = False
                self.prince_current_animation = "idle"
                
                # Mise à jour de l'animation idle du prince à l'arrêt
                self.update_prince_animation()
                
            # Calculer le zoom basé sur la position du prince
            if prince_tile >= self.zoom_start_tile and prince_tile <= self.zoom_end_tile:
                zoom_progress = (prince_tile - self.zoom_start_tile) / (self.zoom_end_tile - self.zoom_start_tile)
                self.zoom_factor = 1.0 + (self.max_zoom_factor - 1.0) * zoom_progress
                
            # Quand le prince atteint la tile 70, attendre 1 seconde puis dézoomer
            if prince_tile >= self.zoom_end_tile and self.state_timer >= 60:
                print("Prince à la tile 70, démarrage séquence finale !")
                self.state = "dezoom_reveal_enemies"
                self.state_timer = 0
                self.setup_final_sequence()
                
        elif self.state == "dezoom_reveal_enemies":
            # Utiliser le système de séquences pour le dézoom et actions finales
            if not hasattr(self, 'dezoom_sequence_started'):
                self.setup_dezoom_sequence()
                self.dezoom_sequence_started = True
            
            # Exécuter les actions de la séquence
            sequence_complete = self.update_sequence()
            
            # Logique de dézoom (en parallèle avec les actions séquentielles)
            frames_for_zoom = (self.zoom_end_tile - self.zoom_start_tile) / self.prince_base_speed * (16 * 2.5) / 2
            
            if self.state_timer <= frames_for_zoom:
                dezoom_progress = self.state_timer / frames_for_zoom
                self.zoom_factor = self.max_zoom_factor - (self.max_zoom_factor - self.min_zoom_factor) * dezoom_progress
            else:
                self.zoom_factor = self.min_zoom_factor  # S'assurer qu'on reste à 1.8x
            
            # Continuer le nettoyage progressif
            self.continue_cleanup_battlefield()
            
            # Mettre à jour l'onde de choc haki si active
            if self.haki_shockwave_active:
                self.haki_shockwave_radius += self.haki_shockwave_speed
                
                # Commencer le fade quand l'onde atteint 50% de sa taille max
                fade_start_radius = self.haki_shockwave_max_radius * 0.5
                if self.haki_shockwave_radius >= fade_start_radius:
                    self.haki_shockwave_alpha = max(0, self.haki_shockwave_alpha - self.haki_shockwave_fade_speed)
                
                # Désactiver quand l'alpha atteint 0 ou radius max
                if (self.haki_shockwave_alpha <= 0 or 
                    self.haki_shockwave_radius >= self.haki_shockwave_max_radius):
                    self.haki_shockwave_active = False
            
            # Mettre à jour les ennemis avec leurs actions aléatoires
            for enemy in self.final_enemies:
                # Tous les ennemis doivent avoir leurs animations mises à jour
                if not hasattr(enemy, 'turned_to_prince'):
                    # Si l'ennemi a une action aléatoire assignée, l'utiliser
                    if hasattr(enemy, 'random_action'):
                        enemy.current_animation = enemy.random_action
                        
                        # Appliquer le mouvement aléatoire si l'ennemi court
                        if enemy.random_action == "run" and hasattr(enemy, 'random_velocity'):
                            new_x = enemy.rect.x + enemy.random_velocity
                            # Empêcher l'ennemi de passer à gauche du prince
                            if new_x >= self.current_prince_x + 30:  # Garder 30px de marge à droite du prince
                                enemy.rect.x = new_x
                            else:
                                # Si l'ennemi essaie d'aller trop à gauche, le faire reculer
                                enemy.rect.x = self.current_prince_x + 30
                                enemy.random_velocity = abs(enemy.random_velocity)  # Inverser vers la droite
                    
                    # Mettre à jour l'animation dans tous les cas
                    enemy.update_animation()
            
            # Mettre à jour l'animation du prince (idle pendant le dézoom)
            # Forcer l'animation idle à chaque frame pendant le dézoom
            self.prince_current_animation = "idle"
            self.update_prince_animation()
            
            # Mettre à jour les animations des ennemis morts de manière synchronisée
            if hasattr(self, 'simultaneous_death_triggered') and self.simultaneous_death_triggered:
                for enemy in self.final_enemies:
                    if enemy.is_dead:
                        enemy.death_timer = self.state_timer - self.simultaneous_death_start_time
                        if enemy.current_animation == "death":
                            time_since_death = enemy.death_timer
                            animation_speed = enemy.animation_speed
                            frame_progress = time_since_death // animation_speed
                            max_frames = len(enemy.sprites["death"]) if "death" in enemy.sprites else 4
                            enemy.animation_frame = min(frame_progress, max_frames - 1)
                    enemy.update_animation()
            
            # Terminer quand la séquence est complète
            if sequence_complete:
                return True
                
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
            self.prince_is_walking = True
            self.prince_current_animation = "run"
            
            # Jouer les pas lents du prince pendant la protection
            self.prince_footstep_timer += 1
            if self.prince_footstep_timer >= self.prince_footstep_interval:
                self.prince_footstep_timer = 0
                if self.footstep_sound:
                    self.footstep_sound.play()
        else:
            self.prince_is_walking = False
            self.prince_current_animation = "idle"
            
        # Mise à jour de l'animation du prince
        self.prince_animation_timer += 1
        if self.prince_animation_timer >= self.prince_animation_speed:
            self.prince_animation_timer = 0
            if self.prince_current_animation == "run":
                self.prince_animation_frame = (self.prince_animation_frame + 1) % len(self.prince_sprites["run"])
            else:  # idle
                self.prince_animation_frame = 0  # Frame fixe pour idle
            
        # Gestion de l'invulnérabilité du prince
        if self.prince_invulnerable:
            self.prince_invulnerable_timer += 1
            if self.prince_invulnerable_timer >= self.prince_invulnerable_duration:
                self.prince_invulnerable = False
                self.prince_invulnerable_timer = 0
                
        # Spawner des flèches qui visent le prince
        # Spawner le burst initial de 3 flèches dès le début
        if not self.initial_burst_spawned:
            for i in range(self.initial_arrow_burst):
                self.spawn_protection_arrow()
            self.initial_burst_spawned = True
            print(f"Burst initial de {self.initial_arrow_burst} flèches spawné !")
        
        self.arrow_spawn_timer += 1
        if self.arrow_spawn_timer >= self.arrow_spawn_interval:
            self.arrow_spawn_timer = 0
            self.arrow_spawn_interval = random.randint(8, 25)  # Intervalle très intense : 0.13-0.42s (encore plus rapide)
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
            prince_rect = pygame.Rect(self.current_prince_x, self.prince_y, 80, 105)  # Ajusté pour la nouvelle taille 80x105
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
        arrow.speed = 12  # Vitesse très rapide (était 8, maintenant 12)
        arrow.max_range = 3000  # Portée étendue pour atteindre le prince
        self.protection_arrows.append(arrow)
        print(f"Flèche tirée depuis tile 62 (x={arrow_x}, y={arrow_y}) vers prince (x={target_x}, y={target_y}) - Vitesse: {arrow.speed}")
        
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
            
            # Formation UNIQUEMENT À DROITE du prince, plus éloignée
            x = self.current_prince_x + 250 + (col * 60) + (row * 30)  # Plus loin du prince
            # TOUS LES ENNEMIS AU MÊME NIVEAU Y (pas de variation en hauteur)
            y = enemy_base_y  # Exactement la même hauteur pour tous
            
            enemy = Enemy(x, y, team="red")
            # Donner des actions aléatoires aux ennemis au début
            import random
            random_actions = ["idle", "run", "attack"]
            enemy.random_action = random.choice(random_actions)  # Attribut pour le système de mise à jour
            enemy.current_animation = enemy.random_action
            
            # Direction aléatoire au début
            enemy.facing_right = random.choice([True, False])
            
            # Mouvement aléatoire léger
            if enemy.random_action == "run":
                enemy.random_velocity = random.uniform(-1, 1)  # Attribut pour le système de mise à jour
                enemy.velocity_x = enemy.random_velocity  # Mouvement lent aléatoire
                enemy.velocity_y = random.uniform(-0.5, 0.5)
            
            # Ils ne visent pas encore le prince
            enemy.is_attacking = False
            enemy.current_behavior = "patrol"  # Comportement de patrouille aléatoire
            self.final_enemies.append(enemy)
        
        # Marquer le moment de création des ennemis pour déclencher la mort après 3 secondes
        self.final_enemies_creation_time = self.state_timer
            
    def update_final_sequence(self):
        """Met à jour la séquence finale (tous les ennemis sont déjà morts, juste attendre)"""
        # Mettre à jour l'onde de choc haki si active
        if self.haki_shockwave_active:
            self.haki_shockwave_radius += self.haki_shockwave_speed
            
            # Commencer le fade quand l'onde atteint 50% de sa taille max
            fade_start_radius = self.haki_shockwave_max_radius * 0.5
            if self.haki_shockwave_radius >= fade_start_radius:
                self.haki_shockwave_alpha = max(0, self.haki_shockwave_alpha - self.haki_shockwave_fade_speed)
            
            # Désactiver quand l'alpha atteint 0 ou radius max
            if (self.haki_shockwave_alpha <= 0 or 
                self.haki_shockwave_radius >= self.haki_shockwave_max_radius):
                self.haki_shockwave_active = False
        
        # Le prince reste en idle mais avec animation normale pendant la séquence finale
        self.prince_current_animation = "idle"
        # Permettre l'animation idle normale au lieu de la figer à la frame 0
        self.update_prince_animation()
        
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
            
            # Debug : afficher les informations du prince (plus fréquent pour final_sequence)
            debug_interval = 30 if self.state == "final_sequence" else 60  # Plus fréquent en final_sequence
            if self.state_timer % debug_interval == 0:
                print(f"Prince Debug - État: {self.state}, Animation: {self.prince_current_animation}, Frame: {self.prince_animation_frame}")
                print(f"Prince Position: screen({screen_x:.1f}, {screen_y:.1f}), world({self.current_prince_x:.1f}, {self.prince_y}), camera({camera_x:.1f}, {camera_y:.1f})")
                print(f"Sprites disponibles: {list(self.prince_sprites.keys()) if self.prince_sprites else 'None'}")
            
            # Utiliser le sprite animé du prince
            if self.prince_sprites and self.prince_current_animation in self.prince_sprites:
                current_sprites = self.prince_sprites[self.prince_current_animation]
                if len(current_sprites) > 0:
                    safe_frame = self.prince_animation_frame % len(current_sprites)
                    current_sprite = current_sprites[safe_frame]
                    
                    # Effet de clignotement si invulnérable
                    if self.prince_invulnerable and (self.prince_invulnerable_timer // 10) % 2 == 0:
                        pass  # Ne pas dessiner (clignotement)
                    else:
                        screen.blit(current_sprite, (screen_x, screen_y))
                        
                        # Debug supplémentaire pour final_sequence
                        if self.state == "final_sequence" and self.state_timer % 30 == 0:
                            print(f"Prince dessiné à l'écran position ({screen_x:.1f}, {screen_y:.1f})")
                else:
                    # Pas de sprites dans l'animation - fallback
                    if not (self.prince_invulnerable and (self.prince_invulnerable_timer // 10) % 2 == 0):
                        pygame.draw.rect(screen, (255, 0, 0), (screen_x, screen_y, 80, 105))  # Rouge pour debug
                        if self.state == "final_sequence":
                            print(f"Prince FALLBACK ROUGE dessiné à ({screen_x:.1f}, {screen_y:.1f})")
            else:
                # Fallback : rectangle doré si les sprites ne sont pas chargés
                if not (self.prince_invulnerable and (self.prince_invulnerable_timer // 10) % 2 == 0):
                    pygame.draw.rect(screen, (255, 215, 0), (screen_x, screen_y, 80, 105))  # Ajusté pour la taille finale 80x105
                    if self.state == "final_sequence":
                        print(f"Prince FALLBACK OR dessiné à ({screen_x:.1f}, {screen_y:.1f})")
        
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
        
        # Dessiner l'effet d'onde de choc haki avec inversion des couleurs
        if self.haki_shockwave_active:
            self.draw_haki_shockwave(screen, camera_x, camera_y)
    
    def draw_haki_shockwave(self, screen, camera_x, camera_y):
        """Dessine l'effet d'onde de choc avec inversion des couleurs, limité au-dessus du sol"""
        # Position de l'onde de choc à l'écran
        center_x = self.haki_shockwave_center_x - camera_x
        center_y = self.haki_shockwave_center_y - camera_y
        
        # Niveau du sol (même que battlefield_manager)
        ground_level = 655
        ground_screen_y = ground_level - camera_y
        
        if self.haki_shockwave_radius > 0:
            screen_width = screen.get_width()
            screen_height = screen.get_height()
            
            # Calculer le rectangle qui contient le cercle, mais limité au-dessus du sol
            circle_rect = pygame.Rect(
                int(center_x - self.haki_shockwave_radius),
                int(center_y - self.haki_shockwave_radius),
                int(self.haki_shockwave_radius * 2),
                int(self.haki_shockwave_radius * 2)
            )
            
            # Limiter le rectangle au-dessus du sol
            if circle_rect.bottom > ground_screen_y:
                circle_rect.height = max(0, ground_screen_y - circle_rect.top)
            
            # Créer le rectangle de l'écran pour intersection
            screen_rect = pygame.Rect(0, 0, screen_width, screen_height)
            
            # Calculer l'intersection entre le cercle et l'écran
            clipped_rect = circle_rect.clip(screen_rect)
            
            # Vérifier que l'intersection est valide
            if clipped_rect.width > 0 and clipped_rect.height > 0:
                try:
                    # Capturer la zone de l'écran qui intersecte avec le cercle
                    area_surface = screen.subsurface(clipped_rect).copy()
                    
                    # Créer un masque circulaire de la même taille que la zone clippée
                    mask_surface = pygame.Surface((clipped_rect.width, clipped_rect.height), pygame.SRCALPHA)
                    mask_surface.fill((0, 0, 0, 0))  # Rendre explicitement transparent
                    
                    # Position relative du centre dans le rectangle clippé
                    rel_center_x = center_x - clipped_rect.x
                    rel_center_y = center_y - clipped_rect.y
                    
                    # S'assurer que le centre est dans la zone clippée
                    if (rel_center_x >= -self.haki_shockwave_radius and 
                        rel_center_y >= -self.haki_shockwave_radius and
                        rel_center_x <= clipped_rect.width + self.haki_shockwave_radius and
                        rel_center_y <= clipped_rect.height + self.haki_shockwave_radius):
                        
                        # Dessiner le cercle sur le masque, mais seulement la partie au-dessus du sol
                        pygame.draw.circle(mask_surface, (255, 255, 255, 255), 
                                         (int(rel_center_x), int(rel_center_y)), 
                                         int(self.haki_shockwave_radius))
                        
                        # Inverser les couleurs de la zone capturée
                        inverted_surface = pygame.Surface((clipped_rect.width, clipped_rect.height), pygame.SRCALPHA)
                        inverted_surface.fill((0, 0, 0, 0))  # Transparent par défaut
                        
                        # Créer une surface temporaire pour l'inversion
                        temp_surface = pygame.Surface((clipped_rect.width, clipped_rect.height))
                        temp_surface.fill((255, 255, 255))
                        temp_surface.blit(area_surface, (0, 0), special_flags=pygame.BLEND_SUB)
                        
                        # Copier seulement la partie du cercle avec le masque
                        inverted_surface.blit(temp_surface, (0, 0))
                        inverted_surface.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_MULT)
                        
                        # Appliquer la zone inversée sur l'écran original avec un blend plus doux
                        screen.blit(inverted_surface, clipped_rect.topleft)
                        
                except (ValueError, pygame.error) as e:
                    # Si l'inversion échoue, continuer sans (juste dessiner les cercles)
                    print(f"Warning: Haki color inversion failed: {e}")
            
            # Dessiner la bordure de l'onde de choc (seulement au-dessus du sol)
            if (center_x + self.haki_shockwave_radius >= 0 and 
                center_x - self.haki_shockwave_radius <= screen_width and
                center_y + self.haki_shockwave_radius >= 0 and 
                center_y - self.haki_shockwave_radius <= screen_height):
                
                # Dessiner uniquement si le centre est au-dessus du sol
                if center_y < ground_screen_y:
                    # Si une partie du cercle est sous le sol, utiliser un cercle simple
                    pygame.draw.circle(screen, (255, 255, 255), 
                                     (int(center_x), int(center_y)), 
                                     int(self.haki_shockwave_radius), 4)
                    
                    # Cercle intérieur plus fin
                    if self.haki_shockwave_radius > 8:
                        pygame.draw.circle(screen, (200, 200, 255), 
                                         (int(center_x), int(center_y)), 
                                         int(self.haki_shockwave_radius - 4), 2)
                
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
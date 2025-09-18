import pygame
import random

class Arrow:
    # Charger les sons une seule fois pour toutes les flèches
    _sounds_loaded = False
    _flying_sound = None
    _impact_sound = None
    
    @classmethod
    def load_sounds(cls):
        """Charge les sons une seule fois"""
        if not cls._sounds_loaded:
            try:
                pygame.mixer.init()
                cls._flying_sound = pygame.mixer.Sound("assets/sounds/arrow-flying.wav")
                cls._impact_sound = pygame.mixer.Sound("assets/sounds/arrow-impact.wav")
                # Réduire le volume des sons
                cls._flying_sound.set_volume(0.3)
                cls._impact_sound.set_volume(0.5)
                cls._sounds_loaded = True
            except pygame.error as e:
                print(f"Erreur lors du chargement des sons de flèche: {e}")
                cls._flying_sound = None
                cls._impact_sound = None
                cls._sounds_loaded = True
    
    def __init__(self, start_x, start_y, target_x, target_y, arrow_type="normal"):
        # Charger les sons si ce n'est pas déjà fait
        Arrow.load_sounds()
        
        self.rect = pygame.Rect(start_x, start_y, 25, 2)  # Flèche encore plus fine et un peu plus courte
        self.arrow_type = arrow_type  # "normal" ou "curtain"
        
        # Jouer le son de vol quand la flèche apparaît
        if Arrow._flying_sound:
            Arrow._flying_sound.play()
        
        # Calculer la trajectoire vers la cible
        import math
        dx = target_x - start_x
        dy = target_y - start_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Vitesse augmentée pour couvrir de grandes distances
        speed = 15  # Augmenté pour une meilleure portée
        
        # Vitesses normalisées
        self.velocity_x = (dx / distance) * speed if distance > 0 else 0
        self.velocity_y = (dy / distance) * speed if distance > 0 else speed
        
        # Gravité encore réduite pour une trajectoire très longue
        self.gravity = 0.05  # Réduit encore pour couvrir toute la map
        self.rotation = math.atan2(dy, dx) * 180 / math.pi  # Rotation initiale
        
        # Gestion de la portée
        self.start_x = start_x
        self.start_y = start_y
        self.max_range = 800  # Sera défini par l'ArrowManager
        self.distance_traveled = 0
        
        # État de la flèche
        self.is_stuck = False
        self.stuck_timer = 0
        self.stuck_duration = 300  # 5 secondes à 60 FPS
        self.impact_sound_played = False  # Pour éviter de jouer le son plusieurs fois
        
        # Créer le sprite de la flèche fine et longue (orientée vers la droite par défaut)
        self.image = pygame.Surface((25, 2), pygame.SRCALPHA)  # Surface encore plus fine
        # Corps de la flèche (horizontal) - très fin
        pygame.draw.rect(self.image, (139, 69, 19), (0, 0, 20, 2))  # Corps bois très fin
        # Pointe de la flèche
        pygame.draw.polygon(self.image, (169, 169, 169), [(20, 0), (25, 1), (20, 2)])  # Pointe grise fine
        # Empennage
        pygame.draw.polygon(self.image, (100, 50, 0), [(0, 0), (2, 1), (0, 2)])  # Empennage brun fin
        
    def update(self):
        """Met à jour la position de la flèche"""
        if self.is_stuck:
            # Si la flèche est plantée, juste compter le timer
            self.stuck_timer += 1
            return
            
        # Calculer la distance avant de bouger
        import math
        old_x, old_y = self.rect.x, self.rect.y
        
        self.velocity_y += self.gravity  # Appliquer la gravité
        self.rect.x += self.velocity_x
        self.rect.y += self.velocity_y
        
        # Calculer la distance parcourue
        dx = self.rect.x - old_x
        dy = self.rect.y - old_y
        self.distance_traveled += math.sqrt(dx*dx + dy*dy)
        
        # Mettre à jour la rotation basée sur la direction actuelle
        self.rotation = math.atan2(self.velocity_y, self.velocity_x) * 180 / math.pi
        
    def stick_to_ground(self, ground_y):
        """Plante la flèche au sol"""
        if not self.impact_sound_played:
            # Jouer le son d'impact une seule fois
            if Arrow._impact_sound:
                Arrow._impact_sound.play()
            self.impact_sound_played = True
            
        self.is_stuck = True
        self.rect.y = ground_y - self.rect.height
        self.velocity_x = 0
        self.velocity_y = 0
        self.stuck_timer = 0
        # Rotation verticale pour une flèche plantée
        self.rotation = 90
        
    def draw(self, screen, camera_x, camera_y):
        """Dessine la flèche avec une orientation correcte et un contour blanc"""
        # Position à l'écran
        screen_x = self.rect.x - camera_x
        screen_y = self.rect.y - camera_y
        
        # Calculer l'angle de rotation en degrés (sans ajustement car le sprite est déjà orienté correctement)
        rotation_angle = self.rotation
        
        # Rotation de l'image
        rotated_image = pygame.transform.rotate(self.image, -rotation_angle)  # Négatif pour rotation dans le bon sens
        rotated_rect = rotated_image.get_rect(center=(screen_x + self.rect.width//2, screen_y + self.rect.height//2))
        
        # Créer un contour blanc autour de la flèche
        # Créer une version agrandie de l'image pour le contour
        outline_size = 2  # Épaisseur du contour
        outline_image = pygame.Surface((rotated_image.get_width() + outline_size * 2, 
                                       rotated_image.get_height() + outline_size * 2), pygame.SRCALPHA)
        
        # Dessiner le contour blanc en décalant l'image dans toutes les directions
        for dx in range(-outline_size, outline_size + 1):
            for dy in range(-outline_size, outline_size + 1):
                if dx != 0 or dy != 0:  # Ne pas dessiner au centre
                    # Créer une version blanche de l'image
                    white_image = rotated_image.copy()
                    white_image.fill((255, 255, 255), special_flags=pygame.BLEND_MULT)
                    outline_image.blit(white_image, (outline_size + dx, outline_size + dy))
        
        # Dessiner l'image originale par-dessus le contour
        outline_image.blit(rotated_image, (outline_size, outline_size))
        
        # Ajuster la position pour centrer le contour
        outline_rect = outline_image.get_rect(center=(screen_x + self.rect.width//2, screen_y + self.rect.height//2))
        
        screen.blit(outline_image, outline_rect)
        
    def is_off_screen(self, screen_height):
        """Vérifie si la flèche est sortie de l'écran ou a atteint sa portée maximale"""
        if self.is_stuck:
            # Si plantée, disparaît après le timer
            return self.stuck_timer > self.stuck_duration
        return (self.rect.y > screen_height + 50 or 
                self.distance_traveled > self.max_range)

class ArrowManager:
    def __init__(self, screen_width, screen_height, castle_door_x):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.castle_door_x = castle_door_x  # Position X de la porte du château
        self.arrows = []
        self.spawn_timer = 0
        self.spawn_delay = random.randint(30, 60)  # Délai réduit pour plus de flèches
        
        # Cooldown entre flèches individuelles (0.5 secondes = 30 frames à 60 FPS)
        self.arrow_cooldown = 30
        self.last_arrow_time = 0
        
        # Gestion des types d'attaque
        self.attack_type_timer = 0
        self.next_attack_type = "normal"  # "normal" ou "curtain"
        self.curtain_delay = random.randint(300, 600)  # 5-10 secondes entre les rideaux
        
        # Gestion du rideau de flèches séquentiel
        self.curtain_active = False
        self.curtain_arrows_to_spawn = []  # Liste des flèches à spawner avec leur timing
        self.curtain_timer = 0
        
        # Position fixe : tile (62, 20) convertie en pixels
        # Propriétés de la tilemap (depuis level1.py)
        tile_size = 16  # Taille originale d'une tile
        scale_factor = 2.5  # Facteur de zoom de la tilemap
        map_height = 20  # Hauteur de la map en tiles
        map_total_height = map_height * tile_size * scale_factor  # 800 pixels
        map_offset_y = screen_height - map_total_height  # Offset Y de la map
        
        # Position de l'archer : retour à la tile 62 comme demandé
        # Le joueur va de droite à gauche, l'archer tire depuis la position 62
        # Map width = 100 tiles * 16 * 2.5 = 4000 pixels
        tile_x = 62  # Position tile 62 comme spécifié
        tile_y = -5  # Plus haut que le sommet de la map pour avoir une meilleure trajectoire
        
        # Conversion en coordonnées pixel
        self.archer_x = tile_x * tile_size * scale_factor  # 62 * 16 * 2.5 = 2480
        self.archer_y = map_offset_y + (tile_y * tile_size * scale_factor)  # Bien au-dessus de la map
        
        # Portée étendue pour couvrir toute la tilemap
        # Map totale = 100 tiles * 16 * 2.5 = 4000 pixels
        # Archer à 2480 pixels, donc portée de 3000 pour couvrir toute la map
        self.arrow_max_range = 3000  # Portée étendue pour couvrir toute la tilemap
        
        # Position du sol pour les flèches plantées
        self.ground_level = screen_height - 100  # Approximation du niveau du sol
        

        
    def should_spawn_arrows(self, player_x):
        """Détermine si on doit spawner des flèches basé sur la position du joueur"""
        # Calculer la position de la tile 70 (début de la zone de bataille)
        tile_size = 16  # Taille originale d'une tile
        scale_factor = 2.5  # Facteur d'échelle
        tile_70_x = 70 * tile_size * scale_factor  # Position X de la tile 70
        
        # Arrêter de tirer si le joueur a atteint ou dépassé la tile 70
        if player_x <= tile_70_x:
            return False  # Plus de tir dans la zone de bataille
        
        return True  # Continuer à tirer avant la tile 70
        
    def update(self, player_x, player_y, collision_tiles=None):
        """Met à jour le gestionnaire de flèches"""
        # Incrémenter le timer pour le cooldown des flèches
        self.last_arrow_time += 1
        
        # Gestion du type d'attaque
        self.attack_type_timer += 1
        if self.attack_type_timer >= self.curtain_delay and not self.curtain_active:
            self.next_attack_type = "curtain"
            self.attack_type_timer = 0
            self.curtain_delay = random.randint(300, 600)  # Prochain rideau dans 5-10 secondes
        
        # Gestion du rideau de flèches séquentiel
        if self.curtain_active:
            self.curtain_timer += 1
            # Vérifier si il faut spawner une flèche du rideau
            arrows_to_remove = []
            for i, (spawn_time, target_x, target_y) in enumerate(self.curtain_arrows_to_spawn):
                if self.curtain_timer >= spawn_time:
                    # Spawner cette flèche
                    arrow = Arrow(self.archer_x, self.archer_y, target_x, target_y, "curtain")
                    arrow.max_range = self.arrow_max_range
                    arrow.start_x = self.archer_x
                    arrow.start_y = self.archer_y
                    self.arrows.append(arrow)
                    arrows_to_remove.append(i)
            
            # Supprimer les flèches spawnées de la liste d'attente
            for i in reversed(arrows_to_remove):
                self.curtain_arrows_to_spawn.pop(i)
            
            # Terminer le rideau si toutes les flèches ont été spawnées
            if not self.curtain_arrows_to_spawn:
                self.curtain_active = False
                self.curtain_timer = 0
        
        # Spawner de nouvelles flèches si le joueur n'a pas atteint la porte
        if self.should_spawn_arrows(player_x) and not self.curtain_active:
            self.spawn_timer += 1
            if self.spawn_timer >= self.spawn_delay:
                if self.next_attack_type == "curtain":
                    # Préparer un rideau de flèches
                    self.prepare_arrow_curtain(player_x, player_y)
                    self.next_attack_type = "normal"
                else:
                    # Spawner des flèches normales avec cooldown
                    num_arrows = random.randint(2, 4)
                    arrows_spawned = 0
                    for _ in range(num_arrows):
                        # Vérifier le cooldown avant de spawner chaque flèche
                        if self.last_arrow_time >= self.arrow_cooldown:
                            self.spawn_arrow(player_x, player_y)
                            self.last_arrow_time = 0  # Reset du cooldown
                            arrows_spawned += 1
                            break  # Une seule flèche par cycle pour respecter le cooldown
                    
                    # Si aucune flèche n'a été spawnée à cause du cooldown, ne pas reset le timer
                    if arrows_spawned > 0:
                        self.spawn_timer = 0
                        self.spawn_delay = random.randint(40, 80)  # Délai réduit pour plus d'action
        
        # Mettre à jour toutes les flèches
        for arrow in self.arrows[:]:  # Copie de la liste pour modification sûre
            arrow.update()
            
            # Vérifier collision avec le sol
            if not arrow.is_stuck and collision_tiles:
                for tile_rect in collision_tiles:
                    if arrow.rect.colliderect(tile_rect):
                        # Planter la flèche au sol
                        arrow.stick_to_ground(tile_rect.top)
                        break
            
            if arrow.is_off_screen(self.screen_height):
                self.arrows.remove(arrow)
                
    def spawn_arrow(self, player_x, player_y):
        """Spawne une nouvelle flèche depuis la position fixe vers le joueur"""
        # Viser directement le joueur avec une marge d'erreur réaliste
        # Réduire la marge d'erreur pour une visée plus précise
        target_x = player_x + random.randint(-30, 30)  # Marge d'erreur réduite
        target_y = player_y + random.randint(-15, 15)  # Marge d'erreur réduite
        
        arrow = Arrow(self.archer_x, self.archer_y, target_x, target_y, "normal")
        arrow.max_range = self.arrow_max_range  # Définir la portée maximale
        arrow.start_x = self.archer_x  # Position de départ pour calculer la distance
        arrow.start_y = self.archer_y

        self.arrows.append(arrow)
        
    def prepare_arrow_curtain(self, player_x, player_y):
        """Prépare un rideau de flèches séquentiel"""
        self.curtain_active = True
        self.curtain_timer = 0
        self.curtain_arrows_to_spawn = []
        
        # Paramètres du rideau
        num_arrows = 8  # Nombre de flèches dans le rideau
        time_between_arrows = 10  # 0.5 secondes à 60 FPS
        spatial_offset = 80  # Décalage spatial entre chaque flèche (augmenté)
        
        # Direction du mouvement du joueur (vers la gauche)
        player_direction = -1  # Le joueur va vers la gauche
        # Le rideau doit aller dans le sens OPPOSÉ (de gauche vers droite)
        curtain_direction = 1  # Rideau va vers la droite
        
        # Calculer la position de départ du rideau (à gauche du joueur)
        start_x = player_x - 300  # Commencer bien à gauche du joueur
        
        # Créer la séquence de flèches qui balaient de gauche à droite
        for i in range(num_arrows):
            spawn_time = i * time_between_arrows
            target_x = start_x + (i * spatial_offset * curtain_direction)  # Balayage vers la droite
            target_y = player_y + random.randint(-30, 30)  # Petite variation verticale
            
            self.curtain_arrows_to_spawn.append((spawn_time, target_x, target_y))
            
    def spawn_arrow_curtain(self, player_x, player_y):
        """Ancienne méthode - gardée pour compatibilité mais remplacée par prepare_arrow_curtain"""
        self.prepare_arrow_curtain(player_x, player_y)
        
    def check_collisions(self, player_rect):
        """Vérifie les collisions avec le joueur"""
        for arrow in self.arrows[:]:
            # Seulement les flèches en mouvement peuvent toucher le joueur
            if not arrow.is_stuck and arrow.rect.colliderect(player_rect):
                self.arrows.remove(arrow)
                return True
        return False
        
    def draw(self, screen, camera_x, camera_y):
        """Dessine toutes les flèches"""

        for arrow in self.arrows:
            arrow.draw(screen, camera_x, camera_y)
            
    def clear_arrows(self):
        """Vide toutes les flèches (utile lors du respawn)"""
        self.arrows.clear()

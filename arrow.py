import pygame
import random

class Arrow:
    def __init__(self, start_x, start_y, target_x, target_y):
        self.rect = pygame.Rect(start_x, start_y, 20, 5)  # Flèche horizontale
        
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
        
        # Créer le sprite de la flèche (orientée vers la droite par défaut)
        self.image = pygame.Surface((20, 5), pygame.SRCALPHA)  # Surface transparente
        # Corps de la flèche (horizontal)
        pygame.draw.rect(self.image, (139, 69, 19), (0, 1, 15, 3))  # Corps bois
        # Pointe de la flèche
        pygame.draw.polygon(self.image, (169, 169, 169), [(15, 0), (20, 2), (15, 4)])  # Pointe grise
        # Empennage
        pygame.draw.polygon(self.image, (100, 50, 0), [(0, 0), (3, 2), (0, 4)])  # Empennage brun
        
    def update(self):
        """Met à jour la position de la flèche"""
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
        
    def draw(self, screen, camera_x, camera_y):
        """Dessine la flèche avec une orientation correcte"""
        # Position à l'écran
        screen_x = self.rect.x - camera_x
        screen_y = self.rect.y - camera_y
        
        # Calculer l'angle de rotation en degrés (sans ajustement car le sprite est déjà orienté correctement)
        rotation_angle = self.rotation
        
        # Rotation de l'image
        rotated_image = pygame.transform.rotate(self.image, -rotation_angle)  # Négatif pour rotation dans le bon sens
        rotated_rect = rotated_image.get_rect(center=(screen_x + self.rect.width//2, screen_y + self.rect.height//2))
        
        screen.blit(rotated_image, rotated_rect)
        
    def is_off_screen(self, screen_height):
        """Vérifie si la flèche est sortie de l'écran ou a atteint sa portée maximale"""
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
        
    def should_spawn_arrows(self, player_x):
        """Détermine si on doit spawner des flèches basé sur la position du joueur"""
        # L'archer tire toujours, peu importe la position du joueur
        # Seule condition : le joueur doit être vivant (cette vérification se fait ailleurs)
        return True  # Tir permanent
        
    def update(self, player_x, player_y):
        """Met à jour le gestionnaire de flèches"""
        # Spawner de nouvelles flèches si le joueur n'a pas atteint la porte
        if self.should_spawn_arrows(player_x):
            self.spawn_timer += 1
            if self.spawn_timer >= self.spawn_delay:
                # Spawner plusieurs flèches à la fois (2 à 4)
                num_arrows = random.randint(2, 4)
                for _ in range(num_arrows):
                    self.spawn_arrow(player_x, player_y)
                
                self.spawn_timer = 0
                self.spawn_delay = random.randint(40, 80)  # Délai réduit pour plus d'action
        
        # Mettre à jour toutes les flèches
        for arrow in self.arrows[:]:  # Copie de la liste pour modification sûre
            arrow.update()
            if arrow.is_off_screen(self.screen_height):
                self.arrows.remove(arrow)
                
    def spawn_arrow(self, player_x, player_y):
        """Spawne une nouvelle flèche depuis la position fixe vers le joueur"""
        # Debug: afficher les positions
        # print(f"Archer: ({self.archer_x}, {self.archer_y}), Joueur: ({player_x}, {player_y})")
        
        # Viser directement le joueur avec une marge d'erreur réaliste
        # Réduire la marge d'erreur pour une visée plus précise
        target_x = player_x + random.randint(-30, 30)  # Marge d'erreur réduite
        target_y = player_y + random.randint(-15, 15)  # Marge d'erreur réduite
        
        arrow = Arrow(self.archer_x, self.archer_y, target_x, target_y)
        arrow.max_range = self.arrow_max_range  # Définir la portée maximale
        arrow.start_x = self.archer_x  # Position de départ pour calculer la distance
        arrow.start_y = self.archer_y
        self.arrows.append(arrow)
        
    def check_collisions(self, player_rect):
        """Vérifie les collisions avec le joueur"""
        for arrow in self.arrows[:]:
            if arrow.rect.colliderect(player_rect):
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

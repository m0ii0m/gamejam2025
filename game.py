import pygame
import sys
from level1 import Level1
from player import Player
from player_manager import PlayerManager
from arrow import ArrowManager
from battlefield_manager import BattlefieldManager

import pygame

class Game:
    def __init__(self, screen):

        pygame.mixer.init()
        pygame.mixer.set_num_channels(8)  
        self.screen = screen
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        
        # États du jeu
        self.game_state = "level1"  # Pour l'instant, on commence directement au niveau 1
        
        # Initialisation du niveau 1
        self.level1 = Level1(self.screen)
        
        # Calculer la position de la porte du château (approximativement 80% de la largeur de la map)
        map_width_pixels = self.level1.map_width * self.level1.tile_size * self.level1.scale_factor
        castle_door_x = map_width_pixels * 0.8  # Position approximative de la porte
        
        # Position de spawn initiale du joueur (côté droit)
        start_x = map_width_pixels - 300  # 300 pixels avant la fin de la map
        
        # Position Y : Sur le sol (ligne 18-19 de la tilemap selon l'image)
        ground_tile_y = 17  # Ligne du sol dans la tilemap
        # Créer un joueur temporaire pour connaître sa hauteur
        temp_player = Player(0, 0)
        start_y = ground_tile_y * self.level1.tile_size * self.level1.scale_factor + self.level1.map_offset_y - temp_player.rect.height
        
        # Gestionnaire de joueurs et système de respawn
        self.player_manager = PlayerManager(start_x, start_y, castle_door_x)
        
        # Gestionnaire de flèches
        self.arrow_manager = ArrowManager(self.screen_width, self.screen_height, castle_door_x)
        
        # Gestionnaire de champ de bataille
        map_width_pixels = self.level1.map_width * self.level1.tile_size * self.level1.scale_factor
        self.battlefield_manager = BattlefieldManager(map_width_pixels, self.screen_height)
        
        # Camera
        self.camera_x = 0
        self.camera_y = 0
        
    def state_manager(self):
        """Gère les différents états du jeu"""
        # Gestion des événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
        
        if self.game_state == "level1":
            self.update_level1()
            self.draw_level1()
    
    def update_level1(self):
        """Met à jour le niveau 1"""
        # Récupération des touches pressées
        keys = pygame.key.get_pressed()
        
        # Mise à jour du gestionnaire de joueurs
        self.player_manager.update(keys, self.level1.get_collision_tiles(), self.arrow_manager)
        
        # Mise à jour du gestionnaire de flèches
        current_player = self.player_manager.get_current_player()
        self.arrow_manager.update(current_player.rect.x, current_player.rect.y, self.level1.get_collision_tiles())
        
        # Mise à jour du champ de bataille
        current_player = self.player_manager.get_current_player()
        self.battlefield_manager.update(self.level1.get_collision_tiles(), current_player)
        
        # Mise à jour de la caméra pour suivre le joueur
        self.update_camera()
    
    def update_camera(self):
        """Met à jour la position de la caméra pour suivre le joueur"""
        # Centrer la caméra sur le joueur actuel
        current_player = self.player_manager.get_current_player()
        target_x = current_player.rect.centerx - self.screen_width // 2
        
        # Limites de la caméra pour ne pas sortir de la map
        map_width = self.level1.map_width * self.level1.tile_size * self.level1.scale_factor
        
        # Permettre à la caméra de voir toute la largeur de la map
        self.camera_x = max(0, min(target_x, map_width - self.screen_width))
        
        # FIXER la caméra Y à 0 pour que la tilemap reste toujours collée en bas
        self.camera_y = 0
    
    def draw_level1(self):
        """Dessine le niveau 1"""
        # Ne pas effacer ici - le niveau 1 gère son propre background
        
        # Dessiner le niveau (background + tilemap background)
        self.level1.draw(self.screen, self.camera_x, self.camera_y)
        
        # Dessiner le champ de bataille (warriors et enemies) EN ARRIÈRE-PLAN
        self.battlefield_manager.draw(self.screen, self.camera_x, self.camera_y)
        
        # Dessiner les flèches
        self.arrow_manager.draw(self.screen, self.camera_x, self.camera_y)
        
        # Dessiner les layers foreground par-dessus les NPCs
        self.level1.draw_foreground_tilemap(self.screen, self.camera_x, self.camera_y)
        
        # Dessiner le gestionnaire de joueurs (joueur actuel + corps morts) AU PREMIER PLAN
        self.player_manager.draw(self.screen, self.camera_x, self.camera_y)
        
        # Dessiner la barre de santé
        self.player_manager.draw_health_bar(self.screen)
        
        # Dessiner l'interface de bataille
        self.battlefield_manager.draw_battle_ui(self.screen)

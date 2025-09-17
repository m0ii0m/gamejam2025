import pygame
from player import Player

class DeadBody:
    """Représente le corps d'un joueur mort"""
    def __init__(self, x, y, player_sprites):
        self.rect = pygame.Rect(x, y, 75, 75)
        self.sprites = player_sprites
        # Utiliser la dernière frame de l'animation de mort
        self.death_sprite = self.sprites["death"][-1] if "death" in self.sprites else None
        
    def draw(self, screen, camera_x, camera_y):
        """Dessine le corps mort"""
        if self.death_sprite:
            screen_x = self.rect.x - camera_x
            screen_y = self.rect.y - camera_y
            screen.blit(self.death_sprite, (screen_x, screen_y))

class PlayerManager:
    """Gère les joueurs, les morts et les respawns"""
    def __init__(self, initial_x, initial_y, castle_door_x):
        self.castle_door_x = castle_door_x
        self.initial_spawn_x = initial_x
        self.initial_spawn_y = initial_y
        
        # Joueur actuel
        self.current_player = Player(initial_x, initial_y)
        
        # Liste des corps morts
        self.dead_bodies = []
        
        # État du respawn
        self.respawning = False
        self.new_player = None
        self.respawn_timer = 0
        self.respawn_duration = 120  # 2 secondes à 60 FPS
        
    def update(self, keys, collision_tiles, arrow_manager):
        """Met à jour le gestionnaire de joueurs"""
        if self.respawning:
            self.handle_respawn(keys, collision_tiles)
        else:
            # Mettre à jour le joueur actuel
            self.current_player.update(keys, collision_tiles)
            
            # Vérifier les collisions avec les flèches
            if arrow_manager.check_collisions(self.current_player.rect):
                self.current_player.take_arrow_hit()
            
            # Vérifier si le joueur est mort et a fini de tomber
            if self.current_player.is_dead and self.current_player.death_fall_complete:
                self.start_respawn()
    
    def handle_respawn(self, keys, collision_tiles):
        """Gère le processus de respawn"""
        self.respawn_timer += 1
        
        if self.new_player is None:
            # Créer le nouveau joueur qui arrive de la droite
            spawn_x = self.castle_door_x + 200  # Commencer hors écran à droite
            self.new_player = Player(spawn_x, self.initial_spawn_y)
            
        # Le nouveau joueur se déplace automatiquement vers la position du corps
        target_x = self.dead_bodies[-1].rect.x if self.dead_bodies else self.initial_spawn_x
        
        if self.new_player.rect.x > target_x + 50:  # S'arrêter près du corps
            self.new_player.rect.x -= 3  # Vitesse d'approche
            self.new_player.current_animation = "run"
            self.new_player.facing_right = False
        else:
            # Le nouveau joueur est arrivé, passer le contrôle
            self.new_player.current_animation = "idle"
            self.current_player = self.new_player
            self.new_player = None
            self.respawning = False
            self.respawn_timer = 0
        
        # Mettre à jour l'animation du nouveau joueur
        if self.new_player:
            self.new_player.update_animation()
    
    def start_respawn(self):
        """Démarre le processus de respawn"""
        # Ajouter le corps mort à la liste
        dead_body = DeadBody(
            self.current_player.rect.x, 
            self.current_player.rect.y,
            self.current_player.sprites
        )
        self.dead_bodies.append(dead_body)
        
        # Commencer le respawn
        self.respawning = True
        self.respawn_timer = 0
    
    def get_current_player(self):
        """Retourne le joueur actuel (celui qu'on contrôle)"""
        return self.current_player
    
    def is_at_castle_door(self):
        """Vérifie si le joueur a atteint la porte du château"""
        return self.current_player.rect.x >= self.castle_door_x - 100
    
    def draw(self, screen, camera_x, camera_y):
        """Dessine tous les éléments"""
        # Dessiner tous les corps morts
        for body in self.dead_bodies:
            body.draw(screen, camera_x, camera_y)
        
        # Dessiner le joueur actuel
        if not self.respawning:
            player_screen_x = self.current_player.rect.x - camera_x
            player_screen_y = self.current_player.rect.y - camera_y
            self.current_player.draw(screen, player_screen_x, player_screen_y)
        
        # Dessiner le nouveau joueur pendant le respawn
        if self.respawning and self.new_player:
            new_player_screen_x = self.new_player.rect.x - camera_x
            new_player_screen_y = self.new_player.rect.y - camera_y
            self.new_player.draw(screen, new_player_screen_x, new_player_screen_y)
    
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

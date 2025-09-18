import pygame
from player import Player
from QTE_manager import QTEManager

class PlayerManager2:
    """Gère les joueurs, les morts et les respawns"""
    def __init__(self, initial_x, initial_y):
        self.initial_spawn_x = initial_x
        self.initial_spawn_y = initial_y
        
        # Joueur actuel
        self.current_player = Player(initial_x, initial_y)
        self.current_player.update_can_move(False)
        
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

        self.horse_x = 450  # Position du cheval
        self.horse_trigger_zone_x = self.horse_x - 10  # Position du cheval
        self.horse_game_triggered = False
        self.horse_game_over = False
        self.horse_timer = 120 
        self.horse_score = 0
        
        self.key_e_img = pygame.image.load("assets/images/sprites/key/e1.png").convert_alpha()
        
    def update(self, keys, collision_tiles):
        """Met à jour le gestionnaire de joueurs"""
        self.QTE_manager.update(keys)

        if not self.horse_game_triggered and self.current_player.rect.x >= self.horse_trigger_zone_x:
            self.horse_game_triggered = True
            self.current_player.update_can_move(False)

        if self.horse_game_triggered and not self.horse_game_over:
            self.horse_timer -= 1
            if keys[pygame.K_e]:
                self.horse_score += 1

        if not self.horse_game_over and self.horse_timer<=0:
            self.horse_game_over = True
            self.current_player.update_can_move(True)
            # self.current_player.speed += self.horse_score

        if self.respawning:
            self.handle_respawn(keys, collision_tiles)
        else:
            # Mettre à jour le joueur actuel
            self.current_player.update(keys, collision_tiles)
            
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
        
        if self.new_player.rect.x > target_x:  # S'arrêter exactement à la position du corps
            self.new_player.rect.x -= 3  # Vitesse d'approche
            self.new_player.current_animation = "run"
            self.new_player.facing_right = False
        else:
            # Le nouveau joueur est arrivé exactement à la position du corps mort
            self.new_player.rect.x = target_x  # Position exacte
            self.new_player.current_animation = "idle"
            self.current_player = self.new_player
            self.new_player = None
            self.respawning = False
            self.respawn_timer = 0
        
        # Mettre à jour l'animation du nouveau joueur
        if self.new_player:
            self.new_player.update_animation()
    
    def get_current_player(self):
        """Retourne le joueur actuel (celui qu'on contrôle)"""
        return self.current_player
    
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

        
        if self.horse_game_triggered and not self.horse_game_over:
            img = self.key_e_img
            pos = (self.horse_x-img.get_width()//2, self.initial_spawn_y - 30)
            screen.blit(img, pos)
        
        self.QTE_manager.draw(screen,camera_x,camera_y)
        # # Dessiner le nouveau joueur pendant le respawn
        # if self.respawning and self.new_player:
        #     new_player_screen_x = self.new_player.rect.x - camera_x
        #     new_player_screen_y = self.new_player.rect.y - camera_y
        #     self.new_player.draw(screen, new_player_screen_x, new_player_screen_y)
    
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
        self.current_player.update_can_move(True)
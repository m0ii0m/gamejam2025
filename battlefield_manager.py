import pygame
import random
from enemy import Enemy
from warrior import Warrior

class BattlefieldManager:
    def __init__(self, tilemap_width=4000, tilemap_height=800):
        self.tilemap_width = tilemap_width
        self.tilemap_height = tilemap_height
        self.ground_level = 600  # Niveau du sol approximatif
        
        # Listes des combattants - Seulement des ennemis maintenant
        self.red_enemies = []    # Ennemis rouges
        self.blue_enemies = []   # Ennemis bleus
        
        # Paramètres de spawn - ENCORE PLUS DE RÉDUCTION DU NOMBRE D'ENNEMIS
        self.max_red_enemies = 15   # Réduit de 25 à 15
        self.max_blue_enemies = 15  # Réduit de 25 à 15
        self.spawn_timer = 0
        self.spawn_interval = 180   # Spawn toutes les 3 secondes au lieu de 2
        
        # Zones de spawn - RANDOM entre les tiles 70 et 100
        tile_size = 16  # Taille d'une tile
        scale_factor = 2.5  # Facteur d'échelle
        
        battlefield_start = 70 * tile_size * scale_factor  # Tile 70
        battlefield_end = 100 * tile_size * scale_factor   # Tile 100
        
        # Zone commune pour spawn aléatoire des deux équipes
        self.spawn_zone_start = int(battlefield_start)
        self.spawn_zone_end = int(battlefield_end)
        
        # Initialiser la bataille
        self.initialize_battlefield()
        
    def initialize_battlefield(self):
        """Initialise le champ de bataille avec les premiers combattants"""
        # Spawner les ennemis rouges - SPAWN RANDOM entre tiles 70-100, TRÈS PEU NOMBREUX
        for i in range(10):  # Réduit de 15 à 10
            x = random.randint(self.spawn_zone_start, self.spawn_zone_end)
            y = self.ground_level - 100  # Au-dessus du sol
            enemy = Enemy(x, y, team="red")
            self.red_enemies.append(enemy)
            
        # Spawner les ennemis bleus - SPAWN RANDOM entre tiles 70-100, TRÈS PEU NOMBREUX
        for i in range(10):  # Réduit de 15 à 10
            x = random.randint(self.spawn_zone_start, self.spawn_zone_end)
            y = self.ground_level - 100  # Au-dessus du sol
            enemy = Enemy(x, y, team="blue")
            self.blue_enemies.append(enemy)
            
    def update(self, collision_tiles, player=None):
        """Met à jour le champ de bataille"""
        self.spawn_timer += 1
        
        # Nettoyer les morts (après un délai)
        self.clean_dead_units()
        
        # Spawner de nouveaux combattants
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_new_units()
            self.spawn_timer = 0
            
        # Mettre à jour tous les ennemis rouges - PAS DE COLLISION ENTRE ENNEMIS
        for enemy in self.red_enemies[:]:
            enemy.update(collision_tiles, self.blue_enemies, self.red_enemies, player=None)  # Pas de joueur
            
        # Mettre à jour tous les ennemis bleus - PAS DE COLLISION ENTRE ENNEMIS
        for enemy in self.blue_enemies[:]:
            enemy.update(collision_tiles, self.red_enemies, self.blue_enemies, player=None)  # Pas de joueur
            
    def clean_dead_units(self):
        """Nettoie les unités mortes après un délai"""
        # Retirer les ennemis morts après 5 secondes
        self.red_enemies = [e for e in self.red_enemies if not e.is_dead or e.death_timer < 300]
        self.blue_enemies = [e for e in self.blue_enemies if not e.is_dead or e.death_timer < 300]
        
    def spawn_new_units(self):
        """Spawne de nouveaux combattants si nécessaire"""
        # Compter les vivants
        alive_red = sum(1 for e in self.red_enemies if not e.is_dead)
        alive_blue = sum(1 for e in self.blue_enemies if not e.is_dead)
        
        # Spawner de nouveaux ennemis rouges si nécessaire - SEUILS TRÈS RÉDUITS
        if len(self.red_enemies) < self.max_red_enemies and alive_red < 10:  # Réduit de 20 à 10
            x = random.randint(self.spawn_zone_start, self.spawn_zone_end)
            y = self.ground_level - 100
            enemy = Enemy(x, y, team="red")
            self.red_enemies.append(enemy)
            
        # Spawner de nouveaux ennemis bleus si nécessaire - SEUILS TRÈS RÉDUITS
        if len(self.blue_enemies) < self.max_blue_enemies and alive_blue < 10:  # Réduit de 20 à 10
            x = random.randint(self.spawn_zone_start, self.spawn_zone_end)
            y = self.ground_level - 100
            enemy = Enemy(x, y, team="blue")
            self.blue_enemies.append(enemy)
            
    def get_battle_statistics(self):
        """Retourne les statistiques de la bataille"""
        alive_red = sum(1 for e in self.red_enemies if not e.is_dead)
        alive_blue = sum(1 for e in self.blue_enemies if not e.is_dead)
        
        return {
            "total_red": len(self.red_enemies),
            "alive_red": alive_red,
            "total_blue": len(self.blue_enemies),
            "alive_blue": alive_blue
        }
        
    def get_nearby_units(self, x, y, radius=200):
        """Retourne les unités proches d'une position donnée"""
        nearby_red = []
        nearby_blue = []
        
        for enemy in self.red_enemies:
            if not enemy.is_dead:
                distance = ((enemy.rect.centerx - x) ** 2 + (enemy.rect.centery - y) ** 2) ** 0.5
                if distance <= radius:
                    nearby_red.append(enemy)
                    
        for enemy in self.blue_enemies:
            if not enemy.is_dead:
                distance = ((enemy.rect.centerx - x) ** 2 + (enemy.rect.centery - y) ** 2) ** 0.5
                if distance <= radius:
                    nearby_blue.append(enemy)
                    
        return nearby_red, nearby_blue
        
    def draw(self, screen, camera_x, camera_y):
        """Dessine tous les combattants"""
        # Dessiner tous les ennemis rouges
        for enemy in self.red_enemies:
            enemy.draw(screen, camera_x, camera_y)
            
        # Dessiner tous les ennemis bleus
        for enemy in self.blue_enemies:
            enemy.draw(screen, camera_x, camera_y)
            
    def draw_battle_ui(self, screen):
        """Interface de bataille supprimée selon la demande"""
        pass

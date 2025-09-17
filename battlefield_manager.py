import pygame
import random
from enemy import Enemy
from warrior import Warrior

class BattlefieldManager:
    def __init__(self, tilemap_width=4000, tilemap_height=800):
        self.tilemap_width = tilemap_width
        self.tilemap_height = tilemap_height
        self.ground_level = 655
        
        # Listes des combattants
        self.red_enemies = []    # Ennemis rouges
        self.blue_enemies = []   # Ennemis bleus
        
        # Paramètres de spawn
        self.max_red_enemies = 50
        self.max_blue_enemies = 50
        self.spawn_timer = 0
        self.spawn_interval = 120  # 2 secondes à 60 FPS (réduit de 180)
        
        # Zones de spawn 
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
        # Spawner les ennemis rouges
        for i in range(25):  # Augmenté à 25 combattants
            x = random.randint(self.spawn_zone_start, self.spawn_zone_end)
            y = self.ground_level - 100  # Au-dessus du sol
            enemy = Enemy(x, y, team="red")
            self.red_enemies.append(enemy)
            
        # Spawner les ennemis bleus
        for i in range(25):  # Augmenté à 25 combattants
            x = random.randint(self.spawn_zone_start, self.spawn_zone_end)
            y = self.ground_level - 100  # Au-dessus du sol
            enemy = Enemy(x, y, team="blue")
            self.blue_enemies.append(enemy)
            
    def update(self, collision_tiles, player=None):
        """Met à jour le champ de bataille"""
        self.spawn_timer += 1
        
        # Nettoyer les morts (après un délai)
        self.clean_dead_units()
        
        # Spawner de nouveaux combattants (seulement si on n'est pas en train de nettoyer)
        if self.spawn_timer >= self.spawn_interval and not hasattr(self, 'clearing_soldiers'):
            self.spawn_new_units()
            self.spawn_timer = 0
            
        # Mettre à jour tous les ennemis rouges - PAS DE COLLISION ENTRE ENNEMIS
        for enemy in self.red_enemies[:]:
            enemy.update(collision_tiles, self.blue_enemies, self.red_enemies, player=None)  # Pas de joueur
            
        # Mettre à jour tous les ennemis bleus - PAS DE COLLISION ENTRE ENNEMIS
        for enemy in self.blue_enemies[:]:
            enemy.update(collision_tiles, self.red_enemies, self.blue_enemies, player=None)  # Pas de joueur
            
    def should_draw_warriors(self, prince_protection_state, current_prince_x):
        """Détermine si les warriors doivent être dessinés (disparaissent à la tile 58)"""
        tile_58_x = 58 * 16 * 2.5  # Tile 58 en pixels
        if prince_protection_state in ["disappearing", "black_screen", "final_sequence"]:
            return False  # Ne pas dessiner pendant ces états
        if current_prince_x >= tile_58_x:
            return False  # Ne pas dessiner après la tile 58
        return True
    
    def clear_soldiers_for_prince_return(self, prince_protection_state, current_prince_x):
        """Supprime progressivement tous les soldats bleus et rouges quand le prince revient à l'extérieur"""
        tile_58_x = 58 * 16 * 2.5  # Tile 58 en pixels
        
        # Déclencher le nettoyage quand le prince atteint la tile 58 ou est dans des états avancés
        if (prince_protection_state in ["zoom_on_prince", "dezoom_reveal_enemies", "final_sequence"] or 
            current_prince_x >= tile_58_x):
            
            # Initialiser le nettoyage progressif si pas encore fait
            if not hasattr(self, 'clearing_soldiers'):
                self.clearing_soldiers = True
                self.clear_timer = 0
                self.clear_phase = 0
                print("Début du nettoyage progressif des soldats du battlefield principal...")
            
            # Continuer le nettoyage progressif
            if hasattr(self, 'clearing_soldiers') and self.clearing_soldiers:
                self.clear_timer += 1
                
                # Phase 1 : Supprimer 1/3 des soldats rouges (après 30 frames)
                if self.clear_phase == 0 and self.clear_timer >= 30:
                    soldiers_to_remove = len(self.red_enemies) // 3
                    for i in range(min(soldiers_to_remove, len(self.red_enemies))):
                        if self.red_enemies:
                            self.red_enemies.pop(0)
                    print(f"Phase 1: {soldiers_to_remove} soldats rouges supprimés. Restants: {len(self.red_enemies)}")
                    self.clear_phase = 1
                    self.clear_timer = 0
                
                # Phase 2 : Supprimer 1/3 des soldats bleus (après 20 frames)
                elif self.clear_phase == 1 and self.clear_timer >= 20:
                    soldiers_to_remove = len(self.blue_enemies) // 3
                    for i in range(min(soldiers_to_remove, len(self.blue_enemies))):
                        if self.blue_enemies:
                            self.blue_enemies.pop(0)
                    print(f"Phase 2: {soldiers_to_remove} soldats bleus supprimés. Restants: {len(self.blue_enemies)}")
                    self.clear_phase = 2
                    self.clear_timer = 0
                
                # Phase 3 : Supprimer le reste des soldats rouges (après 20 frames)
                elif self.clear_phase == 2 and self.clear_timer >= 20:
                    remaining_red = len(self.red_enemies)
                    self.red_enemies.clear()
                    print(f"Phase 3: {remaining_red} soldats rouges finaux supprimés.")
                    self.clear_phase = 3
                    self.clear_timer = 0
                
                # Phase 4 : Supprimer le reste des soldats bleus (après 15 frames)
                elif self.clear_phase == 3 and self.clear_timer >= 15:
                    remaining_blue = len(self.blue_enemies)
                    self.blue_enemies.clear()
                    print(f"Phase 4: {remaining_blue} soldats bleus finaux supprimés.")
                    print("Nettoyage progressif du battlefield principal terminé !")
                    
                    # Nettoyer les variables de nettoyage
                    self.clearing_soldiers = False
                    delattr(self, 'clear_timer')
                    delattr(self, 'clear_phase')
            
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
        
        # Spawner de nouveaux ennemis rouges si nécessaire
        if len(self.red_enemies) < self.max_red_enemies and alive_red < 25:  # Augmenté à 25
            x = random.randint(self.spawn_zone_start, self.spawn_zone_end)
            y = self.ground_level - 100
            enemy = Enemy(x, y, team="red")
            self.red_enemies.append(enemy)
            
        # Spawner de nouveaux ennemis bleus si nécessaire
        if len(self.blue_enemies) < self.max_blue_enemies and alive_blue < 25:  # Augmenté à 25
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
        
    def draw(self, screen, camera_x, camera_y, prince_protection_state="waiting", current_prince_x=0):
        """Dessine tous les combattants"""
        # Appliquer le nettoyage progressif si nécessaire
        self.clear_soldiers_for_prince_return(prince_protection_state, current_prince_x)
        
        # Vérifier si les warriors doivent être dessinés
        should_draw = self.should_draw_warriors(prince_protection_state, current_prince_x)
        
        if should_draw:
            # Dessiner tous les ennemis rouges
            for enemy in self.red_enemies:
                enemy.draw(screen, camera_x, camera_y)
                
            # Dessiner tous les ennemis bleus
            for enemy in self.blue_enemies:
                enemy.draw(screen, camera_x, camera_y)
            
    def draw_battle_ui(self, screen):
        """Interface de bataille supprimée selon la demande"""
        pass

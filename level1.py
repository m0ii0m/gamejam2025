import pygame
import xml.etree.ElementTree as ET
import os

class Level1:
    def __init__(self, screen):
        self.screen = screen
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        
        # Propriétés de la map TMX
        self.map_width = 100
        self.map_height = 20
        self.tile_size = 16
        # Calculer le scale factor pour que toute la map rentre dans la hauteur de l'écran
        # screen_height = 800, map_height = 20 tiles, tile_size = 16
        # Pour éviter le cadrillage, utilisons un scale factor rond
        self.scale_factor = 2.5  # 16x16 → 40x40 (dimensions exactes, pas de décimales)
        
        # Calculer la hauteur totale de la map et l'offset pour la positionner correctement
        self.map_total_height = self.map_height * self.tile_size * self.scale_factor
        # Positionner la tilemap pour que le BAS de la map soit au BAS de l'écran
        # Au lieu de se baser sur le sol, on colle tout en bas
        self.map_offset_y = self.screen_height - self.map_total_height
        
        # Chargement de la tilemap
        self.tiles = {}
        self.map_data = []
        self.background_layers_data = []  # Layers background (derrière le joueur)
        self.foreground_layers_data = []  # Layers foreground (devant le joueur)
        self.collision_tiles = []
        
        # Chargement d'un background fixe (pas de parallax)
        self.background = None
        
        self.load_tileset()
        self.load_map()
        self.load_backgrounds()
    
    def load_tileset(self):
        """Charge le tileset depuis le fichier PNG"""
        try:
            tileset_path = "assets/maps/level1/DirtBrick_Assets_V5.png"
            tileset_image = pygame.image.load(tileset_path).convert_alpha()
            
            # Le tileset fait 20 colonnes selon le fichier TSX
            cols = 20
            rows = tileset_image.get_height() // self.tile_size
            
            for row in range(rows):
                for col in range(cols):
                    x = col * self.tile_size
                    y = row * self.tile_size
                    tile_id = row * cols + col + 1  # Les IDs commencent à 1 dans TMX
                    
                    tile_surface = tileset_image.subsurface((x, y, self.tile_size, self.tile_size))
                    # Agrandir la tile avec smoothscale pour un meilleur rendu
                    scaled_tile = pygame.transform.smoothscale(tile_surface, 
                                                             (int(self.tile_size * self.scale_factor), 
                                                              int(self.tile_size * self.scale_factor)))
                    # Convertir pour optimiser le rendu
                    self.tiles[tile_id] = scaled_tile.convert_alpha()
            
            print(f"Tileset chargé avec {len(self.tiles)} tiles")
            
        except pygame.error as e:
            print(f"Erreur lors du chargement du tileset: {e}")
            # Créer des tiles par défaut
            for i in range(1, 321):  # 320 tiles selon le TSX
                default_tile = pygame.Surface((self.tile_size * self.scale_factor, 
                                             self.tile_size * self.scale_factor))
                default_tile.fill((100, 50, 0) if i == 2 else (50, 150, 50))
                self.tiles[i] = default_tile
    
    def load_map(self):
        """Charge la map TMX et extrait les données des layers"""
        try:
            map_path = "assets/maps/level1/level1.tmx"
            tree = ET.parse(map_path)
            root = tree.getroot()
            
            # Layers utilisés pour la collision
            collision_layers = ["FirstLayer", "GrassLayerOutside"]
            
            # Séparer les layers background et foreground
            background_layers = [
                "CastleBackground",     # Arrière-plan du château
                "DetailsCastle2",       # Détails château 2
                "FirstLayer",           # Layer principal 
                "OutsideDetails",       # Détails extérieurs
                "GrassLayerOutside",    # Couche d'herbe
                "FloorDetailsOutside"   # Détails du sol
            ]
            
            foreground_layers = [
                "DetailsCastle",        # Détails château (foreground)
                "CastleForeground"      # Premier plan du château
            ]
            
            # Stocker tous les layers trouvés
            all_layers_data = {}
            
            for layer in root.findall("layer"):
                layer_name = layer.get("name")
                data_element = layer.find("data")
                if data_element is not None:
                    csv_data = data_element.text.strip()
                    rows = csv_data.split('\n')
                    
                    layer_data = []
                    for y, row in enumerate(rows):
                        if row.strip():
                            tiles_in_row = [int(tile.strip()) for tile in row.split(',') if tile.strip()]
                            layer_data.append(tiles_in_row)
                            
                            # Créer les rectangles de collision SEULEMENT pour les layers de collision
                            if layer_name in collision_layers:
                                for x, tile_id in enumerate(tiles_in_row):
                                    if tile_id > 0:  # Tile non vide
                                        tile_rect = pygame.Rect(
                                            x * self.tile_size * self.scale_factor,
                                            y * self.tile_size * self.scale_factor + self.map_offset_y,
                                            self.tile_size * self.scale_factor,
                                            self.tile_size * self.scale_factor
                                        )
                                        self.collision_tiles.append(tile_rect)
                    
                    all_layers_data[layer_name] = layer_data
            
            # Ajouter les layers background dans l'ordre voulu
            self.background_layers_data = []
            for layer_name in background_layers:
                if layer_name in all_layers_data:
                    self.background_layers_data.append((layer_name, all_layers_data[layer_name]))
            
            # Ajouter les layers foreground séparément
            self.foreground_layers_data = []
            for layer_name in foreground_layers:
                if layer_name in all_layers_data:
                    self.foreground_layers_data.append((layer_name, all_layers_data[layer_name]))
            
            # Maintenir la compatibilité avec l'ancienne structure
            self.map_data = self.background_layers_data
            
            # Ajouter tous les autres layers non listés aux background
            for layer_name, layer_data in all_layers_data.items():
                if layer_name not in background_layers and layer_name not in foreground_layers:
                    self.background_layers_data.append((layer_name, layer_data))
                    self.map_data.append((layer_name, layer_data))
            
            print(f"Map chargée avec {len(self.map_data)} layers")
            print(f"Layers chargés: {[name for name, _ in self.map_data]}")
            print(f"{len(self.collision_tiles)} tiles de collision créées")
            
        except Exception as e:
            print(f"Erreur lors du chargement de la map: {e}")
            # Créer une map par défaut
            self.create_default_map()
    
    def create_default_map(self):
        """Crée une map par défaut en cas d'erreur"""
        # Créer une plateforme simple au bas de l'écran
        default_layer = []
        for y in range(self.map_height):
            row = []
            for x in range(self.map_width):
                if y >= self.map_height - 2:  # Deux dernières lignes
                    tile_id = 2  # Tile de terre
                    tile_rect = pygame.Rect(
                        x * self.tile_size * self.scale_factor,
                        y * self.tile_size * self.scale_factor + self.map_offset_y,
                        self.tile_size * self.scale_factor,
                        self.tile_size * self.scale_factor
                    )
                    self.collision_tiles.append(tile_rect)
                else:
                    tile_id = 0  # Vide
                row.append(tile_id)
            default_layer.append(row)
        
        self.map_data.append(("Default", default_layer))
    
    def load_backgrounds(self):
        """Charge l'image de background unique et fixe"""
        background_path = "assets/backgrounds/level1.png"
        
        try:
            # Charger l'image unique
            bg_image = pygame.image.load(background_path).convert()
            
            # Obtenir les dimensions originales
            original_width = bg_image.get_width()
            original_height = bg_image.get_height()
            
            # Redimensionner pour couvrir TOUT l'écran (1200x800)
            width_ratio = self.screen_width / original_width
            height_ratio = self.screen_height / original_height
            
            # Utiliser le plus grand ratio pour que l'image couvre tout l'écran
            scale_ratio = max(width_ratio, height_ratio)
            new_width = int(original_width * scale_ratio)
            new_height = int(original_height * scale_ratio)
            
            # Redimensionner
            self.background = pygame.transform.smoothscale(bg_image, (new_width, new_height))
                
            print(f"Background unique chargé: {original_width}x{original_height} -> {new_width}x{new_height}")
            
        except pygame.error as e:
            print(f"Erreur lors du chargement du background: {e}")
            # Créer un background par défaut
            self.background = pygame.Surface((self.screen_width, self.screen_height))
            self.background.fill((135, 206, 235))  # Bleu ciel
    
    def get_collision_tiles(self):
        """Retourne la liste des rectangles de collision"""
        return self.collision_tiles
    
    def draw(self, screen, camera_x, camera_y):
        """Dessine le niveau avec background fixe et tilemap"""
        # Effacer l'écran avec une couleur qui s'accorde avec le background
        screen.fill((32, 20, 36))  # Couleur sombre
        
        # Dessiner le background fixe (pas de parallax)
        if self.background:
            # Centrer le background sur l'écran
            bg_width = self.background.get_width()
            bg_height = self.background.get_height()
            
            # Centrer horizontalement et verticalement
            bg_x = (self.screen_width - bg_width) // 2
            bg_y = (self.screen_height - bg_height) // 2
            
            screen.blit(self.background, (bg_x, bg_y))
        
        # Dessiner la tilemap par-dessus (layers background seulement)
        self.draw_background_tilemap(screen, camera_x, camera_y)
    
    def draw_background_tilemap(self, screen, camera_x, camera_y):
        """Dessine les layers background de la tilemap"""
        # Calculer les limites visibles avec une marge pour éviter les coupures
        tile_pixel_size = self.tile_size * self.scale_factor
        start_x = max(0, int(camera_x // tile_pixel_size) - 1)
        end_x = min(self.map_width, int((camera_x + self.screen_width) // tile_pixel_size) + 2)
        start_y = max(0, int(camera_y // tile_pixel_size) - 1)
        end_y = min(self.map_height, int((camera_y + self.screen_height) // tile_pixel_size) + 2)
        
        # Dessiner chaque layer background
        for layer_name, layer_data in self.background_layers_data:
            for y in range(start_y, end_y):
                if y < len(layer_data):
                    for x in range(start_x, end_x):
                        if x < len(layer_data[y]):
                            tile_id = layer_data[y][x]
                            if tile_id > 0 and tile_id in self.tiles:
                                # Position à l'écran calculée de manière plus précise
                                screen_x = round(x * tile_pixel_size - camera_x)
                                screen_y = round(y * tile_pixel_size + self.map_offset_y - camera_y)
                                
                                # Créer un rect pour un placement précis
                                tile_rect = pygame.Rect(screen_x, screen_y, tile_pixel_size, tile_pixel_size)
                                screen.blit(self.tiles[tile_id], tile_rect)
    
    def draw_foreground_tilemap(self, screen, camera_x, camera_y):
        """Dessine les layers foreground de la tilemap (devant le joueur)"""
        # Calculer les limites visibles avec une marge pour éviter les coupures
        tile_pixel_size = self.tile_size * self.scale_factor
        start_x = max(0, int(camera_x // tile_pixel_size) - 1)
        end_x = min(self.map_width, int((camera_x + self.screen_width) // tile_pixel_size) + 2)
        start_y = max(0, int(camera_y // tile_pixel_size) - 1)
        end_y = min(self.map_height, int((camera_y + self.screen_height) // tile_pixel_size) + 2)
        
        # Dessiner chaque layer foreground
        for layer_name, layer_data in self.foreground_layers_data:
            for y in range(start_y, end_y):
                if y < len(layer_data):
                    for x in range(start_x, end_x):
                        if x < len(layer_data[y]):
                            tile_id = layer_data[y][x]
                            if tile_id > 0 and tile_id in self.tiles:
                                # Position à l'écran calculée de manière plus précise
                                screen_x = round(x * tile_pixel_size - camera_x)
                                screen_y = round(y * tile_pixel_size + self.map_offset_y - camera_y)
                                
                                # Créer un rect pour un placement précis
                                tile_rect = pygame.Rect(screen_x, screen_y, tile_pixel_size, tile_pixel_size)
                                screen.blit(self.tiles[tile_id], tile_rect)
    
    def draw_tilemap(self, screen, camera_x, camera_y):
        """Dessine la tilemap"""
        # Calculer les limites visibles
        start_x = max(0, camera_x // (self.tile_size * self.scale_factor))
        end_x = min(self.map_width, (camera_x + self.screen_width) // (self.tile_size * self.scale_factor) + 1)
        start_y = max(0, camera_y // (self.tile_size * self.scale_factor))
        end_y = min(self.map_height, (camera_y + self.screen_height) // (self.tile_size * self.scale_factor) + 1)
        
        # Dessiner chaque layer
        for layer_name, layer_data in self.map_data:
            for y in range(int(start_y), int(end_y)):
                if y < len(layer_data):
                    for x in range(int(start_x), int(end_x)):
                        if x < len(layer_data[y]):
                            tile_id = layer_data[y][x]
                            if tile_id > 0 and tile_id in self.tiles:
                                # Position à l'écran (avec offset Y pour positionner en bas)
                                screen_x = x * self.tile_size * self.scale_factor - camera_x
                                screen_y = y * self.tile_size * self.scale_factor + self.map_offset_y - camera_y
                                
                                screen.blit(self.tiles[tile_id], (screen_x, screen_y))

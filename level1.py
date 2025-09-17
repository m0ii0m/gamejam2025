import pygame
import xml.etree.ElementTree as ET
import os
from parallax_bg import ParallaxBg

def hex_to_rgb(hex_color):
    """Convertit une couleur hexadécimale en tuple RGB"""
    if hex_color.startswith('#'):
        hex_color = hex_color[1:]
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def apply_tint_to_tile(tile_surface, tint_color):
    """Applique une teinte colorée à une tile en préservant la transparence"""
    # Créer une nouvelle surface avec alpha
    tinted_surface = pygame.Surface(tile_surface.get_size(), pygame.SRCALPHA)
    
    # Copier la tile originale
    tinted_surface.blit(tile_surface, (0, 0))
    
    # Appliquer la teinte avec multiplication des couleurs
    tint_overlay = pygame.Surface(tile_surface.get_size(), pygame.SRCALPHA)
    tint_overlay.fill(tint_color)
    
    # Utiliser BLEND_MULT pour multiplier les couleurs (assombrir)
    tinted_surface.blit(tint_overlay, (0, 0), special_flags=pygame.BLEND_MULT)
    
    return tinted_surface

def parse_tile_id(tile_gid):
    """Extrait l'ID de la tile et les flags de transformation depuis un GID TMX"""
    # Flags de transformation TMX
    FLIPPED_HORIZONTALLY_FLAG = 0x80000000
    FLIPPED_VERTICALLY_FLAG = 0x40000000
    FLIPPED_DIAGONALLY_FLAG = 0x20000000
    
    # Extraire les flags
    flipped_horizontally = bool(tile_gid & FLIPPED_HORIZONTALLY_FLAG)
    flipped_vertically = bool(tile_gid & FLIPPED_VERTICALLY_FLAG)
    flipped_diagonally = bool(tile_gid & FLIPPED_DIAGONALLY_FLAG)
    
    # Extraire l'ID réel de la tile (sans les flags)
    tile_id = tile_gid & ~(FLIPPED_HORIZONTALLY_FLAG | FLIPPED_VERTICALLY_FLAG | FLIPPED_DIAGONALLY_FLAG)
    
    return tile_id, flipped_horizontally, flipped_vertically, flipped_diagonally

def apply_tile_transformations(tile_surface, flip_h, flip_v, flip_d):
    """Applique les transformations à une tile"""
    if not (flip_h or flip_v or flip_d):
        return tile_surface
    
    # Appliquer les transformations
    transformed_surface = tile_surface
    
    if flip_d:
        # Rotation diagonale = rotation 90° + flip horizontal
        transformed_surface = pygame.transform.rotate(transformed_surface, -90)
        transformed_surface = pygame.transform.flip(transformed_surface, True, False)
    
    if flip_h:
        transformed_surface = pygame.transform.flip(transformed_surface, True, False)
    
    if flip_v:
        transformed_surface = pygame.transform.flip(transformed_surface, False, True)
    
    return transformed_surface

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
        self.tinted_tiles_cache = {}  # Cache pour les tiles teintées
        self.layer_tintcolors = {}    # Couleurs de teinte par layer
        self.map_data = []
        self.background_layers_data = []  # Layers background (derrière le joueur)
        self.foreground_layers_data = []  # Layers foreground (devant le joueur)
        self.collision_tiles = []
        
        # Chargement d'un background fixe (pas de parallax)
        self.background = ParallaxBg('./assets/backgrounds/level1/', (self.screen_width, self.screen_height), cloud_layers=[2, 3])
        
        self.load_tileset()
        self.load_map()
        #self.load_backgrounds()
    
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
            
            # Stocker tous les layers trouvés avec leurs propriétés
            all_layers_data = {}
            layer_tintcolors = {}
            
            for layer in root.findall("layer"):
                layer_name = layer.get("name")
                tintcolor = layer.get("tintcolor")
                
                # Stocker la tintcolor si elle existe
                if tintcolor:
                    layer_tintcolors[layer_name] = tintcolor
                
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
            
            # Stocker les tintcolors pour utilisation lors du rendu
            self.layer_tintcolors = layer_tintcolors
            
            # Ordre d'affichage du plus profond au plus devant
            # (inverse de l'ordre donné : detailscastle, detailscastle2, castleforeground, castlebackground, floordetailsoutside, grasslayeroutside, outsidedetails, firstlayer)
            layer_display_order = [
                "FirstLayer",            # Le plus profond (arrière-plan)
                "OutsideDetails",
                "GrassLayerOutside", 
                "FloorDetailsOutside",
                "CastleBackground",
                "CastleForeground",
                "DetailsCastle2",
                "DetailsCastle"          # Le plus devant (premier plan)
            ]
            
            # Construire les données des layers dans l'ordre d'affichage
            self.background_layers_data = []
            self.map_data = []
            
            # Ajouter les layers dans l'ordre spécifié
            for layer_name in layer_display_order:
                if layer_name in all_layers_data:
                    self.background_layers_data.append((layer_name, all_layers_data[layer_name]))
                    self.map_data.append((layer_name, all_layers_data[layer_name]))
            
            # Ajouter tous les autres layers non listés à la fin
            for layer_name, layer_data in all_layers_data.items():
                if layer_name not in layer_display_order:
                    self.background_layers_data.append((layer_name, layer_data))
                    self.map_data.append((layer_name, layer_data))
        
            # Plus de séparation foreground/background - tout est dans background
            self.foreground_layers_data = []
            
            print(f"Map chargée avec {len(self.map_data)} layers")
            print(f"Layers chargés: {[name for name, _ in self.map_data]}")
            print(f"Tintcolors trouvées: {self.layer_tintcolors}")
            print(f"{len(self.collision_tiles)} tiles de collision créées")
            
        except Exception as e:
            print(f"Erreur lors du chargement de la map: {e}")
            # Créer une map par défaut
            self.create_default_map()
    
    def create_default_map(self):
        """Crée une map par défaut en cas d'erreur"""
        # Initialiser les tintcolors vides
        self.layer_tintcolors = {}
        
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
    
    def get_tinted_tile(self, tile_gid, layer_name):
        """Obtient une tile avec teinte appliquée et transformations, utilise le cache pour les performances"""
        if tile_gid <= 0:
            return None
            
        # Extraire l'ID réel et les transformations
        tile_id, flip_h, flip_v, flip_d = parse_tile_id(tile_gid)
        
        # Vérifier si on a une couleur de teinte pour ce layer
        has_tint = layer_name in self.layer_tintcolors
        
        # Créer une clé unique pour le cache incluant les transformations
        cache_key = (tile_id, layer_name, flip_h, flip_v, flip_d, has_tint)
        
        # Vérifier le cache
        if cache_key in self.tinted_tiles_cache:
            return self.tinted_tiles_cache[cache_key]
        
        # Obtenir la tile originale
        original_tile = self.tiles.get(tile_id)
        if original_tile is None:
            return None
        
        # Appliquer les transformations d'abord
        transformed_tile = apply_tile_transformations(original_tile, flip_h, flip_v, flip_d)
        
        # Appliquer la teinte si nécessaire
        final_tile = transformed_tile
        if has_tint:
            tint_hex = self.layer_tintcolors[layer_name]
            tint_rgb = hex_to_rgb(tint_hex)
            final_tile = apply_tint_to_tile(transformed_tile, tint_rgb)
        
        # Mettre en cache
        self.tinted_tiles_cache[cache_key] = final_tile
        
        return final_tile

    def get_collision_tiles(self):
        """Retourne la liste des rectangles de collision"""
        return self.collision_tiles
    
    def draw(self, screen, camera_x, camera_y):
        """Dessine le niveau avec background fixe et tilemap"""
        # Effacer l'écran avec une couleur qui s'accorde avec le background
        screen.fill((32, 20, 36))  # Couleur sombre
        
        # Dessiner le background fixe (pas de parallax)
        if self.background:
            self.background.update()
            self.background.draw(screen, camera_x)
        else:
            screen.fill((0, 0, 0))
        # Dessiner la tilemap par-dessus (layers background seulement)
        self.draw_background_tilemap(screen, camera_x, camera_y)
    
    def draw_background_tilemap(self, screen, camera_x, camera_y):
        """Dessine les layers background de la tilemap avec support des tintcolor"""
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
                            tile_gid = layer_data[y][x]
                            if tile_gid > 0:
                                # Obtenir la tile avec teinte appliquée et transformations
                                tile_surface = self.get_tinted_tile(tile_gid, layer_name)
                                if tile_surface is not None:
                                    # Position à l'écran calculée de manière plus précise
                                    screen_x = round(x * tile_pixel_size - camera_x)
                                    screen_y = round(y * tile_pixel_size + self.map_offset_y - camera_y)
                                    
                                    # Créer un rect pour un placement précis
                                    tile_rect = pygame.Rect(screen_x, screen_y, tile_pixel_size, tile_pixel_size)
                                    screen.blit(tile_surface, tile_rect)
    
    def draw_foreground_tilemap(self, screen, camera_x, camera_y):
        """Dessine les layers foreground de la tilemap (devant le joueur) avec support des tintcolor"""
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
                            tile_gid = layer_data[y][x]
                            if tile_gid > 0:
                                # Obtenir la tile avec teinte appliquée et transformations
                                tile_surface = self.get_tinted_tile(tile_gid, layer_name)
                                if tile_surface is not None:
                                    # Position à l'écran calculée de manière plus précise
                                    screen_x = round(x * tile_pixel_size - camera_x)
                                    screen_y = round(y * tile_pixel_size + self.map_offset_y - camera_y)
                                    
                                    # Créer un rect pour un placement précis
                                    tile_rect = pygame.Rect(screen_x, screen_y, tile_pixel_size, tile_pixel_size)
                                    screen.blit(tile_surface, tile_rect)
    
    def draw_tilemap(self, screen, camera_x, camera_y):
        """Dessine la tilemap avec support des tintcolor"""
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
                            tile_gid = layer_data[y][x]
                            if tile_gid > 0:
                                # Obtenir la tile avec teinte appliquée et transformations
                                tile_surface = self.get_tinted_tile(tile_gid, layer_name)
                                if tile_surface is not None:
                                    # Position à l'écran (avec offset Y pour positionner en bas)
                                    screen_x = x * self.tile_size * self.scale_factor - camera_x
                                    screen_y = y * self.tile_size * self.scale_factor + self.map_offset_y - camera_y
                                    
                                    screen.blit(tile_surface, (screen_x, screen_y))

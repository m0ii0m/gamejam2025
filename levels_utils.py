def draw_foreground_tilemap(screen, camera_x, camera_y, foreground_layers_data, tile_size, scale_factor, map_width, map_height, map_offset_y, tiles, tinted_tiles_cache, layer_tintcolors):
    """Dessine les layers foreground de la tilemap avec support des tintcolor et du cache."""
    tile_pixel_size = tile_size * scale_factor
    start_x = max(0, int(camera_x // tile_pixel_size) - 1)
    end_x = min(map_width, int((camera_x + screen.get_width()) // tile_pixel_size) + 2)
    start_y = max(0, int(camera_y // tile_pixel_size) - 1)
    end_y = min(map_height, int((camera_y + screen.get_height()) // tile_pixel_size) + 2)
    for layer_name, layer_data in foreground_layers_data:
        for y in range(start_y, end_y):
            if y < len(layer_data):
                for x in range(start_x, end_x):
                    if x < len(layer_data[y]):
                        tile_gid = layer_data[y][x]
                        if tile_gid > 0:
                            tile_surface = get_tinted_tile(tile_gid, layer_name, tiles, tinted_tiles_cache, layer_tintcolors)
                            if tile_surface is not None:
                                screen_x = round(x * tile_pixel_size - camera_x)
                                screen_y = round(y * tile_pixel_size + map_offset_y - camera_y)
                                tile_rect = pygame.Rect(screen_x, screen_y, tile_pixel_size, tile_pixel_size)
                                screen.blit(tile_surface, tile_rect)

def draw_background_tilemap(screen, camera_x, camera_y, background_layers_data, tile_size, scale_factor, map_width, map_height, map_offset_y, tiles, tinted_tiles_cache, layer_tintcolors):
    """Dessine les layers background de la tilemap avec support des tintcolor et du cache."""
    tile_pixel_size = tile_size * scale_factor
    start_x = max(0, int(camera_x // tile_pixel_size) - 1)
    end_x = min(map_width, int((camera_x + screen.get_width()) // tile_pixel_size) + 2)
    start_y = max(0, int(camera_y // tile_pixel_size) - 1)
    end_y = min(map_height, int((camera_y + screen.get_height()) // tile_pixel_size) + 2)
    for layer_name, layer_data in background_layers_data:
        for y in range(start_y, end_y):
            if y < len(layer_data):
                for x in range(start_x, end_x):
                    if x < len(layer_data[y]):
                        tile_gid = layer_data[y][x]
                        if tile_gid > 0:
                            tile_surface = get_tinted_tile(tile_gid, layer_name, tiles, tinted_tiles_cache, layer_tintcolors)
                            if tile_surface is not None:
                                screen_x = round(x * tile_pixel_size - camera_x)
                                screen_y = round(y * tile_pixel_size + map_offset_y - camera_y)
                                tile_rect = pygame.Rect(screen_x, screen_y, tile_pixel_size, tile_pixel_size)
                                screen.blit(tile_surface, tile_rect)

def draw(screen, background, draw_background_tilemap_func, camera_x, camera_y, fill_color=(32, 20, 36)):
    """Dessine le niveau avec background fixe et tilemap (fonction utilitaire générique)."""
    screen.fill(fill_color)
    if background:
        if hasattr(background, 'update') and hasattr(background, 'draw'):
            background.update()
            background.draw(screen, camera_x)
        else:
            # Cas d'une simple surface
            bg_width = background.get_width()
            bg_height = background.get_height()
            bg_x = (screen.get_width() - bg_width) // 2
            bg_y = (screen.get_height() - bg_height) // 2
            screen.blit(background, (bg_x, bg_y))
    else:
        screen.fill((0, 0, 0))
    # Dessiner la tilemap par-dessus (layers background seulement)
    draw_background_tilemap_func(screen, camera_x, camera_y)

def get_collision_tiles(map_data, tile_size, scale_factor, map_offset_y, collision_tile_ids=None):
    """Retourne la liste des rectangles de collision à partir des données de map."""
    collision_tiles = []
    if collision_tile_ids is None:
        collision_tile_ids = {2}  # Par défaut, tile_id 2 est solide
    for _, layer_data in map_data:
        for y, row in enumerate(layer_data):
            for x, tile_id in enumerate(row):
                if tile_id in collision_tile_ids:
                    tile_rect = pygame.Rect(
                        x * tile_size * scale_factor,
                        y * tile_size * scale_factor + map_offset_y,
                        tile_size * scale_factor,
                        tile_size * scale_factor
                    )
                    collision_tiles.append(tile_rect)
    return collision_tiles

def get_tinted_tile(tile_gid, layer_name, tiles, tinted_tiles_cache, layer_tintcolors):
    """Obtient une tile avec teinte appliquée et transformations, utilise le cache pour les performances"""
    if tile_gid <= 0:
        return None
    tile_id, flip_h, flip_v, flip_d = parse_tile_id(tile_gid)
    has_tint = layer_name in layer_tintcolors
    cache_key = (tile_id, layer_name, flip_h, flip_v, flip_d, has_tint)
    if cache_key in tinted_tiles_cache:
        return tinted_tiles_cache[cache_key]
    original_tile = tiles.get(tile_id)
    if original_tile is None:
        return None
    transformed_tile = apply_tile_transformations(original_tile, flip_h, flip_v, flip_d)
    final_tile = transformed_tile
    if has_tint:
        tint_hex = layer_tintcolors[layer_name]
        tint_rgb = hex_to_rgb(tint_hex)
        final_tile = apply_tint_to_tile(transformed_tile, tint_rgb)
    tinted_tiles_cache[cache_key] = final_tile
    return final_tile

def load_background(background_path, screen_width, screen_height):
    """Charge et redimensionne un background unique pour l'écran donné. Retourne une surface pygame."""
    try:
        bg_image = pygame.image.load(background_path).convert()
        original_width = bg_image.get_width()
        original_height = bg_image.get_height()
        width_ratio = screen_width / original_width
        height_ratio = screen_height / original_height
        scale_ratio = max(width_ratio, height_ratio)
        new_width = int(original_width * scale_ratio)
        new_height = int(original_height * scale_ratio)
        background = pygame.transform.smoothscale(bg_image, (new_width, new_height))
        print(f"Background unique chargé: {original_width}x{original_height} -> {new_width}x{new_height}")
        return background
    except pygame.error as e:
        print(f"Erreur lors du chargement du background: {e}")
        background = pygame.Surface((screen_width, screen_height))
        background.fill((135, 206, 235))  # Bleu ciel
        return background
import pygame
import xml.etree.ElementTree as ET

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

def load_tileset(tileset_path, tile_size, scale_factor, cols):
        """Charge le tileset depuis le fichier PNG"""
        try:
            tiles = {}
            tileset_image = pygame.image.load(tileset_path).convert_alpha()
            
            # Le tileset fait 20 colonnes selon le fichier TSX
            cols = 20
            rows = tileset_image.get_height() // tile_size
            
            for row in range(rows):
                for col in range(cols):
                    x = col * tile_size
                    y = row * tile_size
                    tile_id = row * cols + col + 1  # Les IDs commencent à 1 dans TMX
                    
                    tile_surface = tileset_image.subsurface((x, y, tile_size, tile_size))
                    # Agrandir la tile avec smoothscale pour un meilleur rendu
                    scaled_tile = pygame.transform.smoothscale(tile_surface, 
                                                             (int(tile_size * scale_factor), 
                                                              int(tile_size * scale_factor)))
                    # Convertir pour optimiser le rendu
                    tiles[tile_id] = scaled_tile.convert_alpha()
            return tiles
            print(f"Tileset chargé avec {len(tiles)} tiles")
            
        except pygame.error as e:
            print(f"Erreur lors du chargement du tileset: {e}")
            # Créer des tiles par défaut
            for i in range(1, 321):  # 320 tiles selon le TSX
                default_tile = pygame.Surface((tile_size * scale_factor, 
                                             tile_size * scale_factor))
                default_tile.fill((100, 50, 0) if i == 2 else (50, 150, 50))
                tiles[i] = default_tile
    
def load_map(map_path, collision_layers, tile_size, scale_factor, map_offset_y, layer_display_order):
    """Charge la map TMX et extrait les données des layers"""
    try:
        tree = ET.parse(map_path)
        root = tree.getroot()
        
        # Stocker tous les layers trouvés avec leurs propriétés
        all_layers_data = {}
        layer_tintcolors = {}
        collision_tiles = []
        
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
                                        x * tile_size * scale_factor,
                                        y * tile_size * scale_factor + map_offset_y,
                                        tile_size * scale_factor,
                                        tile_size * scale_factor
                                    )
                                    collision_tiles.append(tile_rect)
                
                all_layers_data[layer_name] = layer_data
        
        # Stocker les tintcolors pour utilisation lors du rendu
        layer_tintcolors = layer_tintcolors

        
        # Construire les données des layers dans l'ordre d'affichage
        background_layers_data = []
        map_data = []
        
        # Ajouter les layers dans l'ordre spécifié
        for layer_name in layer_display_order:
            if layer_name in all_layers_data:
                background_layers_data.append((layer_name, all_layers_data[layer_name]))
                map_data.append((layer_name, all_layers_data[layer_name]))
        
        # Ajouter tous les autres layers non listés à la fin
        for layer_name, layer_data in all_layers_data.items():
            if layer_name not in layer_display_order:
                background_layers_data.append((layer_name, layer_data))
                map_data.append((layer_name, layer_data))
    
        # Plus de séparation foreground/background - tout est dans background
        foreground_layers_data = []
        
        print(f"Map chargée avec {len(map_data)} layers")
        print(f"Layers chargés: {[name for name, _ in map_data]}")
        print(f"Tintcolors trouvées: {layer_tintcolors}")
        print(f"{len(collision_tiles)} tiles de collision créées")
        return {
            "all_layers_data": all_layers_data,
            "layer_tintcolors": layer_tintcolors,
            "background_layers_data": background_layers_data,
            "foreground_layers_data": foreground_layers_data,
            "map_data": map_data,
            "collision_tiles": collision_tiles,
        }
    except Exception as e:
        print(f"Erreur lors du chargement de la map: {e}")
        # Créer une map par défaut
        return create_default_map(tile_size, scale_factor, map_offset_y, 100, 20)
 
def create_default_map(tile_size, scale_factor, map_offset_y, map_width, map_height):
    """Crée une map par défaut en cas d'erreur"""
    layer_tintcolors = {}
    collision_tiles = []
    default_layer = []
    for y in range(map_height):
        row = []
        for x in range(map_width):
            if y >= map_height - 2:
                tile_id = 2
                tile_rect = pygame.Rect(
                    x * tile_size * scale_factor,
                    y * tile_size * scale_factor + map_offset_y,
                    tile_size * scale_factor,
                    tile_size * scale_factor
                )
                collision_tiles.append(tile_rect)
            else:
                tile_id = 0
            row.append(tile_id)
        default_layer.append(row)
    return {
        "all_layers_data": {"Default": default_layer},
        "layer_tintcolors": {},
        "background_layers_data": [("Default", default_layer)],
        "foreground_layers_data": [],
        "map_data": [("Default", default_layer)],
        "collision_tiles": collision_tiles,
    }
    




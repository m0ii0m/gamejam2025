import pygame
import xml.etree.ElementTree as ET
from levels_utils import load_map, load_tileset
from parallax_bg import ParallaxBg

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
        
        self.tiles = load_tileset("assets/maps/level1/DirtBrick_Assets_V5.png", self.tile_size, self.scale_factor, 20)

        map_info = load_map(
            "assets/maps/level1/level1.tmx", ["FirstLayer", "GrassLayerOutside"], self.tile_size, self.scale_factor, self.map_offset_y, [
                "FirstLayer",           
                "OutsideDetails",
                "GrassLayerOutside", 
                "FloorDetailsOutside",
                "CastleBackground",
                "CastleForeground",
                "DetailsCastle2",
                "DetailsCastle" 
            ]
        )

        self.background_layers_data = map_info["background_layers_data"]
        self.foreground_layers_data = map_info["foreground_layers_data"]
        self.map_data = map_info["map_data"]
        self.collision_tiles = map_info["collision_tiles"]
        self.layer_tintcolors = map_info["layer_tintcolors"]

        # Les propriétés de musique seront définies dans game.py
        self.music_channel = None
        self.music_sound = None
        
        #self.load_backgrounds()
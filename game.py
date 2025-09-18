import pygame
import sys
from level1 import Level1
from level2 import Level2
from player import Player
from player_manager import PlayerManager
from player_manager_lvl2 import PlayerManager2
from prince import Prince
from arrow import ArrowManager
from battlefield_manager import BattlefieldManager
from throne_scene import ThroneScene
from levels_utils import (
    draw,
    get_collision_tiles,
    draw_foreground_tilemap,
    draw_background_tilemap,
)
from start_menu import StartMenu
from src.scenes.intro import IntroScene
from prince_protection_manager import PrinceProtectionManager
from credits import Credits


class Game:
    def __init__(self, screen):
        pygame.mixer.init()
        pygame.mixer.set_num_channels(8)
        self.screen = screen
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()

        # États du jeu
        self.game_state = "start_menu"
        
        # Initialisation des scènes
        self.throne = ThroneScene(self.screen)
        self.level1 = Level1(self.screen)
        self.level2 = Level2(self.screen)

        # Camera
        self.camera_x = 0
        self.camera_y = 0

        # Start menu
        self.start_menu = StartMenu(
            screen_size=(self.screen_width, self.screen_height),
            font_path="./assets/fonts/PressStart2P-Regular.ttf",
            bg_image_path="./assets/images/backgrounds/level1/1.png",
            button_image_path="./assets/images/gui/buttons/button.png",
            callbacks={
                "start": self.start_game_function,
                "credits": self.show_credits_function,
                "quit": self.quit_game_function,
            },
        )

        self.credits = Credits(
            (self.screen_width, self.screen_height),
            self.return_start_menu,
            background=self.start_menu.background,
        )

    def return_start_menu(self):
        self.game_state = "start_menu"

    def start_game_function(self):
        from src.scenes.intro import IntroScene
        self.intro_scene = IntroScene(self,
                                      lines=[
            "Notre pays est en guerre, et le roi vient de mourir.",
            "Le prince, dernier espoir du royaume, doit être prévenu.",
            "Un messager courageux part alors accomplir sa mission :",
            "",
            "Avertir le prince, actuellement assiégé dans son château.",
            "",
            "",
            "Appuyez sur ENTER pour commencer (Niveau 1)",
        ], next_state="level1")
        self.game_state = "intro"

    def show_credits_function(self):
        self.game_state = "credits"

    def quit_game_function(self):
        pygame.quit()
        sys.exit()

    def state_manager(self):
        """Gère les différents états du jeu"""
        # Récupérer tous les événements UNE seule fois et gérer le global (ESC/QUIT)
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        if self.game_state == "intro":
            for event in events:
                self.intro_scene.handle_event(event)
            self.intro_scene.draw(self.screen)
            
            if self.intro_scene.is_finished():
                # passer à l'état suivant
                next_state = self.intro_scene.next_state
                if next_state == "level1":
                    self.init_level1()
                elif next_state == "level2":
                    self.init_level2()
                self.game_state = next_state



        if self.game_state == "start_menu":
            self.start_menu.update()
            self.start_menu.draw(self.screen)
        elif self.game_state == "credits":
            self.credits.update()
            self.credits.draw(self.screen)
        elif self.game_state == "throne":
            self.update_throne(events)
            self.draw_throne()
        elif self.game_state == "level1":
            self.update_level1(events)
            self.draw_level1()
        elif self.game_state == "level2":
            self.update_level2()
            self.draw_level2()

    def update_throne(self, events):
        """Met à jour la cinématique du trône; Enter/Espace pour skip"""
        # Lancer la musique de la scène du trône si ce n'est pas déjà fait
        if not hasattr(self, 'throne_music_started') or not self.throne_music_started:
            self.setup_throne_music()
            self.throne_music_started = True

        # Update cinematic
        self.throne.update()
        # Passage automatique au niveau 1 quand la cinématique est terminée
        if getattr(self.throne, "cinematic_phase", None) == "done":
            
            pygame.mixer.music.stop()
            self.start_intro_for_phase("transition_throne_to_menu")
            # self.game_state = "start_menu"

    def draw_throne(self):
        # La scène gère son propre rendu
        self.throne.draw(self.screen)

    def update_level1(self, events=None):
        """Met à jour le niveau 1"""
        # Récupération des touches pressées
        keys = pygame.key.get_pressed()

        # Vérifier si le joueur a atteint le prince pour déclencher la séquence
        current_player = self.player_manager.get_current_player()
        if (
            current_player is not None
            and self.prince_protection.state == "waiting"
            and self.prince_protection.is_player_near_prince(current_player.rect.x)
        ):
            self.prince_protection.start_sequence(current_player.rect.x)

        # Mise à jour du gestionnaire de protection du prince
        if self.prince_protection.state != "waiting":
            level_complete = self.prince_protection.update(
                self.player_manager,
                self.arrow_manager,
                self.level1.collision_tiles,
                keys,
            )
            if level_complete:
                print("Niveau terminé ! Plot Armor activé !")
                # Ici tu peux ajouter la logique de fin de niveau

        # Mise à jour du gestionnaire de joueurs (SAUF pendant la séquence du prince)
        if self.prince_protection.state in ["waiting", "cinematic_slowdown"]:
            # Pendant ces états, laisser le player_manager gérer normalement
            self.player_manager.update(
                keys, self.level1.collision_tiles, self.arrow_manager
            )
        elif self.prince_protection.state in [
            "player_death",
            "pause_after_death",
            "zooming_out",
            "protection",
            "fading_to_black",
            "black_screen",
            "final_sequence",
        ]:
            # Pendant la séquence du prince, ne pas permettre de nouveau spawn
            # Juste mettre à jour les animations du joueur actuel s'il existe
            current_player = self.player_manager.get_current_player()
            if current_player:
                current_player.update_animation()
            # Mettre à jour aussi le nouveau joueur pendant le respawn s'il existe
            if self.player_manager.respawning and self.player_manager.new_player:
                self.player_manager.new_player.update_animation()
        else:
            # État normal - mise à jour complète
            self.player_manager.update(
                keys, self.level1.collision_tiles, self.arrow_manager
            )

        # Mise à jour du gestionnaire de flèches
        current_player = self.player_manager.get_current_player()
        if current_player is not None:
            self.arrow_manager.update(
                current_player.rect.x,
                current_player.rect.y,
                self.level1.collision_tiles,
            )
        else:
            # Pas de joueur actif, juste mettre à jour les flèches sans collision avec joueur
            self.arrow_manager.update(0, 0, self.level1.collision_tiles)

        # Mise à jour du champ de bataille
        current_player = self.player_manager.get_current_player()
        self.battlefield_manager.update(self.level1.collision_tiles, current_player)

        # Mise à jour du prince (animation idle automatique)
        if hasattr(self, "prince"):
            self.prince.update()

        # Gestion du volume de la musique basé sur la position du joueur
        if current_player:
            self.update_music_volume(current_player.rect.x)

        # Mise à jour de la caméra pour suivre le joueur (ou le prince pendant la protection)
        self.update_camera()

    def start_intro_for_phase(self, phase):
        if phase == "intro_game":
            lines = [
                "Notre pays est en guerre, et le roi vient de mourir.",
                "Le prince, dernier espoir du royaume, doit être prévenu.",
                "Un messager courageux part alors accomplir sa mission :",
                "",
                "Avertir le prince, actuellement assiégé dans son château.",
                "",
                "",
                "Appuyez sur ENTER pour commencer (Niveau 1)",
            ]
            next_state = "level1"

        elif phase == "transition_lvl1_to_lvl2":
            lines = [
                "Contre toute attente, le prince parvient à s’échapper d’une situation désespérée.",
                "Grâce à votre aide, il survit. Mais le répit est de courte durée : ",
                "il se retrouve perdu, en pleine nuit, au cœur d’une forêt ennemie.",
                "Deux fidèles serviteurs réussissent à le rejoindre, ",
                "formant une petite troupe décidée à continuer la lutte."
                "",
                "",
                "Appuyez sur ENTER pour commencer (Niveau 2)"
            ]
            next_state = "level2"

        elif phase == "transition_lvl2_to_conclusion":
            lines = [
                "Une fois encore, le prince échappe à ses ennemis.",
                "Cette fois, ce sont le sacrifice de ses compagnons et la bravoure ",
                "de son cheval qui lui offrent la vie sauve."
                "De retour au château royal, il est accueilli en héros.",
                "",
                "",
                "Appuyez sur ENTER pour continuer"
            ]
            next_state ="throne"
        elif phase == "transition_throne_to_menu":
            lines = [
                "Bravo ! Vous avez aidé le prince à sauver le royaume… ",
                "Mais une question demeure : ",
                "que se serait-il passé si vos choix avaient été différents ?",
                "",
                "",
                "Appuyez sur ENTER pour continuer"
            ]
            next_state = "start_menu"

        else:
            lines = ["Texte par défaut..."]
            next_state = "level1"

        self.intro_scene = IntroScene(self, lines=lines, next_state=next_state)
        self.game_state = "intro"


    def update_level2(self):
        """Met à jour le niveau 2"""
        # Récupération des touches pressées
        keys = pygame.key.get_pressed()

        # Mise à jour du gestionnaire de joueurs
        self.player_manager.update(keys, self.level2.collision_tiles)

        # Gestion du volume de la musique basé sur la position du joueur
        if self.player_manager.get_current_player():
            self.update_music_volume(self.player_manager.get_current_player().rect.x)

        # Mise à jour de la caméra pour suivre le joueur (ou le prince pendant la protection)
        self.update_camera()

    def update_camera(self):
        """Met à jour la position de la caméra pour suivre le joueur ou le prince"""
        if self.prince_protection.state == "zooming_out":
            # Phase de dézoomer vers la tile 62 (collée à droite de l'écran)
            tile_62_x = (
                self.prince_protection.target_zoom_tile * 16 * 2.5
            )  # Tile 62 en pixels
            # Tile 62 collée à droite (avec marge de 100px)
            target_x = tile_62_x - self.screen_width + 100

            # Lisser le mouvement de la caméra
            camera_speed = 8
            if abs(self.camera_x - target_x) > camera_speed:
                if self.camera_x < target_x:
                    self.camera_x += camera_speed
                else:
                    self.camera_x -= camera_speed
            else:
                self.camera_x = target_x
                self.prince_protection.zoom_complete = True

        elif self.prince_protection.state in [
            "zoom_on_prince",
            "dezoom_reveal_enemies",
        ]:
            # Gestion du zoom sur le prince
            zoom_target = self.prince_protection.get_zoom_target_position()
            if zoom_target:
                if self.prince_protection.state == "zoom_on_prince":
                    # Centrer sur le prince pendant le zoom
                    target_x = zoom_target[0] - self.screen_width // 2
                elif self.prince_protection.state == "dezoom_reveal_enemies":
                    # Prince à 20px du bord gauche
                    target_x = zoom_target[0]

                # Lisser le mouvement de la caméra
                camera_speed = 5
                if abs(self.camera_x - target_x) > camera_speed:
                    if self.camera_x < target_x:
                        self.camera_x += camera_speed
                    else:
                        self.camera_x -= camera_speed
                else:
                    self.camera_x = target_x

        elif self.prince_protection.state in ["protection"]:
            # Caméra fixe pendant la phase de protection
            # Garder la vue avec la tile 62 à droite
            pass
        elif self.prince_protection.state == "final_sequence":
            # Caméra fixe à la tile 62 (côté gauche) pour voir l'action depuis la gauche
            tile_62_x = 62 * 16 * 2.5  # Tile 62 en pixels
            target_x = (
                tile_62_x - 200
            )  # Un peu à gauche de la tile 62 pour voir l'action
            self.camera_x = target_x
        else:
            # Centrer la caméra sur le joueur actuel s'il existe
            current_player = self.player_manager.get_current_player()
            if current_player is not None:
                target_x = current_player.rect.centerx - self.screen_width // 2
                self.camera_x = target_x
            # Si pas de joueur, garder la caméra où elle est

        # Limites de la caméra pour ne pas sortir de la map
        map_width = (
            self.level1.map_width * self.level1.tile_size * self.level1.scale_factor
        )

        # Permettre à la caméra de voir toute la largeur de la map
        self.camera_x = max(0, min(self.camera_x, map_width - self.screen_width))

        # FIXER la caméra Y à 0 pour que la tilemap reste toujours collée en bas
        self.camera_y = 0

    def draw_level1(self):
        """Dessine le niveau 1"""
        # Ne pas effacer ici - le niveau 1 gère son propre background

        # Vérifier si on est dans l'état "black_screen" pour gérer l'écran noir
        if self.prince_protection.state == "black_screen":
            self.screen.fill((0, 0, 0))
            return  # Écran noir complet, ne rien dessiner d'autre

        # Gérer le zoom pendant les états zoom_on_prince et dezoom_reveal_enemies
        zoom_factor = self.prince_protection.get_zoom_factor()
        if zoom_factor > 1.0:
            self.draw_level1_with_zoom(zoom_factor)
        else:
            self.draw_level1_normal()

    def draw_level1_normal(self):
        """Dessine le niveau 1 normalement sans zoom"""
        # Dessiner le niveau (background + tilemap background)
        draw(
            self.screen,
            self.level1.background,
            lambda screen, camera_x, camera_y: draw_background_tilemap(
                screen,
                camera_x,
                camera_y,
                self.level1.background_layers_data,
                self.level1.tile_size,
                self.level1.scale_factor,
                self.level1.map_width,
                self.level1.map_height,
                self.level1.map_offset_y,
                self.level1.tiles,
                self.level1.tinted_tiles_cache,
                self.level1.layer_tintcolors,
            ),
            self.camera_x,
            self.camera_y,
        )

        # Dessiner le champ de bataille (warriors et enemies) EN ARRIÈRE-PLAN
        self.battlefield_manager.draw(
            self.screen,
            self.camera_x,
            self.camera_y,
            self.prince_protection.state,
            self.prince_protection.current_prince_x,
        )

        # Dessiner le Prince (visible jusqu'à ce que la protection commence)
        if self.prince_protection.state in [
            "waiting",
            "cinematic_slowdown",
            "player_death",
            "pause_after_death",
        ]:
            self.prince.draw(self.screen, self.camera_x, self.camera_y)

        # Dessiner le mini-niveau de protection du prince (SAUF l'écran noir)
        self.prince_protection.draw(self.screen, self.camera_x, self.camera_y)

        # Dessiner les flèches
        self.arrow_manager.draw(self.screen, self.camera_x, self.camera_y)

        # Dessiner les layers foreground par-dessus les NPCs
        draw_foreground_tilemap(
            self.screen,
            self.camera_x,
            self.camera_y,
            self.level1.foreground_layers_data,
            self.level1.tile_size,
            self.level1.scale_factor,
            self.level1.map_width,
            self.level1.map_height,
            self.level1.map_offset_y,
            self.level1.tiles,
            self.level1.tinted_tiles_cache,
            self.level1.layer_tintcolors,
        )

        # Dessiner le gestionnaire de joueurs (joueur actuel + corps morts) AU PREMIER PLAN
        self.player_manager.draw(self.screen, self.camera_x, self.camera_y)

        # Dessiner la barre de santé du joueur
        self.player_manager.draw_health_bar(self.screen)

        # Dessiner la barre de santé du prince (pendant le mini-jeu)
        self.prince_protection.draw_prince_health_bar(self.screen)

        # Dessiner l'interface de bataille
        self.battlefield_manager.draw_battle_ui(self.screen)

    def draw_level1_with_zoom(self, zoom_factor):
        """Dessine le niveau 1 avec zoom sur le prince"""
        # Créer une surface temporaire pour le rendu à la résolution normale
        temp_surface = pygame.Surface((self.screen_width, self.screen_height))

        # Dessiner sur la surface temporaire avec la caméra normale
        # Dessiner le niveau (background + tilemap background) sur la surface temporaire
        draw(
            temp_surface,
            self.level1.background,
            lambda screen, camera_x, camera_y: draw_background_tilemap(
                screen,
                camera_x,
                camera_y,
                self.level1.background_layers_data,
                self.level1.tile_size,
                self.level1.scale_factor,
                self.level1.map_width,
                self.level1.map_height,
                self.level1.map_offset_y,
                self.level1.tiles,
                self.level1.tinted_tiles_cache,
                self.level1.layer_tintcolors,
            ),
            self.camera_x,
            self.camera_y,
        )

        # Dessiner le champ de bataille pendant le dézoom pour voir les ennemis
        if self.prince_protection.state == "dezoom_reveal_enemies":
            self.battlefield_manager.draw(
                temp_surface,
                self.camera_x,
                self.camera_y,
                self.prince_protection.state,
                self.prince_protection.current_prince_x,
            )

        # Dessiner les foreground layers sur la surface temporaire
        draw_foreground_tilemap(
            temp_surface,
            self.camera_x,
            self.camera_y,
            self.level1.foreground_layers_data,
            self.level1.tile_size,
            self.level1.scale_factor,
            self.level1.map_width,
            self.level1.map_height,
            self.level1.map_offset_y,
            self.level1.tiles,
            self.level1.tinted_tiles_cache,
            self.level1.layer_tintcolors,
        )

        # Dessiner le prince
        self.prince_protection.draw(temp_surface, self.camera_x, self.camera_y)

        # Calculer la région à zoomer centrée sur le prince
        prince_screen_x = self.prince_protection.current_prince_x - self.camera_x
        prince_screen_y = self.prince_protection.prince_y - self.camera_y

        # Dimensions de la région à extraire (plus petite que l'écran selon le zoom)
        crop_width = int(self.screen_width / zoom_factor)
        crop_height = int(self.screen_height / zoom_factor)
        
        # Position de début de la région centrée sur le prince avec sécurités
        crop_x = max(0, min(self.screen_width - crop_width, int(prince_screen_x - crop_width // 2)))
        crop_y = max(0, min(self.screen_height - crop_height, int(prince_screen_y - crop_height // 2)))
        
        # Sécurité : s'assurer que la région de crop est valide et contient le prince
        if (crop_width <= 0 or crop_height <= 0 or 
            crop_x + crop_width > self.screen_width or 
            crop_y + crop_height > self.screen_height):
            # Fallback: utiliser la surface complète si le crop échoue
            print(f"Crop invalide (x={crop_x}, y={crop_y}, w={crop_width}, h={crop_height}), utilisation de la surface complète")
            cropped_surface = temp_surface.copy()
        else:
            # Extraire la région à zoomer
            crop_rect = pygame.Rect(crop_x, crop_y, crop_width, crop_height)
            cropped_surface = temp_surface.subsurface(crop_rect).copy()
            
            # Debug pour vérifier que le prince est dans la zone crop
            if self.prince_protection.state == "zoom_on_prince" and self.prince_protection.state_timer % 30 == 0:
                print(f"Zoom Debug - Prince screen: ({prince_screen_x:.1f}, {prince_screen_y:.1f}), Crop: ({crop_x}, {crop_y}, {crop_width}, {crop_height})")
                prince_in_crop = (prince_screen_x >= crop_x and prince_screen_x < crop_x + crop_width and
                                prince_screen_y >= crop_y and prince_screen_y < crop_y + crop_height)
                print(f"Prince dans zone crop: {prince_in_crop}")
        
        # Redimensionner et dessiner sur l'écran principal
        zoomed_surface = pygame.transform.scale(
            cropped_surface, (self.screen_width, self.screen_height)
        )
        self.screen.blit(zoomed_surface, (0, 0))

    def draw_level2(self):
        """Dessine le niveau 2"""
        # Ne pas effacer ici - le niveau 2 gère son propre background

        # Dessiner le niveau (background + tilemap background)
        draw(
            self.screen,
            self.level2.background,
            lambda screen, camera_x, camera_y: draw_background_tilemap(
                screen,
                camera_x,
                camera_y,
                self.level2.background_layers_data,
                self.level2.tile_size,
                self.level2.scale_factor,
                self.level2.map_width,
                self.level2.map_height,
                self.level2.map_offset_y,
                self.level2.tiles,
                self.level2.tinted_tiles_cache,
                self.level2.layer_tintcolors,
            ),
            self.camera_x,
            self.camera_y,
        )

        # Dessiner les layers foreground par-dessus les NPCs
        draw_foreground_tilemap(
            self.screen,
            self.camera_x,
            self.camera_y,
            self.level2.foreground_layers_data,
            self.level2.tile_size,
            self.level2.scale_factor,
            self.level2.map_width,
            self.level2.map_height,
            self.level2.map_offset_y,
            self.level2.tiles,
            self.level2.tinted_tiles_cache,
            self.level2.layer_tintcolors,
        )

        # Dessiner le gestionnaire de joueurs (joueur actuel + corps morts) AU PREMIER PLAN
        self.player_manager.draw(self.screen, self.camera_x, self.camera_y)

    def init_level1(self):
        # Calculer la position de la porte du château (approximativement 80% de la largeur de la map)
        map_width_pixels = (
            self.level1.map_width * self.level1.tile_size * self.level1.scale_factor
        )
        castle_door_x = map_width_pixels * 0.8  # Position approximative de la porte

        # Position de spawn initiale du joueur (côté droit)
        start_x = map_width_pixels - 300  # 300 pixels avant la fin de la map

        # Position Y : Utiliser la même logique que les ennemis dans battlefield_manager
        # Valeur de base (ajustement fait dans player.py maintenant)
        ground_level = 655
        # Gestionnaire de joueurs et système de respawn
        self.player_manager = PlayerManager(start_x, ground_level, castle_door_x)

        # Gestionnaire de flèches
        self.arrow_manager = ArrowManager(
            self.screen_width, self.screen_height, castle_door_x
        )

        # Gestionnaire de champ de bataille
        map_width_pixels = (
            self.level1.map_width * self.level1.tile_size * self.level1.scale_factor
        )
        self.battlefield_manager = BattlefieldManager(
            map_width_pixels, self.screen_height
        )

        # Prince sous l'arbre (tile 25, très vers la gauche)
        # Calculer la position du prince à la tile 25
        prince_tile_x = 25
        prince_x = prince_tile_x * self.level1.tile_size * self.level1.scale_factor
        prince_y = ground_level - 100 - 25  # Baisser le prince sous l'arbre de 25px
        self.prince = Prince(prince_x, prince_y)

        # Gestionnaire du mini-niveau de protection du prince
        self.prince_protection = PrinceProtectionManager(
            prince_x, prince_y, castle_door_x, self.start_intro_for_phase
        )

        # Charger et lancer la musique du niveau 1
        self.setup_level1_music()

        # Gestion du volume musical basé sur la position (tiles 70 à 62)
        self.music_volume_base = 0.5  # Volume de base
        # Début de la baisse de volume (retour à 70)
        self.music_fade_start_tile = 70
        # Fin de la baisse de volume (volume minimal)
        self.music_fade_end_tile = 62

    def init_level2(self):
        # Calculer la position de la porte du château (approximativement 80% de la largeur de la map)
        map_width_pixels = (
            self.level1.map_width * self.level1.tile_size * self.level1.scale_factor
        )
        # firecamp_x = map_width_pixels * 0.1  # Position approximative du camp de base

        start_x = 150

        # Position Y : Sur le sol (ligne 18-19 de la tilemap selon l'image)
        ground_tile_y = 17  # Ligne du sol dans la tilemap

        # Créer un joueur temporaire pour connaître sa hauteur
        temp_player = Player(0, 0)
        start_y = (
            ground_tile_y * self.level1.tile_size * self.level1.scale_factor
            + self.level1.map_offset_y
            - temp_player.rect.height
        )

        self.prince_protection = PrinceProtectionManager(start_x, start_y, 0, None)
        self.prince_protection.state = "waiting"
        # Gestionnaire de joueurs et système de respawn
        self.player_manager = PlayerManager2(start_x, start_y, self.start_intro_for_phase)

        self.setup_level2_music()

        self.music_volume_base = 0  # Volume de base

        # Début de la baisse de volume (retour à 70)
        self.music_fade_start_tile = -30
        # Fin de la baisse de volume (volume minimal)
        self.music_fade_end_tile = -10

    def update_music_volume(self, player_x):
        """Met à jour le volume de la musique basé sur la position du joueur"""
        # Convertir la position du joueur en tile
        player_tile = player_x / (self.level1.tile_size * self.level1.scale_factor)

        # Vérifier si on est dans la phase de sortie du prince du château (coupe complètement la musique)
        if hasattr(self, "prince_protection") and self.prince_protection.state in [
            "zoom_on_prince",
            "dezoom_reveal_enemies",
        ]:
            # Pendant la sortie du prince, couper complètement la musique
            volume = 0.0
        elif player_tile >= self.music_fade_start_tile:
            # Au-delà de la tile 70, volume normal
            volume = self.music_volume_base
        elif player_tile <= self.music_fade_end_tile:
            # En deçà de la tile 62, volume à 0 (complètement muet)
            volume = 0.0
        else:
            # Entre les tiles 70 et 62, interpolation linéaire jusqu'à 0
            fade_range = self.music_fade_start_tile - self.music_fade_end_tile
            fade_progress = (player_tile - self.music_fade_end_tile) / fade_range
            volume = (
                self.music_volume_base * fade_progress
            )  # De 0.0 à music_volume_base

        # Appliquer le volume sur le canal de musique ET sur pygame.mixer.music
        if (hasattr(self.level1, "music_channel") and hasattr(self.level1, "music_sound")) or (hasattr(self.level2, "music_channel") and hasattr(self.level2, "music_sound")):
            self.current_music_channel.set_volume(volume)
        pygame.mixer.music.set_volume(volume)
        
    def setup_music(self, music_path, volume=0.5):
        """Configure et lance la musique de fond pour une scène donnée."""
        try:
            # Créer un canal dédié pour la musique
            music_channel = pygame.mixer.Channel(0)
            music_sound = pygame.mixer.Sound(music_path)

            # Stocker le canal et le son pour contrôle
            self.current_music_channel = music_channel
            self.current_music_sound = music_sound

            # Lancer la musique en boucle
            music_channel.play(music_sound, loops=-1)

            # Aussi charger avec pygame.mixer.music pour compatibilité
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(loops=-1)

            print(f"Musique {music_path} lancée avec succès")
        except pygame.error as e:
            print(f"Erreur lors du chargement de la musique {music_path}: {e}")
            # Initialiser des valeurs par défaut en cas d'erreur
            self.current_music_channel = None
            self.current_music_sound = None

    def setup_level1_music(self):
        """Configure et lance la musique du niveau 1."""
        self.setup_music("./assets/sounds/music/Level1.mp3", volume=0.5)

    def setup_level2_music(self):
        """Configure et lance la musique du niveau 2."""
        self.setup_music("./assets/sounds/night_atmosphere.mp3", volume=0.5)

    def setup_throne_music(self):
        """Configure et lance la musique de la scène du trône."""
        self.setup_music("./assets/sounds/music/crowd-cheering.mp3", volume=0.5)

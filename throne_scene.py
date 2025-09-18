import pygame
import xml.etree.ElementTree as ET


# TMX GID flip flags
FLIP_H = 0x80000000
FLIP_V = 0x40000000
FLIP_D = 0x20000000
GID_MASK = 0x1FFFFFFF


class ThroneScene:
	def __init__(self, screen):
		self.screen = screen
		self.screen_width = screen.get_width()
		self.screen_height = screen.get_height()

		# Map properties (defaults; will be overridden by TMX root attrs)
		self.map_width = 50
		self.map_height = 20
		self.tile_size = 16
		self.scale_factor = 2.5  # keep same as level1 (16px -> 40px)
		self.tile_px = int(self.tile_size * self.scale_factor)

		# Bottom-align the map on screen
		self.map_total_height = self.map_height * self.tile_px
		self.map_offset_y = self.screen_height - self.map_total_height

		# Tiles and layers
		self.tiles = {}  # gid (no flags) -> scaled surface
		self.layers = []  # list[(name, matrix[int gid-with-flags])]
		self.collision_tiles = []  # rects built from layer named "Ground"

		# Cinematic state
		self.camera_x = 0
		self.camera_y = 0
		self.cinematic_phase = "walk"  # walk -> fade_to_black -> zoom_on_throne -> done
		self.zoom_factor = 1.0
		self.max_zoom = 1.7
		self.zoom_speed = 0.005
		self.fade_alpha = 0  # For fade-to-black effect

		# Load TMX map and tilesets
		self._load_map("assets/maps/throne/throne.tmx")

		# Create player using existing Player class
		from player_throne import PlayerThrone
		# Start off-screen left; place roughly on ground line
		self.player = PlayerThrone(-60, 0)
		ground_guess_y = (self.map_height - 3) * self.tile_px + self.map_offset_y - self.player.rect.height
		# If we can find a ground tile under x=0 area, snap to it
		snap_y = None
		sample_x = 2 * self.tile_px
		for rect in self.collision_tiles:
			if rect.left <= sample_x <= rect.right:
				if snap_y is None or rect.top < snap_y:
					snap_y = rect.top
		if snap_y is not None:
			self.player.rect.y = snap_y - self.player.rect.height - 10  # Ajout de -10 pour éviter d'être dans le sol
		else:
			self.player.rect.y = ground_guess_y - 10  # Ajout de -10 pour éviter d'être dans le sol

		# Target near the right side (throne area visually)
		self.target_x = self.map_width * self.tile_px - 58 * self.tile_px
		self.walk_speed = 5 #TODO 3  # will be used as Player.speed during the walk

	# ---------- Map loading ----------
	def _load_map(self, map_path: str):
		tree = ET.parse(map_path)
		root = tree.getroot()

		# Read base map attributes
		try:
			self.map_width = int(root.get("width", self.map_width))
			self.map_height = int(root.get("height", self.map_height))
			self.tile_size = int(root.get("tilewidth", self.tile_size))
		except Exception:
			pass
		# Recompute derived sizes
		self.tile_px = int(self.tile_size * self.scale_factor)
		self.map_total_height = self.map_height * self.tile_px
		self.map_offset_y = self.screen_height - self.map_total_height

		# Load tilesets (supports multiple)
		for ts in root.findall("tileset"):
			firstgid = int(ts.get("firstgid"))
			image = ts.find("image")
			if image is None:
				continue  # external TSX not supported here
			source = image.get("source")
			image_path = f"assets/maps/throne/{source}"
			tilewidth = int(ts.get("tilewidth")) if ts.get("tilewidth") else int(root.get("tilewidth", self.tile_size))
			tileheight = int(ts.get("tileheight")) if ts.get("tileheight") else int(root.get("tileheight", self.tile_size))
			columns = int(ts.get("columns"))

			# Slice tileset
			img = pygame.image.load(image_path).convert_alpha()
			img_w, img_h = img.get_width(), img.get_height()
			rows = img_h // tileheight
			for row in range(rows):
				for col in range(columns):
					x = col * tilewidth
					y = row * tileheight
					if x + tilewidth <= img_w and y + tileheight <= img_h:
						gid = firstgid + row * columns + col
						tile_surf = img.subsurface((x, y, tilewidth, tileheight))
						scaled = pygame.transform.smoothscale(
							tile_surf,
							(int(tilewidth * self.scale_factor), int(tileheight * self.scale_factor)),
						)
						self.tiles[gid] = scaled.convert_alpha()

		# Read layers in file order and parse CSV data
		for layer in root.findall("layer"):
			name = layer.get("name")
			data_element = layer.find("data")
			if data_element is None or not data_element.text:
				continue
			csv_data = data_element.text.strip()
			rows = csv_data.split("\n")
			matrix = []
			for row in rows:
				if row.strip():
					matrix.append([int(v.strip()) if v.strip() else 0 for v in row.split(",")])
			self.layers.append((name, matrix))

			# Build collision rects for the "Ground" layer
			if name == "Ground":
				for y, row_vals in enumerate(matrix):
					for x, gid in enumerate(row_vals):
						if gid:  # any non-zero tile is solid
							rect = pygame.Rect(
								x * self.tile_px,
								y * self.tile_px + self.map_offset_y,
								self.tile_px,
								self.tile_px,
							)
							self.collision_tiles.append(rect)

	# ---------- Camera ----------
	def _update_camera(self):
		# Center camera on player, clamp to map bounds
		target_x = self.player.rect.centerx - self.screen_width // 2
		map_width_px = self.map_width * self.tile_px
		self.camera_x = max(0, min(target_x, max(0, map_width_px - self.screen_width)))
		self.camera_y = 0

	# ---------- Update ----------
	def update(self):
		if self.cinematic_phase == "walk":
			# Simulate right arrow pressed to drive player physics with collisions
			class FakeKeys:
				def __init__(self, pressed):
					self._pressed = set(pressed)
				def __getitem__(self, key):
					return key in self._pressed

			if self.player.rect.centerx < self.target_x:
				# Drive player using its normal update for consistent animations
				try:
					old_speed = getattr(self.player, "speed", 5)
					self.player.speed = self.walk_speed
					keys = FakeKeys({pygame.K_RIGHT})
					self.player.update(keys, self.collision_tiles)
				finally:
					# restore nominal speed for safety
					self.player.speed = old_speed
			else:
				self.cinematic_phase = "fade_to_black"
			self._update_camera()
		elif self.cinematic_phase == "fade_to_black":
			# Gradually fade to black
			self.fade_alpha = min(255, self.fade_alpha + 5)
			if self.fade_alpha >= 255:
				self.cinematic_phase = "zoom_on_throne"
				self.player.rect.centery -= 80
		elif self.cinematic_phase == "zoom_on_throne":
			self.player.rect.centerx = self.map_width * self.tile_px - 53 * self.tile_px

			# Make the prince face left
			self.player.facing_right = False

			# Ensure the prince stops running and transitions to idle
			self.player.current_animation = "idle"
			self.player.animation_frame = 0

			# Slightly increase zoom speed and set a higher maximum zoom level
			self.zoom_speed = 0.005  # Slightly faster zoom
			self.max_zoom = 2.9  # More zoomed-in final state
			self.zoom_factor = min(self.max_zoom, self.zoom_factor + self.zoom_speed)
			self._update_camera()
			if self.zoom_factor >= self.max_zoom:
				self.cinematic_phase = "done"
		else:
			self._update_camera()

	# ---------- Rendering helpers ----------
	def _iter_visible_tiles(self):
		start_x = max(0, int(self.camera_x // self.tile_px) - 1)
		end_x = min(self.map_width, int((self.camera_x + self.screen_width) // self.tile_px) + 2)
		start_y = 0
		end_y = self.map_height
		return start_x, end_x, start_y, end_y

	def _blit_tile(self, surface, gid_with_flags, screen_x, screen_y):
		if gid_with_flags == 0:
			return
		flags = gid_with_flags & (FLIP_H | FLIP_V | FLIP_D)
		gid = gid_with_flags & GID_MASK
		base = self.tiles.get(gid)
		if base is None:
			return
		img = base
		if flags:
			h = bool(flags & FLIP_H)
			v = bool(flags & FLIP_V)
			d = bool(flags & FLIP_D)
			if d:
				img = pygame.transform.rotate(img, 90)
				if h and v:
					pass
				elif h:
					img = pygame.transform.flip(img, False, True)
				elif v:
					img = pygame.transform.flip(img, True, False)
			else:
				if h or v:
					img = pygame.transform.flip(img, h, v)
		surface.blit(img, (screen_x, screen_y))

	# ---------- Draw ----------
	def draw(self, screen):
		# Render to base surface; when zooming, render to an intermediate then scale
		base_surface = screen
		if self.zoom_factor != 1.0:
			base_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)

		# Background clear color
		base_surface.fill((10, 8, 14))

		# Draw TMX layers in file order
		start_x, end_x, start_y, end_y = self._iter_visible_tiles()
		for layer_name, matrix in self.layers:
			for y in range(start_y, end_y):
				if y >= len(matrix):
					continue
				row = matrix[y]
				for x in range(start_x, end_x):
					if x >= len(row):
						continue
					gid = row[x]
					if gid:
						sx = round(x * self.tile_px - self.camera_x)
						sy = round(y * self.tile_px + self.map_offset_y - self.camera_y)
						self._blit_tile(base_surface, gid, sx, sy)

		# Draw player with its own rendering
		if self.player:
			px = round(self.player.rect.x - self.camera_x)
			py = round(self.player.rect.y - self.camera_y)
			try:
				self.player.draw(base_surface, px, py)
			except Exception:
				pygame.draw.rect(base_surface, (0, 128, 255), pygame.Rect(px, py, 40, 40))

		# Draw fade effect if in fade phase
		if self.cinematic_phase == "fade_to_black":
			fade_surface = pygame.Surface((self.screen_width, self.screen_height))
			fade_surface.fill((0, 0, 0))
			fade_surface.set_alpha(self.fade_alpha)
			screen.blit(fade_surface, (0, 0))

		# Adjust zoom to ensure it centers on the player
		if base_surface is not screen:
			zoomed_w = int(self.screen_width * self.zoom_factor)
			zoomed_h = int(self.screen_height * self.zoom_factor)
			zoomed = pygame.transform.smoothscale(base_surface, (zoomed_w, zoomed_h))

			# Compute offsets to center the zoom on the player with a Y offset of 10
			player_screen_x = self.player.rect.centerx - self.camera_x
			player_screen_y = self.player.rect.centery - self.camera_y - 60
			offset_x = self.screen_width // 2 - int(player_screen_x * self.zoom_factor)
			offset_y = self.screen_height // 2 - int(player_screen_y * self.zoom_factor)

			# Blit the zoomed surface centered on the player
			screen.blit(zoomed, (offset_x, offset_y))


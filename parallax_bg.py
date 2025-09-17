
import pygame
from pathlib import Path

class ParallaxBg:
    def __init__(self, folder_path: str, screen_size: tuple, cloud_layers: list[int] = []):
        self.screen_width, self.screen_height = screen_size
        self.layers = []
        self.cloud_offsets = {}  # index -> drift offset
        self.cloud_speeds = {}   # index -> drift speed (based on depth)

        folder = Path(folder_path)
        image_files = sorted(folder.glob("*.png"), key=lambda f: int(f.stem))

        if not image_files:
            raise ValueError(f"No .png files found in {folder_path}")

        self.layer_count = len(image_files)

        for i, file in enumerate(image_files):
            image = pygame.image.load(str(file)).convert_alpha()
            image = pygame.transform.scale(image, (self.screen_width, self.screen_height))

            # Depth scroll factor: 0.0 (furthest) to 1.0 (closest)
            scroll_factor = i / (self.layer_count - 1) if self.layer_count > 1 else 0

            is_cloud = i in cloud_layers
            if is_cloud:
                self.cloud_offsets[i] = 0
                self.cloud_speeds[i] = 0.4 * scroll_factor  # You can adjust base speed here

            self.layers.append({
                "image": image,
                "scroll_factor": scroll_factor,
                "is_cloud": is_cloud,
                "index": i
            })

    def update(self):
        # Move clouds based on their depth-derived speed
        for i in self.cloud_offsets:
            self.cloud_offsets[i] += self.cloud_speeds[i]
            self.cloud_offsets[i] %= self.screen_width

    def draw(self, surface, scroll_x):
        for layer in self.layers:
            img = layer["image"]
            factor = layer["scroll_factor"]
            index = layer["index"]

            if layer["is_cloud"]:
                drift = self.cloud_offsets[index]
                rel_x = (-scroll_x * factor + drift) % self.screen_width
            else:
                rel_x = (-scroll_x * factor) % self.screen_width

            # Draw twice to avoid visual gaps when scrolling
            surface.blit(img, (rel_x, 0))
            surface.blit(img, (rel_x - self.screen_width, 0))


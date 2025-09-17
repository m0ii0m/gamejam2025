import pygame
import random
from game import Game

pygame.init()

# Défini le nom de la fenetre
pygame.display.set_caption("Plot Armor")

# Défini la taille de la fenetre
screen = pygame.display.set_mode((1200, 750))

# Défini l'horloge du jeu
clock = pygame.time.Clock()
IPS = 45
game = Game(screen)

running = True

# Tant que le jeu tourne
while running:


    # On met à jour le jeu
    game.state_manager()
    
    # Mise à jour de l'écran
    pygame.display.flip()

    clock.tick(IPS)
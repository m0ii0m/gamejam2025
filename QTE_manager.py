import random
import pygame
from QTE_guard import Guard
import os

class QTEManager:
    def __init__(self, x, y, onQteEnd):
        self.base_x = x
        self.base_y = y
        self.QTE_rounds_number = 5
        self.QTE_rounds_done = 0
        self.QTE_minimum_time = 15
        self.QTE_maximum_time = 30
        self.QTE_waiting_timer = 60

        self.onQteEnd = onQteEnd

        self.QTE_keys = ['left', 'right']
        self.current_sequence = []
        self.sequence_score = 0
        self.current_index = 0
        self.current_timer = 0
        self.waiting = True
        self.waiting_timer = self.QTE_waiting_timer
        self.progress = 0

        self.show_left = False
        self.show_right = False
        self.left_ally = Guard(x-90,y, team="blue", facing="left")
        self.right_ally = Guard(x+60,y, team="blue", facing="right")
        self.left_ennemy = Guard(x-140,y, team="red", facing="right")
        self.right_ennemy = Guard(x+110,y, team="red", facing="left")

        self.key_pressed = False

        self.key_q_img = pygame.image.load("assets/images/sprites/key/q1.png").convert_alpha()
        self.key_d_img = pygame.image.load("assets/images/sprites/key/d1.png").convert_alpha()


    def start_round(self):
        self.current_sequence = [random.choice(self.QTE_keys) for _ in range(random.randint(1, 2))]
        self.current_index = 0
        self.waiting = False
        self.progress = 0
        self.state = 'waiting_instruction'  # 'waiting_instruction', 'instruction', 'result', 'finished'
        self.timer = random.randint(60, 90)  # délai avant affichage instruction (ex: 2-3s à 60fps)
        self.reaction_window = 0
        self.last_instruction = None
        self.last_result = None
        self.left_ennemy.current_animation = 'idle'
        self.right_ennemy.current_animation = 'idle'

    def update(self, keys):
        """
        Nouveau déroulement QTE :
        - Attend un délai, puis affiche l'instruction (gauche/droite) au-dessus de l'ennemi
        - Ouvre une fenêtre de réaction (1-2s)
        - Selon la réaction, joue l'animation (fight/dead/idle)
        """
        if self.waiting:
            self.waiting_timer -= 1
            if self.waiting_timer <= 0:
                self.start_round()
            return None

        if self.state == 'waiting_instruction':
            self.left_ennemy.set_animation('idle') 
            self.right_ennemy.set_animation('idle') 
            self.right_ally.set_animation('idle') 
            self.left_ally.set_animation('idle') 
            self.timer -= 1
            if self.timer <= 0:
                # Affiche l'instruction
                if self.current_index < len(self.current_sequence):
                    self.last_instruction = self.current_sequence[self.current_index]
                    self.state = 'instruction'
                    self.reaction_window = 45  
                    self.success = False

        if self.state == 'instruction':
            self.reaction_window -= 1

            # Check si le joueur appuie sur la bonne touche
            if not self.success:
                if self.last_instruction == 'left':
                    self.success = self.success or keys[pygame.K_LEFT] or keys[pygame.K_q]
                else:
                    self.success = self.success or keys[pygame.K_RIGHT] or keys[pygame.K_d]

            if self.reaction_window <= 0:
                self.state = 'animation'
                self.animation_timer = 20
                if self.success:
                    self.sequence_score += 1
                    if self.last_instruction == 'left':
                        self.left_ally.set_animation('attack1')
                        self.left_ennemy.set_animation('attack1')
                    else:
                        self.right_ally.set_animation('attack1')
                        self.right_ennemy.set_animation('attack1')
                else:
                    if self.last_instruction == 'left':
                        self.left_ally.set_animation('hit')
                        self.left_ennemy.set_animation('attack1')
                    else:
                        self.right_ally.set_animation('hit')
                        self.right_ennemy.set_animation('attack1')

        if self.state == 'animation':
            self.animation_timer -= 1
            if self.animation_timer <= 0:
                self.current_index += 1
                if self.current_index < len(self.current_sequence):
                    self.state = 'waiting_instruction'
                    self.right_ally.set_animation('idle')
                    self.left_ally.set_animation('idle')
                    self.right_ennemy.set_animation('idle')
                    self.left_ennemy.set_animation('idle')
                    self.timer = random.randint(30, 60)
                else:
                    self.state = 'finished'
                    self.right_ennemy.set_animation('death')
                    self.left_ennemy.set_animation('death')
                    if self.sequence_score >= (len(self.current_sequence) / 2):
                        self.right_ally.set_animation('idle')
                        self.left_ally.set_animation('idle')
                    else:
                        self.right_ally.set_animation('death')
                        self.left_ally.set_animation('death')
                    self.onQteEnd()

        self.left_ally.update()
        self.right_ally.update()
        self.right_ennemy.update()
        self.left_ennemy.update()


    def draw(self, screen, camera_x, camera_y):
        self.left_ennemy.draw(screen,  camera_x, camera_y)
        self.right_ennemy.draw(screen, camera_x, camera_y)
        self.left_ally.draw(screen,  camera_x, camera_y)
        self.right_ally.draw(screen,  camera_x, camera_y)
        # Affiche l'instruction au-dessus de l'ennemi concerné (debug/visuel)
        if hasattr(self, 'last_instruction') and self.state == 'instruction':
            font = pygame.font.SysFont(None, 36)
            if self.last_instruction == 'left':
                img = self.key_q_img
                pos = (self.left_ennemy.x + 35  - img.get_width()//2, self.left_ennemy.y - 30)
            else:
                img = self.key_d_img
                pos = (self.right_ennemy.x + 35 -img.get_width()//2, self.right_ennemy.y - 30)
            screen.blit(img, pos)

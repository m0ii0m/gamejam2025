import random
import pygame
from QTE_guard import Guard

class QTEManager:
    def __init__(self, x, y):
        self.base_x = x
        self.base_y = y
        self.QTE_rounds_number = 5
        self.QTE_rounds_done = 0
        self.QTE_minimum_time = 15
        self.QTE_maximum_time = 30
        self.QTE_waiting_timer = 60

        self.QTE_keys = ['left', 'right']
        self.current_sequence = []
        self.current_index = 0
        self.current_timer = 0
        self.waiting = True
        self.waiting_timer = self.QTE_waiting_timer
        self.progress = 0

        self.show_left = False
        self.show_right = False
        self.left_ally = Guard(x-30,y, team="blue", facing="left")
        self.right_ally = Guard(x+30,y, team="blue", facing="right")
        self.left_ennemy = Guard(x-80,y, team="red", facing="right")
        self.right_ennemy = Guard(x+80,y, team="red", facing="left")


    def start_round(self):
        print("Starting QTE round")
        self.current_sequence = [random.choice(self.QTE_keys) for _ in range(random.randint(3, 5))]
        self.current_index = 0
        self.waiting = False
        self.progress = 0
        self.state = 'waiting_instruction'  # 'waiting_instruction', 'instruction', 'result', 'finished'
        self.timer = random.randint(120, 180)  # délai avant affichage instruction (ex: 2-3s à 60fps)
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
        print(self.waiting, self.waiting_timer, self.state, self.timer, self.current_sequence, self.current_index)
        if self.waiting:
            self.waiting_timer -= 1
            if self.waiting_timer <= 0:
                self.start_round()
            return None

        if self.state == 'waiting_instruction':
            self.timer -= 1
            if self.timer <= 0:
                # Affiche l'instruction
                if self.current_index < len(self.current_sequence):
                    self.last_instruction = self.current_sequence[self.current_index]
                    self.state = 'instruction'
                    self.reaction_window = random.randint(60, 120)  # 1-2s à 60fps

        if self.state == 'instruction':
            if self.reaction_window < 5:
                if self.last_instruction == 'left':
                    self.left_ennemy.set_animation('attack1') 
                else:
                    self.right_ennemy.set_animation('attack1')
            self.reaction_window -= 1
            # Check si le joueur appuie sur la bonne touche
            if self.last_instruction == 'left':
                key_pressed = keys[pygame.K_LEFT] or keys[pygame.K_q]
            else:
                key_pressed = keys[pygame.K_RIGHT] or keys[pygame.K_d]

            if key_pressed:
                # Succès : animation idle, passe à l'instruction suivante
                if self.last_instruction == 'left':
                    self.left_ally.set_animation('attack1')
                else:
                    self.right_ally.set_animation('attack1')
                self.current_index += 1
                if self.current_index < len(self.current_sequence):
                    self.state = 'waiting_instruction'
                    self.left_ennemy.set_animation('attack1')
                    self.right_ennemy.set_animation('attack1')
                    self.timer = random.randint(60, 90)
                else:
                    self.state = 'finished'

            if self.reaction_window <= 0:
                # Échec : animation dead
                if self.last_instruction == 'left':
                    self.left_ally.set_animation('hit')
                else:
                    self.right_ally.set_animation('hit')
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

        self.left_ally.update()
        self.right_ally.update()
        self.right_ennemy.update()
        self.left_ennemy.update()

        # Si QTE terminé, ne rien faire
        if self.state == 'finished':
            return None


    def draw_progress_bar(self, screen, x, y, width, height):
        pygame.draw.rect(screen, (100, 100, 100), (x, y, width, height))
        pygame.draw.rect(screen, (0, 200, 0), (x, y, width * self.progress, height))

    def draw(self, screen, camera_x, camera_y):
        self.left_ennemy.draw(screen,  camera_x, camera_y)
        self.right_ennemy.draw(screen, camera_x, camera_y)
        self.left_ally.draw(screen,  camera_x, camera_y)
        self.right_ally.draw(screen,  camera_x, camera_y)
        # Affiche l'instruction au-dessus de l'ennemi concerné (debug/visuel)
        if hasattr(self, 'last_instruction') and self.state == 'instruction':
            font = pygame.font.SysFont(None, 36)
            if self.last_instruction == 'left':
                text = font.render('GAUCHE', True, (255,255,0))
                pos = (self.left_ennemy.x, self.left_ennemy.y - 40)
            else:
                text = font.render('DROITE', True, (255,255,0))
                pos = (self.right_ennemy.x, self.right_ennemy.y - 40)
            screen.blit(text, pos)

import numpy as np
from collections import namedtuple
from enum import Enum
import sys
import os
import time
import copy
from IPython.display import clear_output
import pandas as pd 
from Agents import Agents

class Env:

    def __init__(self, size, ufo_prob, bomb_prob, time_step, training_frames=None):
        self.size = size
        self.level = 1
        self.player = [self.size -3, (self.size//2 - 2), Agents['PLAYER'].health]
        self.actions = ['stay', 'left', 'right', 'attack']
        self.actions_prob = [0.25, 0.25, 0.25, 0.25]
        self.bullet = [-1, -1, Agents['BULLET'].health]
        self.bullet_flag = False
        self.reward = 0

        self.enemies = {'ENEMY_WEAK': [],
                        'ENEMY_STRONG': [],
                        'ENEMY_UFO': []}
        self.number_of_enemies_in_a_row = self.size//(2 * 4)
        
        # UFO PROBABILITY TO APEAR
        self.ufo_prob = ufo_prob
        self.bomb_prob = bomb_prob
        self.bomb = [-1, -1, Agents['BOMB'].health]
        self.bomb_flag = False
        
        # COUNTERS FOR TIME STEP AND SPEED
        self.time_step = time_step
        self.player_counter = 0
        self.bullet_counter = 0
        self.enemy_weak_strong_counter = 0
        self.ufo_counter = 0
        self.bomb_counter = 0
        self.ufo_time_counter = 3 * self.time_step

        # GAME BOARD LINE FOR DISPLAY
        self.game_board_line = ' ' * self.size

        # EXTERMUM POSITIONS OF ENEMY FLEET
        self.ws_max_x = - np.inf
        self.ws_min_x = np.inf
        self.ws_max_y = 0

        # REACHED WALL FLAGS AND DIRECTION
        self.enemy_fleet_direction = 1
        self.ws_reached_wall = False

        # TRAINING FRAMES
        if training_frames !=None:
            if os.path.exists(training_frames):
                self.frames = pd.read_csv(training_frames)
                self.frames = list(self.frames['frame'].values)

        else:
            self.frames= [['Game Over'], ['Congratulations you won!']]

        # CURRENT STATE
        self.game_over = False
        self.current_state = []


    def reset(self, ):

        self.player = [self.size -3, (self.size//2 - 2), Agents['PLAYER'].health]
        self.bullet[:2] = [-1, -1]
        self.bullet_flag = False
        if self.level == 1:
            self.reward = 0
        
        enemies_pos_x = (
            self.size - self.number_of_enemies_in_a_row * 4)//2
        
        self.enemies = {'ENEMY_WEAK': [],
                        'ENEMY_STRONG': [],
                        'ENEMY_UFO': []}
        for i in range(self.number_of_enemies_in_a_row):
            self.enemies['ENEMY_WEAK'].append(
                [6, enemies_pos_x, Agents(1).health])
            self.enemies['ENEMY_STRONG'].append(
                [3, enemies_pos_x, Agents(2).health])
            enemies_pos_x += 4  # 4 IS THE WIDTH OF AN ENEMY (WEAK AND STRONG TYPE)
        self.enemies['ENEMY_UFO'].append([-1, -1, Agents['ENEMY_UFO'].health])
        self.bomb = [-1, -1, Agents['BOMB'].health]
        
        # ENEMY FLAG AND COUNTER RESET
        self.ufo_flag = False
        self.bomb_flag = False
        self.enemy_weak_strong_counter = 0
        self.ufo_counter = 0
        self.bomb_counter = 0
        self.ufo_time_counter = 3 * self.time_step
        
        # EXTERMUM POSITION POINTS RESET
        self.ws_max_x = - np.inf
        self.ws_min_x = np.inf
        self.ws_max_y = 0

        # REACHED WALL FLAGS AND DIRECTION
        self.enemy_fleet_direction = 1
        self.ws_reached_wall = False

        # CURRENT STATE
        self.current_state = self.current_state_calc()

    def play(self, ):

        try:

            self.game_over = False
            while self.game_over == False:

                self.enemies_health_check()
                if sum([value[2] for key, values in self.enemies.items() for value in values]) == 0:
                    self.reward += self.level * 50
                    self.level += 1  # IF ALL ENEMIES KILLED GO TO NEXT LEVEL
                    self.reset()
                
                if self.level == 11:
                    
                    self.current_state = self.current_state_calc()
                    
                    print('Congratulations you won!')
                    
                    frames_to_save = pd.DataFrame(self.frames, columns=['frame'])
                    frames_to_save.to_csv('training_frames.csv')
                    break

                if self.player[2] == 0:
                    self.game_over = True

                if self.game_over == True:
                    
                    self.current_state = self.current_state_calc()
                    
                    self.reward += -100
                    self.display()
                    self.level = 1
                    self.game_over = False
                    self.reset()
                    frames_to_save = pd.DataFrame(self.frames, columns=['frame'])
                    frames_to_save.to_csv('training_frames.csv')
                    break
                
                if (self.ufo_flag == False and self.enemies['ENEMY_UFO'][0][2] > 0):
                    self.ufo_flag_generator()
                
                self.reached_wall()
                
                self.current_state = self.current_state_calc()

                self.display()
                time.sleep(0.01)
                
                self.step()

        except:
            print('Something went wrong!')
            frames_to_save = pd.DataFrame(self.frames, columns=['frame'])
            frames_to_save.to_csv('training_frames.csv')

    def current_state_calc(self, ):

        current_frame = ''

        if self.game_over == True:
            if 'Game Over' not in self.frames:
                self.frames.append('Game Over')
            
            current_frame = 'Game Over'

        elif self.level == 11:
            if 'Congratulations you won!' not in self.frames.values:
                self.frames.append('Congratulations you won!')
            
            current_frame = 'Congratulations you won!'    
        
        else:        
            
            current_frame += 'LEVEL'
            element = '0' * int(np.ceil(np.log10(self.size))) + str(self.level)
            current_frame += element[-int(np.ceil(np.log10(self.size))):]

            current_frame += 'PLAYER'
            for element in self.player:
                element = '0' * int(np.ceil(np.log10(self.size))) + str(element)
                current_frame += element[-int(np.ceil(np.log10(self.size))):]
            
            current_frame += 'BULLET'
            for element in self.bullet:
                element = '0' * int(np.ceil(np.log10(self.size))) + str(element)
                current_frame += element[-int(np.ceil(np.log10(self.size))):]

            for key, values in self.enemies.items():
                current_frame += key
                for value in values:
                    for element in value:
                        element = '0' * int(np.ceil(np.log10(self.size))) + str(element)
                        current_frame += element[-int(np.ceil(np.log10(self.size))):]
            
            current_frame += 'BOMB'
            for element in self.bomb:
                element = '0' * int(np.ceil(np.log10(self.size))) + str(element)
                current_frame += element[-int(np.ceil(np.log10(self.size))):]

            if current_frame not in self.frames:
                self.frames.append(current_frame)

        return self.frames.index(current_frame)

    def step(self, ):

        if sum([sum([enemy[2] for enemy in self.enemies['ENEMY_WEAK']]), 
                sum([enemy[2] for enemy in self.enemies['ENEMY_STRONG']])]) > 0:
            self.enemy_weak_strong_counter += 1

        self.player_counter += 1
        self.player_policy()

        if self.ws_reached_wall:
            self.enemy_fleet_direction = -1 * self.enemy_fleet_direction  # CHANGE DIRECTION
            self.reward += -5  # FOR EACH TIME THE ENEMY FLEET REACH ONE SIDE OF THE GAME BOARD
            for key, values in self.enemies.items():
                if key != 'ENEMY_UFO':
                    for value in values:
                        if value[2] != 0:
                            value[0] += 1
                            value[1] += self.enemy_fleet_direction
            self.ws_reached_wall = False

        else:
            for key, values in self.enemies.items():
                if key != 'ENEMY_UFO':
                    if (np.round(self.level * Agents['ENEMY_WEAK'].speed * self.enemy_weak_strong_counter / self.time_step) > 0):
                        for value in values:
                            if value[2] != 0:
                                value[1] += self.enemy_fleet_direction

        self.ufo_time_counter += 1
        if self.enemies['ENEMY_UFO'][0][2] > 0:
            self.ufo_counter += 1
        
        if self.ufo_time_counter > 3 * self.time_step :
            self.ufo_flag_generator()

        if self.ufo_flag == True:
            self.ufo_policy()
        
        if self.bomb_flag == True: 
            self.bomb_counter += 1
            self.bomb_state()

        if ((np.round(self.level * Agents['ENEMY_WEAK'].speed * self.enemy_weak_strong_counter / self.time_step) > 0) and \
            (sum([sum([enemy[2] for enemy in self.enemies['ENEMY_WEAK']]),sum([enemy[2] for enemy in self.enemies['ENEMY_STRONG']])]) > 0)):
                self.enemy_weak_strong_counter=0

    def player_policy(self, ):
        
        if ((np.round(self.level * Agents['PLAYER'].speed * self.player_counter / self.time_step) > 0) and (self.player[2] !=0) ):
            self.player_action()

        if self.bullet_flag == True: 
            self.bullet_counter += 1
            self.bullet_state()

    def player_action(self, ):
        if self.bullet_flag == False:
            current_action = np.random.choice(self.actions, 1, self.actions_prob)[0]
        else:
            current_action = np.random.choice([action for action in self.actions if action != 'attack'], 1, [prob + self.actions_prob[3]/3 for prob in self.actions_prob[:3]] )[0]

        if current_action == 'stay':
            self.player_counter = 0
        elif current_action == 'left':
            if self.player[1] != 0:
                self.player[1] += -1
            self.player_counter = 0
        elif current_action == 'right':
            if (self.player[1] != (self.size - 6)):  # SIZE OF THE PLAYER IS 5  
                self.player[1] += 1
            self.player_counter = 0
        elif current_action == 'attack':
            self.bullet_flag = True
            self.bullet[:2] = [self.player[0] - 1, self.player[1] + 2]
            self.player_counter = 0
    
    def bullet_state(self, ):
        
        self.bullet_hit()

        if ((np.round(self.level * Agents['BULLET'].speed * self.bullet_counter / self.time_step) > 0) and (self.bullet_flag == True)):
            self.bullet[0] += -1
            self.bullet_counter = 0

    def bullet_hit(self,):

        for key, values in self.enemies.items():
            if self.bullet_flag == True:
                if key != 'ENEMY_UFO':
                    for value in values:
                        if value[2] !=0:
                            if ((self.bullet[0] >= value[0] and self.bullet[0] <= value[0] + 2) and \
                                (self.bullet[1] >= value[1] and self.bullet[1] <= value[1] + 3)): # THE LENGTH OF AN ENEMY (WEAK STRONG FLEET) IS 4
                                
                                value[2] += -1 * self.bullet[2]
                                self.reward += Agents[key].reward
                                self.bullet_flag = False
                                self.bullet[:2] = [-1, -1]
                else:
                    if ((self.enemies['ENEMY_UFO'][0][2] != 0) and (self.ufo_flag == True)):
                        if ((self.bullet[0] >= self.enemies['ENEMY_UFO'][0][0] and self.bullet[0] <= self.enemies['ENEMY_UFO'][0][0] + 2) and\
                            (self.bullet[1] >= self.enemies['ENEMY_UFO'][0][1] and self.bullet[1] <= self.enemies['ENEMY_UFO'][0][1] + 6)): # THE LENGTH OF AN ENEMY FLEET IS 7
                            
                            self.enemies['ENEMY_UFO'][0][2] += -1  * self.bullet[2]
                            self.reward += Agents[key].reward
                            if self.enemies['ENEMY_UFO'][0][2] <= 0:
                                self.ufo_flag = False
                                self.enemies['ENEMY_UFO'][0][:2] = [-1, -1]
                            self.bullet_flag = False
                            self.bullet[:2] = [-1, -1]
    
    def ufo_flag_generator(self,):

        if (self.enemies['ENEMY_UFO'][0][2] > 0 ):
            if np.random.rand(1) < self.ufo_prob:
                self.ufo_flag = True
                self.enemies['ENEMY_UFO'][0][:2]=[0, np.random.randint(self.size - 8)]
                self.ufo_time_counter = 0
            else:
                self.ufo_flag=False
                self.enemies['ENEMY_UFO'][0][:2]=[-1, -1]

        else:
            self.enemies['ENEMY_UFO'][0][:2]=[-1, -1]
            self.ufo_flag = False

    def ufo_policy(self, ):
        
        if ((np.round(self.level * Agents['ENEMY_UFO'].speed * self.ufo_counter / self.time_step) > 0) and (self.enemies['ENEMY_UFO'][0][2] > 0) ):
            self.ufo_action()

    def ufo_action(self, ):
        if self.bomb_flag == False:
            current_action = np.random.choice(self.actions, 1, self.actions_prob)[0]
        else:
            current_action = np.random.choice([action for action in self.actions if action != 'attack'], 1, [prob + self.actions_prob[3]/3 for prob in self.actions_prob[:3]] )[0]

        if current_action == 'stay':
            self.ufo_counter = 0
        elif current_action == 'left':
            if self.enemies['ENEMY_UFO'][0][1] != 0:
                self.enemies['ENEMY_UFO'][0][1] += -1
            self.ufo_counter = 0
        elif current_action == 'right':
            if (self.enemies['ENEMY_UFO'][0][1] != (self.size - 8)):  # SIZE OF THE UFO IS 7  
                self.enemies['ENEMY_UFO'][0][1] += 1
            self.ufo_counter = 0
        elif current_action == 'attack':
            self.bomb_flag = True
            self.bomb = [self.enemies['ENEMY_UFO'][0][0] + 3, self.enemies['ENEMY_UFO'][0][1] + 3, Agents['BOMB'].health]
            self.ufo_counter = 0

    def bomb_state(self, ):
        
        self.bomb_hit()

        if ((np.round(self.level * Agents['BOMB'].speed * self.bomb_counter / self.time_step) > 0) and (self.bomb_flag == True)):
            self.bomb[0] += 1
            self.bomb_counter = 0

    def bomb_hit(self, ):
        if ((self.bomb[0] >= self.player[0] and self.bomb[0] <= self.player[0] + 2) and \
            (self.bomb[1] >= self.player[1] and self.bomb[1] <= self.player[1] + 4)): # THE LENGTH THE PLAYER IS 5
            self.player[2] += -1 * self.bomb[2]
            self.reward += Agents['PLAYER'].reward
            self.bomb[:2] = [-1, -1]
            self.bomb_flag = False

    def position_extermum_xy(self,):
        
        self.ws_max_x = - np.inf
        self.ws_min_x = np.inf
        self.ws_max_y = 0
        ws_max_x = []
        ws_min_x = []
        ws_max_y = []

        for key, values in self.enemies.items():

            if key != 'ENEMY_UFO':
                
                ws_max_x = [value[1] for value in values if value[2] != 0]
                if len(ws_max_x) > 0:
                    ws_max_x = np.max(ws_max_x)

                ws_min_x = [value[1] for value in values if value[2] != 0]
                if len(ws_min_x) > 0:
                    ws_min_x = np.min(ws_min_x)

                ws_max_y = [value[0] for value in values if value[2] != 0]
                if len(ws_max_y) > 0:
                    ws_max_y = np.max(ws_max_y)

        if type(ws_max_x) != list:
            if ws_max_x > self.ws_max_x:
                self.ws_max_x = ws_max_x

        if type(ws_min_x) != list:
            if ws_min_x < self.ws_min_x:
                self.ws_min_x = ws_min_x
        
        if type(ws_max_y) != list:
            if ws_max_y > self.ws_max_y:
                self.ws_max_y = ws_max_y

    def reached_wall(self, ):

        self.position_extermum_xy()

        if self.ws_min_x == 0: 
            self.ws_reached_wall = True

        # 4 IS THE WIDTH OF A WEAK OR STRONG ENEMIES
        if self.ws_max_x == (self.size - 5):
            self.ws_reached_wall = True

        if self.ws_max_y == (self.size - 8):  # FLEET REACH DOWN 8 = (3 ENEMY + 3 PLAYER + 1 BULLET+ 1 INDEX)
            self.game_over = True 

        if self.bullet[0] == 0:
            self.bullet_flag = False
            self.bullet[:2] = [-1, -1]

        if self.bomb[0] == (self.size - 2):
            self.bomb_flag = False
            self.bomb[:2] = [-1, -1]
    
    def enemies_health_check(self, ):
        for key, values in self.enemies.items():
            for value in values:
                if value[2] <= 0:
                    value[:2] = [-1, -1]

    def display(self, ):

        if self.game_over:
            print(f'Game Over\nReward:{self.reward}')

        else:

            row_cnt = 0
            col_cnt = 0
            game_board = []
            for i in range(self.size):

                if i == self.player[0]:
                    row_cnt = 3
                    game_board.append(' ' * (copy.deepcopy(self.player[1]) - 1) + Agents['PLAYER'].frame.split('\n')[0])
                    game_board.append(' ' * (copy.deepcopy(self.player[1]) - 1) + Agents['PLAYER'].frame.split('\n')[1])
                    game_board.append(' ' * (copy.deepcopy(self.player[1]) - 1) + Agents['PLAYER'].frame.split('\n')[2])
                    
                    game_board[i] += ' ' * (self.size - len(game_board[i]))
                    game_board[i+1] += ' ' * (self.size - len(game_board[i+1]))
                    game_board[i+2] += ' ' * (self.size - len(game_board[i+2]))

                if row_cnt > 0:
                    row_cnt -= 1
                    if self.bullet_flag == True:
                        if self.bullet[0] == i:
                            game_board[i].replace(game_board[i][self.bullet[1]], Agents['BULLET'].frame)
                    
                    if self.bomb_flag == True:
                        if self.bomb[0] == i:
                            game_board[i].replace(game_board[i][self.bomb[1]], Agents['BOMB'].frame)                    
                    continue
                
                for key, values in self.enemies.items():

                    col_cnt = 0

                    for value in values:

                        if value[0] == i:

                            if col_cnt == 0:

                                col_cnt += 1

                                if value[2] != 0:
                                    row_cnt = 2

                                    game_board.append(
                                        ' ' * (copy.deepcopy(value[1]) - 1) + Agents[key].frame.split('\n')[0])
                                    game_board.append(
                                        ' ' * (copy.deepcopy(value[1]) - 1) + Agents[key].frame.split('\n')[1])
                                    game_board.append(
                                        ' ' * (copy.deepcopy(value[1]) - 1) + Agents[key].frame.split('\n')[2])

                                else:
                                    game_board.append(
                                        ' ' * (copy.deepcopy(value[1]) + 3))
                                    game_board.append(
                                        ' ' * (copy.deepcopy(value[1]) + 3))
                                    game_board.append(
                                        ' ' * (copy.deepcopy(value[1]) + 3))

                            else:
                                col_cnt += 1
                                if value[2] != 0:
                                    game_board[i] += Agents[key].frame.split('\n')[
                                        0]
                                    game_board[i + 1] += Agents[key].frame.split('\n')[
                                        1]
                                    game_board[i + 2] += Agents[key].frame.split('\n')[
                                        2]
                                else:
                                    game_board[i] += ' ' * 4
                                    game_board[i + 1] += ' ' * 4
                                    game_board[i + 2] += ' ' * 4

                    if col_cnt > 0:

                        game_board[i] += ' ' * (self.size - len(game_board[i]))
                        game_board[i + 1] += ' ' * (self.size - len(game_board[i + 1]))
                        game_board[i + 2] += ' ' * (self.size - len(game_board[i + 2]))

                if row_cnt == 0:
                    if self.bullet[0] == i:
                        game_board.append(' ' * (self.bullet[1] - 1) + Agents['BULLET'].frame)
                        game_board[i] +=  ' ' * (self.size - len(game_board[i]))
                        if self.bomb[0] == i:
                            game_board[i].replace(game_board[i][self.bomb[1]], Agents['BOMB'].frame)    

                    else:
                        if self.bomb[0] == i:
                            game_board.append(' ' * (self.bomb[1] - 1) + Agents['BOMB'].frame)
                            game_board[i] +=  ' ' * (self.size - len(game_board[i]))
                        else:
                            game_board.append(self.game_board_line)
                    
                else: 
                    if self.bullet[0] == i:
                        game_board[i].replace(game_board[i][self.bullet[1]], Agents['BULLET'].frame)
                    
                    if self.bomb[0] == i:
                        game_board[i].replace(game_board[i][self.bomb[1]], Agents['BOMB'].frame)


            current_board_string = ''
            for i in range(self.size):
                current_board_string += ('\r' + game_board[i] + '\n')
            clear_output()
            sys.stdout.write(current_board_string)
            print(f'level:{self.level} reward:{self.reward} health:{self.player[2]}\n'
                  f'enemies_health:{[value[2] for key, values in self.enemies.items() for value in values]}')
            sys.stdout.flush()